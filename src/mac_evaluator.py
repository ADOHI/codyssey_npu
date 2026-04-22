import time
from typing import List

from config import EPSILON, PERF_REPEAT
from matrix_ops import mac_score


class MacEvaluator:
    """MAC 점수·판정·벤치마크를 한 곳에서 다룬다."""

    def __init__(
        self,
        epsilon: float = EPSILON,
        perf_repeat: int = PERF_REPEAT,
    ) -> None:
        self.epsilon = epsilon
        self.perf_repeat = perf_repeat

    def score(self, pattern: List[List[int]], filt: List[List[int]]) -> int:
        return mac_score(pattern, filt)

    def decide_label(self, score_cross: int, score_x: int) -> str:
        if abs(score_cross - score_x) < self.epsilon:
            return "UNDECIDED"
        return "Cross" if score_cross > score_x else "X"

    def decide_ab(self, score_a: int, score_b: int) -> str:
        """모드 1: 필터 A·B 점수만 비교한다. 'UNDECIDED' | 'A' | 'B'."""
        if abs(score_a - score_b) < self.epsilon:
            return "UNDECIDED"
        return "A" if score_a > score_b else "B"

    def measure_runtime_ms(
        self, pattern: List[List[int]], filt: List[List[int]]
    ) -> float:
        start = time.perf_counter()
        for _ in range(self.perf_repeat):
            mac_score(pattern, filt)
        end = time.perf_counter()
        return ((end - start) * 1000.0) / self.perf_repeat
