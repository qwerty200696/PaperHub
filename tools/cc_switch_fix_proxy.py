#!/usr/bin/env python3
"""
cc-switch 流式修复代理

问题: cc-switch 将 OpenAI streaming 转 Anthropic 格式时，
      每个 token 都生成独立的 content_block，导致 Claude Code
      渲染时每个 token 独占一行。还插入空的 thinking block。

修复: 合并所有 text content_block 为一个 block，过滤空 thinking block。

用法:
    python3 cc_switch_fix_proxy.py [--port 15722] [--upstream http://127.0.0.1:15721]

链路: Claude Code -> Proxy :15722 -> cc-switch :15721 -> iFlytek API
"""

import argparse
import json
import sys
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("cc-fix-proxy")

CONFIG = {
    "upstream": "http://127.0.0.1:15721",
    "port": 15722,
}


class SSEEvent:
    def __init__(self, event_type=None, data=None):
        self.event_type = event_type
        self.data = data

    def parse_data(self):
        if self.data:
            return json.loads(self.data)
        return None

    def serialize(self):
        lines = []
        if self.event_type:
            lines.append(f"event: {self.event_type}")
        if self.data:
            lines.append(f"data: {self.data}")
        return "\n".join(lines) + "\n\n"


class StreamingFixer:
    """
    Fixes cc-switch's fragmented Anthropic SSE output.
    - Filter out empty thinking blocks
    - Merge ALL text blocks into a single text block at index 0
    - Non-empty thinking blocks: close text, emit thinking, reopen text
    """

    def __init__(self):
        self.text_block_open = False
        self.TEXT_INDEX = 0
        self.in_thinking_block = False
        self.thinking_has_content = False
        self.thinking_buffer = []

    def process_event(self, event):
        if event.event_type is None:
            yield event
            return

        data = event.parse_data()
        if data is None:
            yield event
            return

        evt_type = data.get("type", "")

        if evt_type == "message_start":
            yield event

        elif evt_type == "content_block_start":
            block = data.get("content_block", {})
            block_type = block.get("type", "")

            if block_type == "text":
                if not self.text_block_open:
                    self.text_block_open = True
                    data["index"] = self.TEXT_INDEX
                    event.data = json.dumps(data, ensure_ascii=False)
                    yield event
            elif block_type == "thinking":
                self.in_thinking_block = True
                self.thinking_has_content = False
                self.thinking_buffer = [event]
            else:
                if self.text_block_open:
                    yield self._make_stop(self.TEXT_INDEX)
                    self.text_block_open = False
                yield event

        elif evt_type == "content_block_delta":
            delta = data.get("delta", {})
            delta_type = delta.get("type", "")

            if delta_type == "text_delta":
                if not self.text_block_open:
                    self.text_block_open = True
                    yield self._make_start_text(self.TEXT_INDEX)
                data["index"] = self.TEXT_INDEX
                event.data = json.dumps(data, ensure_ascii=False)
                yield event
            elif delta_type == "thinking_delta":
                if delta.get("thinking", ""):
                    self.thinking_has_content = True
                if self.in_thinking_block:
                    self.thinking_buffer.append(event)
            else:
                yield event

        elif evt_type == "content_block_stop":
            if self.in_thinking_block:
                self.in_thinking_block = False
                if self.thinking_has_content:
                    if self.text_block_open:
                        yield self._make_stop(self.TEXT_INDEX)
                        self.text_block_open = False
                    for buf_event in self.thinking_buffer:
                        yield buf_event
                self.thinking_buffer = []
            elif self.text_block_open:
                pass  # keep text block open
            else:
                yield event

        elif evt_type in ("message_delta", "message_stop"):
            if self.text_block_open:
                yield self._make_stop(self.TEXT_INDEX)
                self.text_block_open = False
            yield event

        else:
            yield event

    def flush(self):
        if self.text_block_open:
            yield self._make_stop(self.TEXT_INDEX)
            self.text_block_open = False

    def _make_start_text(self, index):
        return SSEEvent(
            "content_block_start",
            json.dumps({
                "type": "content_block_start",
                "index": index,
                "content_block": {"type": "text", "text": ""}
            }, ensure_ascii=False)
        )

    def _make_stop(self, index):
        return SSEEvent(
            "content_block_stop",
            json.dumps({"type": "content_block_stop", "index": index},
                       ensure_ascii=False)
        )


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP proxy handler that fixes SSE streams."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def _upstream_url(self):
        return f"{CONFIG['upstream']}{self.path}"

    def _forward_headers(self, req):
        for key, value in self.headers.items():
            if key.lower() not in ("host", "content-length"):
                req.add_header(key, value)

    def _send_event(self, event):
        output = event.serialize().encode("utf-8")
        self.wfile.write(output)
        self.wfile.flush()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        is_stream = False
        try:
            req_json = json.loads(body)
            is_stream = req_json.get("stream", False)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        upstream_url = self._upstream_url()
        req = Request(upstream_url, data=body, method="POST")
        self._forward_headers(req)

        try:
            resp = urlopen(req, timeout=300)
        except (URLError, OSError) as e:
            log.error("Upstream error: %s", e)
            self.send_error(502, f"Upstream connection failed: {e}")
            return

        if is_stream:
            self.send_response(resp.status)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            fixer = StreamingFixer()
            line_buf = b""
            done = False

            try:
                while not done:
                    line = resp.readline()
                    if not line:
                        break

                    line_buf += line

                    if line == b"\n" or line == b"\r\n":
                        if line_buf.strip():
                            event_type = None
                            data_lines = []
                            for raw_line in line_buf.decode("utf-8", errors="replace").split("\n"):
                                raw_line = raw_line.rstrip("\r")
                                if raw_line.startswith("event:"):
                                    event_type = raw_line[len("event:"):].strip()
                                elif raw_line.startswith("data:"):
                                    data_lines.append(raw_line[len("data:"):].strip())

                            if event_type or data_lines:
                                data = "\n".join(data_lines) if data_lines else None
                                sse_event = SSEEvent(event_type, data)

                                # Check if this is message_stop
                                if event_type == "message_stop":
                                    done = True

                                for fixed in fixer.process_event(sse_event):
                                    try:
                                        self._send_event(fixed)
                                    except (BrokenPipeError, ConnectionResetError, OSError):
                                        return

                        line_buf = b""

                # Flush remaining buffer
                if line_buf.strip():
                    event_type = None
                    data_lines = []
                    for raw_line in line_buf.decode("utf-8", errors="replace").split("\n"):
                        raw_line = raw_line.rstrip("\r")
                        if raw_line.startswith("event:"):
                            event_type = raw_line[len("event:"):].strip()
                        elif raw_line.startswith("data:"):
                            data_lines.append(raw_line[len("data:"):].strip())
                    if event_type or data_lines:
                        data = "\n".join(data_lines) if data_lines else None
                        sse_event = SSEEvent(event_type, data)
                        for fixed in fixer.process_event(sse_event):
                            try:
                                self._send_event(fixed)
                            except (BrokenPipeError, ConnectionResetError, OSError):
                                return

                # Flush fixer
                for fixed in fixer.flush():
                    try:
                        self._send_event(fixed)
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        return

            except (ConnectionResetError, OSError) as e:
                log.warning("Stream interrupted: %s", e)
            finally:
                try:
                    resp.close()
                except Exception:
                    pass

        else:
            resp_body = resp.read()
            self.send_response(resp.status)
            for key, value in dict(resp.headers).items():
                if key.lower() not in ("transfer-encoding", "content-length"):
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)

    def do_GET(self):
        upstream_url = self._upstream_url()
        req = Request(upstream_url, method="GET")
        self._forward_headers(req)
        try:
            resp = urlopen(req, timeout=30)
            resp_body = resp.read()
            self.send_response(resp.status)
            for key, value in dict(resp.headers).items():
                if key.lower() not in ("transfer-encoding", "content-length"):
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        except (URLError, OSError) as e:
            self.send_error(502, str(e))

    def do_DELETE(self):
        upstream_url = self._upstream_url()
        req = Request(upstream_url, method="DELETE")
        self._forward_headers(req)
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            req.data = body
        try:
            resp = urlopen(req, timeout=30)
            resp_body = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        except (URLError, OSError) as e:
            self.send_error(502, str(e))


def main():
    parser = argparse.ArgumentParser(description="cc-switch streaming fix proxy")
    parser.add_argument("--port", type=int, default=CONFIG["port"],
                        help=f"Listen port (default: {CONFIG['port']})")
    parser.add_argument("--upstream", default=CONFIG["upstream"],
                        help=f"Upstream cc-switch URL (default: {CONFIG['upstream']})")
    args = parser.parse_args()

    CONFIG["upstream"] = args.upstream
    CONFIG["port"] = args.port

    server = ThreadingHTTPServer(("127.0.0.1", CONFIG["port"]), ProxyHandler)
    log.info("Listening on 127.0.0.1:%d", CONFIG["port"])
    log.info("Upstream: %s", CONFIG["upstream"])
    log.info("Fix: merging fragmented content blocks + filtering empty thinking")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
