from typing import Dict, List, Optional, Sequence, Tuple

from labels import extract_size_from_key, normalize_label
from mac_evaluator import MacEvaluator
from matrix_ops import (
    benchmark_mac_variants_ms,
    generate_cross_pattern,
    generate_x_pattern,
    normalize_int_matrix,
    validate_square_matrix,
)
from models import CaseResult

DEFAULT_PERF_SIZES: Tuple[int, ...] = (3, 5, 13, 25)


def performance_analysis(
    filters_by_size: Dict[int, Dict[str, List[List[int]]]],
    evaluator: MacEvaluator,
    *,
    section_no: int = 3,
    sizes: Sequence[int] = DEFAULT_PERF_SIZES,
) -> None:
    print("\n#---------------------------------------")
    print(f"# [{section_no}] 성능 분석 (평균/{evaluator.perf_repeat}회)")
    print("#---------------------------------------")
    print("크기       평균 시간(ms)    연산 횟수")
    print("-------------------------------------")
    for size in sizes:
        filt = None
        pattern = None
        if size in filters_by_size:
            filt = filters_by_size[size].get("Cross")
        if filt is None:
            filt = generate_cross_pattern(size)
        pattern = generate_x_pattern(size)
        avg_ms = evaluator.measure_runtime_ms(pattern, filt)
        label = f"{size}×{size}"
        print(f"{label:<10} {avg_ms:>12.6f} {size * size:>12}")


def print_mac_variant_comparison(
    pattern: List[List[int]],
    filt: List[List[int]],
    repeat: int,
    *,
    section_no: Optional[int] = None,
    subtitle: str = "",
) -> None:
    """동일 패턴·필터에 대해 MAC 세 구현의 평균 시간을 출력한다."""
    base, row_c, flat_v = benchmark_mac_variants_ms(pattern, filt, repeat)
    print("\n#---------------------------------------")
    head = (
        f"# [{section_no}] MAC 구현 3종 비교 (평균/{repeat}회){subtitle}"
        if section_no is not None
        else f"# MAC 구현 3종 비교 (평균/{repeat}회){subtitle}"
    )
    print(head)
    print("#---------------------------------------")
    print("(1D MAC: 2D→1D 변환은 측정 전 1회만, 반복 구간은 곱·누적만)")
    print("구분                 평균 시간(ms)")
    print("-------------------------------------")
    print(f"기본(2D[i][j])      {base:>12.6f}")
    print(f"행 참조 캐시        {row_c:>12.6f}")
    print(f"1D 벡터 MAC         {flat_v:>12.6f}")


def print_mac_variant_table_by_sizes(
    filters_by_size: Dict[int, Dict[str, List[List[int]]]],
    sizes: Sequence[int],
    repeat: int,
) -> None:
    """성능 분석과 동일한 filt/pattern 출처로 크기별 3종 MAC 시간을 표로 출력."""
    print("\n#---------------------------------------")
    print(f"# MAC 구현 3종 비교 - 크기별 (평균/{repeat}회)")
    print("#---------------------------------------")
    print("(각 행: X 패턴 x Cross 필터, 1D열은 선행 flatten 제외·MAC만 반복)")
    print("크기       기본(2D)   행캐시  1D MAC")
    print("-------------------------------------")
    for size in sizes:
        filt = None
        if size in filters_by_size:
            filt = filters_by_size[size].get("Cross")
        if filt is None:
            filt = generate_cross_pattern(size)
        pattern = generate_x_pattern(size)
        base, row_c, flat_v = benchmark_mac_variants_ms(pattern, filt, repeat)
        label = f"{size}×{size}"
        print(
            f"{label:<10} {base:>10.6f} {row_c:>10.6f} {flat_v:>10.6f}"
        )


def analyze_patterns(
    patterns: dict,
    filters_by_size: Dict[int, Dict[str, List[List[int]]]],
    evaluator: MacEvaluator,
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

        pattern = normalize_int_matrix(matrix, size)
        cross_filter = filters_by_size[size]["Cross"]
        x_filter = filters_by_size[size]["X"]

        cross_score = evaluator.score(pattern, cross_filter)
        x_score = evaluator.score(pattern, x_filter)
        predicted = evaluator.decide_label(cross_score, x_score)
        passed = predicted == expected
        reason_text = ""
        if not passed:
            reason_text = (
                "동점 규칙"
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
                if item.predicted == "UNDECIDED":
                    print(
                        f"- {item.case_id}: 동점(UNDECIDED) 처리 규칙에 따라 FAIL"
                    )
                else:
                    print(f"- {item.case_id}: {item.reason}")
