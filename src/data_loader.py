import json
import os
from typing import Dict, List, Optional, Tuple

from labels import normalize_label
from matrix_ops import normalize_int_matrix, validate_square_matrix


def _print_filter_loaded_line(size: int) -> None:
    """기술문서 예시(✓)와 호환하되, cp949 콘솔에서는 ASCII로 대체한다."""
    primary = f"✓ size_{size}  필터 로드 완료 (Cross, X)"
    fallback = f"[OK] size_{size}  필터 로드 완료 (Cross, X)"
    try:
        print(primary)
    except UnicodeEncodeError:
        print(fallback)


def load_json_file(json_path: str) -> Optional[dict]:
    if not os.path.exists(json_path):
        print(f"오류: data.json 파일을 찾을 수 없습니다. ({json_path})")
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        print(f"오류: JSON 파싱 실패 - {exc}")
    except OSError as exc:
        print(f"오류: 파일 읽기 실패 - {exc}")
    return None


def load_filters(
    raw_filters: dict,
) -> Tuple[Dict[int, Dict[str, List[List[int]]]], List[str]]:
    filters_by_size: Dict[int, Dict[str, List[List[int]]]] = {}
    failures: List[str] = []
    for size_key, value in raw_filters.items():
        if not size_key.startswith("size_"):
            failures.append(f"{size_key}: 필터 키 규칙 오류")
            continue
        try:
            size = int(size_key.split("_")[1])
        except (IndexError, ValueError):
            failures.append(f"{size_key}: 크기 파싱 실패")
            continue

        if not isinstance(value, dict):
            failures.append(f"{size_key}: 필터 구조 오류(dict 필요)")
            continue

        normalized: Dict[str, List[List[int]]] = {}
        for k, matrix in value.items():
            label = normalize_label(k)
            if label is None:
                continue
            if not isinstance(matrix, list):
                failures.append(f"{size_key}/{k}: 행렬 타입 오류")
                continue
            is_valid, reason = validate_square_matrix(matrix, size)
            if not is_valid:
                failures.append(f"{size_key}/{k}: {reason}")
                continue
            normalized[label] = normalize_int_matrix(matrix, size)

        if "Cross" not in normalized or "X" not in normalized:
            failures.append(f"{size_key}: Cross/X 필터가 모두 필요")
            continue

        filters_by_size[size] = normalized
        _print_filter_loaded_line(size)
    return filters_by_size, failures
