#!/usr/bin/env python3
"""
STLoop — 向后兼容入口
推荐使用: stloop demo blink 或 python -m stloop
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stloop.cli import main

if __name__ == "__main__":
    sys.exit(main())
