#!/usr/bin/env python3
"""
PhotoPainter - 墨水屏电子相框
随机展示图片目录中的照片，支持子文件夹

用法：
    python3 show_photo.py                    # 单次展示
    python3 show_photo.py --daemon           # 守护进程模式（定时刷新）
    python3 show_photo.py --dir /path/to/dir # 指定目录
"""

import os
import sys
import time
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 尝试导入墨水屏驱动
try:
    from waveshare_epd import epd7in3e
    EPD_AVAILABLE = True
except ImportError:
    EPD_AVAILABLE = False
    print("[警告] 未找到 waveshare-epd 库，将仅保存图片路径到日志")

from config import (
    PHOTO_DIR,
    REFRESH_INTERVAL,
    IMAGE_EXTENSIONS,
    LOG_FILE
)


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
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


def display_on_epd(image_path: str, logger) -> bool:
    """在墨水屏上显示图片"""
    if not EPD_AVAILABLE:
        logger.info(f"图片路径: {image_path}")
        return True

    try:
        logger.info(f"初始化墨水屏...")
        epd = epd7in3e.EPD()
        epd.init()
        logger.info(f"显示图片: {image_path}")

        # 使用 PIL 加载和缩放图片
        from PIL import Image
        img = Image.open(image_path)
        
        # 获取墨水屏分辨率
        width = epd.width
        height = epd.height
        
        # 缩放图片以适应屏幕
        img = img.convert('RGB')
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # 墨水屏是单色的，这里做简单转换
        # 实际使用时可能需要根据屏幕特性调整
        img = img.convert('1', dither=Image.Dither.FLOYDSTEINBERG)

        epd.display(epd.getbuffer(img))
        
        logger.info("图片显示完成")
        return True

    except Exception as e:
        logger.error(f"显示失败: {e}")
        return False


def show_photo(directory: str, logger) -> bool:
    """展示一张随机照片"""
    photo_path = select_random_photo(directory)
    
    if not photo_path:
        logger.warning(f"目录 {directory} 中未找到图片")
        return False

    logger.info(f"随机选择: {photo_path}")
    return display_on_epd(photo_path, logger)


def daemon_mode(directory: str, logger):
    """守护进程模式：定时刷新"""
    logger.info(f"启动守护进程模式，间隔 {REFRESH_INTERVAL} 秒")
    logger.info(f"图片目录: {directory}")

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"=== 刷新时刻: {timestamp} ===")
        show_photo(directory, logger)
        logger.info(f"等待 {REFRESH_INTERVAL} 秒...")
        time.sleep(REFRESH_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description="PhotoPainter 墨水屏电子相框")
    parser.add_argument('--dir', '-d', default=PHOTO_DIR, help='图片目录路径')
    parser.add_argument('--daemon', action='store_true', help='守护进程模式')
    parser.add_argument('--once', action='store_true', help='单次展示')
    args = parser.parse_args()

    logger = setup_logging()

    # 检查目录
    if not os.path.isdir(args.dir):
        logger.error(f"目录不存在: {args.dir}")
        sys.exit(1)

    # 运行模式
    if args.daemon:
        daemon_mode(args.dir, logger)
    else:
        # 默认单次模式
        success = show_photo(args.dir, logger)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
