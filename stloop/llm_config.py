"""LLM 配置 — 支持 OpenAI、Kimi 等兼容 API"""
import os
from pathlib import Path
from typing import Optional, Tuple

# 启动时加载 .env
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    # 也尝试工作目录的 .env
    load_dotenv()
except ImportError:
    pass


def get_llm_config(work_dir: Optional[Path] = None) -> Tuple[Optional[str], Optional[str], str]:
    """
    获取 LLM 配置。
    返回 (api_key, base_url, model)
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("STLOOP_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE") or os.environ.get("STLOOP_API_BASE")
    model = os.environ.get("OPENAI_MODEL") or os.environ.get("STLOOP_MODEL") or "gpt-4o-mini"

    # 尝试从 config.yaml 读取 base_url、model（api_key 建议用环境变量）
    if work_dir:
        config_path = Path(work_dir) / "config" / "config.yaml"
        if config_path.exists():
            try:
                import yaml
                with open(config_path, encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                if cfg and "llm" in cfg:
                    llm = cfg["llm"]
                    api_key = api_key or llm.get("api_key")
                    base_url = base_url or llm.get("base_url")
                    model = llm.get("model") or model
            except Exception:
                pass

    return api_key, base_url, model


def is_llm_configured(work_dir: Optional[Path] = None) -> bool:
    """检查 LLM 是否已配置"""
    api_key, _, _ = get_llm_config(work_dir)
    return bool(api_key)
