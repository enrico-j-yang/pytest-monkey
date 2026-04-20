"""测试RandomSelector随机选择器"""
import pytest
from runner.selector import RandomSelector


class TestRandomSelector:
    """测试RandomSelector类"""

    def test_create_selector_with_seed(self):
        """测试使用种子创建选择器"""
        selector = RandomSelector(seed=42)
        assert selector.seed == 42

    def test_create_selector_without_seed(self):
        """测试不使用种子创建选择器（自动生成种子）"""
        selector = RandomSelector()
        assert selector.seed is not None
        assert isinstance(selector.seed, int)

    def test_select_returns_correct_count(self):
        """测试select返回正确数量的选择"""
        selector = RandomSelector(seed=42)
        items = ["a", "b", "c", "d", "e"]
        result = selector.select(items, 10)
        assert len(result) == 10
        # 所有选择都应该来自原始列表
        for item in result:
            assert item in items

    def test_same_seed_same_sequence(self):
        """测试相同种子产生相同的选择序列"""
        selector1 = RandomSelector(seed=42)
        selector2 = RandomSelector(seed=42)
        items = ["a", "b", "c", "d", "e"]
        result1 = selector1.select(items, 5)
        result2 = selector2.select(items, 5)
        assert result1 == result2

    def test_different_seed_different_sequence(self):
        """测试不同种子产生不同的选择序列"""
        selector1 = RandomSelector(seed=42)
        selector2 = RandomSelector(seed=123)
        items = ["a", "b", "c", "d", "e"]
        result1 = selector1.select(items, 5)
        result2 = selector2.select(items, 5)
        # 不同种子应该产生不同的结果
        assert result1 != result2

    def test_select_with_single_item(self):
        """测试从单个元素列表中选择"""
        selector = RandomSelector(seed=42)
        items = ["only_one"]
        result = selector.select(items, 10)
        assert len(result) == 10
        # 所有选择都应该是唯一元素
        for item in result:
            assert item == "only_one"