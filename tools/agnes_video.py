#!/usr/bin/env python3
"""
Agnes Video V2.0 - Python 视频生成脚本
支持: 文生视频 / 图生视频 / 多图视频 / 关键帧动画
API 文档: docs/agens/Agnes-Video-V2.0.md
"""

from __future__ import annotations

import os
import json
import time
import argparse
from typing import Any

import requests

API_CREATE = "https://apihub.agnes-ai.com/v1/videos"
API_RESULT = "https://apihub.agnes-ai.com/v1/videos/{}"
DEFAULT_MODEL = "agnes-video-v2.0"
DEFAULT_API_KEY = os.environ.get("AGNES_API_KEY", "")

# num_frames 必须满足 8n+1 且 <= 441
NUM_FRAMES_OPTIONS = [81, 121, 161, 201, 241, 281, 321, 361, 401, 441]


# ── API 调用 ───────────────────────────────────────────────

def api_request(api_key: str, method: str, url: str, payload: dict | None = None) -> dict:
    """通用 API 请求，带重试和代理绕过。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, 4):
        try:
            if method == "POST":
                resp = requests.post(url, json=payload, headers=headers,
                                     timeout=120, proxies={"http": None, "https": None})
            else:
                resp = requests.get(url, headers=headers, timeout=120,
                                    proxies={"http": None, "https": None})
            return resp.json()
        except requests.exceptions.RequestException as e:
            if attempt == 3:
                raise RuntimeError(f"API 请求失败 (尝试 3 次后仍失败): {e}") from e
            wait = 2 ** attempt
            print(f"  请求失败 ({e})，{wait} 秒后重试 ({attempt}/3)...")
            time.sleep(wait)


def create_task(api_key: str, prompt: str, mode: str = "txt2vid",
                width: int = 1152, height: int = 768,
                num_frames: int = 121, frame_rate: float = 24.0,
                image: list[str] | str | None = None,
                negative_prompt: str | None = None,
                seed: int | None = None,
                num_inference_steps: int | None = None,
                extra: dict | None = None) -> dict:
    """创建视频生成任务，返回任务信息。"""
    payload: dict[str, Any] = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_frames": num_frames,
        "frame_rate": frame_rate,
    }
    if mode != "txt2vid":
        if isinstance(image, str):
            payload["image"] = image
        elif isinstance(image, list):
            if extra is None:
                extra = {}
            extra["image"] = image
            payload["extra_body"] = extra
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    if seed is not None:
        payload["seed"] = seed
    if num_inference_steps is not None:
        payload["num_inference_steps"] = num_inference_steps
    return api_request(api_key, "POST", API_CREATE, payload)


def poll_result(api_key: str, task_id: str, interval: float = 5.0,
                timeout: int = 1800) -> dict:
    """轮询任务结果，等待 completed 或 failed。"""
    start = time.time()
    while time.time() - start < timeout:
        result = api_request(api_key, "GET", API_RESULT.format(task_id))
        status = result.get("status", "")
        progress = result.get("progress", 0)
        print(f"  状态: {status}  进度: {progress}%")

        if status == "completed":
            return result
        if status == "failed":
            error = result.get("error") or result.get("message") or "未知错误"
            raise RuntimeError(f"视频生成失败: {error}")
        if status == "in_progress":
            elapsed = int(time.time() - start)
            print(f"  已等待 {elapsed} 秒...")

        time.sleep(interval)

    raise RuntimeError(f"任务超时 ({timeout} 秒)。任务 ID: {task_id}")


def download_video(url: str, save_path: str) -> None:
    """下载视频到本地。"""
    print(f"  下载中: {url}")
    resp = requests.get(url, timeout=300, proxies={"http": None, "https": None}, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get("Content-Length", 0))
    downloaded = 0
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 512):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"  已下载 {downloaded // (1024*1024)}MB / {total // (1024*1024)}MB ({pct:.0f}%)")
            else:
                print(f"  已下载 {downloaded // (1024*1024)}MB")
    print(f"  已保存: {save_path}")


def extract_video_url(data: dict) -> str | None:
    """从结果响应中提取视频 URL。"""
    # 可能在不同字段名
    for key in ("video_url", "url", "remixed_from_video_id", "output_url"):
        if key in data and data[key]:
            return data[key]
    # 也可能在嵌套的 body 里
    body = data.get("body") or data.get("response", {})
    if isinstance(body, dict):
        for key in ("video_url", "url", "remixed_from_video_id", "output_url"):
            if key in body and body[key]:
                return body[key]
    print("  警告: 无法从响应中提取视频 URL，完整响应:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return None


# ── CLI 入口 ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agnes Video V2.0 - Python 视频生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文生视频
  python agnes_video.py --mode txt2vid --prompt "一只猫在海边日落时散步"

  # 图生视频
  python agnes_video.py --mode img2vid --prompt "人物转头看向镜头" \\
      --image "https://example.com/photo.jpg" --output cat.mp4

  # 多图视频
  python agnes_video.py --mode multi_img --prompt "两张图之间的平滑过渡" \\
      --image "https://example.com/img1.jpg" --image "https://example.com/img2.jpg" \\
      --output transition.mp4

  # 关键帧动画
  python agnes_video.py --mode keyframes --prompt "关键帧之间的平滑过渡" \\
      --image "https://example.com/kf1.png" --image "https://example.com/kf2.png" \\
      --output animation.mp4

  # 自定义参数
  python agnes_video.py --mode txt2vid --prompt "赛博朋克城市" --duration 10 --fps 30

  # 使用 Prompt 模板
  python agnes_video.py --mode txt2vid \\
      --subject "宇航员" --action "在红色沙漠星球上行走" \\
      --scene "风暴席卷的火星表面" --camera "慢速追踪镜头" \\
      --lighting "戏剧性日落" --style "写实科幻"
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["txt2vid", "img2vid", "multi_img", "keyframes"],
        default="txt2vid",
        help="生成模式 (默认: txt2vid)",
    )
    parser.add_argument("--prompt", required=True, help="视频描述提示词")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="输入图像 URL (可多次指定)",
    )
    parser.add_argument("--width", type=int, default=1152, help="视频宽度 (默认: 1152)")
    parser.add_argument("--height", type=int, default=768, help="视频高度 (默认: 768)")
    parser.add_argument(
        "--num-frames", type=int, default=None,
        help="帧数 (8n+1, <=441). 可选值: 81, 121, 161, 201, 241, 281, 321, 361, 401, 441",
    )
    parser.add_argument("--fps", type=float, default=24.0, help="帧率 FPS (默认: 24.0)")
    parser.add_argument(
        "--duration", type=float, default=None,
        help="时长(秒), 自动计算 num_frames. 可选: 5, 10, 18",
    )
    parser.add_argument("--negative-prompt", default=None, help="负向提示词")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--steps", type=int, dest="num_inference_steps", default=None,
                        help="推理步数")
    parser.add_argument("--output", "-o", default=None,
                        help="保存视频文件路径 (默认: agnes_时间戳.mp4)")
    parser.add_argument("--api-key", default=None, help="API Key (或环境变量 AGNES_API_KEY)")
    parser.add_argument(
        "--poll-interval", type=float, default=15.0,
        help="轮询间隔秒数 (默认: 15)",
    )

    args = parser.parse_args()

    # API Key
    api_key = args.api_key or DEFAULT_API_KEY
    if not api_key:
        parser.error("未提供 API Key。通过 --api-key 或环境变量 AGNES_API_KEY 传入。")

    # 计算 num_frames
    num_frames = args.num_frames
    if args.duration is not None:
        if num_frames is not None:
            parser.error("--duration 和 --num-frames 只能二选一")
        # 找到最接近的 8n+1 值
        target = int(args.duration * args.fps)
        num_frames = min(NUM_FRAMES_OPTIONS, key=lambda x: abs(x - target))
    if num_frames is None:
        num_frames = 121
    if num_frames not in NUM_FRAMES_OPTIONS:
        num_frames = min(NUM_FRAMES_OPTIONS, key=lambda x: abs(x - num_frames))
        print(f"  警告: num_frames={num_frames} 不在标准列表中, 已调整为 {num_frames}")
    if num_frames > 441:
        num_frames = 441

    print(f"模型: {DEFAULT_MODEL}")
    print(f"模式: {args.mode}")
    print(f"分辨率: {args.width}x{args.height}")
    print(f"帧数: {num_frames}  帧率: {args.fps} FPS")
    print(f"提示词: {args.prompt}")

    if args.mode in ("multi_img", "keyframes"):
        if not args.image:
            parser.error(f"{args.mode} 模式需要至少一张 --image")

    # 创建任务
    print("\n正在创建视频生成任务...")
    extra = {"mode": args.mode} if args.mode == "keyframes" else None
    task_data = create_task(
        api_key,
        prompt=args.prompt,
        mode=args.mode,
        width=args.width,
        height=args.height,
        num_frames=num_frames,
        frame_rate=args.fps,
        image=args.image if args.image else None,
        negative_prompt=args.negative_prompt,
        seed=args.seed,
        num_inference_steps=args.num_inference_steps,
        extra=extra,
    )

    task_id = task_data.get("task_id") or task_data.get("id")
    print(f"\n任务已创建: {task_id}")
    print(f"状态: {task_data.get('status')}  进度: {task_data.get('progress', 0)}%")

    # 轮询结果
    print("\n等待视频生成完成 (轮询中)...")
    result = poll_result(api_key, task_id, interval=args.poll_interval)

    print("\n视频生成完成!")
    print(f"  状态: {result.get('status')}")
    print(f"  进度: {result.get('progress')}%")
    print(f"  时长: {result.get('seconds')}s")
    print(f"  分辨率: {result.get('size')}")

    video_url = extract_video_url(result)
    if video_url:
        print(f"\n视频 URL: {video_url}")
        if args.output:
            save_path = args.output
        else:
            save_path = f"agnes_{int(time.time())}.mp4"
        download_video(video_url, save_path)
        print(f"\n完成! 视频已保存至: {save_path}")
    else:
        print("\n无法提取视频 URL，但任务状态为 completed。")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
