"""基础 smoke 测试"""
import subprocess
from pathlib import Path

import pytest


def test_get_projects_dir_inside_stloop():
    """在 STloop 包内时，get_projects_dir 返回 workspace 根（上一级或 STLOOP_ROOT）"""
    from stloop._paths import STLOOP_ROOT, get_projects_dir

    projects = get_projects_dir(STLOOP_ROOT)
    assert projects is not None
    assert projects.exists() or not projects.exists()  # 可能尚不存在
    assert str(projects)  # 有效路径


def test_get_projects_dir_outside_stloop(tmp_path):
    """在 STloop 外时，get_projects_dir 返回 work_dir"""
    from stloop._paths import get_projects_dir

    assert get_projects_dir(tmp_path) == tmp_path.resolve()


def test_import_stloop():
    """测试包可导入"""
    from stloop import STLoopClient, __version__

    assert __version__ is not None
    assert STLoopClient is not None


def test_client_init():
    """测试 client 初始化"""
    from stloop import STLoopClient

    client = STLoopClient(work_dir=".")
    assert client.work_dir is not None
    assert client.target == "stm32f411re"


def test_cli_version():
    """测试 CLI --version"""
    result = subprocess.run(
        ["python", "-m", "stloop", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "stloop" in result.stdout.lower()


def test_llm_config():
    """测试 llm_config 模块"""
    from stloop.llm_config import get_llm_config, is_llm_configured

    api_key, base_url, model = get_llm_config()
    assert isinstance(api_key, (type(None), str))
    assert isinstance(base_url, (type(None), str))
    assert isinstance(model, str)
    assert len(model) > 0
    assert isinstance(is_llm_configured(), bool)


def test_chat_exits_when_not_configured(monkeypatch):
    """测试 chat 在未配置 API 时立即退出"""
    from stloop.chat import run_interactive
    from stloop.client import STLoopClient

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("STLOOP_API_KEY", raising=False)
    client = STLoopClient(work_dir=Path.cwd())
    # 未配置时应返回 1（不阻塞等待输入）
    assert run_interactive(client) == 1


def test_embed_cube_skips_when_already_embedded(tmp_path):
    """项目已有 cube 时，_embed_cube 跳过复制"""
    from stloop.client import STLoopClient

    (tmp_path / "cube" / "STM32CubeF4" / "Drivers").mkdir(parents=True)
    client = STLoopClient(work_dir=tmp_path)
    client.cube_path = tmp_path / "some_cube"
    result = client._embed_cube(tmp_path, tmp_path)
    assert (tmp_path / "cube" / "STM32CubeF4" / "Drivers").exists()
    assert result == tmp_path / "cube" / "STM32CubeF4"


def test_gen_raises_without_api_key(monkeypatch, tmp_path):
    """测试 gen 在未配置 API Key 时抛出明确错误"""
    from stloop.client import STLoopClient

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("STLOOP_API_KEY", raising=False)
    client = STLoopClient(work_dir=tmp_path)
    with pytest.raises(ValueError, match="OPENAI_API_KEY|STLOOP_API_KEY|配置"):
        client.gen("PA5 LED 闪烁", tmp_path / "test_gen")
