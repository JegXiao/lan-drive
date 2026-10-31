# 局域网网盘 | LAN Drive

> 基于 FastAPI 的局域网文件互传网盘：任何人上传、下载、拖拽传输，服务器本机打开即是管理员控制台。仅供可信局域网使用。

**简体中文** · [ English](#english)

---

## 功能特性

- **所有用户**：上传文件（可附昵称，存于浏览器本地）、拖拽上传、下载、明暗主题切换；文件列表每 5 秒自动刷新。
- **管理员（即服务器本机）**：实时在线人数与访客列表（IP + 设备识别）、网盘总占用、删除任意文件、一键打开本地存储目录。
- 身份由来源 IP 决定：`127.0.0.1` / `::1` 即管理员，局域网其他设备为普通用户，无登录系统。

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

浏览器访问控制台打印的 `http://<局域网IP>:8000`（默认端口 8000）。

## 配置

**文件存储目录**：`main.py` 顶部的 `WATCH_DIR`（默认 `r'E:\JEGPAN'`），改成你自己的路径。

### 启用 HTTPS（可选）

```bash
cd ssl
python cert_gen.py
```

⚠️ 必须**先进入 `ssl/` 目录再运行**：脚本把证书写到当前工作目录，而 `main.py` 只认 `ssl/cert.pem` 与 `ssl/key.pem`。

存在证书则以 HTTPS 启动，否则自动降级 HTTP（自签证书浏览器会提示不受信任，属正常现象）。

## 说明

- `file_records.json` 是运行时生成的上传记录（谁传的、昵称、是否管理员），已加入 `.gitignore`，无需提交。
- 上传同名文件会直接覆盖；本系统**无任何鉴权**，请只在可信局域网中使用。

---

# English

> A FastAPI-powered file sharing drive for your LAN: anyone can upload (with drag & drop) and download, while the server machine itself gets an admin console. For trusted LANs only.

## Features

- **All users**: upload with an optional nickname (stored in localStorage), drag & drop, download, light/dark theme; the file list auto-refreshes every 5 seconds.
- **Admin (the server machine itself)**: live online-user list (IP + device fingerprint), total storage usage, delete any file, open the storage folder locally.
- Identity is decided by source IP: `127.0.0.1` / `::1` is admin, everyone else on the LAN is a regular user. There is no login system.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Open the printed `http://<LAN-IP>:8000` in a browser (default port 8000).

## Configuration

**Storage folder**: `WATCH_DIR` at the top of `main.py` (default `r'E:\JEGPAN'`) — change it to your own path.

### Enable HTTPS (optional)

```bash
cd ssl
python cert_gen.py
```

⚠️ You must run it **from inside the `ssl/` folder**: the script writes to the current working directory, while `main.py` only looks for `ssl/cert.pem` and `ssl/key.pem`.

With certificates present the server starts as HTTPS; otherwise it falls back to HTTP automatically (self-signed certificates trigger a browser warning — that is expected).

## Notes

- `file_records.json` is a runtime-generated upload record (uploader IP/nickname/admin flag); it is gitignored and should not be committed.
- Uploading a file with an existing name overwrites it. There is **no authentication at all** — use only on a trusted LAN.
