"""支持 python -m stloop"""

import sys

# 尝试使用新版 Rich UI，失败时回退到旧版
try:
    from .cli_rich import main
except ImportError as e:
    # 如果 Rich UI 依赖未安装，使用旧版
    from .cli import main

sys.exit(main())
