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
echo "[3/4] 安装 Python 包（使用虚拟环境，避免 PEP 668 限制）..."
if [ ! -d "${VENV_DIR}" ]; then
    echo "  - 创建虚拟环境: ${VENV_DIR}"
    mkdir -p "$(dirname "${VENV_DIR}")"
    python3 -m venv "${VENV_DIR}"
else
    echo "  - 复用已有虚拟环境: ${VENV_DIR}"
fi

# 在项目目录创建 .venv 软链接，兼容已有运行命令
if [ -e "${SCRIPT_DIR}/.venv" ] || [ -L "${SCRIPT_DIR}/.venv" ]; then
    rm -rf "${SCRIPT_DIR}/.venv"
fi
ln -s "${VENV_DIR}" "${SCRIPT_DIR}/.venv"

echo "  - 升级 pip（会显示下载/安装进度）..."
"${VENV_DIR}/bin/pip" install --upgrade pip --progress-bar on

echo "  - 安装 Python 依赖（首次安装可能需要几分钟）..."
"${VENV_DIR}/bin/pip" install \
    RPi.GPIO \
    spidev \
    gpiozero \
    Pillow \
    opencv-python-headless \
    opencv-contrib-python-headless \
    --progress-bar on

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
