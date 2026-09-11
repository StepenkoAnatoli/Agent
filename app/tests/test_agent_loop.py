"""End-to-end test of the agent loop with a mock provider.

No network and no API key needed: a fake provider drives run_agent through
a tool-call iteration, and we assert the event stream, budget cap, workspace
enforcement and cost accounting.

Run from app/:  .venv/bin/python tests/test_agent_loop.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import agent as agent_mod
from config import get_workspace


class MockProvider:
    """Fake provider: first turn asks for a tool, second turn answers."""

    calls = 0
    model = "claude-sonnet-4-5"

    async def stream(self, messages, system, tools):
        self.calls += 1
        if self.calls == 1:
            yield {"type": "delta", "text": "Let me check "}
            yield {
                "type": "tool_call",
                "id": "call_1",
                "name": "read_file",
                "input": json.dumps({"path": "hello.txt"}),
            }
            yield {"type": "usage", "input": 12, "output": 5}
        else:
            yield {"type": "delta", "text": "It says hello."}
            yield {"type": "usage", "input": 40, "output": 9}


class LoopForeverProvider(MockProvider):
    """Always asks for a tool -> must hit the iteration cap."""

    async def stream(self, messages, system, tools):
        yield {
            "type": "tool_call",
            "id": f"call_{self.calls}",
            "name": "list_dir",
            "input": json.dumps({"path": "."}),
        }
        yield {"type": "usage", "input": 5, "output": 1}
        self.calls += 1


async def collect(provider_factory, message, max_iterations=6):
    events = []
    old_get = agent_mod.get_provider
    old_load = agent_mod.load_settings
    agent_mod.get_provider = provider_factory
    agent_mod.load_settings = lambda: {
        "provider": "anthropic",
        "model": "claude-sonnet-4-5",
        "max_iterations": max_iterations,
    }
    try:
        async for ev in agent_mod.run_agent(None, [], message):
            events.append(ev)
    finally:
        agent_mod.get_provider = old_get
        agent_mod.load_settings = old_load
    return events


async def main():
    ws = get_workspace()
    (ws / "hello.txt").write_text("Hello from the workspace.\n", encoding="utf-8")
    fail = []

    # --- 1. happy path with a tool call -------------------------------
    ev = await collect(MockProvider, "read my hello file")
    types = [e["type"] for e in ev]
    assert "delta" in types and "tool_start" in types and "tool_end" in types and "done" in types, types
    tool_end = next(e for e in ev if e["type"] == "tool_end")
    assert tool_end["name"] == "read_file" and tool_end["ok"] is True, tool_end
    done = next(e for e in ev if e["type"] == "done")
    assert done["usage"]["input"] == 52 and done["usage"]["output"] == 14, done["usage"]
    assert done["usage"]["tools"] == 1, done["usage"]
    assert len(done["tools"]) == 1 and "Hello from the workspace" in done["tools"][0]["result"], done["tools"]
    assert done["cost"] > 0, done["cost"]
    print("1. tool loop happy path ......... OK")

    # --- 2. workspace escape is refused --------------------------------
    class EscapeProvider(MockProvider):
        async def stream(self, messages, system, tools):
            yield {"type": "tool_call", "id": "c1", "name": "read_file",
                   "input": json.dumps({"path": "../../etc/passwd"})}
            yield {"type": "usage", "input": 1, "output": 1}

    ev = await collect(EscapeProvider, "try to escape")
    tool_end = next(e for e in ev if e["type"] == "tool_end")
    assert tool_end["ok"] is False and "outside the workspace" in tool_end["detail"], tool_end
    print("2. workspace escape refused ..... OK")

    # --- 3. iteration budget cap ---------------------------------------
    ev = await collect(LoopForeverProvider, "loop", max_iterations=3)
    notices = [e for e in ev if e["type"] == "notice"]
    assert any("tool limit" in n["text"] for n in notices), notices
    tool_ends = [e for e in ev if e["type"] == "tool_end"]
    assert len(tool_ends) == 3, len(tool_ends)
    print("3. iteration budget cap ......... OK")

    # --- 4. tools unsupported -> degrade gracefully ----------------------
    from providers import ProviderError as PE

    class DegradeProvider(MockProvider):
        def __init__(self):
            self.calls = 0

        async def stream(self, messages, system, tools):
            self.calls += 1
            if self.calls == 1:
                raise PE("tools_unsupported", "this model has no tool support")
            assert tools is None, "after degradation, tools must be None"
            yield {"type": "delta", "text": "plain answer"}
            yield {"type": "usage", "input": 3, "output": 2}

    ev = await collect(DegradeProvider, "hi")
    types = [e["type"] for e in ev]
    assert "notice" in types, types
    assert "done" in types and "error" not in types, types
    print("4. tools-unsupported degrade ... OK")

    if fail:
        print("FAILED:", fail)
        sys.exit(1)
    print("\nAll agent-loop tests passed.")


asyncio.run(main())
