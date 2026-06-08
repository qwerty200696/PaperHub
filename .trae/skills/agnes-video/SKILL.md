---
name: "agnes-video"
description: "Generate videos using Agnes Video V2.0 API. Invoke when user wants to create videos from text prompts, generate multi-scene videos, or mentions Agnes video generation."
---

# Agnes Video Generator

Generate videos using Agnes Video V2.0 API. Supports text-to-video, image-to-video, multi-image video, and keyframe animation.

## Script Location

`tools/agnes_video.py` — the core CLI script.

## API Overview

| Item | Value |
|------|-------|
| Create Task | `POST https://apihub.agnes-ai.com/v1/videos` |
| Query Result | `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>` |
| Model | `agnes-video-v2.0` |
| Auth | `Authorization: Bearer <API_KEY>` |

## API Key

Read from environment variable `AGNES_API_KEY` or pass via `--api-key`.

## Workflow

1. **Analyze the user's prompt** — determine how many scenes/segments are needed
2. **Split into scenes** — if the prompt describes multiple scenes (e.g., different days, different situations), split into separate video generation requests
3. **Generate each scene** — run `agnes_video.py` for each scene in parallel
4. **Concatenate** — if multiple scenes, use ffmpeg to merge into one final video

## CLI Usage

```bash
# Basic text-to-video
python3 tools/agnes_video.py --mode txt2vid --prompt "<PROMPT>" --api-key "<KEY>"

# With custom parameters
python3 tools/agnes_video.py --mode txt2vid --prompt "<PROMPT>" \
  --num-frames 121 --fps 24 --width 1152 --height 768 \
  --output output.mp4 --poll-interval 10 --api-key "<KEY>"

# Image-to-video
python3 tools/agnes_video.py --mode img2vid --prompt "<PROMPT>" \
  --image "https://example.com/photo.jpg" --api-key "<KEY>"

# Multi-image video
python3 tools/agnes_video.py --mode multi_img --prompt "<PROMPT>" \
  --image "https://example.com/img1.jpg" --image "https://example.com/img2.jpg" \
  --api-key "<KEY>"

# Keyframe animation
python3 tools/agnes_video.py --mode keyframes --prompt "<PROMPT>" \
  --image "https://example.com/kf1.png" --image "https://example.com/kf2.png" \
  --api-key "<KEY>"
```

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--mode` | txt2vid | txt2vid / img2vid / multi_img / keyframes |
| `--prompt` | required | Video description (English recommended for best results) |
| `--num-frames` | 121 | Must be 8n+1, max 441. Options: 81, 121, 161, 201, 241, 281, 321, 361, 401, 441 |
| `--fps` | 24 | Frame rate, range 1-60 |
| `--duration` | auto | Duration in seconds, auto-calculates num_frames |
| `--width` | 1152 | Video width |
| `--height` | 768 | Video height |
| `--output` | auto | Output file path |
| `--poll-interval` | 15 | Polling interval in seconds |
| `--seed` | none | Random seed for reproducibility |
| `--negative-prompt` | none | Negative prompt |
| `--steps` | none | Inference steps |

## Duration Reference

| Target Duration | num_frames | fps |
|----------------|------------|-----|
| ~5s | 121 | 24 |
| ~10s | 241 | 24 |
| ~18s | 441 | 24 |

## Scene Analysis Rules

When the user provides a prompt, intelligently analyze:

1. **Single scene** — one prompt, one video request
2. **Multiple scenes** — split by natural breaks (days, events, situations, etc.)
   - Generate each scene as a separate video request in parallel
   - After all complete, concatenate with ffmpeg
3. **Prompt enhancement** — translate Chinese prompts to English for better results, add cinematic descriptors (lighting, camera, style, mood)
4. **Character consistency** — if the user specifies character traits (age, gender, ethnicity), include them in every scene prompt
5. **Scene framing** — describe the scene directly, avoid transition actions like "opening a door" unless specifically requested

## Prompt Best Practices

For best results, structure prompts as:

```
[Subject description] + [Action/Scene] + [Environment] + [Camera/Lighting] + [Style/Mood]
```

Example:
```
A 22-year-old Chinese girl sitting on the sofa exhausted after work, Monday evening. Her roommate is singing loudly with a hairbrush as a microphone, dancing wildly in the living room. The girl looks tired and annoyed, rubbing her temples. Cinematic indoor lighting, realistic style, comedic mood
```

## Video Concatenation

After generating multiple scene videos, concatenate with ffmpeg:

```bash
# Create concat list
echo "file 'scene1.mp4'
file 'scene2.mp4'
file 'scene3.mp4'" > concat_list.txt

# Concatenate (copy codec, no re-encode)
/opt/homebrew/bin/ffmpeg -y -f concat -safe 0 -i concat_list.txt -c copy output_final.mp4
```

## Important Notes

- Always use `PYTHONUNBUFFERED=1` when running the script to see real-time output
- The API returns `video_id` (not task_id) — use it to query results via `/agnesapi?video_id=<VIDEO_ID>`
- Video generation takes ~2-3 minutes per scene
- Run multiple scene requests in parallel for efficiency
- The script has built-in retry (3 attempts) and proxy bypass
- API response `video_id` field is base64-encoded long format; the `id` field in query results is a shorter format — both work
