"""随机选择器模块"""
import random
from typing import List, TypeVar, Optional

T = TypeVar('T')


class RandomSelector:
    """随机选择器，支持可重复选择"""

    def __init__(self, seed: Optional[int] = None):
        """
        初始化随机选择器

        Args:
            seed: 随机种子，如果为None则自动生成10位数字
        """
        if seed is None:
            # 自动生成10位数字种子
            self.seed = random.randint(1000000000, 9999999999)
        else:
            self.seed = seed
        self.rng = random.Random(self.seed)

    def select(self, items: List[T], count: int) -> List[T]:
        """
        从列表中随机选择指定数量的元素（可重复）

        Args:
            items: 待选择的元素列表
            count: 选择数量

        Returns:
            随机选择的元素列表
        """
        if not items:
            raise ValueError("items list cannot be empty")

        return [self.rng.choice(items) for _ in range(count)]