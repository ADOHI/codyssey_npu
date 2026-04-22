import math
import time
from typing import Any, Callable, List, Optional, Tuple


def _cell_to_int(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("bool")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return int(value)
        raise ValueError("non_integer_float")
    raise TypeError("not_numeric")


def parse_numeric_row(row_text: str, expected_size: int) -> Optional[List[int]]:
    parts = row_text.strip().split()
    if len(parts) != expected_size:
        return None
    row: List[int] = []
    for token in parts:
        try:
            x = float(token)
        except ValueError:
            return None
        if not math.isfinite(x) or not x.is_integer():
            return None
        row.append(int(x))
    return row


def validate_square_matrix(matrix: Any, size: int) -> Tuple[bool, str]:
    if not isinstance(matrix, list) or len(matrix) != size:
        return False, f"행 개수 불일치(기대: {size})"
    for row in matrix:
        if not isinstance(row, list) or len(row) != size:
            return False, f"열 개수 불일치(기대: {size})"
        for value in row:
            if isinstance(value, bool):
                return False, "bool 값은 허용되지 않음"
            if isinstance(value, int):
                continue
            if isinstance(value, float):
                if math.isfinite(value) and value.is_integer():
                    continue
                return False, "셀은 정수 값만 허용합니다"
            return False, "숫자 이외 값 포함"
    return True, ""


def normalize_int_matrix(matrix: List[list], size: int) -> List[List[int]]:
    """검증된 2차원 배열을 int 행렬로 변환한다."""
    out: List[List[int]] = []
    for row in matrix:
        out.append([_cell_to_int(v) for v in row])
    return out


def mac_score(pattern: List[List[int]], filt: List[List[int]]) -> int:
    total = 0
    n = len(pattern)
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filt[i][j]
    return total


def mac_score_row_cached(pattern: List[List[int]], filt: List[List[int]]) -> int:
    """행 참조를 한 번만 잡고 같은 행끼리 MAC (2중 인덱스 완화)."""
    total = 0
    n = len(pattern)
    for i in range(n):
        row_p = pattern[i]
        row_f = filt[i]
        for j in range(n):
            total += row_p[j] * row_f[j]
    return total


def flatten_matrix(matrix: List[List[int]]) -> List[int]:
    """n×n 행렬을 행 우선(row-major)으로 길이 n² 1차원 리스트로 만든다."""
    n = len(matrix)
    out: List[int] = []
    for i in range(n):
        out.extend(matrix[i])
    return out


def mac_score_flat(flat_p: List[int], flat_f: List[int]) -> int:
    """이미 flatten된 두 벡터의 위치별 곱 누적."""
    total = 0
    for k in range(len(flat_p)):
        total += flat_p[k] * flat_f[k]
    return total


def mac_score_flat_from_2d(pattern: List[List[int]], filt: List[List[int]]) -> int:
    """2D 입력을 매번 flatten한 뒤 1D 루프로 MAC (변환 비용 포함)."""
    return mac_score_flat(flatten_matrix(pattern), flatten_matrix(filt))


def benchmark_mac_variants_ms(
    pattern: List[List[int]],
    filt: List[List[int]],
    repeat: int,
) -> Tuple[float, float, float]:
    """(기본 mac_score, 행 캐시, 1D MAC) 각 repeat회 평균 ms.

    1D MAC 측정: flatten은 타이머 밖에서 1회만 수행하고, 반복 구간에는
    mac_score_flat(선행된 1차원 벡터)만 실행한다.
    """

    def avg_ms(fn: Callable[[], int]) -> float:
        t0 = time.perf_counter()
        for _ in range(repeat):
            fn()
        return ((time.perf_counter() - t0) * 1000.0) / repeat

    base = avg_ms(lambda: mac_score(pattern, filt))
    row_c = avg_ms(lambda: mac_score_row_cached(pattern, filt))

    flat_p = flatten_matrix(pattern)
    flat_f = flatten_matrix(filt)
    flat_mac = avg_ms(lambda: mac_score_flat(flat_p, flat_f))
    return base, row_c, flat_mac


def generate_cross_pattern(size: int) -> List[List[int]]:
    center = size // 2
    out: List[List[int]] = []
    for i in range(size):
        row: List[int] = []
        for j in range(size):
            row.append(1 if (i == center or j == center) else 0)
        out.append(row)
    return out


def generate_x_pattern(size: int) -> List[List[int]]:
    out: List[List[int]] = []
    for i in range(size):
        row: List[int] = []
        for j in range(size):
            row.append(1 if (i == j or i + j == size - 1) else 0)
        out.append(row)
    return out
