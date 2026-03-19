#!/usr/bin/env python3
"""E2E Test for GitHub Actions - 兼容原 workflow 的测试入口"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.test_zephyr_renode_e2e import (
    check_prerequisites,
    test_build_with_stloop,
    test_generate_renode_script,
    test_renode_simulation,
)


def main():
    parser = argparse.ArgumentParser(description="STLoop E2E Test")
    parser.add_argument(
        "--skip-simulation", action="store_true", help="Skip Renode simulation (for CI without GUI)"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("STLoop E2E Test")
    print("=" * 70)

    ok, checks = check_prerequisites()
    if not ok:
        print("\n[FAIL] Prerequisites check failed")
        for name, passed, detail in checks:
            status = "OK" if passed else "FAIL"
            print(f"  [{status}] {name}: {detail}")
        return 1

    print("\n[OK] All prerequisites met")

    ok, elf_path = test_build_with_stloop()
    if not ok:
        print("\n[FAIL] Build test failed")
        return 1

    print(f"\n[OK] Build successful: {elf_path}")

    ok, script_path = test_generate_renode_script(elf_path)
    if not ok:
        print("\n[FAIL] Renode script generation failed")
        return 1

    print(f"\n[OK] Script generated: {script_path}")

    if not args.skip_simulation:
        ok = test_renode_simulation(elf_path, script_path)
        if not ok:
            print("\n[FAIL] Renode simulation failed")
            return 1
        print("\n[OK] Simulation test passed")
    else:
        print("\n[INFO] Simulation skipped (--skip-simulation)")

    import tempfile
    import shutil

    artifact_dir = Path(tempfile.gettempdir()) / "stloop_e2e_artifacts"
    artifact_dir.mkdir(exist_ok=True)

    if elf_path and elf_path.exists():
        shutil.copy(elf_path, artifact_dir / "firmware.elf")
    if script_path and script_path.exists():
        shutil.copy(script_path, artifact_dir / "simulation.resc")

    report = f"""STLoop E2E Test Report
======================
Build: {"PASS" if ok else "FAIL"}
ELF: {elf_path}
Script: {script_path}
Simulation: {"SKIPPED" if args.skip_simulation else "PASS"}
"""
    (artifact_dir / "test_report.txt").write_text(report)

    print(f"\n[OK] All tests passed!")
    print(f"Artifacts saved to: {artifact_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
