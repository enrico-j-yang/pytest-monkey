"""Pytest plugin for random test runner.

This plugin provides a --random-runner option to run tests in random order
multiple times using RunnerCore.
"""
import pytest
from runner import RunnerCore


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add random runner command line options."""
    group = parser.getgroup("random-runner", "Random test runner options")
    group.addoption(
        "--random-runner",
        action="store_true",
        default=False,
        help="Enable random test runner mode"
    )
    group.addoption(
        "--random-count",
        type=int,
        default=None,
        help="Number of test runs to execute (required when --random-runner is enabled)"
    )
    group.addoption(
        "--random-seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: auto-generated 10-digit number)"
    )
    group.addoption(
        "--random-continue-on-fail",
        action="store_true",
        default=False,
        help="Continue execution on test failure (default: stop on first failure)"
    )
    group.addoption(
        "--random-no-capture",
        action="store_true",
        default=False,
        help="Disable output capture (show stdout/stderr during test execution)"
    )


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list
) -> None:
    """Modify test collection to run random tests when enabled."""
    if not config.getoption("--random-runner"):
        return

    # Get options
    random_count = config.getoption("--random-count")
    if random_count is None:
        raise pytest.UsageError("--random-count is required when using --random-runner")

    random_seed = config.getoption("--random-seed")
    continue_on_fail = config.getoption("--random-continue-on-fail")
    no_capture = config.getoption("--random-no-capture")

    # Get test spec from collected items
    # Use the first item's nodeid to get the test spec
    if items:
        # Get the file path from the first item
        first_item = items[0]
        # nodeid format: tests/test_runner/sample_tests.py::test_sample_pass_1
        test_spec = first_item.nodeid
    else:
        # No items collected, use the base directory
        test_spec = str(session.config.invocation_params.dir)

    # Create and run RunnerCore
    runner = RunnerCore(
        test_spec=test_spec,
        count=random_count,
        seed=random_seed,
        continue_on_fail=continue_on_fail,
        report_dir="./reports",
        verbose=config.getoption("-v") or config.getoption("--verbose"),
        capture_output=not no_capture
    )

    # Execute the runner
    exit_code = runner.run()

    # Clear items to prevent pytest from running them again
    items.clear()

    # Store exit code in config for later use
    config._random_runner_exit_code = exit_code


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int
) -> None:
    """Set the final exit status after session ends."""
    config = session.config
    if hasattr(config, "_random_runner_exit_code"):
        # Use the exit code from our random runner
        session.exitstatus = config._random_runner_exit_code