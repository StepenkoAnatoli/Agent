"""The agent loop: model turn → tool execution → repeat, with budgets.

Implements the research core: per-run iteration budget (Rule R3/R7),
visible tool events, token/cost accounting (Rule R14 spirit), graceful
degradation when a local model does not support tools.
"""

import json

from config import estimate_cost, load_settings
from providers import ProviderError, get_provider
from system_prompt import SYSTEM_PROMPT
from tools import TOOL_DEFS, execute_tool


async def run_agent(emit, history: list, user_message: str):
    """Run one user turn. `history` = canonical messages BEFORE this turn."""
    settings = load_settings()
    max_iterations = int(settings.get("max_iterations", 6))
    provider_name = settings.get("provider", "anthropic")

    messages = history + [{"role": "user", "content": user_message}]
    totals = {"input": 0, "output": 0, "tools": 0}
    tool_trace = []  # for the UI chips and stored meta

    try:
        provider = get_provider()
    except ProviderError as e:
        yield {"type": "error", "kind": e.kind, "message": e.message}
        return
    # The model actually in use (provider resolves defaults), used for the
    # usage footer and cost estimate.
    model_name = getattr(provider, "model", None) or settings.get("model") or provider_name

    tools_enabled = True
    for iteration in range(max_iterations + 1):
        tool_calls = []
        try:
            stream = provider.stream(messages, SYSTEM_PROMPT, TOOL_DEFS if tools_enabled else None)
        except ProviderError as e:
            yield {"type": "error", "kind": e.kind, "message": e.message}
            return

        try:
            async for event in stream:
                if event["type"] == "delta":
                    yield event
                elif event["type"] == "tool_call":
                    tool_calls.append(event)
                elif event["type"] == "usage":
                    totals["input"] += event.get("input", 0)
                    totals["output"] += event.get("output", 0)
        except ProviderError as e:
            if e.kind == "tools_unsupported":
                tools_enabled = False
                yield {"type": "notice", "text": "Local model does not support tools — continuing without them."}
                continue
            yield {"type": "error", "kind": e.kind, "message": e.message}
            return

        yield {
            "type": "usage",
            "input": totals["input"],
            "output": totals["output"],
            "tools": totals["tools"],
        }

        if not tool_calls:
            break

        if iteration >= max_iterations:
            yield {"type": "notice", "text": f"Reached the tool limit ({max_iterations} steps) — stopping here."}
            break

        assistant_calls = []
        for tc in tool_calls:
            try:
                args = json.loads(tc.get("input") or "{}")
            except Exception:
                args = {}
            assistant_calls.append(
                {
                    "id": tc.get("id") or f"call_{iteration}_{len(assistant_calls)}",
                    "name": tc.get("name", ""),
                    "args": args,
                }
            )

        messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": c["id"], "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                    for c in assistant_calls
                ],
            }
        )
        for c in assistant_calls:
            yield {"type": "tool_start", "name": c["name"], "input": c["args"]}
            result = await execute_tool(c["name"], c["args"])
            totals["tools"] += 1
            trace = {"name": c["name"], "input": c["args"], "ok": result["ok"], "summary": result["summary"], "result": result["result"]}
            tool_trace.append(trace)
            yield {"type": "tool_end", "name": c["name"], "ok": result["ok"], "summary": result["summary"], "detail": result["result"]}
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": result["result"]})

    cost = estimate_cost(provider_name, model_name, totals["input"], totals["output"])
    yield {
        "type": "done",
        "usage": totals,
        "cost": round(cost, 5),
        "model": model_name,
        "tools": tool_trace,
    }
