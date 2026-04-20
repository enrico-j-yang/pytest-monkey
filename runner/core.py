"""RunnerCore - integrates all components for random test execution"""
import random
from pathlib import Path
from typing import Optional, List

from tqdm import tqdm

from .models import TestResult
from .collector import TestCollector
from .selector import RandomSelector
from .executor import TestExecutor
from .reporter import ResultReporter


class RunnerCore:
    """Core runner that integrates all components for random test execution.

    This class orchestrates:
    - TestCollector: collects pytest test items
    - RandomSelector: selects random test sequence
    - TestExecutor: executes each test
    - ResultReporter: tracks results and generates reports
    """

    def __init__(
        self,
        test_spec: str,
        count: int,
        seed: Optional[int] = None,
        continue_on_fail: bool = False,
        report_dir: str = "./reports",
        verbose: bool = False
    ):
        """Initialize the runner core.

        Args:
            test_spec: Test specification (file/class/method/directory path)
            count: Number of test runs to execute (required)
            seed: Random seed for reproducibility. If None, auto-generates 10-digit number.
            continue_on_fail: Whether to continue on failure (default: stop on first failure)
            report_dir: Directory to save reports
            verbose: Whether to print verbose output

        Raises:
            ValueError: If test_spec path does not exist
        """
        self.test_spec = test_spec
        self.count = count
        self.continue_on_fail = continue_on_fail
        self.report_dir = Path(report_dir)
        self.verbose = verbose

        # Generate or use provided seed (10-digit number if auto-generated)
        if seed is None:
            self.seed = random.randint(1000000000, 9999999999)
        else:
            self.seed = seed

        # Initialize components
        self.collector = TestCollector()
        self.selector = RandomSelector(seed=self.seed)
        self.executor = TestExecutor()
        self.reporter = ResultReporter()

        # Validate test spec path exists
        self._validate_test_spec()

        # Collected test items
        self._items: Optional[List] = None

    def _validate_test_spec(self) -> None:
        """Validate that the test spec path exists.

        Raises:
            ValueError: If path does not exist
        """
        # Extract the file/directory path from the test spec
        path_part = self.test_spec.split("::")[0]
        full_path = Path(path_part)

        if not full_path.exists():
            raise ValueError(f"Path does not exist: {path_part}")

    def _collect_tests(self) -> List:
        """Collect tests from test spec.

        Returns:
            List of pytest.Item objects
        """
        if self._items is None:
            self._items = self.collector.collect(self.test_spec)
        return self._items

    def run(self) -> int:
        """Execute the random test run.

        Returns:
            Exit code: 0 if all tests passed, 1 if any failure
        """
        # Collect tests
        items = self._collect_tests()

        # Initialize report
        self.reporter.init_report(seed=self.seed, total_count=self.count)

        # Print seed at start for reproducibility
        print(f"Random seed: {self.seed}")

        # Select random test sequence
        selected_tests = self.selector.select(items, self.count)

        # Ensure report directory exists
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # Execute tests with progress bar
        disable_progress = self.verbose  # Disable tqdm if verbose for cleaner output

        with tqdm(total=self.count, desc="Running tests", disable=disable_progress) as pbar:
            for run_index, item in enumerate(selected_tests, start=1):
                # Execute test
                result: TestResult = self.executor.execute(item)
                result.run_index = run_index  # Set the run index

                # Add result to reporter
                self.reporter.add_result(result)

                # Update progress bar
                status = "PASS" if result.passed else "FAIL"
                pbar.set_postfix_str(f"{status}: {item.nodeid[:50]}")
                pbar.update(1)

                # Print verbose output if enabled
                if self.verbose:
                    duration = f"{result.duration:.3f}s"
                    print(f"[{run_index}/{self.count}] {status} - {result.test_name} ({duration})")
                    if result.error_msg:
                        print(f"    Error: {result.error_msg[:200]}")

                # Stop on failure unless continue_on_fail is set
                if not self.continue_on_fail and not result.passed:
                    if self.verbose:
                        print(f"\nStopping on first failure (run {run_index}/{self.count})")
                    break

        # Finalize report
        self.reporter.finalize()

        # Save reports
        json_path = self.report_dir / "report.json"
        html_path = self.report_dir / "report.html"

        self.reporter.save_json(str(json_path))
        self.reporter.save_html(str(html_path))

        # Print summary
        print(self.reporter.get_summary_string())

        # Return exit code
        if self.reporter.report.failed_count > 0:
            return 1
        return 0