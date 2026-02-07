"""下载 STM32CubeF4 软件包"""
import logging
import shutil
import sys
import time
import zipfile
import urllib.request
from pathlib import Path

log = logging.getLogger("stloop")

CUBE_VERSION = "1.28.0"
CUBE_URL = f"https://github.com/STMicroelectronics/STM32CubeF4/archive/refs/tags/v{CUBE_VERSION}.zip"
MAX_RETRIES = 3
RETRY_DELAY = 2

DOWNLOAD_FAIL_HINT = """
若自动下载反复失败，可手动下载后解压到 cube/STM32CubeF4：
  • GitHub: https://github.com/STMicroelectronics/STM32CubeF4/releases
  • 官方: https://www.st.com/en/embedded-software/stm32cubef4.html
  • 国内网络可配置代理: $env:HTTPS_PROXY="http://127.0.0.1:7890"
"""


def _do_download(zip_path: Path) -> None:
    """执行单次下载"""
    req = urllib.request.Request(CUBE_URL, headers={"User-Agent": "STLoop/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = resp.headers.get("Content-Length")
        total_size = int(total) if total else -1

        with open(zip_path, "wb") as f:
            downloaded = 0
            block_size = 8192
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = min(100, downloaded * 100 // total_size)
                    mb = downloaded / (1024 * 1024)
                    total_mb = total_size / (1024 * 1024)
                    print(f"\r  下载进度: {pct}% ({mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
                else:
                    print(f"\r  已下载: {downloaded / (1024*1024):.1f} MB", end="", flush=True)
    print()


def _find_existing_cube(target_dir: Path) -> Path | None:
    """下载前确认：若 cube 文件夹已有芯片库（含 Drivers），返回路径，否则 None"""
    target_dir = Path(target_dir).resolve()
    if (target_dir / "Drivers").exists():
        return target_dir
    cube_dir = target_dir.parent
    if cube_dir.exists():
        for d in cube_dir.iterdir():
            if d.is_dir() and "STM32CubeF4" in d.name and (d / "Drivers").exists():
                return d
    return None


def download_cube(target_dir: Path, raise_on_fail: bool = True) -> Path:
    """
    下载并解压 STM32CubeF4 到 target_dir。
    raise_on_fail: True 时抛异常，False 时 sys.exit(1)
    """
    target_dir = Path(target_dir).resolve()
    log.info("检查 STM32CubeF4: %s", target_dir)

    existing = _find_existing_cube(target_dir)
    if existing is not None:
        log.info("cube 目录已有芯片库，跳过下载: %s", existing)
        return existing

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir.parent / "STM32CubeF4.zip"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        log.info("下载尝试 %d/%d: %s", attempt, MAX_RETRIES, CUBE_URL)
        print(f"正在下载 STM32CubeF4 v{CUBE_VERSION}... (尝试 {attempt}/{MAX_RETRIES})")
        try:
            _do_download(zip_path)
            last_error = None
            break
        except urllib.error.HTTPError as e:
            last_error = e
            log.warning("HTTP 错误 %s: %s (尝试 %d/%d)", e.code, e.reason, attempt, MAX_RETRIES)
            print(f"\n下载失败: HTTP {e.code} {e.reason}")
            if zip_path.exists():
                zip_path.unlink(missing_ok=True)
            if attempt < MAX_RETRIES:
                print(f"  {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
        except urllib.error.URLError as e:
            last_error = e
            log.warning("URL 错误: %s (尝试 %d/%d)", e.reason, attempt, MAX_RETRIES)
            print(f"\n下载失败: {e.reason}")
            if zip_path.exists():
                zip_path.unlink(missing_ok=True)
            if attempt < MAX_RETRIES:
                print(f"  {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
        except Exception as e:
            last_error = e
            log.exception("下载异常")
            print(f"\n下载失败: {e}")
            if zip_path.exists():
                zip_path.unlink(missing_ok=True)
            if attempt < MAX_RETRIES:
                print(f"  {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)

    if last_error is not None:
        print(DOWNLOAD_FAIL_HINT, file=sys.stderr)
        if raise_on_fail:
            raise RuntimeError(f"STM32CubeF4 下载失败: {last_error}") from last_error
        sys.exit(1)

    if not zip_path.exists() or zip_path.stat().st_size < 1000:
        msg = "下载的文件无效或过小"
        if raise_on_fail:
            raise RuntimeError(msg)
        print(msg, file=sys.stderr)
        sys.exit(1)

    log.info("下载完成，大小: %.1f MB", zip_path.stat().st_size / (1024 * 1024))

    # 解压
    log.info("正在解压...")
    print("正在解压...")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(target_dir.parent)
    except zipfile.BadZipFile as e:
        zip_path.unlink(missing_ok=True)
        msg = f"ZIP 文件损坏: {e}"
        if raise_on_fail:
            raise RuntimeError(msg) from e
        print(msg, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        msg = f"解压失败: {e}"
        if raise_on_fail:
            raise RuntimeError(msg) from e
        print(msg, file=sys.stderr)
        sys.exit(1)

    zip_path.unlink(missing_ok=True)

    # 重命名
    extracted = target_dir.parent / f"STM32CubeF4-{CUBE_VERSION}"
    if not extracted.exists():
        dirs = [d for d in target_dir.parent.iterdir() if d.is_dir() and "STM32CubeF4" in d.name]
        extracted = dirs[0] if dirs else None
    if extracted and extracted.exists() and extracted != target_dir:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        extracted.rename(target_dir)
        log.info("已重命名: %s -> %s", extracted.name, target_dir)

    if not (target_dir / "Drivers").exists():
        msg = "解压后未找到 Drivers 目录"
        if raise_on_fail:
            raise RuntimeError(msg)
        print(msg, file=sys.stderr)
        sys.exit(1)

    log.info("STM32CubeF4 就绪: %s", target_dir)
    return target_dir


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(levelname)s: %(message)s")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "cube" / "STM32CubeF4"
    try:
        download_cube(out, raise_on_fail=False)
    except RuntimeError:
        sys.exit(1)
