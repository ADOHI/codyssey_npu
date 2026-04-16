import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


EPSILON = 1e-9
PERF_REPEAT = 10
STANDARD_LABELS = ("Cross", "X")


@dataclass
class CaseResult:
    case_id: str
    predicted: str
    expected: str
    cross_score: float
    x_score: float
    passed: bool
    reason: str = ""


def normalize_label(raw: str) -> Optional[str]:
    """외부 라벨을 내부 표준 라벨(Cross/X)로 정규화한다."""
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value in ("cross", "+", "plus"):
        return "Cross"
    if value in ("x", "ex"):
        return "X"
    return None


def parse_numeric_row(row_text: str, expected_size: int) -> Optional[List[float]]:
    parts = row_text.strip().split()
    if len(parts) != expected_size:
        return None
    row: List[float] = []
    for token in parts:
        try:
            row.append(float(token))
        except ValueError:
            return None
    return row


def read_matrix_from_console(name: str, size: int) -> List[List[float]]:
    print(f"{name} ({size}줄 입력, 공백 구분)")
    matrix: List[List[float]] = []
    while len(matrix) < size:
        raw = input().strip()
        row = parse_numeric_row(raw, size)
        if row is None:
            print(
                f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요."
            )
            print(f"다시 입력하세요. ({len(matrix) + 1}/{size}번째 줄)")
            continue
        matrix.append(row)
    return matrix


def validate_square_matrix(matrix: List[List[float]], size: int) -> Tuple[bool, str]:
    if not isinstance(matrix, list) or len(matrix) != size:
        return False, f"행 개수 불일치(기대: {size})"
    for row in matrix:
        if not isinstance(row, list) or len(row) != size:
            return False, f"열 개수 불일치(기대: {size})"
        for value in row:
            if not isinstance(value, (int, float)):
                return False, "숫자 이외 값 포함"
    return True, ""


def mac_score(pattern: List[List[float]], filt: List[List[float]]) -> float:
    total = 0.0
    n = len(pattern)
    for i in range(n):
        for j in range(n):
            total += pattern[i][j] * filt[i][j]
    return total


def decide_label(score_cross: float, score_x: float, epsilon: float = EPSILON) -> str:
    if abs(score_cross - score_x) < epsilon:
        return "UNDECIDED"
    return "Cross" if score_cross > score_x else "X"


def measure_mac_runtime_ms(
    pattern: List[List[float]], filt: List[List[float]], repeat: int = PERF_REPEAT
) -> float:
    start = time.perf_counter()
    for _ in range(repeat):
        mac_score(pattern, filt)
    end = time.perf_counter()
    return ((end - start) * 1000.0) / repeat


def generate_cross_pattern(size: int) -> List[List[float]]:
    center = size // 2
    out: List[List[float]] = []
    for i in range(size):
        row: List[float] = []
        for j in range(size):
            row.append(1.0 if (i == center or j == center) else 0.0)
        out.append(row)
    return out


def generate_x_pattern(size: int) -> List[List[float]]:
    out: List[List[float]] = []
    for i in range(size):
        row: List[float] = []
        for j in range(size):
            row.append(1.0 if (i == j or i + j == size - 1) else 0.0)
        out.append(row)
    return out


def performance_analysis(filters_by_size: Dict[int, Dict[str, List[List[float]]]]) -> None:
    print("\n#---------------------------------------")
    print(f"# [3] 성능 분석 (평균/{PERF_REPEAT}회)")
    print("#---------------------------------------")
    print("크기       평균 시간(ms)    연산 횟수")
    print("-------------------------------------")
    for size in (3, 5, 13, 25):
        filt = None
        pattern = None
        if size in filters_by_size:
            filt = filters_by_size[size].get("Cross")
        if filt is None:
            filt = generate_cross_pattern(size)
        pattern = generate_x_pattern(size)
        avg_ms = measure_mac_runtime_ms(pattern, filt)
        print(f"{size}x{size:<4} {avg_ms:>12.6f} {size * size:>12}")


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


def extract_size_from_key(key: str) -> Optional[int]:
    # size_13_2 -> 13
    parts = key.split("_")
    if len(parts) < 3 or parts[0] != "size":
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def load_filters(raw_filters: dict) -> Tuple[Dict[int, Dict[str, List[List[float]]]], List[str]]:
    filters_by_size: Dict[int, Dict[str, List[List[float]]]] = {}
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

        normalized: Dict[str, List[List[float]]] = {}
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
            normalized[label] = [[float(v) for v in row] for row in matrix]

        if "Cross" not in normalized or "X" not in normalized:
            failures.append(f"{size_key}: Cross/X 필터가 모두 필요")
            continue

        filters_by_size[size] = normalized
        print(f"[OK] size_{size} 필터 로드 완료 (Cross, X)")
    return filters_by_size, failures


