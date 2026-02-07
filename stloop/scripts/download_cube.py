"""下载 STM32CubeF4 软件包"""
import shutil
import sys
import zipfile
import urllib.request
from pathlib import Path

CUBE_VERSION = "1.28.0"
CUBE_URL = f"https://github.com/STMicroelectronics/STM32CubeF4/archive/refs/tags/v{CUBE_VERSION}.zip"


def download_cube(target_dir: Path) -> Path:
    """下载并解压 STM32CubeF4 到 target_dir"""
    target_dir = Path(target_dir).resolve()
    if (target_dir / "Drivers").exists():
        print(f"STM32CubeF4 已存在: {target_dir}")
        return target_dir
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir.parent / "STM32CubeF4.zip"

    print(f"Downloading STM32CubeF4 v{CUBE_VERSION}...")
    urllib.request.urlretrieve(CUBE_URL, zip_path)

    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(target_dir.parent)
    zip_path.unlink(missing_ok=True)

    extracted = target_dir.parent / f"STM32CubeF4-{CUBE_VERSION}"
    if extracted.exists() and extracted != target_dir:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        extracted.rename(target_dir)

    if not (target_dir / "Drivers").exists():
        print("ERROR: Drivers not found after extract", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {target_dir}")
    return target_dir


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd() / "cube" / "STM32CubeF4"
    download_cube(out)
