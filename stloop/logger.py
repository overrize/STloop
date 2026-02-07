"""STLoop 日志配置"""
import logging
import sys

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger("stloop")
        _logger.setLevel(logging.DEBUG)
        if not _logger.handlers:
            h = logging.StreamHandler(sys.stdout)
            h.setLevel(logging.INFO)
            h.setFormatter(logging.Formatter("[stloop] %(levelname)s: %(message)s"))
            _logger.addHandler(h)
    return _logger


def set_verbose(verbose: bool) -> None:
    """启用/关闭 DEBUG 输出"""
    log = get_logger()
    for h in log.handlers:
        h.setLevel(logging.DEBUG if verbose else logging.INFO)
