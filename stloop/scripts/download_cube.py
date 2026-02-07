"""下载 STM32Cube 软件包（按芯片系列 F1/F4/F7 等）"""
import logging
import shutil
import sys
import time
import zipfile
import urllib.request
from pathlib import Path

log = logging.getLogger("stloop")

# 系列 -> (版本, 包名)，模板目前仅支持 F4
CUBE_FAMILIES = {
    "F1": ("1.8.0", "STM32CubeF1"),
    "F4": ("1.28.0", "STM32CubeF4"),
    "F7": ("1.17.0", "STM32CubeF7"),
    "H7": ("1.11.0", "STM32CubeH7"),
    "L4": ("1.18.0", "STM32CubeL4"),
    "G4": ("1.5.0", "STM32CubeG4"),
}
MAX_RETRIES = 3
RETRY_DELAY = 2


def _get_cube_url(family: str) -> str:
    version, pkg = CUBE_FAMILIES.get(family.upper(), CUBE_FAMILIES["F4"])
    return f"https://github.com/STMicroelectronics/{pkg}/archive/refs/tags/v{version}.zip"


def get_fail_hint(family: str = "F4") -> str:
    _, pkg = CUBE_FAMILIES.get(family.upper(), CUBE_FAMILIES["F4"])
    return f"""
若自动下载反复失败，可手动下载后解压到 cube/{pkg}：
  • GitHub: https://github.com/STMicroelectronics/{pkg}/releases
  • 官方: https://www.st.com/en/embedded-software/stm32cube{family.lower()}.html
  • 国内网络可配置代理: $env:HTTPS_PROXY="http://127.0.0.1:7890"
"""


def _do_download(url: str, zip_path: Path) -> None:
    """执行单次下载"""
    req = urllib.request.Request(url, headers={"User-Agent": "STLoop/1.0"})
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


def download_cube(
    target_dir: Path,
    family: str = "F4",
    raise_on_fail: bool = True,
) -> Path:
    """
    下载并解压 STM32Cube{family} 到 target_dir。
    family: F1/F4/F7
    """
    target_dir = Path(target_dir).resolve()
    family = family.upper()
    version, pkg = CUBE_FAMILIES.get(family, CUBE_FAMILIES["F4"])
    url = _get_cube_url(family)
    fail_hint = get_fail_hint(family)

    log.info("检查 %s: %s", pkg, target_dir)

    if (target_dir / "Drivers").exists():
        log.info("%s 已存在，跳过下载", pkg)
        return target_dir

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir.parent / f"{pkg}.zip"

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        log.info("下载尝试 %d/%d: %s", attempt, MAX_RETRIES, url)
        print(f"正在下载 {pkg} v{version}... (尝试 {attempt}/{MAX_RETRIES})")
        try:
            _do_download(url, zip_path)
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
        print(fail_hint, file=sys.stderr)
        if raise_on_fail:
            raise RuntimeError(f"{pkg} 下载失败: {last_error}") from last_error
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
    extracted = target_dir.parent / f"{pkg}-{version}"
    if not extracted.exists():
        dirs = [d for d in target_dir.parent.iterdir() if d.is_dir() and pkg in d.name]
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

    log.info("%s 就绪: %s", pkg, target_dir)
    return target_dir


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(levelname)s: %(message)s")
    family = sys.argv[1] if len(sys.argv) > 1 else "F4"
    out = Path.cwd() / "cube" / f"STM32Cube{family}"
    try:
        download_cube(out, family=family, raise_on_fail=False)
    except RuntimeError:
        sys.exit(1)
