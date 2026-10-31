/* static/admin.js 内容 */
async function deleteFile(filename) {
    if (!confirm(`确定要永久删除 ${filename} 吗？\n该操作不可撤销。`)) return;
    try {
        const res = await fetch(`/delete/${filename}`, { method: "DELETE" });
        const data = await res.json();
        if (data.success) {
            console.log(`文件 ${filename} 已移除`);
            location.reload();
        } else {
            alert("删除失败: 权限不足或文件不存在");
        }
    } catch (e) {
        alert("服务器连接失败");
    }
}

let lastVisitorHTML = ""; // 确保在函数外部定义了这个变量

async function syncAdminData() {
    try {
        const response = await fetch('/');
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');

        // 1. 抓取新数据
        const newCountSpan = doc.getElementById('online-count');
        const newUsageSpan = doc.getElementById('storage-usage');
        const newVisitorBox = doc.getElementById('visitor-display');

        // // 2. 实时更新数字（人数和容量随时可能变，直接更新）
        // if (newCountSpan) {
        //     const count = newCountSpan.innerText;
        //     document.getElementById('online-count').innerText = count;
        //     // 动态修改浏览器标签页标题
        //     document.title = `💎 (${count}人在线) JEGPAN 管理后台`;
        // }

        if (newUsageSpan) {
            document.getElementById('storage-usage').innerText = newUsageSpan.innerText;
        }

        // 3. 局部刷新访客列表（仅在 HTML 发生变化时更新，防止闪烁）
        if (newVisitorBox) {
            const currentVisitorHTML = newVisitorBox.innerHTML;
            if (currentVisitorHTML !== lastVisitorHTML) {
                document.getElementById('visitor-display').innerHTML = currentVisitorHTML;
                lastVisitorHTML = currentVisitorHTML;
                console.log("💎 管理员提示：访客轨迹已同步");
            }
        }
    } catch (e) {
        console.error("管理员同步失败:", e);
    }
}

// 管理员可以设定更快的频率，例如 2 秒一次
setInterval(syncAdminData, 2000);

async function openLocalFolder() {
    try {
        const res = await fetch("/open-folder", { method: "POST" });
        const data = await res.json();
        if (!data.success) {
            alert("打开失败: " + (data.error || "未知错误"));
        }
    } catch (e) {
        alert("无法连接到后端服务器");
    }
}