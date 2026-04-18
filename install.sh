#!/bin/bash
# PhotoPainter 安装脚本 - 在树莓派上运行一次即可
set -e

echo "======================================"
echo " PhotoPainter 安装脚本"
echo "======================================"

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
echo "[3/4] 安装 Python 包..."
pip3 install --upgrade pip -q
pip3 install RPi.GPIO spidev gpiozero Pillow -q

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
echo "3. 运行: python3 show_photo.py --once    (单次展示)"
echo "   或: python3 show_photo.py --daemon   (定时刷新)"
echo ""
