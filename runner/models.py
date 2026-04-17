"""数据结构定义"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class TestResult:
    """单个测试执行结果"""
    run_index: int
    test_name: str
    passed: bool
    duration: float
    error_msg: Optional[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "run_index": self.run_index,
            "test_name": self.test_name,
            "passed": self.passed,
            "duration": self.duration,
            "error_msg": self.error_msg,
            "timestamp": self.timestamp,
        }

@dataclass
class RunReport:
    """运行报告"""
    seed: int
    total_count: int
    results: List[TestResult] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None

    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.results.append(result)
        if result.passed:
            self.passed_count += 1
        else:
            self.failed_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要统计"""
        total = len(self.results)
        pass_rate = (self.passed_count / total * 100) if total > 0 else 0
        return {
            "seed": self.seed,
            "total": total,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "pass_rate": round(pass_rate, 2),
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results],
        }