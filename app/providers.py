"""Provider clients: Anthropic, OpenAI-compatible, Ollama.

Each provider exposes one method:

    async def stream(self, messages, system, tools) -> AsyncIterator[dict]

yielding canonical events:
    {"type": "delta", "text": "..."}
    {"type": "tool_call", "id": ..., "name": ..., "input": "<json string>"}
    {"type": "usage", "input": n, "output": n}
    {"type": "error", "kind": "auth|network|timeout|rate_limited|provider|request", "message": "..."}

Retry policy (per docs/core/06 Rule R12): only transient errors retry,
with exponential backoff + jitter. Deterministic errors surface immediately.
"""

import asyncio
import json
import random

import httpx

from config import effective_base_url, effective_key, effective_model

TIMEOUT = httpx.Timeout(connect=15.0, read=300.0, write=30.0, pool=15.0)


class ProviderError(Exception):
    def __init__(self, kind: str, message: str):
        self.kind = kind
        self.message = message
        super().__init__(message)


async def _post_stream(client: httpx.AsyncClient, url: str, headers: dict, body: dict):
    """POST with streaming response; 2 retries on transient failures only."""
    last = None
    for attempt in range(3):
        try:
            req = client.build_request("POST", url, headers=headers, json=body)
            resp = await client.send(req, stream=True)
        except httpx.TimeoutException:
            raise ProviderError("timeout", "The model took too long to respond. Try again.")
        except httpx.TransportError as e:
            last = ProviderError("network", f"Could not reach the model server: {e}")
            await asyncio.sleep(1.5 * (2 ** attempt) + random.uniform(0, 0.6))
            continue

        if resp.status_code == 429:
            raise ProviderError(
                "rate_limited",
                "Rate limited by the provider. Wait a minute and try again.",
            )
        if resp.status_code in (401, 403):
            raise ProviderError("auth", "The API key was rejected. Check it in Settings.")
        if resp.status_code == 404 and "/api/chat" in url:
            raise ProviderError(
                "request",
                "Model not found. Is it installed? Run: ollama pull <model>",
            )
        if resp.status_code == 404:
            raise ProviderError("request", "Endpoint not found (HTTP 404). Check the Base URL.")
        if resp.status_code >= 500:
            last = ProviderError("provider", f"Provider error (HTTP {resp.status_code}).")
            await asyncio.sleep(1.5 * (2 ** attempt) + random.uniform(0, 0.6))
            continue
        if resp.status_code != 200:
            try:
                detail = (await resp.aread())[:300].decode("utf-8", "replace")
            except Exception:
                detail = ""
            raise ProviderError("request", f"Request failed (HTTP {resp.status_code}): {detail}")
        return resp
    raise last or ProviderError("network", "Request failed.")


def _merge_user_turns(messages: list) -> list:
    """Anthropic requires alternating roles; merge consecutive user turns."""
    out = []
    for m in messages:
        if m["role"] == "user" and out and out[-1]["role"] == "user":
            out[-1]["content"] = f"{out[-1]['content']}\n\n{m['content']}"
        else:
            out.append(dict(m))
    return out


