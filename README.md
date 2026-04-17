# PhotoPainter 墨水屏电子相框

Raspberry Pi Zero W + Waveshare 7.3" 三色墨水屏驱动脚本。

## 功能

- 从指定目录（含子文件夹）随机选择照片展示
- 支持两种运行模式：单次 / 守护进程
- 适配 epd7in3e 墨水屏

## 安装

### 1. 安装系统依赖

```bash
# Raspberry Pi OS
sudo apt update
sudo apt install -y python3-pip python3-pil

# 安装墨水屏驱动（参考 Waveshare 官方）
cd ~
git clone https://github.com/waveshare/e-Paper
cd e-Paper/RaspberryPi\&JetsonNano/python
sudo python3 install -e .
```

### 2. 配置图片目录

编辑 `config.py`，修改 `PHOTO_DIR` 为你的 NAS 挂载路径：

```python
PHOTO_DIR = "/home/pi/photos"  # 或 NAS 挂载路径
```

### 3. 安装依赖

```bash
pip3 install -r requirements.txt
```

## 使用方法

### 单次展示

```bash
python3 show_photo.py
```

### 指定目录

```bash
python3 show_photo.py --dir /path/to/your/photos
```

### 守护进程模式（推荐）

后台持续运行，每 15 分钟自动更换图片：

```bash
nohup python3 show_photo.py --daemon &
```

### Cron 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每15分钟执行一次）
*/15 * * * * /usr/bin/python3 /home/pi/photos/show_photo.py >> /var/log/photopainter.log 2>&1
```

## NAS 挂载建议

推荐使用 SMB/CIFS 挂载 NAS 图片目录：

```bash
# 安装 cifs-utils
sudo apt install -y cifs-utils

# 挂载 NAS
sudo mount -t cifs //NAS_IP/Photos /mnt/nas/Photos -o username=xxx,password=xxx,uid=1000,gid=1000

# 启动时自动挂载（添加到 /etc/fstab）
//NAS_IP/Photos /mnt/nas/Photos cifs username=xxx,password=xxx,uid=1000,gid=1000 0 0
```

## 日志

日志文件位置：`/var/log/photopainter.log`

```bash
# 查看日志
tail -f /var/log/photopainter.log
```

## 配置

编辑 `config.py` 修改以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| PHOTO_DIR | /home/pi/photos | 图片目录 |
| REFRESH_INTERVAL | 900 | 刷新间隔（秒） |
| LOG_FILE | /var/log/photopainter.log | 日志文件 |

## 目录结构

```
photos/
├── show_photo.py      # 主程序
├── config.py          # 配置文件
├── requirements.txt   # Python 依赖
└── README.md          # 说明文档
```

## 作者

花火 🎭
