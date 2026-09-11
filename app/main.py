"""Agent — a local chat agent with a Claude/ChatGPT-style interface.

Run from this folder:
    python -m uvicorn main:app --host 127.0.0.1 --port 8000
Then open http://localhost:8000
"""

import asyncio
import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config as cfg
import storage
from agent import run_agent
from providers import ProviderError

app = FastAPI(title="Agent", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(cfg.BASE_DIR / "static")), name="static")


class ChatIn(BaseModel):
    message: str


class SettingsIn(BaseModel):
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    workspace: str | None = None
    max_iterations: int | None = None
    theme: str | None = None
    tavily_key: str | None = None


class RenameIn(BaseModel):
    title: str


# ---------------------------------------------------------------- pages
@app.get("/")
async def index():
    return FileResponse(cfg.BASE_DIR / "static" / "index.html")


# ---------------------------------------------------------------- config
@app.get("/api/config")
async def get_config():
    settings = cfg.load_settings()
    provider = settings.get("provider", "anthropic")
    key = cfg.effective_key(provider)
    return {
        "providers": [
            {
                "id": pid,
                "label": p["label"],
                "needs_key": p["needs_key"],
                "models": p["models"],
                "default_model": p["default_model"],
                "base_url_placeholder": p["base_url_placeholder"],
                "key_hint": p["key_hint"],
            }
            for pid, p in cfg.PROVIDERS.items()
        ],
        "current": {
            "provider": provider,
            "has_key": bool(key),
            "model": cfg.effective_model(provider),
            "base_url": cfg.effective_base_url(provider),
            "workspace": settings.get("workspace"),
            "max_iterations": settings.get("max_iterations", 6),
            "theme": settings.get("theme", "light"),
            "has_tavily": bool(settings.get("tavily_key", "")),
        },
    }


@app.post("/api/settings")
async def set_settings(body: SettingsIn):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    settings = cfg.save_settings(updates)
    return {
        "ok": True,
        "provider": settings.get("provider"),
        "model": cfg.effective_model(settings.get("provider", "anthropic")),
    }


# ---------------------------------------------------------------- conversations
@app.get("/api/conversations")
async def list_convs():
    return {"conversations": storage.list_conversations()}


@app.post("/api/conversations")
async def create_conv():
    return storage.create_conversation()


@app.get("/api/conversations/{cid}")
async def get_conv(cid: str):
    conv = storage.get_conversation(cid)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    return {"conversation": conv, "messages": storage.get_messages(cid)}


@app.patch("/api/conversations/{cid}")
async def rename_conv(cid: str, body: RenameIn):
    storage.rename_conversation(cid, body.title)
    return {"ok": True}


@app.delete("/api/conversations/{cid}")
async def delete_conv(cid: str):
    storage.delete_conversation(cid)
    return {"ok": True}


# ---------------------------------------------------------------- chat
def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _stream_turn(cid: str, message: str, history: list, request: Request):
    """Yield SSE events for one user turn; persists the assistant message."""
    buffer = {"text": "", "usage": None, "tools": []}
    try:
        async for event in run_agent(None, history, message):
            if await request.is_disconnected():
                break
            if event["type"] == "delta":
                buffer["text"] += event["text"]
            elif event["type"] == "usage":
                buffer["usage"] = {
                    "input": event.get("input", 0),
                    "output": event.get("output", 0),
                    "tools": event.get("tools", 0),
                }
            elif event["type"] == "tool_end":
                buffer["tools"].append(
                    {
                        "name": event.get("name"),
                        "ok": event.get("ok"),
                        "summary": event.get("summary"),
                        "result": event.get("detail", ""),
                    }
                )
            elif event["type"] == "done":
                meta = {
                    "usage": buffer["usage"],
                    "cost": event.get("cost"),
                    "model": event.get("model"),
                    "tools": event.get("tools") or buffer["tools"],
                }
                storage.add_message(cid, "assistant", buffer["text"].strip(), meta)
            yield _sse(event)
    except asyncio.CancelledError:
        storage.add_message(cid, "assistant", buffer["text"].strip() or "(stopped)")
        raise


async def _run_plain(cid: str, message: str, history: list):
    """Non-streaming fallback (used by the frontend if SSE is unavailable)."""
    chunks = []
    meta = None
    try:
        async for event in run_agent(None, history, message):
            if event["type"] == "delta":
                chunks.append(event["text"])
            elif event["type"] == "done":
                meta = {
                    "usage": event.get("usage"),
                    "cost": event.get("cost"),
                    "model": event.get("model"),
                    "tools": event.get("tools"),
                }
            elif event["type"] == "error":
                return None, event
    except ProviderError as e:
        return None, {"type": "error", "kind": e.kind, "message": e.message}
    except Exception as e:  # pragma: no cover - defensive
        return None, {"type": "error", "kind": "request", "message": str(e)}
    text = "".join(chunks).strip()
    storage.add_message(cid, "assistant", text, meta or {})
    return {"text": text, "meta": meta or {}}, None


@app.post("/api/chat/{cid}")
async def chat(cid: str, body: ChatIn, request: Request):
    conv = storage.get_conversation(cid)
    if conv is None:
        raise HTTPException(404, "Conversation not found")
    if not body.message.strip():
        raise HTTPException(400, "Empty message")

    message = body.message.strip()
    history = storage.model_history(cid)
    storage.add_message(cid, "user", message)
    storage.set_first_title(cid, message)

    if request.query_params.get("plain") == "1":
        result, error = await _run_plain(cid, message, history)
        if error:
            return JSONResponse({"error": error}, status_code=502)
        return result

    stream = _stream_turn(cid, message, history, request)
    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/chat/{cid}/stop")
async def stop_chat(cid: str):
    # Streaming stops on client disconnect (request.is_disconnected in the
    # stream loop). This endpoint exists for future server-side cancellation.
    return {"ok": True}
