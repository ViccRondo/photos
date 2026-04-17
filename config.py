#!/usr/bin/env python3
"""
PhotoPainter 配置
"""

import os

# 图片目录（支持子文件夹）
PHOTO_DIR = "/home/pi/photos"

# 刷新间隔（秒），15分钟 = 900秒
REFRESH_INTERVAL = 900

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}

# 日志文件
LOG_FILE = "/var/log/photopainter.log"
