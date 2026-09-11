# 08 — UX, PRODUCT & THE OSS REFERENCE LANDSCAPE

## 8.1 Why chat-first UX fails for agents

The interface must be designed for **delegation and oversight**, not conversation (K63). The structural insight with the strongest evidence: **separate the activity panel from the conversation thread** — conversation = clarification/feedback; activity panel = autonomous work, tool calls, progress, approval requests, as a persistent auditable log (K59). Conflating them causes cognitive overload and makes auditing impossible (K59).

Build order that minimizes rework (K63): **controls (start/stop/pause) → receipts (what happened) → logs (activity timeline) → approvals (human checkpoints) → memory (what's remembered) → eval (confidence over time).** v1 definition-of-done: the user can predict what the agent will do, pause it mid-flight, approve critical actions, and recover from failures (K63).

## 8.2 Human-in-the-loop as a designed product surface

`WELL_SUPPORTED` (K59–K61):

| Pattern | Mechanism | Notes |
|---|---|---|
| Approval gates | pause before irreversible/sensitive ops with full context (what, why, consequences); durable checkpoint while waiting (LangGraph interrupt) | default **deny on timeout** (K60) |
| Progressive delegation | conservative autonomy envelope expanding with trust | experienced users auto-approve in **>40% of sessions** (2× new users) and *also* interrupt more (K59) — trust + oversight grow together |
| Plan-and-execute preview | show step-by-step plan; approve/modify/remove steps | highest-ROI UX for tasks >30 s (K59) |
| Multi-channel approvals | Slack/email/SMS/web per risk class | context-rich request, logged decisions (K60) |
| Autonomy levels | explicit autonomy slider / mode (safe mode fallback) | matches Claude Code permission modes (S5) |
| Ambient patterns | listen to event streams; Notify/Question/Review; only interrupt on important signals | saves attention; avoids notification fatigue (K62) |
| Undo/rollback | receipts + undo for every mutating action | Codex removed /undo → 77-comment issue (B9 #9203); it's a requirement |

**Risk classification for approvals** (K60): cost thresholds, data sensitivity, reversibility. Gate types: approve plan / approve execution / approve final output / approve exceptions (K63).

## 8.3 Distribution & the Windows-first signature surface

`WELL_SUPPORTED` (bugs report §5.3, S4, S6, brief §32):
- Codex Windows: no standalone installer (84-comment request #13993), app freezes on capable hardware (#20214), desktop fails to start after updates (#40752), WSL-thread resume broken (#40819/#40715).
- Claude Code Windows: orphaned-process relaunch lock (#42776); native support limited — WSL2 recommended (B7).
- **Conclusion: nobody has shipped a polished "Download → Install → Open → Run" agent for Windows.** This is the demonstrated gap → our signature surface (Decision D6).
- Requirements derived from the bug corpus: standalone installer; **updater with rollback** (both vendors ship breaking auto-updates); no-terminal happy path; WSL and native paths both tested; graceful degradation on quota/capacity.

## 8.4 The OSS reference landscape (what to study, reuse, and avoid)

Live GitHub API data, 2026-09-11 (GH-OSS) + K40–K43:

| Project | Stars | License | What to take from it |
|---|---|---|---|
| **OpenHands** | 87,271 | MIT | autonomous issue→PR loop; CodeAct execution model; 72% SWE-bench Verified harness (K42) |
| **Cline** | 67,801 | Apache-2.0 | Plan/Act separation, approval UX, MCP marketplace; ~8M active devs (K42) |
| **Goose** | 54,100 | Apache-2.0 | extensible plugin architecture (Block → Linux Foundation) |
| **Aider** | 48,889 | Apache-2.0 | **diff/patch edit model**: 2–5K tokens/round vs 15–50K full-file (K42); git-native reversibility |
| **LangGraph** | 41,413 | MIT | stateful orchestration reference, checkpoints |
| **openai-agents-python** | 29,337 | MIT | handoff primitives, guardrails, tracing |
| **qwen-code** | 27,758 | Apache-2.0 | arena/multi-model execution reference (B17) |
| **pydantic-ai** | 19,856 | MIT | type-safe agent logic, durable-execution integrations |

Others in the landscape (K40, K43): opencode (198K★, closest Claude Code drop-in), Codex CLI (OSS, sandbox-first), Continue (final release — do not build on), Kilo Code, Open Interpreter, Plandex, Tabby (self-hosted completion), Devin/Jules/Manus (cloud platforms), Cursor/Windsurf/Zed/Antigravity (dedicated IDEs), Warp 2.0.

**Editing-model decision for our system:** Aider's diff/patch model wins on tokens/cost/reversibility; full-file wins on simplicity/robustness for weak models; Claude Code/Cline use full-file + diff review (K42). v1 choice: full-file write with **automatic diff preview + undo receipt** (simplest that passes eval — S16), with the Aider-style git-native fallback for large refactors.

**Category map** (K40): IDE extensions (Copilot, Cline, Augment) · dedicated IDEs (Cursor, Devin, Zed, Antigravity, Kiro) · CLI tools (Claude Code, Aider, Codex, Goose, opencode, Qwen Code) · cloud platforms (Devin, OpenHands, Jules, Manus). Our one system targets CLI + web first, IDE extension later — matching the incumbents' own evolution.

## 8.5 Product principles (locked)

1. **One loop, one identity** — the system is one agent with subagents, not a fleet (Rule R7).
2. **Trust is the feature** — receipts, undo, audit log, honest quota UX (no "wasted reset" — B9 #31606), model identity disclosed (Arena's opacity was a complaint, B15; also Art. 50).
3. **Windows-first distribution** as the wedge (Decision D6), with §32-compliant beginner instructions when terminals are unavoidable (report 1 §14.6).
4. **Streaming everything** — AG-UI tool-call events in real time (K59, ch. 04 §4.5).
5. **Progressive delegation by default** (K59).
6. **Simplicity gate**: every product feature must map to a demonstrated failure mode or eval gap before being built (S16, K61: "choose a pattern only after you've seen the symptom").