class AnthropicProvider:
    def __init__(self):
        self.key = effective_key("anthropic")
        self.model = effective_model("anthropic")
        self.base = effective_base_url("anthropic").rstrip("/")
        if not self.key:
            raise ProviderError(
                "auth",
                "No Anthropic API key configured. Add one in Settings (console.anthropic.com).",
            )

    def _convert(self, messages: list):
        out = []
        for m in _merge_user_turns(messages):
            if m["role"] == "assistant":
                content = []
                if m.get("content"):
                    content.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls", []):
                    try:
                        args = json.loads(tc["function"].get("arguments") or "{}")
                    except Exception:
                        args = {}
                    content.append(
                        {"type": "tool_use", "id": tc["id"], "name": tc["function"]["name"], "input": args}
                    )
                out.append({"role": "assistant", "content": content or [{"type": "text", "text": ""}]})
            elif m["role"] == "tool":
                out.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                        ],
                    }
                )
            else:
                out.append({"role": "user", "content": m["content"]})
        return out

    async def stream(self, messages, system, tools):
        body = {
            "model": self.model,
            "max_tokens": 8192,
            "stream": True,
            "system": system,
            "messages": self._convert(messages),
        }
        if tools:
            body["tools"] = [{"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]} for t in tools]
        headers = {
            "x-api-key": self.key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await _post_stream(client, f"{self.base}/v1/messages", headers, body)
            input_tokens = output_tokens = 0
            tool_use = None
            try:
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        data = json.loads(line[5:].strip())
                    except Exception:
                        continue
                    t = data.get("type")
                    if t == "message_start":
                        input_tokens = (data.get("message") or {}).get("usage", {}).get("input_tokens", 0)
                    elif t == "content_block_start":
                        cb = data.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_use = {"id": cb["id"], "name": cb["name"], "input": ""}
                    elif t == "content_block_delta":
                        d = data.get("delta", {})
                        if d.get("type") == "text_delta":
                            yield {"type": "delta", "text": d.get("text", "")}
                        elif d.get("type") == "input_json_delta" and tool_use is not None:
                            tool_use["input"] += d.get("partial_json", "")
                    elif t == "content_block_stop":
                        if tool_use is not None:
                            yield {"type": "tool_call", **tool_use}
                            tool_use = None
                    elif t == "message_delta":
                        output_tokens = (data.get("usage") or {}).get("output_tokens", output_tokens)
                    elif t == "error":
                        raise ProviderError("provider", str(data.get("error", {}).get("message", "Unknown provider error")))
            finally:
                await resp.aclose()
            yield {"type": "usage", "input": input_tokens, "output": output_tokens}


class OpenAIProvider:
    def __init__(self):
        self.key = effective_key("openai")
        self.model = effective_model("openai")
        self.base = effective_base_url("openai").rstrip("/")
        if not self.key:
            raise ProviderError(
                "auth",
                "No API key configured. Add one in Settings (platform.openai.com or any compatible endpoint).",
            )

    async def stream(self, messages, system, tools):
        msgs = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "assistant" and m.get("tool_calls"):
                msgs.append(
                    {
                        "role": "assistant",
                        "content": m.get("content") or None,
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["function"]["name"], "arguments": tc["function"].get("arguments", "{}")},
                            }
                            for tc in m["tool_calls"]
                        ],
                    }
                )
            elif m["role"] == "tool":
                msgs.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
            else:
                msgs.append({"role": m["role"], "content": m["content"]})
        body = {
            "model": self.model,
            "stream": True,
            "stream_options": {"include_usage": True},
            "messages": msgs,
        }
        if tools:
            body["tools"] = [
                {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
                for t in tools
            ]
        url = self.base if self.base.endswith("/chat/completions") else f"{self.base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "content-type": "application/json"}
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await _post_stream(client, url, headers, body)
            calls = {}
            input_tokens = output_tokens = 0
            try:
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        data = json.loads(payload)
                    except Exception:
                        continue
                    if data.get("usage"):
                        input_tokens = data["usage"].get("prompt_tokens", input_tokens)
                        output_tokens = data["usage"].get("completion_tokens", output_tokens)
                    for choice in data.get("choices", []):
                        delta = choice.get("delta") or {}
                        if delta.get("content"):
                            yield {"type": "delta", "text": delta["content"]}
                        for tc in delta.get("tool_calls") or []:
                            idx = tc.get("index", 0)
                            slot = calls.setdefault(idx, {"id": "", "name": "", "input": ""})
                            slot["id"] = tc.get("id") or slot["id"] or f"call_{idx}"
                            fn = tc.get("function") or {}
                            slot["name"] += fn.get("name") or ""
                            slot["input"] += fn.get("arguments") or ""
            finally:
                await resp.aclose()
            for slot in calls.values():
                if slot["name"]:
                    yield {"type": "tool_call", "id": slot["id"], "name": slot["name"], "input": slot["input"]}
            yield {"type": "usage", "input": input_tokens, "output": output_tokens}


class OllamaProvider:
    def __init__(self):
        self.model = effective_model("ollama")
        self.base = effective_base_url("ollama").rstrip("/")

    async def stream(self, messages, system, tools):
        msgs = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "assistant" and m.get("tool_calls"):
                msgs.append(
                    {
                        "role": "assistant",
                        "content": m.get("content") or "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": tc["function"]["name"],
                                    "arguments": json.loads(tc["function"].get("arguments") or "{}"),
                                }
                            }
                            for tc in m["tool_calls"]
                        ],
                    }
                )
            elif m["role"] == "tool":
                msgs.append({"role": "tool", "tool_name": m["tool_call_id"], "content": m["content"]})
            else:
                msgs.append({"role": m["role"], "content": m["content"]})
        body = {"model": self.model, "stream": True, "messages": msgs, "options": {"temperature": 0.7}}
        if tools:
            body["tools"] = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}} for t in tools]
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await _post_stream(client, f"{self.base}/api/chat", {}, body)
            input_tokens = output_tokens = 0
            try:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    if data.get("error"):
                        err = str(data["error"])
                        if "tools" in err.lower():
                            raise ProviderError(
                                "tools_unsupported",
                                "This local model does not support tools — it will answer without them.",
                            )
                        raise ProviderError("request", err)
                    msg = data.get("message") or {}
                    if msg.get("content"):
                        yield {"type": "delta", "text": msg["content"]}
                    if msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            fn = tc.get("function", {})
                            yield {
                                "type": "tool_call",
                                "id": fn.get("name", "call_0"),
                                "name": fn.get("name", ""),
                                "input": json.dumps(fn.get("arguments") or {}),
                            }
                    if data.get("done"):
                        input_tokens = data.get("prompt_eval_count", 0)
                        output_tokens = data.get("eval_count", 0)
            finally:
                await resp.aclose()
            yield {"type": "usage", "input": input_tokens, "output": output_tokens}


def get_provider():
    from config import load_settings

    settings = load_settings()
    provider = settings.get("provider", "anthropic")
    if provider == "anthropic":
        return AnthropicProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "ollama":
        return OllamaProvider()
    raise ProviderError("request", f"Unknown provider: {provider}")
