"""用于测试随机运行器的示例测试用例"""
import pytest

def test_sample_pass_1():
    """一个通过的测试"""
    assert 1 + 1 == 2

def test_sample_pass_2():
    """另一个通过的测试"""
    assert "hello" == "hello"

def test_sample_fail():
    """一个失败的测试"""
    assert 1 == 2, "这个测试故意失败"

class TestSampleClass:
    """示例测试类"""

    def test_class_pass_1(self):
        assert True

    def test_class_pass_2(self):
        assert [1, 2, 3] == [1, 2, 3]

    def test_class_fail(self):
        assert False, "类中的失败测试"