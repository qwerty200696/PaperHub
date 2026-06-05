"""
讯飞开放平台 推理服务 HTTP 协议 测试脚本
模型: Qwen3.6-35B-A3B (讯飞 model ID: xopqwen36v35b)
接口: OpenAI 兼容格式

使用前请在 .env 中设置 XFYUN_API_KEY 环境变量。
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# ========== 配置 ==========
XFYUN_API_KEY = os.getenv("XFYUN_API_KEY", "YOUR_XFYUN_API_KEY")
BASE_URL = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
MODEL_ID = "xopqwen36v35b"  # 讯飞平台上 Qwen3.6-35B-A3B 的实际 model ID

# 绕过系统代理，避免流式连接被代理干扰
NO_PROXY = {"http": None, "https": None}


def test_basic_chat():
    """测试1: 基础对话（非流式）"""
    print("=" * 60)
    print("测试1: 基础对话（非流式）")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json={
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "请用一句话介绍你自己。"}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 512
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XFYUN_API_KEY}"
        },
        timeout=60,
        proxies=NO_PROXY
    )

    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        print(f"模型回复: {content}")
        print(f"Token 用量: prompt={usage.get('prompt_tokens', 'N/A')}, "
              f"completion={usage.get('completion_tokens', 'N/A')}, "
              f"total={usage.get('total_tokens', 'N/A')}")
    else:
        print(f"请求失败: status={response.status_code}, body={response.text}")

    return response.status_code == 200


def test_stream_chat():
    """测试2: 流式对话"""
    print("\n" + "=" * 60)
    print("测试2: 流式对话")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json={
            "model": MODEL_ID,
            "messages": [
                {"role": "user", "content": "写一首关于春天的五言绝句。"}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 256
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XFYUN_API_KEY}"
        },
        timeout=60,
        stream=True,
        proxies=NO_PROXY
    )

    if response.status_code == 200:
        print("模型回复: ", end="", flush=True)
        full_content = []
        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_content.append(content)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
        print()  # 换行
        print(f"完整内容: {''.join(full_content)}")
    else:
        print(f"请求失败: status={response.status_code}, body={response.text}")

    return response.status_code == 200


def test_multi_turn():
    """测试3: 多轮对话"""
    print("\n" + "=" * 60)
    print("测试3: 多轮对话")
    print("=" * 60)

    messages = [
        {"role": "system", "content": "你是一个房产领域的专业助手。"},
        {"role": "user", "content": "什么是'南北通透'的户型？"},
    ]

    # 第一轮
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json={
            "model": MODEL_ID,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 256
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XFYUN_API_KEY}"
        },
        timeout=60,
        proxies=NO_PROXY
    )

    if response.status_code == 200:
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        print(f"[第1轮] 助手: {reply}")

        # 将助手回复加入上下文，继续第二轮
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": "这种户型有什么缺点吗？"})

        response2 = requests.post(
            f"{BASE_URL}/chat/completions",
            json={
                "model": MODEL_ID,
                "messages": messages,
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 256
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {XFYUN_API_KEY}"
            },
            timeout=60,
            proxies=NO_PROXY
        )

        if response2.status_code == 200:
            result2 = response2.json()
            reply2 = result2["choices"][0]["message"]["content"]
            print(f"[第2轮] 助手: {reply2}")
        else:
            print(f"第2轮请求失败: status={response2.status_code}, body={response2.text}")
    else:
        print(f"第1轮请求失败: status={response.status_code}, body={response.text}")

    return response.status_code == 200


def test_with_openai_sdk():
    """测试4: 使用 OpenAI SDK 调用（与项目现有模式一致）"""
    print("\n" + "=" * 60)
    print("测试4: 使用 OpenAI SDK 调用")
    print("=" * 60)

    try:
        from openai import OpenAI
        import httpx
    except ImportError:
        print("未安装 openai/httpx 库，跳过此测试。")
        return False

    # 使用 httpx.Client 绕过系统代理
    client = OpenAI(
        api_key=XFYUN_API_KEY,
        base_url=BASE_URL,
        http_client=httpx.Client(proxies=None)
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "user", "content": "用 Python 写一个快速排序函数。"}
            ],
            temperature=0.7,
            max_tokens=512,
            stream=False
        )
        content = response.choices[0].message.content
        print(f"模型回复:\n{content}")
        return True
    except Exception as e:
        print(f"OpenAI SDK 调用失败: {e}")
        return False


if __name__ == "__main__":
    if XFYUN_API_KEY == "YOUR_XFYUN_API_KEY":
        print("请先设置 API Key！")
        print("方式1: 在 .env 文件中添加 XFYUN_API_KEY=你的密钥")
        print("方式2: 直接修改脚本中的 XFYUN_API_KEY 变量")
        exit(1)

    print(f"Base URL: {BASE_URL}")
    print(f"Model:    {MODEL_ID}")
    print(f"API Key:  {XFYUN_API_KEY[:8]}...{XFYUN_API_KEY[-4:]}")
    print()

    results = {}
    results["基础对话"] = test_basic_chat()
    results["流式对话"] = test_stream_chat()
    results["多轮对话"] = test_multi_turn()
    results["OpenAI SDK"] = test_with_openai_sdk()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
