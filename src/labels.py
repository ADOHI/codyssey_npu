from typing import Optional


def normalize_label(raw: str) -> Optional[str]:
    """expected·필터 키 등을 표준 라벨 Cross/X로 정규화한다.

    명세: expected `+`→Cross, `x`→X / 필터 키 `cross`→Cross, `x`→X.
    """
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value in ("cross", "+", "plus"):
        return "Cross"
    if value in ("x", "ex"):
        return "X"
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