def analyze_patterns(
    patterns: dict, filters_by_size: Dict[int, Dict[str, List[List[float]]]]
) -> Tuple[List[CaseResult], List[str]]:
    results: List[CaseResult] = []
    load_failures: List[str] = []

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    for case_id, payload in patterns.items():
        print(f"\n--- {case_id} ---")
        if not isinstance(payload, dict):
            load_failures.append(f"{case_id}: 패턴 구조 오류(dict 필요)")
            print("FAIL | 사유: 패턴 구조 오류")
            continue

        size = extract_size_from_key(case_id)
        if size is None:
            load_failures.append(f"{case_id}: 키 규칙 오류(size_N_idx 필요)")
            print("FAIL | 사유: 키 규칙 오류")
            continue

        if size not in filters_by_size:
            load_failures.append(f"{case_id}: size_{size} 필터 없음")
            print(f"FAIL | 사유: size_{size} 필터 없음")
            continue

        matrix = payload.get("input")
        expected_raw = payload.get("expected")
        expected = normalize_label(expected_raw)
        if expected is None:
            load_failures.append(f"{case_id}: expected 라벨 정규화 실패({expected_raw})")
            print(f"FAIL | 사유: expected 라벨 정규화 실패({expected_raw})")
            continue

        is_valid, reason = validate_square_matrix(matrix, size)
        if not is_valid:
            load_failures.append(f"{case_id}: {reason}")
            print(f"FAIL | 사유: {reason}")
            continue

        pattern = [[float(v) for v in row] for row in matrix]
        cross_filter = filters_by_size[size]["Cross"]
        x_filter = filters_by_size[size]["X"]

        cross_score = mac_score(pattern, cross_filter)
        x_score = mac_score(pattern, x_filter)
        predicted = decide_label(cross_score, x_score, EPSILON)
        passed = predicted == expected
        reason_text = ""
        if not passed:
            reason_text = (
                "동점(UNDECIDED) 처리 규칙"
                if predicted == "UNDECIDED"
                else f"예상 {expected}와 불일치"
            )

        print(f"Cross 점수: {cross_score}")
        print(f"X 점수: {x_score}")
        print(
            f"판정: {predicted} | expected: {expected} | {'PASS' if passed else 'FAIL'}"
            + (f" ({reason_text})" if reason_text else "")
        )

        results.append(
            CaseResult(
                case_id=case_id,
                predicted=predicted,
                expected=expected,
                cross_score=cross_score,
                x_score=x_score,
                passed=passed,
                reason=reason_text,
            )
        )

    return results, load_failures


def print_summary(results: List[CaseResult], load_failures: List[str]) -> None:
    total = len(results) + len(load_failures)
    passed = sum(1 for item in results if item.passed)
    failed = total - passed

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed > 0:
        print("\n실패 케이스:")
        for message in load_failures:
            print(f"- {message}")
        for item in results:
            if not item.passed:
                print(f"- {item.case_id}: {item.reason}")


def run_user_input_mode() -> None:
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = read_matrix_from_console("필터 A", 3)
    filter_b = read_matrix_from_console("필터 B", 3)

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = read_matrix_from_console("패턴", 3)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    score_a = mac_score(pattern, filter_a)
    score_b = mac_score(pattern, filter_b)
    avg_ms = measure_mac_runtime_ms(pattern, filter_a, PERF_REPEAT)
    decision = decide_label(score_a, score_b, EPSILON)
    decision_text = (
        "판정 불가 (|A-B| < 1e-9)"
        if decision == "UNDECIDED"
        else ("A" if decision == "Cross" else "B")
    )
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{PERF_REPEAT}회): {avg_ms:.6f} ms")
    print(f"판정: {decision_text}")

    performance_analysis(
        {
            3: {
                "Cross": filter_a,
                "X": filter_b,
            }
        }
    )


def run_json_mode() -> None:
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "data.json",
    )
    loaded = load_json_file(data_path)
    if loaded is None:
        return

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    raw_filters = loaded.get("filters")
    raw_patterns = loaded.get("patterns")
    if not isinstance(raw_filters, dict) or not isinstance(raw_patterns, dict):
        print("오류: data.json 스키마 오류(filters/patterns dict 필요)")
        return

    filters_by_size, filter_failures = load_filters(raw_filters)
    results, pattern_failures = analyze_patterns(raw_patterns, filters_by_size)
    all_load_failures = filter_failures + pattern_failures

    performance_analysis(filters_by_size)
    print_summary(results, all_load_failures)


def main() -> None:
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        selected = input("선택: ").strip()
        if selected == "1":
            run_user_input_mode()
            break
        if selected == "2":
            run_json_mode()
            break
        print("입력 오류: 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
