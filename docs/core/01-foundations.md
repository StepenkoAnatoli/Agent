# 01 — FOUNDATIONS: What the System Is

## 1.1 The irreducible core

Every production agent system — Claude Code, Codex, Arena Agent Mode, and ours — is the same skeleton
(`ESTABLISHED_FACT`, S1–S2, K03):

```
User request ─▶ context assembly ─▶ model ─▶ tool call(s) ─▶ permission gate ─▶ sandbox ─▶ observation ─▶ loop
                                              (reason → act → observe until the model stops calling tools)
```

Everything else in this knowledge base is a layer on that loop. The layers, in the order the incumbents themselves added them
(`REASONABLE_INFERENCE` from S1, S14, K03):

1. **Tools** (read/edit/shell/web)
2. **Sandbox** (isolation for execution)
3. **Permission gate** (deterministic policy; cannot be talked past)
4. **Context engineering** (memory files, budgets, compaction)
5. **Context discipline** (subagents, skills, tool filtering)
6. **Connectors** (MCP)
7. **Hooks** (deterministic side-effects on events)
8. **Evals + telemetry** (the control loop for the builders)

**The orchestrator does not decide *what* to do; the model does.** Each turn is a fresh decision informed by observed results. Planning is emergent, not architectural (S2). This is the single most important mental model for designing our system.

## 1.2 System taxonomy (what kind of "agent system" exists)

Per Arize's layered taxonomy (K03):

| Layer | What it provides | Examples |
|---|---|---|
| Agent SDK/framework | Code primitives: agents, tools, model calls, handoffs, state, structured outputs | OpenAI Agents SDK, Pydantic AI, Strands |
| Orchestration runtime | Execution engine: graphs, branches, retries, checkpoints, long-running workflows | LangGraph, LlamaIndex Workflows |
| **Agent harness** | Complete operating environment: loop + context + tools + permissions + persistence + recovery + hooks + subagents | **Claude Agent SDK**, MS Agent Framework harness, Mastra harness |
| Managed runtime/platform | Hosted deployment, scaling, security, observability, governance | AWS Bedrock AgentCore |

**Decision D1:** we are building a **harness** (the middle layer), on top of provider APIs, with a managed-runtime ambition only if the product path (Path C) is chosen. This maps to the strongest evidence in report 1 §14.

## 1.3 Workflow vs. Agent — the discipline against over-engineering

Anthropic's guidance (Dec 2024, still the industry reference in 2026): **find the simplest pattern that passes evaluation**. Most production needs are workflows (fixed path), not autonomous agents (model chooses path). Use an agent only where the path can't be hardcoded **and** progress is verifiable (tests, environment state) (S16, K61).

Six canonical workflow patterns (S16, S17): augmented LLM call · prompt chaining · routing · parallelization · orchestrator–workers · evaluator–optimizer. The agent is the seventh: open-ended loop with verifiable feedback.

> **Rule R1:** Label every feature as task / workflow / agent before building it. Default to the simplest label. (S16)

## 1.4 The three reference systems (condensed from report 1)

| Dimension | Claude Code | ChatGPT / Codex | Arena.ai Agent Mode |
|---|---|---|---|
| Surface | Terminal-first, repo-native | Everywhere: web/desktop/mobile/cloud tasks | Browser + sandbox + GitHub PR flow |
| Context | CLAUDE.md + auto-memory + skills | AGENTS.md + automatic memory | Session memory |
| Enforcement | Permission modes + sandboxed Bash (OS-enforced) | Sandbox + approvals | Platform sandbox (internals UNKNOWN) |
| Extensibility | Skills, MCP, hooks, subagents, Agent SDK | Skills, MCP, apps/connectors | Built-in tool suite |
| Signature strength | Planning, large-codebase reasoning, automation depth | Cloud tasks, computer use, speed, UX polish | Causal real-task evaluation at scale (160,480 tasks/7-day slice) |

**The durable product insight** (S4, S6): winners pair a tight core loop with **one or two signature surfaces**, not feature parity. Our candidate signature surface: a Windows-first "Download → Install → Open → Run" experience nobody has nailed (bugs report §5.3: Codex #13993/#20214/#40752; Claude Code #42776).

## 1.5 The build decision in one paragraph

Evidence across all passes converges on: **harness over model, evals over leaderboards, containment over detection, simplicity over architecture** (report 1 §13, §14). The cost of being wrong on any of these is documented in the bugs report (vendor postmortems) and ch. 07 (real-world RCE).

**Next chapters:** 02 covers the models and the economics of calling them; 03 covers what goes into the context window and how it stays sane.
