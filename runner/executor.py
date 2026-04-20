"""TestExecutor - executes pytest test items and returns results"""
import pytest
import sys
from datetime import datetime
from io import StringIO
from typing import Optional

from .models import TestResult


class _ExecutionPlugin:
    """Internal plugin to capture test execution results"""

    def __init__(self):
        self.result: Optional[TestResult] = None

    def pytest_runtest_logreport(self, report):
        """Capture test result from the call phase"""
        if report.when == 'call':
            passed = report.passed
            error_msg: Optional[str] = None
            if report.failed and report.longrepr:
                error_msg = str(report.longrepr)

            self.result = TestResult(
                run_index=0,
                test_name=report.nodeid,
                passed=passed,
                duration=report.duration,
                error_msg=error_msg,
                timestamp=datetime.now().isoformat()
            )


class TestExecutor:
    """Execute pytest test items and return TestResult objects"""

    def __init__(self, capture_output: bool = True):
        """Initialize executor.

        Args:
            capture_output: Whether to capture stdout/stderr during test execution.
                           Set False for -s mode (show output).
        """
        self.capture_output = capture_output

    def execute(self, item: pytest.Item) -> TestResult:
        """
        Execute a single pytest test item.

        Uses pytest's runtestprotocol mechanism internally by running
        pytest.main with the item's nodeid and capturing the result.

        Args:
            item: pytest.Item to execute

        Returns:
            TestResult with execution details
        """
        # Record start time
        start_time = datetime.now()

        # Create plugin to capture result
        plugin = _ExecutionPlugin()

        # Suppress output only if capture_output is True
        if self.capture_output:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()

        try:
            # Run the test using pytest.main with the item's nodeid
            # This ensures proper pytest session context for execution
            pytest_args = ['-v', '--tb=short', item.nodeid]
            pytest.main(
                pytest_args,
                plugins=[plugin]
            )
        finally:
            # Restore stdout/stderr only if we captured them
            if self.capture_output:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        # Return the captured result
        if plugin.result:
            return plugin.result

        # Fallback: create a result if plugin didn't capture one
        # This shouldn't happen normally, but provides safety
        return TestResult(
            run_index=0,
            test_name=item.nodeid,
            passed=False,
            duration=0.0,
            error_msg="Failed to capture test result",
            timestamp=start_time.isoformat()
        )