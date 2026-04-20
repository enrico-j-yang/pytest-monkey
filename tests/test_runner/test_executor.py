"""Tests for TestExecutor"""
import pytest
from runner.collector import TestCollector
from runner.executor import TestExecutor
from runner.models import TestResult


class TestTestExecutor:
    """Test cases for TestExecutor class"""

    @pytest.fixture
    def collector(self):
        """Create a TestCollector instance"""
        return TestCollector()

    @pytest.fixture
    def executor(self):
        """Create a TestExecutor instance"""
        return TestExecutor()

    @pytest.fixture
    def sample_tests_path(self):
        """Path to sample_tests.py"""
        return "tests/test_runner/sample_tests.py"

    def test_execute_passing_test(self, collector, executor, sample_tests_path):
        """Test executing a passing test"""
        # Collect the passing test
        test_spec = f"{sample_tests_path}::test_sample_pass_1"
        items = collector.collect(test_spec)

        assert len(items) == 1
        item = items[0]

        # Execute the test
        result = executor.execute(item)

        # Verify result
        assert isinstance(result, TestResult)
        assert result.passed is True
        assert result.run_index == 0
        assert result.error_msg is None
        assert result.duration > 0
        assert result.timestamp is not None

    def test_execute_failing_test(self, collector, executor, sample_tests_path):
        """Test executing a failing test"""
        # Collect the failing test
        test_spec = f"{sample_tests_path}::test_sample_fail"
        items = collector.collect(test_spec)

        assert len(items) == 1
        item = items[0]

        # Execute the test
        result = executor.execute(item)

        # Verify result
        assert isinstance(result, TestResult)
        assert result.passed is False
        assert result.run_index == 0
        assert result.error_msg is not None
        assert "AssertionError" in result.error_msg
        assert result.duration > 0
        assert result.timestamp is not None

    def test_execute_class_test(self, collector, executor, sample_tests_path):
        """Test executing a class test method"""
        # Collect the class test
        test_spec = f"{sample_tests_path}::TestSampleClass::test_class_pass_1"
        items = collector.collect(test_spec)

        assert len(items) == 1
        item = items[0]

        # Execute the test
        result = executor.execute(item)

        # Verify result
        assert isinstance(result, TestResult)
        assert result.passed is True
        assert result.run_index == 0
        assert result.error_msg is None
        assert result.duration > 0
        assert result.timestamp is not None

    def test_result_has_correct_test_name(self, collector, executor, sample_tests_path):
        """Test that result contains the correct test nodeid"""
        # Collect a specific test
        test_spec = f"{sample_tests_path}::test_sample_pass_1"
        items = collector.collect(test_spec)

        assert len(items) == 1
        item = items[0]

        # Execute the test
        result = executor.execute(item)

        # Verify test_name is the nodeid
        assert result.test_name == item.nodeid
        assert "test_sample_pass_1" in result.test_name