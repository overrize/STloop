#!/bin/bash
# Zephyr 环境设置和构建脚本

# 查找 Zephyr 安装
if [ -z "$ZEPHYR_BASE" ]; then
    # 尝试常见安装路径
    if [ -d "$HOME/zephyrproject/zephyr" ]; then
        export ZEPHYR_BASE="$HOME/zephyrproject/zephyr"
    elif [ -d "/opt/zephyrproject/zephyr" ]; then
        export ZEPHYR_BASE="/opt/zephyrproject/zephyr"
    elif [ -d "C:/zephyrproject/zephyr" ]; then
        export ZEPHYR_BASE="C:/zephyrproject/zephyr"
    else
        echo "Error: ZEPHYR_BASE not set and Zephyr not found in common locations"
        echo "Please install Zephyr: https://docs.zephyrproject.org/latest/develop/getting_started/index.html"
        exit 1
    fi
fi

echo "Using Zephyr from: $ZEPHYR_BASE"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${1:-$SCRIPT_DIR}"
BOARD="${2:-nucleo_f411re}"
BUILD_DIR="$PROJECT_DIR/build"

# 检查 west 工具
if ! command -v west &> /dev/null; then
    echo "Error: west tool not found"
    echo "Please install: pip install west"
    exit 1
fi

# 构建
echo "Building Zephyr project..."
echo "  Board: $BOARD"
echo "  Project: $PROJECT_DIR"
echo "  Build: $BUILD_DIR"

cd "$PROJECT_DIR"

# 清理之前的构建
rm -rf "$BUILD_DIR"

# 执行构建
west build -p auto -b "$BOARD" "$PROJECT_DIR" -d "$BUILD_DIR"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Build successful!"
    echo "  ELF: $BUILD_DIR/zephyr/zephyr.elf"
    echo "  BIN: $BUILD_DIR/zephyr/zephyr.bin"
    echo "  HEX: $BUILD_DIR/zephyr/zephyr.hex"
else
    echo ""
    echo "✗ Build failed!"
    exit 1
fi
