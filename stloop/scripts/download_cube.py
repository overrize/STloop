"""下载 STM32CubeF4 软件包"""
import logging
import shutil
import sys
import zipfile
import urllib.request
from pathlib import Path

log = logging.getLogger("stloop")

CUBE_VERSION = "1.28.0"
CUBE_URL = f"https://github.com/STMicroelectronics/STM32CubeF4/archive/refs/tags/v{CUBE_VERSION}.zip"


def _progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    """下载进度回调"""
    if total_size > 0:
        downloaded = block_num * block_size
        pct = min(100, downloaded * 100 // total_size)
        mb = downloaded / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        print(f"\r  下载进度: {pct}% ({mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
    else:
        mb = (block_num * block_size) / (1024 * 1024)
        print(f"\r  已下载: {mb:.1f} MB", end="", flush=True)


def download_cube(target_dir: Path) -> Path:
    """下载并解压 STM32CubeF4 到 target_dir"""
    target_dir = Path(target_dir).resolve()
    log.info("检查 STM32CubeF4: %s", target_dir)

    if (target_dir / "Drivers").exists():
        log.info("STM32CubeF4 已存在，跳过下载")
        return target_dir

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir.parent / "STM32CubeF4.zip"

    # 下载
    log.info("正在下载 STM32CubeF4 v%s from %s", CUBE_VERSION, CUBE_URL)
    req = urllib.request.Request(CUBE_URL, headers={"User-Agent": "STLoop/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = resp.headers.get("Content-Length")
            total_size = int(total) if total else -1
            log.debug("响应状态: %s, Content-Length: %s", resp.status, total_size)

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
    except urllib.error.HTTPError as e:
        log.error("HTTP 错误 %s: %s", e.code, e.reason)
        print(f"\n下载失败: HTTP {e.code} {e.reason}", file=sys.stderr)
        print("请检查网络，或使用代理。", file=sys.stderr)
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        sys.exit(1)
    except urllib.error.URLError as e:
        log.error("URL 错误: %s", e.reason)
        print(f"\n下载失败: {e.reason}", file=sys.stderr)
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        sys.exit(1)
    except Exception as e:
        log.exception("下载异常")
        print(f"\n下载失败: {e}", file=sys.stderr)
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        sys.exit(1)

    if not zip_path.exists() or zip_path.stat().st_size < 1000:
        log.error("下载的文件无效，大小: %s", zip_path.stat().st_size if zip_path.exists() else 0)
        print("下载的文件无效或过小", file=sys.stderr)
        sys.exit(1)
    log.info("下载完成，大小: %.1f MB", zip_path.stat().st_size / (1024 * 1024))

    # 解压
    log.info("正在解压...")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()
            log.debug("ZIP 包含 %d 个文件", len(names))
            z.extractall(target_dir.parent)
    except zipfile.BadZipFile as e:
        log.error("ZIP 文件损坏: %s", e)
        print(f"解压失败: ZIP 文件可能损坏 - {e}", file=sys.stderr)
        zip_path.unlink(missing_ok=True)
        sys.exit(1)
    except Exception as e:
        log.exception("解压异常")
        print(f"解压失败: {e}", file=sys.stderr)
        sys.exit(1)

    zip_path.unlink(missing_ok=True)

    # 重命名解压目录
    extracted = target_dir.parent / f"STM32CubeF4-{CUBE_VERSION}"
    if not extracted.exists():
        # 尝试查找实际解压出的目录
        dirs = [d for d in target_dir.parent.iterdir() if d.is_dir() and "STM32CubeF4" in d.name]
        extracted = dirs[0] if dirs else None
    if extracted and extracted.exists() and extracted != target_dir:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        extracted.rename(target_dir)
        log.info("已重命名: %s -> %s", extracted.name, target_dir)
    elif not (target_dir / "Drivers").exists():
        log.error("解压后未找到 Drivers 目录")
        print("解压后未找到 Drivers 目录，请检查下载是否完整", file=sys.stderr)
        sys.exit(1)

    if not (target_dir / "Drivers").exists():
        log.error("Drivers 不存在于 %s", target_dir)
        sys.exit(1)

    log.info("STM32CubeF4 就绪: %s", target_dir)
    return target_dir


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(levelname)s: %(message)s")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "cube" / "STM32CubeF4"
    download_cube(out)
