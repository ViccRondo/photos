# PhotoPainter 🖼️

Waveshare 7.3" 六色墨水屏电子相框驱动，支持 NAS 图片随机展示。

**分辨率**: 800 × 480（黑、白、绿、蓝、红、黄六色）

---

## 快速开始

### 1. 安装（一键，在树莓派上运行一次）

```bash
git clone https://github.com/ViccRondo/photos.git
cd photos
chmod +x install.sh
./install.sh
```

> ⚠️ 如果 SPI 未启用，按提示运行 `sudo raspi-config → Interface Options → SPI → Enable`，然后重启。

> ℹ️ 安装脚本会把虚拟环境创建在项目目录外（默认 `~/.venvs/photopainter`），并在项目内生成 `.venv` 软链接。这样即使你删库重拉，已安装环境也能复用。虚拟环境会使用 `--system-site-packages`，可直接复用系统安装的 `python3-opencv` / `python3-pil`，避免反复下载大体积 wheel。
>
> 如需自定义虚拟环境路径，可在安装前设置：
> `export PHOTOPAINTER_VENV_DIR=/your/path/venv`

### 2. 配置

编辑 `config.py`，修改图片目录：

```python
PHOTO_DIR = "/mnt/nas/photos"  # NAS 挂载路径，或本地目录
```

### 3. 运行

```bash
# 可选：先确认系统包在 venv 中可见
source .venv/bin/activate
python -c "import cv2; print(cv2.__version__)"
python -c "from PIL import Image; print('PIL OK')"

# 单次展示（自动选一张随机图片）
./.venv/bin/python show_photo.py

# 守护进程模式（每15分钟自动换图）
./.venv/bin/python show_photo.py --daemon

# 指定刷新间隔（5分钟 = 300秒）
./.venv/bin/python show_photo.py --daemon --interval 300

# 模拟模式（无屏幕时测试图片处理）
./.venv/bin/python show_photo.py --simulate
```

---

## 开机自启（systemd）

```bash
# 创建服务
sudo nano /etc/systemd/system/photopainter.service
```

写入以下内容：

```ini
[Unit]
Description=PhotoPainter e-Paper Photo Frame
After=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/photos
ExecStart=/home/pi/photos/.venv/bin/python /home/pi/photos/show_photo.py --daemon --interval 900
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable photopainter
sudo systemctl start photopainter
```

查看状态：

```bash
sudo systemctl status photopainter
tail -f /var/log/photopainter.log
```

---

## NAS 挂载

推荐使用 SMB/CIFS 挂载：

```bash
# 安装 cifs-utils
sudo apt install -y cifs-utils

# 创建挂载点
sudo mkdir -p /mnt/nas

# 挂载（按实际情况修改）
sudo mount -t cifs //NAS_IP/Photos /mnt/nas -o username=xxx,password=xxx,uid=1000,gid=1000

# 开机自动挂载（/etc/fstab）
//NAS_IP/Photos /mnt/nas cifs username=xxx,password=xxx,uid=1000,gid=1000 0 0
```

---

## 图片要求

- 支持格式：JPG、PNG、BMP、GIF、WebP
- 支持子文件夹（会自动递归搜索）
- 脚本会自动缩放/裁剪到 800×480
- 建议图片分辨率 ≥ 800×480 以获得最佳效果

---

## 目录结构

```
photos/
├── show_photo.py       # 主程序
├── config.py           # 配置文件
├── install.sh          # 一键安装脚本
├── requirements.txt    # Python 依赖
├── lib/
│   └── waveshare_epd/  # 官方墨水屏驱动（MIT 协议）
│       ├── epd7in3e.py
│       └── epdconfig.py
└── README.md
```

其中 `.venv` 是一个软链接，指向项目外的真实虚拟环境目录（默认 `~/.venvs/photopainter`）。

---

## 常见问题

**Q: 显示异常/偏色？**
A: 六色墨水屏刷新会有残影，首次全刷建议断电静置 30 秒。

**Q: 报 SPI 错误？**
A: 运行 `sudo raspi-config` 启用 SPI 后重启。

**Q: 图片方向不对？**
A: 当前版本会在输出前整体旋转 180°，并对竖图自动旋转 90° 后再适配。

**Q: 如何停止守护进程？**
A: `pkill -f show_photo.py` 或 `sudo systemctl stop photopainter`
