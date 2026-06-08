#!/usr/bin/env bash
# SchemaMap-CLI 一键构建脚本
set -e

echo "========================================"
echo "  SchemaMap-CLI Build Script"
echo "========================================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# 清理旧构建
echo "[1/5] Cleaning old builds..."
rm -rf build/ dist/ *.egg-info/

# 运行单元测试
echo "[2/5] Running unit tests..."
python3 -m unittest discover -s tests -v

# 构建分发包
echo "[3/5] Building distribution packages..."
python3 setup.py sdist bdist_wheel

# 验证构建
echo "[4/5] Verifying build..."
if [ -f "dist/SchemaMap-CLI-1.0.0.tar.gz" ]; then
    echo "  Source distribution: OK"
else
    echo "  Source distribution: FAILED"
    exit 1
fi

if [ -d "dist/SchemaMap_CLI-1.0.0-py3-none-any.whl" ] || [ -f "dist/SchemaMap_CLI-1.0.0-py3-none-any.whl" ]; then
    echo "  Wheel distribution: OK"
else
    # 某些版本wheel文件名可能不同，使用通配符检查
    wheel_count=$(ls dist/*.whl 2>/dev/null | wc -l)
    if [ "$wheel_count" -gt 0 ]; then
        echo "  Wheel distribution: OK ($wheel_count wheel(s))"
    else
        echo "  Wheel distribution: FAILED"
        exit 1
    fi
fi

# 运行示例
echo "[5/5] Running example..."
python3 -m schemamap.cli.main --help

echo ""
echo "========================================"
echo "  Build completed successfully!"
echo "  Packages are in dist/"
echo "========================================"
