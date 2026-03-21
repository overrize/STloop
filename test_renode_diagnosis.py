#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def check_renode():
    result = subprocess.run(["which", "renode"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Renode path: {result.stdout.strip()}")
        ver = subprocess.run(["renode", "--version"], capture_output=True, text=True)
        print(f"Version: {ver.stdout.strip()}")
        return True
    print("Renode not found")
    return False


def check_platforms():
    platforms = [
        "/f/Renode/platforms/cpus/stm32f4.repl",
        "/f/Renode/platforms/boards/stm32f4_discovery.repl",
    ]
    print("\nPlatform files:")
    for p in platforms:
        path = Path(p)
        status = "exists" if path.exists() else "NOT FOUND"
        print(f"  {p} - {status}")


def generate_test_resc(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    script = """mach create "test"
machine LoadPlatformDescription @/f/Renode/platforms/cpus/stm32f4.repl
mach show
echo "Platform loaded successfully"
"""
    resc_path = output_dir / "test_diagnosis.resc"
    resc_path.write_text(script)
    print(f"\nTest script: {resc_path}")
    return resc_path


def run_diagnosis():
    print("=" * 60)
    print("Renode Diagnosis")
    print("=" * 60)

    if not check_renode():
        sys.exit(1)

    check_platforms()

    test_dir = Path("E:/bitloop_embedderdev-kind/test_renode_diagnosis")
    resc_path = generate_test_resc(test_dir)

    print("\nRunning test script...")
    print("-" * 60)

    result = subprocess.run(
        ["renode", str(resc_path), "--console", "--disable-gui"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print(f"Return code: {result.returncode}")

    print("\nError analysis:")
    if result.returncode != 0:
        if "FileNotFound" in result.stderr or "not found" in result.stderr.lower():
            print("  - File not found error")
        if "Platform" in result.stderr:
            print("  - Platform loading error")
        if "ELF" in result.stderr:
            print("  - ELF loading error")
    else:
        print("  Test script ran successfully")


if __name__ == "__main__":
    run_diagnosis()
