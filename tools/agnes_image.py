#!/usr/bin/env python3
"""
Agnes Image 2.1 Flash - Python 图像生成脚本
支持文生图 (Text-to-Image) 和 图生图 (Image-to-Image)
API 文档: https://agnes-ai.com/doc/agnes-image-21-flash
"""

import os
import json
import time
import argparse

from typing import Any

import requests

API_URL = "https://apihub.agnes-ai.com/v1/images/generations"
DEFAULT_MODEL = "agnes-image-2.1-flash"
DEFAULT_API_KEY = os.environ.get("AGNES_API_KEY", "")


def api_request(api_key: str, payload: dict, max_retries: int = 3) -> dict:
    """发送 API 请求并返回解析后的 JSON 响应（带重试）。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                API_URL, json=payload, headers=headers, timeout=120,
                proxies={"http": None, "https": None},
            )
            return resp.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                raise RuntimeError(f"API 请求失败 (尝试 {max_retries} 次后仍失败): {e}") from e
            wait = 2 ** attempt
            print(f"  请求失败 ({e})，{wait} 秒后重试 ({attempt}/{max_retries})...")
            time.sleep(wait)


def text_to_image(
    api_key: str,
    prompt: str,
    size: str = "1024x1024",
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    文生图: 根据文本提示词生成图像。

    Args:
        api_key: 你的 API Key
        prompt: 图像描述提示词
        size: 输出尺寸, 如 "1024x1024", "1024x768", "768x1024"
        model: 模型名称

    Returns:
        API 返回的原始 JSON dict
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
    }
    return api_request(api_key, payload)


def image_to_image(
    api_key: str,
    prompt: str,
    image_urls: Any,
    size: str = "1024x1024",
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    图生图: 基于现有图像 + 提示词进行转换或编辑。

    Args:
        api_key: 你的 API Key
        prompt: 编辑/转换指令
        image_urls: 输入图像的 URL 列表
        size: 输出尺寸
        model: 模型名称

    Returns:
        API 返回的原始 JSON dict
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "extra_body": {
            "image": image_urls,
            "response_format": "url",
        },
    }
    return api_request(api_key, payload)


def download_image(url: str, save_path: str) -> None:
    """从 URL 下载图片到本地文件。"""
    print(f"  下载中: {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(resp.content)
    print(f"  已保存: {save_path}")


def parse_response(data: dict) -> Any:
    """从 API 响应中提取图像 URL。"""
    # OpenAI 兼容格式: data[0].url
    if "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
        return data["data"][0].get("url")
    # 也可能直接在顶层
    if "url" in data:
        return data["url"]
    print("  警告: 无法从响应中提取图片 URL，完整响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return None


def build_prompt(subject, scene, style, lighting, composition, quality):
    """辅助函数: 构建推荐的 Prompt 结构。

    结构: [Subject] + [Scene / Environment] + [Style] + [Lighting] + [Composition] + [Quality Requirements]
    """
    parts = [p for p in [subject, scene, style, lighting, composition, quality] if p]
    return ", ".join(parts)


# ── 命令行入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agnes Image 2.1 Flash - Python 生图工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文生图 (API Key 通过环境变量 AGNES_API_KEY 传入)
  python agnes_image.py --mode txt2img --prompt "一只在月球上吃鱼的猫"

  # 文生图 (指定尺寸和保存路径)
  python agnes_image.py --mode txt2img --prompt "赛博朋克城市夜景" --size 1024x768 --output cyberpunk.png

  # 图生图
  python agnes_image.py --mode img2img --prompt "转换为水彩风格" \
      --image-url "https://example.com/input.png" --output watercolor.png

  # 使用 Prompt 模板
  python agnes_image.py --mode txt2img --subject "一只猫" --scene "樱花树下" \
      --style "水彩" --lighting "柔和晨光" --composition "特写" --quality "高清"
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["txt2img", "img2img"],
        default="txt2img",
        help="生成模式: txt2img=文生图, img2img=图生图 (默认: txt2img)",
    )
    parser.add_argument("--prompt", help="图像描述提示词 (文生图的必需参数)")
    parser.add_argument(
        "--size",
        default="1024x1024",
        help="输出尺寸, 如 1024x1024, 1024x768 (默认: 1024x1024)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="保存图片的文件路径 (默认: 保存在当前目录 agnes_时间戳.png)",
    )
    parser.add_argument(
        "--image-url",
        action="append",
        default=[],
        help="图生图: 输入图像的 URL (可多次指定)",
    )
    # Prompt 模板参数
    parser.add_argument("--subject", help="主体 (用于 Prompt 模板)")
    parser.add_argument("--scene", help="场景/环境 (用于 Prompt 模板)")
    parser.add_argument("--style", help="风格 (用于 Prompt 模板)")
    parser.add_argument("--lighting", help="光照 (用于 Prompt 模板)")
    parser.add_argument("--composition", help="构图 (用于 Prompt 模板)")
    parser.add_argument("--quality", help="质量要求 (用于 Prompt 模板)")
    parser.add_argument(
        "--api-key",
        default=None,
        help="API Key (也可以通过环境变量 AGNES_API_KEY 传入)",
    )

    args = parser.parse_args()

    # 获取 API Key
    api_key = args.api_key or DEFAULT_API_KEY
    if not api_key:
        parser.error(
            "未提供 API Key。请通过 --api-key 参数或设置环境变量 AGNES_API_KEY 传入。"
        )

    # 构建 prompt
    prompt = args.prompt
    if not prompt and (args.subject or args.scene or args.style):
        prompt = build_prompt(
            args.subject, args.scene, args.style,
            args.lighting, args.composition, args.quality,
        )
    if not prompt:
        parser.error("请提供 --prompt 参数，或使用 --subject/--scene/--style 等构建 Prompt 模板")

    # 执行生成
    print(f"模型: {DEFAULT_MODEL}")
    print(f"模式: {args.mode}")
    print(f"尺寸: {args.size}")
    print(f"提示词: {prompt}")

    if args.mode == "txt2img":
        print("正在生成图像...")
        result = text_to_image(api_key, prompt, args.size)
    else:
        if not args.image_url:
            parser.error("图生图模式需要提供 --image-url 参数")
        print(f"输入图像: {args.image_url}")
        print("正在生成图像...")
        result = image_to_image(api_key, prompt, args.image_url, args.size)

    # 提取并下载图片
    img_url = parse_response(result)
    if img_url:
        if args.output:
            save_path = args.output
        else:
            save_path = f"agnes_{int(time.time())}.png"
        print(f"\n图片 URL: {img_url}")
        download_image(img_url, save_path)
        print(f"\n完成! 图片已保存至: {save_path}")
    else:
        print("\n生成结果解析失败。")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
