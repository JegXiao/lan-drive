from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os, shutil, time, socket, sys, asyncio, logging, json
import subprocess

# --- [1. 初始化配置与路径定义] ---
# 初始化 FastAPI 实例
app = FastAPI()

# 文件存储绝对路径
WATCH_DIR = r'E:\JEGPAN'
# 项目根目录绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 文件元数据记录路径（用于存储 IP 和昵称）
RECORDS_FILE = os.path.join(BASE_DIR, "file_records.json")

# 确保必要的文件夹存在
for folder in [WATCH_DIR, os.path.join(BASE_DIR, "static"), os.path.join(BASE_DIR, "ssl")]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 挂载模板与静态资源逻辑
templates = Jinja2Templates(directory=BASE_DIR)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 在内存中存储活跃会话
active_sessions = {}


# --- [2. 元数据持久化工具函数] ---
# 负责读取和保存文件关联的昵称与 IP 信息
def load_records():
    """从 JSON 文件加载文件上传记录"""
    if os.path.exists(RECORDS_FILE):
        try:
            with open(RECORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_records(records):
    """将记录持久化保存到 JSON 文件"""
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)


# --- [3. 中间件：实时访问追踪] ---
# 实现“实时刷新”和“在线统计”的核心逻辑
@app.middleware("http")
async def track_visitors(request: Request, call_next):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")

    # 更新活跃会话记录
    active_sessions[client_ip] = {
        "last_seen": time.time(),
        "ua": user_agent
    }

    # 清理离线用户
    now = time.time()
    for ip in list(active_sessions.keys()):
        if now - active_sessions[ip]["last_seen"] > 5:
            del active_sessions[ip]

    return await call_next(request)


# --- [4. 路由逻辑：首页渲染] ---
# 处理主页请求，扫描文件库并匹配上传者元数据
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    is_admin = request.client.host in ("127.0.0.1", "localhost", "::1")
    records = load_records()

    def parse_ua(ua_string):
        ua = ua_string.lower()
        if "iphone" in ua or "ipad" in ua:
            device = "🍎 Apple 设备"
        elif "android" in ua:
            device = "📱 Android 手机"
        elif "windows" in ua:
            device = "💻 Windows 电脑"
        elif "macintosh" in ua:
            device = "🖥️ Mac 电脑"
        else:
            device = "🌐 未知设备"

        if "edg" in ua:
            browser = "Edge"
        elif "chrome" in ua and "safari" in ua:
            browser = "Chrome"
        elif "safari" in ua:
            browser = "Safari"
        elif "firefox" in ua:
            browser = "Firefox"
        else:
            browser = "浏览器"
        return f"{device} ({browser})"

    display_visitors = {}
    if is_admin:
        for ip, info in active_sessions.items():
            display_visitors[ip] = {"device": parse_ua(info["ua"])}

    files = []
    total_bytes = 0
    if os.path.exists(WATCH_DIR):
        for f in os.listdir(WATCH_DIR):
            p = os.path.join(WATCH_DIR, f)
            if os.path.isfile(p):
                size = os.path.getsize(p)
                total_bytes += size
                info = records.get(f, {"ip": "未知", "nickname": "", "is_admin": False})
                files.append({
                    "name": f,
                    "size": format_size(size),
                    "ip": info["ip"],
                    "nickname": info["nickname"],
                    "is_admin": info["is_admin"]
                })

    return templates.TemplateResponse("index.html", {
        "request": request,
        "files": files,
        "is_admin": is_admin,
        "visitors": display_visitors if is_admin else None,
        "total_usage": format_size(total_bytes)
    })


# --- [5. 路由逻辑：文件上传] ---
# 接收上传的文件，并同步保存发送者的昵称和 IP 信息
@app.post("/upload")
async def upload(request: Request, file: UploadFile = File(...), nickname: str = Form(None)):
    client_ip = request.client.host
    is_admin_upload = client_ip in ("127.0.0.1", "localhost", "::1")

    dest = os.path.join(WATCH_DIR, file.filename)
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    records = load_records()
    records[file.filename] = {
        "ip": client_ip,
        "nickname": nickname if nickname else "",
        "is_admin": is_admin_upload
    }
    save_records(records)
    return {"message": "上传成功"}


# --- [6. 路由逻辑：文件下载与删除] ---
# 处理文件下载请求以及管理员的删除操作
@app.get("/download/{filename}")
async def download(filename: str):
    file_path = os.path.join(WATCH_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="文件未找到")


@app.delete("/delete/{filename}")
async def delete_file(filename: str, request: Request):
    if request.client.host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="拒绝访问")

    file_path = os.path.join(WATCH_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        records = load_records()
        if filename in records:
            del records[filename]
            save_records(records)
        return {"success": True}
    return {"success": False}


# --- [7. 路由逻辑：系统操作] ---
# 仅允许本机管理员打开本地存储目录
@app.post("/open-folder")
async def open_folder(request: Request):
    if request.client.host not in ("127.0.0.1", "localhost", "::1"):
        raise HTTPException(status_code=403, detail="拒绝访问")
    try:
        if sys.platform == 'win32':
            os.startfile(WATCH_DIR)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', WATCH_DIR])
        else:
            subprocess.Popen(['xdg-open', WATCH_DIR])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- [8. 辅助功能函数] ---
# 格式化字节大小
def format_size(bytes):
    if bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / (1024 * 1024):.2f} MB"
    return f"{bytes / (1024 * 1024 * 1024):.2f} GB"


# --- [9. 服务启动与日志静默配置] ---
if __name__ == "__main__":
    import uvicorn

    # Windows 异步补丁
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 核心：日志静默配置，屏蔽 200 OK 等访问信息
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": True
            }
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr"
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"level": "WARNING"},  # 关键：屏蔽正常的访问日志
        },
    }


    # 获取局域网 IP
    def get_host_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip


    local_ip, port = get_host_ip(), 8000
    cert_path, key_path = os.path.join(BASE_DIR, "ssl/cert.pem"), os.path.join(BASE_DIR, "ssl/key.pem")

    # 基础运行参数
    run_args = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": port,
        "log_config": LOGGING_CONFIG,
        "reload": False
    }

    # 核心：判定 HTTPS/HTTP 模式并打印精美终端界面
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("\n" + "✅" * 25)
        print("🛡️  JEGPAN HTTPS 系统已就绪 (已开启静音模式)")
        print(f"🔗 外部访问: https://{local_ip}:{port}")
        print(f"🏠 本机管理: https://127.0.0.1:{port}")
        print("✅" * 25 + "\n")
        run_args["ssl_keyfile"] = key_path
        run_args["ssl_certfile"] = cert_path
    else:
        print("\n" + "⚠️" * 25)
        print("🚀 以 HTTP 模式启动 (未在 ssl/ 发现证书)")
        print(f"🔗 访问地址: http://{local_ip}:{port}")
        print("⚠️" * 25 + "\n")

    uvicorn.run(**run_args)