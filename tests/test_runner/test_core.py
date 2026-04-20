"""Tests for RunnerCore"""
import pytest
from pathlib import Path
import tempfile
import os

from runner.core import RunnerCore


class TestRunnerCore:
    """Test cases for RunnerCore class"""

    def test_run_with_seed(self):
        """Test running with a specific seed produces expected results"""
        # Use sample_tests.py which has passing tests
        sample_tests = Path(__file__).parent / "sample_tests.py"

        runner = RunnerCore(
            test_spec=str(sample_tests),
            count=5,
            seed=42,
            stop_on_fail=False,
            report_dir="./reports",
            verbose=False
        )

        exit_code = runner.run()

        # All sample tests should pass (only passing ones are selected by chance)
        # But with seed=42, we should get consistent results
        assert exit_code in [0, 1], f"Exit code should be 0 or 1, got {exit_code}"

        # Verify the seed was used
        assert runner.seed == 42

        # Verify 5 runs were completed
        assert runner.reporter.report is not None
        assert runner.reporter.report.total_count == 5
        assert len(runner.reporter.report.results) == 5

    def test_run_with_failure_stop(self):
        """Test that stop_on_fail=True stops execution on first failure"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        # Create runner with stop_on_fail=True and select many tests
        # Use a seed that we know will eventually hit a failing test
        runner = RunnerCore(
            test_spec=str(sample_tests),
            count=100,  # High count to ensure we hit a failure
            seed=42,
            stop_on_fail=True,
            report_dir="./reports",
            verbose=False
        )

        exit_code = runner.run()

        # Should have stopped on first failure (or completed all if all passed)
        assert runner.reporter.report is not None
        assert runner.reporter.report.failed_count <= 1, "Should stop on first failure"

        # If there's a failure, should have exit code 1
        if runner.reporter.report.failed_count > 0:
            assert exit_code == 1
            # Should have stopped early (not all 100 runs)
            assert len(runner.reporter.report.results) < 100

    def test_run_with_failure_continue(self):
        """Test that stop_on_fail=False continues execution on failures"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        runner = RunnerCore(
            test_spec=str(sample_tests),
            count=5,
            seed=123,  # Use a seed that produces failures
            stop_on_fail=False,
            report_dir="./reports",
            verbose=False
        )

        exit_code = runner.run()

        # Should complete all 5 runs regardless of failures
        assert runner.reporter.report is not None
        assert len(runner.reporter.report.results) == 5

        # Exit code should reflect results
        if runner.reporter.report.failed_count > 0:
            assert exit_code == 1
        else:
            assert exit_code == 0

    def test_run_mixed_tests(self):
        """Test running 20 times from sample_tests.py"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        runner = RunnerCore(
            test_spec=str(sample_tests),
            count=20,
            seed=42,
            stop_on_fail=False,
            report_dir="./reports",
            verbose=False
        )

        exit_code = runner.run()

        # Verify total runs
        assert runner.reporter.report is not None
        assert runner.reporter.report.total_count == 20
        assert len(runner.reporter.report.results) == 20

        # Verify counts match
        total = runner.reporter.report.passed_count + runner.reporter.report.failed_count
        assert total == 20

    def test_same_seed_reproducible(self):
        """Test that same seed produces same test sequence"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        # First run
        runner1 = RunnerCore(
            test_spec=str(sample_tests),
            count=5,
            seed=42,
            stop_on_fail=False,
            report_dir="./reports",
            verbose=False
        )
        runner1.run()

        # Second run with same seed
        runner2 = RunnerCore(
            test_spec=str(sample_tests),
            count=5,
            seed=42,
            stop_on_fail=False,
            report_dir="./reports",
            verbose=False
        )
        runner2.run()

        # Verify same test sequence
        results1 = runner1.reporter.report.results
        results2 = runner2.reporter.report.results

        assert len(results1) == len(results2) == 5

        for r1, r2 in zip(results1, results2):
            assert r1.test_name == r2.test_name, f"Test names should match: {r1.test_name} vs {r2.test_name}"
            assert r1.passed == r2.passed, f"Test results should match for {r1.test_name}"

    def test_invalid_test_spec(self):
        """Test that ValueError is raised for nonexistent path"""
        with pytest.raises(ValueError, match="does not exist"):
            RunnerCore(
                test_spec="nonexistent/path/to/tests.py",
                count=5,
                seed=42
            )

    def test_report_generation(self):
        """Test that reports are generated correctly"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            runner = RunnerCore(
                test_spec=str(sample_tests),
                count=3,
                seed=42,
                stop_on_fail=False,
                report_dir=tmpdir,
                verbose=False
            )

            exit_code = runner.run()

            # Check that JSON report was created
            json_report = Path(tmpdir) / "report.json"
            assert json_report.exists(), "JSON report should be created"

            # Check that HTML report was created
            html_report = Path(tmpdir) / "report.html"
            assert html_report.exists(), "HTML report should be created"

            # Verify JSON content
            import json
            with open(json_report, 'r', encoding='utf-8') as f:
                report_data = json.load(f)

            assert 'summary' in report_data
            assert 'results' in report_data
            assert report_data['summary']['seed'] == 42
            assert report_data['summary']['total'] == 3

    def test_verbose_mode(self):
        """Test that verbose mode doesn't break functionality"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        runner = RunnerCore(
            test_spec=str(sample_tests),
            count=2,
            seed=42,
            stop_on_fail=False,
            report_dir="./reports",
            verbose=True
        )

        exit_code = runner.run()

        # Should still work correctly
        assert runner.reporter.report is not None
        assert len(runner.reporter.report.results) == 2

    def test_default_seed_generation(self):
        """Test that seed is auto-generated when None"""
        sample_tests = Path(__file__).parent / "sample_tests.py"

        runner = RunnerCore(
            test_spec=str(sample_tests),
            count=2,
            seed=None,  # Should auto-generate
            stop_on_fail=False,
            report_dir="./reports",
            verbose=False
        )

        # Should have a valid seed
        assert runner.seed is not None
        assert isinstance(runner.seed, int)
        assert runner.seed >= 0