from dataclasses import dataclass


@dataclass
class CaseResult:
    case_id: str
    predicted: str
    expected: str
    cross_score: int
    x_score: int
    passed: bool
    reason: str = ""
