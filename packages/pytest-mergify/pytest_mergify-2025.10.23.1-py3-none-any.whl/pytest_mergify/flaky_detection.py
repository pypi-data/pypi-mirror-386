import dataclasses
import datetime
import os
import typing

import _pytest
import _pytest.main
import _pytest.reports
import requests

from pytest_mergify import utils


@dataclasses.dataclass
class _FlakyDetectionContext:
    budget_ratio: float
    existing_test_names: typing.List[str]
    existing_tests_mean_duration_ms: int
    max_test_execution_count: int
    max_test_name_length: int
    min_budget_duration_ms: int
    min_test_execution_count: int

    @property
    def existing_tests_mean_duration(self) -> datetime.timedelta:
        return datetime.timedelta(milliseconds=self.existing_tests_mean_duration_ms)

    @property
    def min_budget_duration(self) -> datetime.timedelta:
        return datetime.timedelta(milliseconds=self.min_budget_duration_ms)


@dataclasses.dataclass
class _NewTestMetrics:
    "Represents metrics collected for a new test."

    initial_duration: datetime.timedelta = dataclasses.field(
        default_factory=datetime.timedelta
    )
    "Represents the duration of the initial execution of the test."

    # NOTE(remyduthu): We need this flag because we may have processed a test
    # without scheduling retries for it (e.g., because it was too slow).
    is_processed: bool = dataclasses.field(default=False)

    retry_count: int = dataclasses.field(default=0)
    "Represents the number of times the test has been retried so far."

    scheduled_retry_count: int = dataclasses.field(default=0)
    "Represents the number of retries that have been scheduled for this test depending on the budget."

    total_duration: datetime.timedelta = dataclasses.field(
        default_factory=datetime.timedelta
    )
    "Represents the total duration spent executing this test, including retries."

    def add_duration(self, duration: datetime.timedelta) -> None:
        if not self.initial_duration:
            self.initial_duration = duration

        self.retry_count += 1
        self.total_duration += duration


