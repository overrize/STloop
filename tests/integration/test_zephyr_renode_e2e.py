#!/usr/bin/env python3
"""
Zephyr + Renode 端到端测试脚本

此脚本演示完整的 Zephyr -> 构建 -> Renode 仿真流程
适用于 STLoop 工具链

使用方法:
    python test_zephyr_renode_e2e.py

环境要求:
    - Python 3.10+
    - West (pip install west)
    - arm-none-eabi-gcc
    - CMake >= 3.20
    - Ninja
    - Renode (https://renode.io)
    - Zephyr SDK (设置 ZEPHYR_BASE 环境变量)
"""

import os
import sys
import shutil
from pathlib import Path


def check_prerequisites():
    """检查所有前置条件"""
    print("=" * 60)
    print("检查前置条件")
    print("=" * 60)

    checks = []

    # 1. 检查 stloop
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from stloop.builder import check_zephyr_environment, build
        from stloop.simulators.renode import find_renode_bin, generate_resc_script, RenodeConfig

        checks.append(("stloop 库", True, "已导入"))
    except ImportError as e:
        checks.append(("stloop 库", False, f"导入失败: {e}"))
        return False, checks

    # 2. 检查 west
    west = shutil.which("west")
    checks.append(("West 工具", west is not None, west or "未找到"))

    # 3. 检查 Zephyr 环境
    ready, msg = check_zephyr_environment()
    checks.append(("Zephyr 环境", ready, msg))

    # 4. 检查工具链
    gcc = shutil.which("arm-none-eabi-gcc")
    cmake = shutil.which("cmake")
    ninja = shutil.which("ninja")
    checks.append(("ARM GCC", gcc is not None, gcc or "未找到"))
    checks.append(("CMake", cmake is not None, cmake or "未找到"))
    checks.append(("Ninja", ninja is not None, ninja or "未找到"))

    # 5. 检查 Renode
    renode = find_renode_bin()
    checks.append(("Renode", renode is not None, str(renode) if renode else "未找到"))

    # 打印结果
    all_ok = True
    for name, ok, detail in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}: {detail}")
        if not ok:
            all_ok = False

    return all_ok, checks


def test_build_with_stloop():
    """使用 stloop 构建 Zephyr 兼容项目"""
    print("\n" + "=" * 60)
    print("测试 1: 使用 stloop 构建项目")
    print("=" * 60)

    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from stloop.builder import build

    # 使用 test_zephyr 作为测试项目
    project_dir = Path(__file__).parent / "test_zephyr"

    if not project_dir.exists():
        print(f"  [FAIL] 项目目录不存在: {project_dir}")
        return False, None

    print(f"  项目目录: {project_dir}")

    try:
        # 清理旧的构建目录
        build_dir = project_dir / "build_e2e"
        if build_dir.exists():
            import shutil

            shutil.rmtree(build_dir)

        # 构建项目
        elf_path = build(project_dir, build_dir=build_dir, board="nucleo_f411re", use_zephyr=False)
        print(f"  [OK] 构建成功: {elf_path}")
        return True, elf_path
    except Exception as e:
        print(f"  [FAIL] 构建失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


def test_generate_renode_script(elf_path):
    """生成 Renode 仿真脚本"""
    print("\n" + "=" * 60)
    print("测试 2: 生成 Renode 脚本")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent))
    from stloop.simulators.renode import generate_resc_script, RenodeConfig

    try:
        config = RenodeConfig(mcu="STM32F411RE", show_gui=False, enable_uart=True)
        script_path = generate_resc_script(elf_path, mcu="STM32F411RE", config=config)
        print(f"  [OK] 脚本生成成功: {script_path}")

        # 显示脚本内容
        content = script_path.read_text()
        print(f"\n  脚本内容预览:")
        for line in content.split("\n")[:10]:
            if line.strip():
                print(f"    {line}")

        return True, script_path
    except Exception as e:
        print(f"  [FAIL] 脚本生成失败: {e}")
        import traceback

        traceback.print_exc()
        return False, None


def test_renode_simulation(elf_path, script_path):
    """测试 Renode 仿真（仅验证脚本，不启动 GUI）"""
    print("\n" + "=" * 60)
    print("测试 3: 验证 Renode 仿真配置")
    print("=" * 60)

    sys.path.insert(0, str(Path(__file__).parent))
    from stloop.simulators.renode import find_renode_bin

    renode_bin = find_renode_bin()
    if not renode_bin:
        print("  [FAIL] Renode 未安装")
        return False

    print(f"  [OK] Renode 路径: {renode_bin}")
    print(f"  [OK] ELF 文件: {elf_path}")
    print(f"  [OK] 脚本文件: {script_path}")

    # 验证文件存在
    checks = [
        ("ELF 文件存在", elf_path.exists()),
        ("脚本文件存在", script_path.exists()),
    ]

    for name, ok in checks:
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {name}")

    # 手动运行命令提示
    print(f"\n  手动运行仿真:")
    print(f"    renode --console {script_path}")

    return all(ok for _, ok in checks)


def main():
    """主函数"""
    print("\n")
    print("*" * 60)
    print("* Zephyr + Renode 端到端测试")
    print("* STLoop 工具链验证")
    print("*" * 60)

    # 1. 检查前置条件
    ok, checks = check_prerequisites()
    if not ok:
        print("\n" + "=" * 60)
        print("[FAIL] 前置条件检查失败，请安装缺失的工具")
        print("=" * 60)
        sys.exit(1)

    # 2. 构建项目
    ok, elf_path = test_build_with_stloop()
    if not ok:
        print("\n" + "=" * 60)
        print("[FAIL] 构建测试失败")
        print("=" * 60)
        sys.exit(1)

    # 3. 生成 Renode 脚本
    ok, script_path = test_generate_renode_script(elf_path)
    if not ok:
        print("\n" + "=" * 60)
        print("[FAIL] Renode 脚本生成失败")
        print("=" * 60)
        sys.exit(1)

    # 4. 验证仿真配置
    ok = test_renode_simulation(elf_path, script_path)
    if not ok:
        print("\n" + "=" * 60)
        print("[FAIL] Renode 仿真配置验证失败")
        print("=" * 60)
        sys.exit(1)

    # 成功
    print("\n" + "=" * 60)
    print("[OK] 端到端测试全部通过！")
    print("=" * 60)
    print(f"\n构建产物: {elf_path}")
    print(f"仿真脚本: {script_path}")
    print("\n手动运行仿真:")
    print(f"  renode --console {script_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
