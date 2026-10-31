/**
 * 1. 初始化监听器
 * 确保页面加载完成后，绑定“选择文件”后的更名逻辑
 */
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');

    // 检查文件输入框是否存在
    if (fileInput) {
        // 监听文件选择变动（点击上传按钮时触发）
        fileInput.addEventListener('change', function() {
            updateFileDisplay(this.files);
        });
    }
});

/**
 * 界面显示更新逻辑（辅助函数）
 * 供初始化监听器和拖拽逻辑共同调用，确保文件名实时刷新并控制上传按钮显示
 */
function updateFileDisplay(files) {
    const fileDisplay = document.getElementById('fileNameDisplay');
    const uploadBtn = document.querySelector('.btn-primary'); // 获取确认上传按钮
    if (!fileDisplay || !uploadBtn) return;

    if (files && files.length > 0) {
        // 获取文件名并处理过长的显示
        const fileName = files[0].name;
        fileDisplay.innerText = fileName.length > 20 ? fileName.substring(0, 20) + "..." : fileName;

        // 根据当前模式设置文字高亮颜色
        const isAdmin = document.body.classList.contains('mode-admin');
        fileDisplay.style.color = isAdmin ? "#fd9f00" : "var(--primary)";

        // 有文件时显示上传按钮
        uploadBtn.classList.add('show');
    } else {
        // 未选择文件时的默认状态
        fileDisplay.innerText = "未选择文件";
        fileDisplay.style.color = "#888";

        // 无文件时隐藏上传按钮
        uploadBtn.classList.remove('show');
    }
}

/**
 * 2. 亮暗模式切换逻辑
 * 处理主题存储、图标切换，并针对管理员模式进行空引用保护
 */
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;

    // --- 关键保护点 ---
    // 如果是管理员模式，Jinja2 不渲染此按钮。若找不到按钮则静默退出
    if (!themeToggle) return;

    const sunIcon = themeToggle.querySelector('.icon-sun');
    const moonIcon = themeToggle.querySelector('.icon-moon');

    // 1. 初始化检查
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        enableDarkMode();
    }

    // 2. 绑定点击事件
    themeToggle.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });

    function enableDarkMode() {
        body.classList.add('dark-mode');
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = 'inline';
        localStorage.setItem('theme', 'dark');
    }

    function disableDarkMode() {
        body.classList.remove('dark-mode');
        if (sunIcon) sunIcon.style.display = 'inline';
        if (moonIcon) moonIcon.style.display = 'none';
        localStorage.setItem('theme', 'light');
    }
});

/**
 * 3. 文件上传核心逻辑
 * 处理按钮点击、Fetch 请求以及上传后的 UI 重置
 */
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const status = document.getElementById('status');
    const fileDisplay = document.getElementById('fileNameDisplay');
    const uploadBtn = document.querySelector('.btn-primary');

    if (!fileInput || fileInput.files.length === 0) return alert("请先选择文件");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // --- 携带昵称逻辑 ---
    const savedNickname = localStorage.getItem('userNickname');
    if (savedNickname) {
        formData.append("nickname", savedNickname);
    }

    // --- 1. 上传开始前的动作 ---
    uploadBtn.disabled = true;
    uploadBtn.style.opacity = "0.7";
    uploadBtn.style.cursor = "not-allowed";

    if (status) {
        status.innerText = "🚀 正在上传，请稍候...";
        status.style.color = "var(--primary)";
    }

    try {
        // --- 2. 执行实际的上传 Fetch 请求 ---
        const res = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        if (res.ok) {
            // --- 3. 上传成功后的 UI 响应 ---
            if (status) {
                status.innerText = "✅ 上传成功！正在刷新列表...";
                status.style.color = "var(--success)";
            }

            fileInput.value = "";
            updateFileDisplay(null); // 自动隐藏上传按钮

            setTimeout(() => location.reload(), 800);
        } else {
            throw new Error("服务器响应错误");
        }
    } catch (e) {
        // --- 4. 异常捕获与状态恢复 ---
        if (status) {
            status.innerText = "❌ 上传失败，请重试";
            status.style.color = "var(--danger)";
        }
        uploadBtn.disabled = false;
        uploadBtn.style.opacity = "1";
        uploadBtn.style.cursor = "pointer";
        console.error("上传出错:", e);
    }
}

/**
 * 4. 自动同步逻辑 (文件变更检测)
 */
let lastFileCount = -1;

async function syncBasicData() {
    try {
        const response = await fetch('/');
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');

        const currentFiles = doc.querySelectorAll('tbody tr').length;

        if (lastFileCount !== -1 && currentFiles !== lastFileCount) {
            console.log("检测到文件列表更新，执行自动刷新...");
            location.reload();
            return;
        }

        lastFileCount = currentFiles;
    } catch (e) {
        console.error("基础数据同步失败:", e);
    }
}

// 设定每 5 秒执行一次同步
setInterval(syncBasicData, 5000);

/**
 * 5. 拖拽交互逻辑
 */
document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.container');
    const fileInput = document.getElementById('fileInput');

    if (!container || !fileInput) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        container.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    container.addEventListener('dragenter', () => container.classList.add('drag-over'));

    container.addEventListener('dragleave', (e) => {
        if (e.relatedTarget === null || !container.contains(e.relatedTarget)) {
            container.classList.remove('drag-over');
        }
    });

    container.addEventListener('drop', (e) => {
        container.classList.remove('drag-over');
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files.length > 0) {
            fileInput.files = files;
            updateFileDisplay(files);
        }
    });
});

/**
 * 6. 昵称管理逻辑
 * 注意：必须放在全局作用域，确保 HTML 的 onclick 能找到它
 */
function changeNickname() {
    const oldName = localStorage.getItem('userNickname') || "";
    const newName = prompt("请输入您的昵称（留空并确定可清除）：", oldName);

    if (newName === null) return;

    const trimmedName = newName.trim();
    if (trimmedName === "") {
        localStorage.removeItem('userNickname');
        alert("昵称已清除，上传将仅显示 IP");
    } else {
        localStorage.setItem('userNickname', trimmedName);
        alert("昵称设置成功：" + trimmedName);
    }
}