@dataclasses.dataclass
class FlakyDetector:
    token: str
    url: str
    full_repository_name: str

    _context: _FlakyDetectionContext = dataclasses.field(init=False)
    _deadline: typing.Optional[datetime.datetime] = dataclasses.field(
        init=False, default=None
    )
    _new_test_metrics: typing.Dict[str, _NewTestMetrics] = dataclasses.field(
        init=False, default_factory=dict
    )
    _over_length_tests: typing.Set[str] = dataclasses.field(
        init=False, default_factory=set
    )

    def __post_init__(self) -> None:
        self._context = self._fetch_context()

    def _fetch_context(self) -> _FlakyDetectionContext:
        owner, repository_name = utils.split_full_repo_name(
            self.full_repository_name,
        )

        response = requests.get(
            url=f"{self.url}/v1/ci/{owner}/repositories/{repository_name}/flaky-detection-context",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10,
        )

        response.raise_for_status()

        result = _FlakyDetectionContext(**response.json())
        if len(result.existing_test_names) == 0:
            raise RuntimeError(
                f"No existing tests found for '{self.full_repository_name}' repository",
            )

        return result

    def detect_from_report(self, report: _pytest.reports.TestReport) -> bool:
        if report.when != "call":
            return False

        if report.outcome not in ["failed", "passed"]:
            return False

        test = report.nodeid
        if test in self._context.existing_test_names:
            return False

        if len(test) > self._context.max_test_name_length:
            self._over_length_tests.add(test)
            return False

        metrics = self._new_test_metrics.setdefault(report.nodeid, _NewTestMetrics())
        metrics.add_duration(datetime.timedelta(seconds=report.duration))

        return True

    def filter_existing_tests_with_session(self, session: _pytest.main.Session) -> None:
        session_tests = {item.nodeid for item in session.items}
        self._context.existing_test_names = [
            test for test in self._context.existing_test_names if test in session_tests
        ]

    def get_retry_count_for_new_test(self, test: str) -> int:
        metrics = self._new_test_metrics.get(test)
        if not metrics:
            return 0

        budget_per_test = (
            self._get_duration_before_deadline() / self._count_remaining_new_tests()
        )
        result = int(budget_per_test / metrics.initial_duration)
        result = min(result, self._context.max_test_execution_count)

        # NOTE(remyduthu): Count as processed even if it's too slow.
        metrics.is_processed = True

        if result < self._context.min_test_execution_count:
            return 0

        metrics.scheduled_retry_count = result

        return result

    def is_deadline_exceeded(self) -> bool:
        return (
            self._deadline is not None
            and datetime.datetime.now(datetime.timezone.utc) >= self._deadline
        )

    def make_report(self) -> str:
        result = "🐛 Flaky detection"
        if self._over_length_tests:
            result += (
                f"{os.linesep}- Skipped {len(self._over_length_tests)} "
                f"test{'s' if len(self._over_length_tests) > 1 else ''}:"
            )
            for test in self._over_length_tests:
                result += (
                    f"{os.linesep}    • '{test}' has not been tested multiple times because the name of the test "
                    f"exceeds our limit of {self._context.max_test_name_length} characters"
                )

        if not self._new_test_metrics:
            result += f"{os.linesep}- No new tests detected, but we are watching 👀"

            return result

        total_retry_duration_seconds = sum(
            metrics.total_duration.total_seconds()
            for metrics in self._new_test_metrics.values()
        )
        budget_duration_seconds = self._get_budget_duration().total_seconds()
        result += (
            f"{os.linesep}- Used {total_retry_duration_seconds / budget_duration_seconds * 100:.2f} % of the budget "
            f"({total_retry_duration_seconds:.2f} s/{budget_duration_seconds:.2f} s)"
        )

        result += (
            f"{os.linesep}- Active for {len(self._new_test_metrics)} new "
            f"test{'s' if len(self._new_test_metrics) > 1 else ''}:"
        )
        for test, metrics in self._new_test_metrics.items():
            if metrics.scheduled_retry_count == 0:
                result += (
                    f"{os.linesep}    • '{test}' is too slow to be tested at least "
                    f"{self._context.min_test_execution_count} times within the budget"
                )
                continue

            if metrics.retry_count < metrics.scheduled_retry_count:
                result += (
                    f"{os.linesep}    • '{test}' has been tested only {metrics.retry_count} "
                    f"time{'s' if metrics.retry_count > 1 else ''} instead of {metrics.scheduled_retry_count} "
                    f"time{'s' if metrics.scheduled_retry_count > 1 else ''} to avoid exceeding the budget"
                )
                continue

            retry_duration_seconds = metrics.total_duration.total_seconds()
            result += (
                f"{os.linesep}    • '{test}' has been tested {metrics.retry_count} "
                f"time{'s' if metrics.retry_count > 1 else ''} using approx. "
                f"{retry_duration_seconds / budget_duration_seconds * 100:.2f} % of the budget "
                f"({retry_duration_seconds:.2f} s/{budget_duration_seconds:.2f} s)"
            )

        return result

    def set_deadline(self) -> None:
        self._deadline = (
            datetime.datetime.now(datetime.timezone.utc)
            + self._context.existing_tests_mean_duration
            + self._get_budget_duration()
        )

    def _count_remaining_new_tests(self) -> int:
        return sum(
            1 for metrics in self._new_test_metrics.values() if not metrics.is_processed
        )

    def _get_budget_duration(self) -> datetime.timedelta:
        total_duration = self._context.existing_tests_mean_duration * len(
            self._context.existing_test_names
        )

        # NOTE(remyduthu): We want to ensure a minimum duration even for very short test suites.
        return max(
            self._context.budget_ratio * total_duration,
            self._context.min_budget_duration,
        )

    def _get_duration_before_deadline(self) -> datetime.timedelta:
        if not self._deadline:
            return datetime.timedelta()

        return max(
            self._deadline - datetime.datetime.now(datetime.timezone.utc),
            datetime.timedelta(),
        )
