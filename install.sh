#!/bin/bash
# PhotoPainter 安装脚本 - 在树莓派上运行一次即可
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_VENV_DIR="${HOME}/.venvs/photopainter"
VENV_DIR="${PHOTOPAINTER_VENV_DIR:-${DEFAULT_VENV_DIR}}"

echo "======================================"
echo " PhotoPainter 安装脚本"
echo "======================================"
echo "虚拟环境路径: ${VENV_DIR}"

# 检查是否在树莓派上运行
if [ ! -f /usr/bin/raspi-config ]; then
    echo "警告: 未检测到 raspi-config，可能不在树莓派上"
fi

echo ""
echo "[1/4] 更新 apt..."
sudo apt-get update -qq

echo ""
echo "[2/4] 安装系统依赖..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-pil \
    python3-opencv \
    libopencv-highgui-dev \
    python3-dev \
    gcc \
    git \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libfreetype6-dev

echo ""
echo "[3/4] 准备 Python 虚拟环境（共享系统包，避免重复下载大型 wheel）..."
if [ ! -d "${VENV_DIR}" ]; then
    echo "  - 创建虚拟环境: ${VENV_DIR}"
    mkdir -p "$(dirname "${VENV_DIR}")"
    python3 -m venv --system-site-packages "${VENV_DIR}"
else
    echo "  - 复用已有虚拟环境: ${VENV_DIR}"
fi

# 在项目目录创建 .venv 软链接，兼容已有运行命令
if [ -e "${SCRIPT_DIR}/.venv" ] || [ -L "${SCRIPT_DIR}/.venv" ]; then
    rm -rf "${SCRIPT_DIR}/.venv"
fi
ln -s "${VENV_DIR}" "${SCRIPT_DIR}/.venv"

echo "  - 安装 Python 依赖（仅安装系统仓库没有的 GPIO 相关包）..."
"${VENV_DIR}/bin/pip" install \
    RPi.GPIO \
    spidev \
    gpiozero \
    --progress-bar on

echo "  - 验证系统包可见性..."
"${VENV_DIR}/bin/python" -c "import cv2; print('cv2 OK:', cv2.__version__)"
"${VENV_DIR}/bin/python" -c "from PIL import Image; print('PIL OK')"

echo ""
echo "[4/4] 检查 SPI 状态..."
if [ -c /dev/spidev0.0 ]; then
    echo "✓ SPI 已启用 (/dev/spidev0.0 存在)"
else
    echo "⚠ SPI 未启用！请运行: sudo raspi-config"
    echo "  选择: Interface Options → SPI → Enable"
    echo "  然后重启: sudo reboot"
fi

echo ""
echo "======================================"
echo " 安装完成！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 将 NAS 图片目录挂载到 /home/pi/photos"
echo "2. 修改 config.py 中的 PHOTO_DIR 为你的图片路径"
echo "3. 运行: ${SCRIPT_DIR}/.venv/bin/python show_photo.py --once    (单次展示)"
echo "   或: ${SCRIPT_DIR}/.venv/bin/python show_photo.py --daemon   (定时刷新)"
echo ""
