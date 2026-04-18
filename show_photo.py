#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
PhotoPainter - 墨水屏电子相框
随机从 NAS/本地目录展示照片，支持子文件夹

使用方式：
    python3 show_photo.py                           # 单次展示
    python3 show_photo.py --daemon                 # 守护进程（默认15分钟）
    python3 show_photo.py --daemon --interval 600  # 守护进程（10分钟）
    python3 show_photo.py --install                # 安装系统依赖（首次使用）
    python3 show_photo.py --simulate               # 模拟显示（无屏幕时测试）
"""

import os
import sys
import time
import random
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# 尝试导入配置
try:
    from config import PHOTO_DIR, REFRESH_INTERVAL, IMAGE_EXTENSIONS, LOG_FILE
except ImportError:
    PHOTO_DIR = "/home/pi/photos"
    REFRESH_INTERVAL = 900
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    LOG_FILE = "photopainter.log"

# 屏幕分辨率
DISP_WIDTH = 800
DISP_HEIGHT = 480

# 驱动库路径
DRIVER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
sys.path.insert(0, DRIVER_DIR)


def setup_logging():
    """配置日志"""
    log_path = Path(LOG_FILE)
    if not log_path.is_absolute():
        log_path = Path.cwd() / log_path

    if log_path.parent:
        os.makedirs(log_path.parent, exist_ok=True)

    handlers = [logging.StreamHandler()]
    try:
        handlers.insert(0, logging.FileHandler(log_path, encoding='utf-8'))
    except OSError as e:
        fallback_path = Path.cwd() / "photopainter.log"
        handlers.insert(0, logging.FileHandler(fallback_path, encoding='utf-8'))
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=handlers
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"日志文件不可写，已回退到: {fallback_path} ({e})")
        return logger

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)


def find_all_photos(directory: str) -> list:
    """递归查找目录下所有图片"""
    photos = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if Path(file).suffix.lower() in IMAGE_EXTENSIONS:
                photos.append(os.path.join(root, file))
    return photos


def select_random_photo(directory: str) -> str | None:
    """从目录中随机选择一张照片"""
    photos = find_all_photos(directory)
    if not photos:
        return None
    return random.choice(photos)


def process_image_opencv(image_path: str, logger) -> any:
    """使用 OpenCV + 智能裁剪处理图片（高质量）"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    logger.info("使用 OpenCV 智能裁剪...")
    image = cv2.imread(image_path)
    if image is None:
        return None

    img_h, img_w = image.shape[:2]
    logger.info(f"原始图片分辨率: {img_w} x {img_h}")

    # 检查是否需要旋转
    if img_w == DISP_HEIGHT and img_h == DISP_WIDTH:
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        logger.info("图片已旋转 90°")
        img_h, img_w = image.shape[:2]

    img_aspect = img_w / img_h
    disp_aspect = DISP_WIDTH / DISP_HEIGHT

    # 等比缩放
    if img_aspect < disp_aspect:
        resize = (DISP_WIDTH, int(DISP_WIDTH / img_aspect))
    else:
        resize = (int(DISP_HEIGHT * img_aspect), DISP_HEIGHT)

    image = cv2.resize(image, resize)
    img_h, img_w = image.shape[:2]

    # 中心裁剪
    x_off = max(0, (img_w - DISP_WIDTH) // 2)
    y_off = max(0, (img_h - DISP_HEIGHT) // 2)
    image = image[y_off:y_off + DISP_HEIGHT, x_off:x_off + DISP_WIDTH]

    logger.info(f"处理后分辨率: {image.shape[1]} x {image.shape[0]}")
    return image


def process_image_pil(image_path: str, logger) -> any:
    """使用 PIL 简单缩放处理图片（无 OpenCV 时备用）"""
    try:
        from PIL import Image
    except ImportError:
        return None

    logger.info("使用 PIL 缩放...")
    img = Image.open(image_path)
    logger.info(f"原始图片分辨率: {img.size}")

    # 强制转换为 RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 检查是否需要旋转
    w, h = img.size
    if w == DISP_HEIGHT and h == DISP_WIDTH:
        img = img.rotate(90, expand=True)
        logger.info("图片已旋转 90°")
        w, h = img.size

    # 等比缩放 + 中心裁剪
    disp_aspect = DISP_WIDTH / DISP_HEIGHT
    img_aspect = w / h

    if img_aspect < disp_aspect:
        new_w = int(h * disp_aspect)
        new_h = h
        x_off = (w - new_w) // 2
        y_off = 0
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img = img.crop((x_off, y_off, x_off + DISP_WIDTH, y_off + DISP_HEIGHT))
    else:
        new_w = w
        new_h = int(w / disp_aspect)
        x_off = 0
        y_off = (h - new_h) // 2
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img = img.crop((x_off, y_off, x_off + DISP_WIDTH, y_off + DISP_HEIGHT))

    logger.info(f"处理后分辨率: {img.size}")
    return img


def display_image(image, logger, simulate: bool = False) -> bool:
    """在墨水屏上显示图片"""
    if simulate:
        logger.info("[模拟模式] 跳过实际屏幕显示")
        return True

    try:
        from waveshare_epd import epd7in3e
    except ImportError as e:
        logger.error(f"无法加载墨水屏驱动: {e}")
        return False

    try:
        logger.info("初始化墨水屏...")
        epd = epd7in3e.EPD()
        epd.init()
        logger.info("墨水屏初始化完成")

        # 处理图片（优先用 OpenCV，不可用时自动回退 PIL）
        if isinstance(image, str):
            proc_img = process_image_opencv(image, logger)
            if proc_img is None:
                proc_img = process_image_pil(image, logger)
        else:
            proc_img = image

        if proc_img is None:
            logger.error("图片处理失败")
            return False

        # OpenCV ndarray (BGR) → RGB；PIL 图像直接使用
        if hasattr(proc_img, 'shape') and hasattr(proc_img, '__getitem__'):
            proc_img = proc_img[:, :, ::-1]

        from PIL import Image as PILImage
        if not isinstance(proc_img, PILImage.Image):
            proc_img = PILImage.fromarray(proc_img)

        logger.info("刷新屏幕...")
        epd.display(epd.getbuffer(proc_img))
        time.sleep(1)
        epd.sleep()
        logger.info("显示完成，屏幕进入休眠")
        return True

    except Exception as e:
        logger.error(f"显示失败: {e}")
        try:
            from waveshare_epd import epdconfig
            epdconfig.module_exit()
        except:
            pass
        return False


def show_single_photo(directory: str, logger, simulate: bool = False) -> bool:
    """展示一张随机照片"""
    photo_path = select_random_photo(directory)
    if not photo_path:
        logger.warning(f"目录 {directory} 中未找到图片")
        return False
    logger.info(f"随机选择: {photo_path}")
    return display_image(photo_path, logger, simulate)


def install_dependencies(logger):
    """安装系统依赖（首次设置时调用）"""
    logger.info("开始安装系统依赖...")

    commands = [
        # 系统包
        ["sudo", "apt-get", "update"],
        ["sudo", "apt-get", "install", "-y", "python3-pip python3-pil python3-opencv",
         "libopencv-core-dev libopencv-highgui-dev python3-dev gcc",
         "git", "libjpeg-dev", "zlib1g-dev", "libpng-dev"],
        # Python 包
        ["pip3", "install", "--upgrade", "pip"],
        ["pip3", "install", "RPi.GPIO", "spidev", "gpiozero", "Pillow"],
    ]

    for cmd in commands:
        logger.info(f"执行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"命令部分输出: {result.stderr[:500]}")

    # 检查 SPI
    result = subprocess.run(["ls", "/dev/spidev0.0"], capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("✓ SPI 已启用")
    else:
        logger.warning("⚠ SPI 可能未启用，请运行: sudo raspi-config → Interface Options → SPI → Enable")

    logger.info("安装完成！现在可以运行 python3 show_photo.py")
    return True


def daemon_mode(directory: str, interval: int, logger, simulate: bool = False):
    """守护进程模式"""
    logger.info(f"启动守护进程模式，间隔 {interval} 秒")
    logger.info(f"图片目录: {directory}")
    logger.info(f"模式: {'模拟' if simulate else '实际'}显示")

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"=== 刷新时刻: {timestamp} ===")
        success = show_single_photo(directory, logger, simulate)
        if success:
            logger.info(f"显示成功，{interval} 秒后再次刷新")
        else:
            logger.warning("显示失败，继续尝试")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="PhotoPainter 墨水屏电子相框",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--dir', '-d', default=PHOTO_DIR,
                        help=f'图片目录路径 (默认: {PHOTO_DIR})')
    parser.add_argument('--interval', '-i', type=int, default=REFRESH_INTERVAL,
                        help=f'刷新间隔秒数 (默认: {REFRESH_INTERVAL})')
    parser.add_argument('--daemon', action='store_true',
                        help='守护进程模式（定时刷新）')
    parser.add_argument('--once', action='store_true',
                        help='单次展示（默认行为）')
    parser.add_argument('--install', action='store_true',
                        help='安装系统依赖（首次使用）')
    parser.add_argument('--simulate', '-s', action='store_true',
                        help='模拟模式（无屏幕时测试）')
    args = parser.parse_args()

    logger = setup_logging()

    # 安装模式
    if args.install:
        install_dependencies(logger)
        sys.exit(0)

    # 检查目录
    if not os.path.isdir(args.dir):
        logger.error(f"目录不存在: {args.dir}")
        logger.error("请先创建目录或修改 config.py 中的 PHOTO_DIR")
        sys.exit(1)

    # 运行模式
    if args.daemon:
        daemon_mode(args.dir, args.interval, logger, args.simulate)
    else:
        # 默认单次模式
        success = show_single_photo(args.dir, logger, args.simulate)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
