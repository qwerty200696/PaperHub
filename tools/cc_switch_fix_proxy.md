# cc-switch 讯飞 Qwen3.6 流式响应换行修复

## 问题描述

通过 cc-switch 将 Claude Code 接入讯飞 MaaS API (Qwen3.6-35B-A3B) 时，
Claude Code 的纯文本回复每个 token 独占一行，显示效果极差：

```
⏺ 你
⏺ 好
⏺ ！请问
⏺ 有什么
⏺ 我可以
⏺ 帮您的
⏺ 吗？
```

## 根因分析

cc-switch 将 OpenAI 流式格式转换为 Anthropic 格式时存在两个问题：

### 1. 每个 token 生成独立的 content_block

正常的 Anthropic 流式格式应该是一个 text content_block 包含多个 text_delta：

```
content_block_start (index:0, type:text)
content_block_delta (text:"你好")
content_block_delta (text:"！请问")
content_block_delta (text:"有什么")
content_block_stop
```

但 cc-switch 为每个 OpenAI streaming chunk 创建了独立的 content_block：

```
content_block_start (index:0, type:text) → content_block_delta ("你好") → content_block_stop
content_block_start (index:1, type:text) → content_block_delta ("！请问") → content_block_stop
content_block_start (index:2, type:text) → content_block_delta ("有什么") → content_block_stop
```

Claude Code 把每个 content_block 渲染为独立段落，导致每个 token 独占一行。

### 2. 插入空的 thinking block

Qwen 模型的推理输出 (reasoning_content) 被 cc-switch 转换为 thinking block，
但大部分 thinking block 内容为空，穿插在每个 text block 之间，进一步加剧碎片化。

## 解决方案

### 架构

在 Claude Code 和 cc-switch 之间插入一个 Python 流式修复代理：

```
Claude Code
    |  (Anthropic SSE, 修复后格式)
    v
Fix Proxy :15722
    |  (读取 cc-switch 输出, 合并 content_block, 过滤空 thinking)
    v
cc-switch :15721
    |  (OpenAI -> Anthropic 转换, 有碎片化问题)
    v
iFlytek MaaS API
    (Qwen3.6-35B-A3B, model ID: xopqwen36v35b)
```

### 修复逻辑

StreamingFixer 状态机：

1. **合并 text block** -- 第一个 text content_block_start 正常发出，后续全部抑制，
   所有 text_delta 都路由到 index 0，直到 message 结束才关闭
2. **过滤空 thinking** -- 缓冲 thinking block 的事件，
   如果 thinking_delta 内容为空则整体丢弃，有内容才发出
3. **修正 index** -- content_block_stop 的 index 统一修正为对应的 block index

## 文件说明

| 文件 | 路径 | 说明 |
|------|------|------|
| 代理脚本 | `common/tools/cc_switch_fix_proxy.py` | Python HTTP 代理，修复 SSE 流 |
| 启动脚本 | `~/cc-switch-fix-start.sh` | 启动代理 + 修改 settings.json |
| 停止脚本 | `~/cc-switch-fix-stop.sh` | 停止代理 + 恢复 settings.json |
| API 测试 | `common/tools/xfyun_api_test.py` | 讯飞 API 连通性测试 (4 项) |

## 使用方法

### 前置条件

- cc-switch 已配置讯飞 Qwen3.6 provider (Chatxunfei-Qwen3.6-35B-A3B)
- cc-switch 中 API 格式选 "OpenAI Chat Completions"，地址选 "完整 URL"
- 讯飞 API Key 已配置

### 日常使用

```bash
# 1. 启动 CC Switch 应用 (菜单栏图标)

# 2. 运行启动脚本
bash ~/cc-switch-fix-start.sh

# 3. 正常使用 Claude Code

# 4. 不用时恢复直连
bash ~/cc-switch-fix-stop.sh
```

### 手动操作

```bash
# 单独启动代理 (后台运行)
nohup python3 common/tools/cc_switch_fix_proxy.py \
    --port 15722 --upstream http://127.0.0.1:15721 \
    > /tmp/cc-switch-fix-proxy.log 2>&1 &

# 修改 settings.json 指向代理
python3 -c "
import json
p = '$HOME/.claude/settings.json'
s = json.load(open(p))
s['env']['ANTHROPIC_BASE_URL'] = 'http://127.0.0.1:15722'
json.dump(s, open(p, 'w'), indent=2, ensure_ascii=False)
"

# 停止代理
kill $(lsof -t -i :15722)
```

### 代理参数

```
--port PORT         监听端口 (默认: 15721)
--upstream URL      上游 cc-switch 地址 (默认: http://127.0.0.1:15722)
```

## 已知限制

1. **cc-switch 重启会重写 settings.json** -- cc-switch 的 "Live 配置恢复" 机制会在启动时将
   `ANTHROPIC_BASE_URL` 写回自身端口，因此每次重启 cc-switch 后需重新运行启动脚本

2. **非流式请求不受影响** -- 代理仅修复流式 (stream=true) 响应，非流式请求直接透传

3. **工具调用未测试** -- 代理对 tool_use 类型的 content_block 直接透传，
   Qwen3.6 模型的 function calling 兼容性未验证

4. **模型响应速度** -- 讯飞 MaaS 上 Qwen3.6-35B-A3B 的推理速度较慢（单次请求可能需数分钟），
   这是模型本身的限制，非代理问题

## 代理实现要点

开发过程中遇到并修复的三个关键问题：

### 1. 单线程阻塞 (HTTPServer -> ThreadingHTTPServer)
Python `HTTPServer` 是单线程的，一个请求处理期间无法接受新请求。
当流式请求耗时较长时，后续请求全部排队。改用 `ThreadingHTTPServer` 解决。

### 2. 逐字节读取 (read(1) -> readline())
最初用 `resp.read(1)` 逐字节读取 SSE 流，性能极差且容易卡死。
改为 `resp.readline()` 按行读取，SSE 每行以 `\n` 结尾，效率提升约 100 倍。

### 3. 连接不关闭 (keep-alive -> close)
HTTP/1.1 默认 keep-alive，SSE 流结束后代理不关闭连接，
导致客户端一直等待直到超时。设置 `Connection: close` 响应头，
并在收到 `message_stop` 事件后立即停止读取上游、关闭上游连接。

## 讯飞 API 配置参考

| 项目 | 值 |
|------|-----|
| API 地址 | `https://maas-api.cn-huabei-1.xf-yun.com/v2/chat/completions` |
| Base URL | `https://maas-api.cn-huabei-1.xf-yun.com/v2` |
| Model ID | `xopqwen36v35b` (非显示名，通过 /v2/models 接口获取) |
| 协议 | OpenAI 兼容 (需 cc-switch 选 "完整 URL" 模式) |
| API Key | 环境变量 `XFYUN_API_KEY`，存在 `.env` 中 |

### SakuraCat / mihomo 代理注意

如果使用了 SakuraCat (mihomo) 做系统代理，需要添加直连规则避免 502：

```yaml
rules:
  - DOMAIN-SUFFIX,xf-yun.com,DIRECT   # 讯飞 API 直连
```

不使用系统代理时，无需开着 SakuraCat。
