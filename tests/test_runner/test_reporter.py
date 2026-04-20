"""测试ResultReporter结果报告器"""
import json
from runner.models import TestResult
from runner.reporter import ResultReporter


class TestResultReporter:
    """测试ResultReporter类"""

    def test_create_reporter(self):
        """测试创建报告器 - report is None"""
        reporter = ResultReporter()
        assert reporter.report is None

    def test_init_report(self):
        """测试初始化报告 - seed和total_count设置"""
        reporter = ResultReporter()
        reporter.init_report(seed=42, total_count=10)
        assert reporter.report is not None
        assert reporter.report.seed == 42
        assert reporter.report.total_count == 10

    def test_add_result(self):
        """测试添加结果 - passed_count递增"""
        reporter = ResultReporter()
        reporter.init_report(seed=42, total_count=5)
        result = TestResult(
            run_index=1,
            test_name="test_func",
            passed=True,
            duration=0.5,
            error_msg=None,
            timestamp="2026-04-20T10:00:00"
        )
        reporter.add_result(result)
        assert reporter.report.passed_count == 1
        assert reporter.report.failed_count == 0
        assert len(reporter.report.results) == 1

    def test_generate_json_report(self):
        """测试生成JSON报告 - 验证JSON结构"""
        reporter = ResultReporter()
        reporter.init_report(seed=42, total_count=2)
        reporter.add_result(TestResult(
            run_index=1,
            test_name="test_pass",
            passed=True,
            duration=0.1,
            error_msg=None,
            timestamp="2026-04-20T10:00:00"
        ))
        reporter.add_result(TestResult(
            run_index=2,
            test_name="test_fail",
            passed=False,
            duration=0.2,
            error_msg="AssertionError",
            timestamp="2026-04-20T10:00:01"
        ))
        reporter.finalize()
        json_str = reporter.generate_json()
        data = json.loads(json_str)
        assert "summary" in data
        assert "results" in data
        assert data["summary"]["seed"] == 42
        assert data["summary"]["total"] == 2
        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1
        assert len(data["results"]) == 2

    def test_save_json_report(self, tmp_path):
        """测试保存JSON报告 - 文件存在，内容正确"""
        reporter = ResultReporter()
        reporter.init_report(seed=42, total_count=1)
        reporter.add_result(TestResult(
            run_index=1,
            test_name="test_func",
            passed=True,
            duration=0.1,
            error_msg=None,
            timestamp="2026-04-20T10:00:00"
        ))
        reporter.finalize()
        json_file = tmp_path / "report.json"
        reporter.save_json(str(json_file))
        assert json_file.exists()
        content = json_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["summary"]["seed"] == 42
        assert data["results"][0]["test_name"] == "test_func"

    def test_save_html_report(self, tmp_path):
        """测试保存HTML报告 - 文件存在，包含seed和test_name"""
        reporter = ResultReporter()
        reporter.init_report(seed=42, total_count=1)
        reporter.add_result(TestResult(
            run_index=1,
            test_name="test_sample",
            passed=True,
            duration=0.1,
            error_msg=None,
            timestamp="2026-04-20T10:00:00"
        ))
        reporter.finalize()
        html_file = tmp_path / "report.html"
        reporter.save_html(str(html_file))
        assert html_file.exists()
        content = html_file.read_text(encoding="utf-8")
        assert "42" in content  # seed
        assert "test_sample" in content  # test_name
        assert "<!DOCTYPE html>" in content or "<html" in content

    def test_get_summary_string(self):
        """测试获取摘要字符串 - 包含"种子: 42" """
        reporter = ResultReporter()
        reporter.init_report(seed=42, total_count=5)
        reporter.add_result(TestResult(
            run_index=1,
            test_name="test_1",
            passed=True,
            duration=0.1,
            error_msg=None,
            timestamp="2026-04-20T10:00:00"
        ))
        reporter.add_result(TestResult(
            run_index=2,
            test_name="test_2",
            passed=False,
            duration=0.2,
            error_msg="Error",
            timestamp="2026-04-20T10:00:01"
        ))
        reporter.finalize()
        summary = reporter.get_summary_string()
        assert "种子: 42" in summary
        assert "总计: 2" in summary
        assert "通过: 1" in summary
        assert "失败: 1" in summary
        assert "通过率: 50.0%" in summary