"""结果报告器"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import TestResult, RunReport


class ResultReporter:
    """结果报告器，负责生成和管理测试报告"""

    def __init__(self):
        """初始化报告器"""
        self.report: Optional[RunReport] = None

    def init_report(self, seed: int, total_count: int) -> None:
        """初始化报告

        Args:
            seed: 随机种子
            total_count: 总测试数
        """
        self.report = RunReport(seed=seed, total_count=total_count)

    def add_result(self, result: TestResult) -> None:
        """添加测试结果

        Args:
            result: 测试结果
        """
        if self.report is None:
            raise RuntimeError("Report not initialized. Call init_report() first.")
        self.report.add_result(result)

    def finalize(self) -> None:
        """完成报告，设置结束时间"""
        if self.report is None:
            raise RuntimeError("Report not initialized. Call init_report() first.")
        self.report.end_time = datetime.now().isoformat()

    def generate_json(self) -> str:
        """生成JSON报告

        Returns:
            JSON字符串
        """
        if self.report is None:
            raise RuntimeError("Report not initialized. Call init_report() first.")
        return json.dumps(self.report.to_dict(), ensure_ascii=False, indent=2)

    def save_json(self, filepath: str) -> None:
        """保存JSON报告到文件

        Args:
            filepath: 文件路径
        """
        json_str = self.generate_json()
        Path(filepath).write_text(json_str, encoding="utf-8")

    def generate_html(self) -> str:
        """生成HTML报告

        Returns:
            HTML字符串
        """
        if self.report is None:
            raise RuntimeError("Report not initialized. Call init_report() first.")

        summary = self.report.get_summary()

        # 构建结果表格行
        table_rows = []
        for i, result in enumerate(self.report.results, 1):
            status_text = "通过" if result.passed else "失败"
            status_class = "pass" if result.passed else "fail"
            error_cell = ""
            if result.error_msg:
                error_cell = f'<div class="error-msg">{result.error_msg}</div>'
            table_rows.append(f"""
            <tr class="{status_class}">
                <td>{i}</td>
                <td>{result.test_name}</td>
                <td>{status_text}</td>
                <td>{result.duration:.3f}s</td>
                <td>{result.timestamp}</td>
            </tr>
            {error_cell}
            """)

        # 构建错误信息区块
        error_rows = []
        for result in self.report.results:
            if result.error_msg:
                error_rows.append(f"""
            <tr class="error-row">
                <td colspan="5">
                    <div class="error-detail">
                        <strong>{result.test_name}</strong><br>
                        {result.error_msg}
                    </div>
                </td>
            </tr>
            """)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>随机测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .summary-cards {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1;
            min-width: 150px;
            text-align: center;
        }}
        .card h3 {{
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }}
        .card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }}
        .card.seed .value {{ color: #6366f1; }}
        .card.total .value {{ color: #64748b; }}
        .card.passed .value {{ color: #22c55e; }}
        .card.failed .value {{ color: #ef4444; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #475569;
        }}
        tr.pass {{ background: #f0fdf4; }}
        tr.fail {{ background: #fef2f2; }}
        .error-row td {{
            background: #fefce8;
            border-bottom: 1px solid #fef08a;
        }}
        .error-detail {{
            padding: 10px;
            font-family: monospace;
            white-space: pre-wrap;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <h1>随机测试运行报告</h1>

    <div class="summary-cards">
        <div class="card seed">
            <h3>种子</h3>
            <div class="value">{summary['seed']}</div>
        </div>
        <div class="card total">
            <h3>总计</h3>
            <div class="value">{summary['total']}</div>
        </div>
        <div class="card passed">
            <h3>通过</h3>
            <div class="value">{summary['passed']}</div>
        </div>
        <div class="card failed">
            <h3>失败</h3>
            <div class="value">{summary['failed']}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>测试名称</th>
                <th>状态</th>
                <th>耗时</th>
                <th>时间戳</th>
            </tr>
        </thead>
        <tbody>
            {''.join(table_rows)}
            {''.join(error_rows)}
        </tbody>
    </table>
</body>
</html>
"""
        return html

    def save_html(self, filepath: str) -> None:
        """保存HTML报告到文件

        Args:
            filepath: 文件路径
        """
        html_str = self.generate_html()
        Path(filepath).write_text(html_str, encoding="utf-8")

    def get_summary_string(self) -> str:
        """获取摘要字符串

        Returns:
            摘要字符串，格式为: 种子: X\\n总计: X\\n通过: X\\n失败: X\\n通过率: X%
        """
        if self.report is None:
            raise RuntimeError("Report not initialized. Call init_report() first.")

        summary = self.report.get_summary()
        return (
            f"种子: {summary['seed']}\n"
            f"总计: {summary['total']}\n"
            f"通过: {summary['passed']}\n"
            f"失败: {summary['failed']}\n"
            f"通过率: {summary['pass_rate']}%"
        )