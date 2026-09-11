# 02 — MODELS & ECONOMICS: What We Call, and What It Costs

## 2.1 Model landscape (2026) — directional, not absolute

**Standing finding:** aggregator benchmark numbers conflict (report 1 §8 C1). Direction is consistent: Claude's Opus line leads coding; GPT-5.x/Codex leads terminal/computer-use; Gemini 3.x is strong on context/multimodal/value; open-weight (MiniMax, GLM, Qwen, DeepSeek) is within a few points of frontier at far lower cost (S15, S18, S25, S26). **All exact numbers are `CONTESTED` — our own evals are the only trustworthy signal** (ch. 06).

Hard facts from this pass:
- Open-weight models reach "useful for daily work" at **~32B parameters** (Qwen2.5-Coder-class) (K42).
- Providers deprecate models on **90–180-day cycles** (K64) → model identity must be **config, not code**.
- OpenAI measured uptime Dec 2025–Mar 2026: **99.76% ≈ 16 h/year down**; ChatGPT 99.62% (B13, K65). Capacity incidents are a monthly-class event (~18/month observed, B13).

## 2.2 Provider-native SDK vs. independent framework

The 2026 landscape splits into provider-native SDKs (Claude Agent SDK, OpenAI Agents SDK, Google ADK) — deepest integration, lock-in — and independent frameworks (LangGraph, Pydantic AI, Mastra, Strands, CrewAI) — model flexibility, more abstraction (K04, K02).

**Implication for our one system:** the harness must be **provider-agnostic at the gateway level** with a default provider and a fallback chain. This is the anti-C6 mitigation (bugs report §9) and the anti-churn mitigation (2.1).

## 2.3 Model routing & cascading — the highest-leverage cost lever

`WELL_SUPPORTED` (K26–K29, K64):

| Pattern | How | Savings |
|---|---|---|
| Static routing | cheap model for simple tasks (FAQ, extraction, status) | 40–60% of requests qualify (K26) |
| **Dynamic cascade** | small model first → confidence-gated escalation to frontier | **75–85% cost cut at ~95% of frontier quality** (RouteLLM: only 14–26% of calls reach the strong model) (K29) |
| Cascade routing (unified) | Dekoninck et al. framework | approaches theoretical optimal cost-quality (K28) |
| Fallback chain + circuit breaker | provider outage → next provider | recovers in <30 s (K64) |

Escalation must be **eval-gated**: "cost reduction that breaks answers is not savings" (K27). Track the escalation rate as a metric (K29).

## 2.4 Prompt caching — the best single ROI

`WELL_SUPPORTED` (K07, K26, K28, K29):
- Provider-side prompt caching on stable prefixes: **~90% reduction on cached input tokens**; Anthropic `cache_control: ephemeral`.
- **Rule R2:** the system prompt + tool definitions must be **byte-identical across turns**; timestamps/session IDs/per-turn data go in the final user message, never the prefix (K07). This is why our system prompt is assembled, versioned software (ch. 06 §6.6).
- Warning: compaction **invalidates cached prefixes** — caching and compaction are in fundamental tension; both vendors were bitten (bugs report §4.1). Design compaction and caching together.

## 2.5 The rest of the cost stack, in priority order

`WELL_SUPPORTED` (K29, K64, K65):

1. **Prompt caching** (90% off cached input) — no quality risk.
2. **Batch APIs** (~50% off) for latency-tolerant work — async tasks, evals, indexing.
3. **Routing/cascade** (75–85% on routed traffic).
4. **Right-size the model** — open-weight options run 15–30× cheaper per token (K29).
5. **Semantic caching** — ~31% of redundant queries eliminated before any API call (K28); exact-match alone gets ~2% hit rate on natural language; semantic 40–60% (K64).
6. **Context compression** — 20–40% (K26); combined stack: **60–95% total reduction** (K26, K28).

**Cost baseline to design against:** agent workloads cost **3–10× chat** due to multi-turn context accumulation, tool-call overhead, and loop iterations (K28). Metering is a tested subsystem, not bookkeeping — both vendors shipped metering bugs in 2026 (bugs report §5.1, §4.2).

## 2.6 Budget guardrails — the four dimensions

`WELL_SUPPORTED` (K65, K27, S16): token · cycle (loop iterations) · time (wall-clock) · cost. Budget guardrails cut ~40% token waste in complex loops (K65). Enforcement tiers: per-request → per-user-hour → per-user-day → global (K64). Anomaly alerts at 50% and 80% of budget (K25).

> **Rule R3:** every agent run carries all four budgets, enforced by the harness (not by the model's good behavior), with graceful degradation on exhaustion (checkpoint-and-resume, not silent kill — bugs report §9 C6).

## 2.7 What we do NOT do

- We do not train or fine-tune a base model (report 1 §14.1 — the economics of frontier training are out of reach by design).
- We do not commit to a single provider in code (2.1–2.2).
- We do not use local models for the default path in v1 — they are a **fallback/degraded mode** (K42: 32B-class is "useful daily work" but below frontier).

## 2.8 Reasoning models & thinking budgets (M2 — closed 2026-09-11)

`WELL_SUPPORTED` (K68, K69, K70, K71):

- **Mechanics & cost**: extended thinking = the model spends tokens on internal reasoning before answering; thinking tokens are billed as output at the model's output rate ($15/M Sonnet-class, $25/M Opus-class) → per-request cost jumps **3–10×**; measured example: $0.0134 → $0.0978 (7.3×) for the same problem (K69).
- **Budget guidance**: 1,024 tokens hard minimum; **5–10K typical**; 20K+ for hard problems; up to 128K on Opus 4.6; **adaptive thinking + effort levels** exist on Sonnet 4.6/Opus 4.6 (K68). Do not blindly maximize effort — overthinking on easy tasks is real (B8).
- **Provider differences**: Claude = explicit `budget_tokens`, thinking streamed and readable (debuggable, predictable); OpenAI o-series = `reasoning_effort` (low/medium/high), thinking hidden (less debuggable) (K69).
- **The loop failure mode**: recursive agents without per-turn thinking caps accumulate thinking across dozens of turns → **$40–100 for a single task** (K70). Countermeasure: **tiered thinking enforcement** — simple: budget 0 · medium: ~1,500 · complex: ~5,000 — plus per-call `max_cost` caps (K70).
- **Production rule**: log actual thinking tokens consumed; <30% of budget used → task simpler than assumed; consistently at ceiling → raise budget or accept truncation (K69).
- **Gateway integration**: the thinking tier joins the routing decision (§2.3): cheap model + small thinking budget for routine turns; escalate effort only when the cheap tier fails — the escalation discipline observed in real-task testing (K71).

> **Rule R14:** every model call in the loop carries an explicit thinking budget by task tier, a per-turn cost cap, and a run-level thinking-token budget. No unbounded reasoning in loops.
