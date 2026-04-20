"""Tests for TestCollector"""
import pytest
from runner.collector import TestCollector


class TestTestCollector:
    """Test cases for TestCollector class"""

    @pytest.fixture
    def collector(self):
        """Create a TestCollector instance"""
        return TestCollector()

    @pytest.fixture
    def sample_tests_path(self):
        """Path to sample_tests.py"""
        return "tests/test_runner/sample_tests.py"

    def test_collect_from_file(self, collector, sample_tests_path):
        """Test collecting all test items from a file"""
        items = collector.collect(sample_tests_path)

        # Should collect 6 items: 3 function tests + 3 class tests
        assert len(items) == 6

        # All items should be pytest.Item instances
        for item in items:
            assert hasattr(item, 'nodeid')
            assert hasattr(item, 'name')

    def test_collect_from_class(self, collector, sample_tests_path):
        """Test collecting test items from a class"""
        test_spec = f"{sample_tests_path}::TestSampleClass"
        items = collector.collect(test_spec)

        # Should collect 3 items from TestSampleClass
        assert len(items) == 3

        # All items should be from TestSampleClass
        for item in items:
            assert "TestSampleClass" in item.nodeid

    def test_collect_from_method(self, collector, sample_tests_path):
        """Test collecting a single test method"""
        test_spec = f"{sample_tests_path}::TestSampleClass::test_class_pass_1"
        items = collector.collect(test_spec)

        # Should collect exactly 1 item
        assert len(items) == 1

        # The item should be the specific test method
        assert "test_class_pass_1" in items[0].nodeid

    def test_collect_from_nonexistent_path(self, collector):
        """Test that collecting from a nonexistent path raises ValueError"""
        with pytest.raises(ValueError, match="Path does not exist"):
            collector.collect("tests/nonexistent_test.py")

    def test_collect_from_nonexistent_class(self, collector, sample_tests_path):
        """Test that collecting from a nonexistent class raises ValueError"""
        test_spec = f"{sample_tests_path}::NonExistentClass"
        with pytest.raises(ValueError, match="No tests found"):
            collector.collect(test_spec)

    def test_collect_from_nonexistent_method(self, collector, sample_tests_path):
        """Test that collecting from a nonexistent method raises ValueError"""
        test_spec = f"{sample_tests_path}::TestSampleClass::nonexistent_method"
        with pytest.raises(ValueError, match="No tests found"):
            collector.collect(test_spec)

    def test_get_item_names(self, collector, sample_tests_path):
        """Test getting test names (nodeids) from collected items"""
        items = collector.collect(sample_tests_path)
        names = collector.get_item_names(items)

        # Should return list of 6 nodeids
        assert len(names) == 6
        assert isinstance(names, list)

        # All names should be strings
        for name in names:
            assert isinstance(name, str)
            assert "tests/test_runner/sample_tests.py" in name

    def test_get_item_names_function_tests(self, collector, sample_tests_path):
        """Test that function test names are correct"""
        items = collector.collect(sample_tests_path)
        names = collector.get_item_names(items)

        # Check function test names
        function_tests = [n for n in names if "::TestSampleClass" not in n]
        assert len(function_tests) == 3

        # Each function test should be in the format: path::test_name
        for name in function_tests:
            assert "tests/test_runner/sample_tests.py::" in name
            assert "test_sample" in name

    def test_get_item_names_class_tests(self, collector, sample_tests_path):
        """Test that class test names are correct"""
        items = collector.collect(sample_tests_path)
        names = collector.get_item_names(items)

        # Check class test names
        class_tests = [n for n in names if "TestSampleClass" in n]
        assert len(class_tests) == 3

        # Each class test should be in the format: path::Class::method
        for name in class_tests:
            assert "TestSampleClass::test_class" in name

    def test_validate_path_exists(self, collector, sample_tests_path):
        """Test _validate_path with existing path"""
        # Should not raise any exception
        collector._validate_path(sample_tests_path)  # pylint: disable=protected-access

    def test_validate_path_not_exists(self, collector):
        """Test _validate_path with non-existing path"""
        with pytest.raises(ValueError, match="Path does not exist"):
            collector._validate_path("tests/nonexistent_test.py")  # pylint: disable=protected-access

    def test_collect_from_directory(self, collector):
        """Test collecting all tests from a directory"""
        items = collector.collect("tests/test_runner/")

        # Should collect at least the sample tests (6 items)
        # plus any other tests in the directory
        assert len(items) >= 6

        # All items should be pytest.Item instances
        for item in items:
            assert hasattr(item, 'nodeid')


class TestTestCollectorEdgeCases:
    """Edge case tests for TestCollector"""

    @pytest.fixture
    def collector(self):
        """Create a TestCollector instance"""
        return TestCollector()

    def test_collect_empty_items(self, collector):
        """Test get_item_names with empty list"""
        names = collector.get_item_names([])
        assert names == []

    def test_collect_function_test_directly(self, collector):
        """Test collecting a specific function test"""
        test_spec = "tests/test_runner/sample_tests.py::test_sample_pass_1"
        items = collector.collect(test_spec)

        assert len(items) == 1
        assert "test_sample_pass_1" in items[0].nodeid