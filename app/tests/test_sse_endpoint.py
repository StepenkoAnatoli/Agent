"""HTTP-level SSE end-to-end test: real FastAPI app + fake provider.

Validates the full pipeline: POST /api/chat/{cid} -> SSE events
(delta, tool_start, tool_end, usage, done) -> persisted assistant
message with tool trace. Uses a temp database.

Run from app/:  .venv/bin/python tests/test_sse_endpoint.py
"""

import asyncio
import json
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import uvicorn

import storage
import agent as agent_mod


class FakeProvider:
    calls = 0
    model = "claude-sonnet-4-5"

    async def stream(self, messages, system, tools):
        self.calls += 1
        if self.calls == 1:
            yield {"type": "delta", "text": "Let me look "}
            yield {"type": "tool_call", "id": "c1", "name": "list_dir", "input": json.dumps({"path": "."})}
            yield {"type": "usage", "input": 10, "output": 4}
        else:
            yield {"type": "delta", "text": "Done."}
            yield {"type": "usage", "input": 20, "output": 5}


def parse_sse(text: str) -> list:
    events = []
    for chunk in text.split("\n\n"):
        for line in chunk.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


def main():
    # --- isolate the database -----------------------------------------
    tmp = Path(tempfile.mkdtemp(prefix="agent-test-"))
    storage.DATA_DIR = tmp
    storage.DB_FILE = tmp / "test.db"
    storage._conn = None

    # --- patch provider into the running app ---------------------------
    agent_mod.get_provider = lambda: FakeProvider()
    import main as main_mod  # noqa: E402  (import after patches)

    config = uvicorn.Config(main_mod.app, host="127.0.0.1", port=8123, log_level="error")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.5)

    ok = True
    try:
        with httpx.Client(base_url="http://127.0.0.1:8123", timeout=20) as client:
            cid = client.post("/api/conversations").json()["id"]
            with client.stream(
                "POST", f"/api/chat/{cid}",
                headers={"Content-Type": "application/json"},
                json={"message": "list the workspace"},
            ) as resp:
                assert resp.status_code == 200, resp.status_code
                body = "".join(resp.iter_text())
            events = parse_sse(body)
            types = [e["type"] for e in events]
            print("event sequence:", types)

            assert types[0] == "delta", types
            assert "tool_start" in types and "tool_end" in types, types
            assert types[-1] == "done", types

            tool_end = next(e for e in events if e["type"] == "tool_end")
            assert tool_end["name"] == "list_dir" and tool_end["ok"] is True, tool_end

            done = next(e for e in events if e["type"] == "done")
            assert done["usage"]["input"] == 30 and done["usage"]["output"] == 9, done["usage"]
            assert done["usage"]["tools"] == 1, done["usage"]
            assert done["cost"] > 0, done
            assert len(done["tools"]) == 1, done

            conv = client.get(f"/api/conversations/{cid}").json()
            msgs = [(m["role"], m["content"]) for m in conv["messages"]]
            assert msgs[0] == ("user", "list the workspace"), msgs
            assert msgs[1][0] == "assistant" and "Done." in msgs[1][1], msgs
            stored_meta = conv["messages"][1]["meta"]
            assert stored_meta["tools"][0]["name"] == "list_dir", stored_meta
            assert "result" in stored_meta["tools"][0], stored_meta
            assert stored_meta["cost"] > 0, stored_meta
            print("persisted:", msgs[1][1], "| meta ok")

            # client-abort path: response stops cleanly without exception
            with client.stream(
                "POST", f"/api/chat/{cid}",
                headers={"Content-Type": "application/json"},
                json={"message": "again"},
            ) as resp2:
                it = resp2.iter_text()
                next(it)  # read one chunk, then disconnect
            print("client abort path ............... OK")
    except Exception as e:
        ok = False
        print("FAILED:", type(e).__name__, e)
        raise
    finally:
        server.should_exit = True
        t.join(timeout=5)
    if ok:
        print("\nSSE endpoint tests passed.")
    else:
        sys.exit(1)


main()
