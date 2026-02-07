"""基础 smoke 测试"""
import pytest


def test_import_stloop():
    """测试包可导入"""
    from stloop import STLoopClient, __version__
    assert __version__ is not None


def test_client_init():
    """测试 client 初始化"""
    from stloop import STLoopClient
    client = STLoopClient(work_dir=".")
    assert client.work_dir is not None
    assert client.target == "stm32f411re"


def test_cli_version():
    """测试 CLI --version"""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "stloop", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "stloop" in result.stdout.lower()
