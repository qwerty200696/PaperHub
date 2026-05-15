#!/usr/bin/env python3
"""
知乎 Cookie 自动获取工具（Chrome DevTools Protocol）

⚠️ 仅供备份参考，暂未集成到入库流程
使用方法：
1. 确保 Chrome 浏览器已关闭
2. 运行：python tools/zhihu_cookie_get.py
3. 在弹出的独立 Chrome 窗口中登录知乎
4. 回到终端按回车，自动输出 Cookie
"""
import json
import asyncio
import websockets
import requests
import subprocess
import time
import os
import signal

# 保存调试Chrome进程
CHROME_PROC = None
# 临时独立用户目录（不和你日常Chrome冲突）
USER_DATA_DIR = "/tmp/chrome_debug_zhihu"
DEBUG_PORT = 9222


def start_debug_chrome():
    global CHROME_PROC
    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    cmd = [
        chrome_bin,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "https://www.zhihu.com"
    ]
    # 后台启动，不占用终端
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    CHROME_PROC = proc
    print("✅ 已弹出独立调试Chrome，请手动登录知乎一次")
    time.sleep(15)


def stop_debug_chrome():
    # 杀掉调试Chrome进程
    global CHROME_PROC
    if CHROME_PROC:
        try:
            os.kill(CHROME_PROC.pid, signal.SIGTERM)
        except Exception:
            pass
        CHROME_PROC = None
    # 清理临时目录
    try:
        subprocess.run(["rm", "-rf", USER_DATA_DIR],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except Exception:
        pass
    print("✅ 已自动关闭调试Chrome并清理缓存")


def get_zhihu_ws_url():
    try:
        res = requests.get(f"http://127.0.0.1:{DEBUG_PORT}/json/list", timeout=5)
        pages = res.json()
        for page in pages:
            if "zhihu.com" in page.get("url", ""):
                return page.get("webSocketDebuggerUrl")
    except Exception:
        pass
    return None

async def fetch_zhihu_cookie(ws_url):
    try:
        async with websockets.connect(
            ws_url,
            ping_interval=None,
            open_timeout=10
        ) as ws:
            await ws.send(json.dumps({"id":1, "method":"Network.enable"}))
            await ws.recv()

            await ws.send(json.dumps({"id":2, "method":"Network.getCookies"}))
            raw = await ws.recv()
            data = json.loads(raw)
            cookies = data.get("result", {}).get("cookies", [])
            return "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    except Exception as e:
        print("❌ 获取Cookie失败：", e)
        return ""

async def main():
    try:
        # 启动独立调试Chrome
        start_debug_chrome()

        print("请手动登录知乎")
        input("登录后，请输入任意字符以继续...")

        # 等待获取知乎页面WS地址
        ws_url = None
        for _ in range(15):
            ws_url = get_zhihu_ws_url()
            if ws_url:
                break
            time.sleep(10)
        if not ws_url:
            print("❌ 未检测到知乎页面")
            return

        # 抓取Cookie
        cookie_str = await fetch_zhihu_cookie(ws_url)
        if cookie_str:
            print("\n🎉 获取到知乎Cookie：\n")
            print(cookie_str)
            print("\n💡 请复制以上内容粘贴到 PaperHub 入库界面的 Cookie 框")
        else:
            print("\n❌ 未获取到有效Cookie，请确认已登录知乎")
    finally:
        # 无论成功失败，都自动关闭调试Chrome+清理
        stop_debug_chrome()

if __name__ == "__main__":
    asyncio.run(main())
