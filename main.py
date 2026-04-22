"""프로젝트 루트에서 `python main.py`로 실행하기 위한 진입점."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(_SRC))


def main() -> None:
    from app import MiniNpuApp

    MiniNpuApp().run()


if __name__ == "__main__":
    main()
