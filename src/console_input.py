from typing import List

from matrix_ops import parse_numeric_row


def read_matrix_from_console(name: str, size: int) -> List[List[int]]:
    print(f"{name} ({size}줄 입력, 공백 구분, 각 칸은 정수)")
    matrix: List[List[int]] = []
    while len(matrix) < size:
        raw = input().strip()
        row = parse_numeric_row(raw, size)
        if row is None:
            print(
                f"입력 형식 오류: 각 줄에 {size}개의 정수를 공백으로 구분해 입력하세요."
            )
            print(f"다시 입력하세요. ({len(matrix) + 1}/{size}번째 줄)")
            continue
        matrix.append(row)
    return matrix
