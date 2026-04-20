"""测试数据结构定义"""
from runner.models import TestResult, RunReport

class TestTestResult:
    """测试TestResult数据结构"""

    def test_create_test_result_pass(self):
        """测试创建通过的TestResult"""
        result = TestResult(
            run_index=1,
            test_name="tests/test_x.py::test_func",
            passed=True,
            duration=0.5,
            error_msg=None,
            timestamp="2026-04-17T10:00:00"
        )
        assert result.run_index == 1
        assert result.passed is True
        assert result.error_msg is None

    def test_create_test_result_fail(self):
        """测试创建失败的TestResult"""
        result = TestResult(
            run_index=2,
            test_name="tests/test_x.py::test_func",
            passed=False,
            duration=1.2,
            error_msg="AssertionError: 1 != 2",
            timestamp="2026-04-17T10:01:00"
        )
        assert result.passed is False
        assert result.error_msg == "AssertionError: 1 != 2"

    def test_test_result_to_dict(self):
        """测试TestResult转换为字典"""
        result = TestResult(
            run_index=1,
            test_name="test_func",
            passed=True,
            duration=0.5,
            error_msg=None,
            timestamp="2026-04-17T10:00:00"
        )
        data = result.to_dict()
        assert data["run_index"] == 1
        assert data["test_name"] == "test_func"
        assert data["passed"] is True

class TestRunReport:
    """测试RunReport数据结构"""

    def test_create_empty_report(self):
        """测试创建空报告"""
        report = RunReport(seed=42, total_count=10)
        assert report.seed == 42
        assert report.total_count == 10
        assert report.results == []
        assert report.passed_count == 0
        assert report.failed_count == 0

    def test_add_result(self):
        """测试添加结果"""
        report = RunReport(seed=42, total_count=10)
        result = TestResult(
            run_index=1,
            test_name="test_func",
            passed=True,
            duration=0.5,
            error_msg=None,
            timestamp="2026-04-17T10:00:00"
        )
        report.add_result(result)
        assert report.passed_count == 1
        assert report.failed_count == 0

    def test_report_summary(self):
        """测试报告摘要"""
        report = RunReport(seed=42, total_count=5)
        for i in range(4):
            report.add_result(TestResult(
                run_index=i+1,
                test_name=f"test_{i}",
                passed=True,
                duration=0.1,
                error_msg=None,
                timestamp="2026-04-17T10:00:00"
            ))
        report.add_result(TestResult(
            run_index=5,
            test_name="test_fail",
            passed=False,
            duration=0.2,
            error_msg="Error",
            timestamp="2026-04-17T10:00:00"
        ))
        summary = report.get_summary()
        assert summary["total"] == 5
        assert summary["passed"] == 4
        assert summary["failed"] == 1
        assert summary["pass_rate"] == 80.0