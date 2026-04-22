import os
from typing import List

from analysis import (
    DEFAULT_PERF_SIZES,
    analyze_patterns,
    performance_analysis,
    print_mac_variant_comparison,
    print_mac_variant_table_by_sizes,
    print_summary,
)
from console_input import read_matrix_from_console
from data_loader import load_filters, load_json_file
from mac_evaluator import MacEvaluator


class MiniNpuApp:
    """콘솔 메뉴·사용자 입력 모드·JSON 분석 모드를 담당한다."""

    def __init__(self) -> None:
        self._evaluator = MacEvaluator()

    def run(self) -> None:
        print("=== Mini NPU Simulator ===")
        print("\n[모드 선택]")
        print("1. 사용자 입력 (3×3)")
        print("2. data.json 분석")

        while True:
            selected = input("선택: ").strip()
            if selected == "1":
                self._run_user_input_mode()
                break
            if selected == "2":
                self._run_json_mode()
                break
            print("입력 오류: 1 또는 2를 입력하세요.")

    def _run_user_input_mode(self) -> None:
        ev = self._evaluator
        print("\n#----------------------------------------")
        print("# [1] 필터 입력")
        print("#---------------------------------------")
        filter_a = read_matrix_from_console("필터 A", 3)
        filter_b = read_matrix_from_console("필터 B", 3)

        print("\n#---------------------------------------")
        print("# [1-확인] 저장된 필터 확인")
        print("#---------------------------------------")
        print("아래에 저장된 필터 A, B가 입력과 일치하는지 확인하세요.")
        self._print_matrix_for_confirmation("필터 A (저장됨)", filter_a)
        self._print_matrix_for_confirmation("필터 B (저장됨)", filter_b)

        print("\n#---------------------------------------")
        print("# [2] 패턴 입력")
        print("#---------------------------------------")
        pattern = read_matrix_from_console("패턴", 3)

        score_a = ev.score(pattern, filter_a)
        score_b = ev.score(pattern, filter_b)
        avg_ms = ev.measure_runtime_ms(pattern, filter_a)
        decision_ab = ev.decide_ab(score_a, score_b)

        print("\n#---------------------------------------")
        if decision_ab == "UNDECIDED":
            print("# [3] MAC 결과 (판정 불가)")
        else:
            print("# [3] MAC 결과")
        print("#---------------------------------------")
        decision_text = (
            "판정 불가 (|A-B| < 1e-9)"
            if decision_ab == "UNDECIDED"
            else decision_ab
        )
        print(f"A 점수: {float(score_a)}")
        print(f"B 점수: {float(score_b)}")
        print(f"연산 시간(평균/{ev.perf_repeat}회): {avg_ms:.6f} ms")
        print(f"판정: {decision_text}")

        performance_analysis(
            {
                3: {
                    "Cross": filter_a,
                    "X": filter_b,
                }
            },
            ev,
            section_no=4,
            sizes=(3,),
        )
        print_mac_variant_comparison(
            pattern,
            filter_a,
            ev.perf_repeat,
            section_no=5,
            subtitle=" - 입력 패턴 x 필터 A",
        )

    @staticmethod
    def _print_matrix_for_confirmation(title: str, matrix: List[List[int]]) -> None:
        print(f"\n{title}")
        for row in matrix:
            print("  " + " ".join(str(int(v)) for v in row))

    def _run_json_mode(self) -> None:
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

        ev = self._evaluator
        filters_by_size, filter_failures = load_filters(raw_filters)
        results, pattern_failures = analyze_patterns(raw_patterns, filters_by_size, ev)
        all_load_failures = filter_failures + pattern_failures

        performance_analysis(filters_by_size, ev)
        print_mac_variant_table_by_sizes(
            filters_by_size, DEFAULT_PERF_SIZES, ev.perf_repeat
        )
        print_summary(results, all_load_failures)
