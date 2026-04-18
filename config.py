#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
PhotoPainter 配置
直接修改以下配置即可
"""

# 图片目录（支持子文件夹，会递归搜索）
PHOTO_DIR = "/home/pi/photos"

# 刷新间隔（秒），守护进程模式下生效
# 15分钟 = 900秒，1小时 = 3600秒
REFRESH_INTERVAL = 900

# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

# 日志文件
LOG_FILE = "/var/log/photopainter.log"
