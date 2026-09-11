# 09 — DISCONFIRMATION AUDIT: What We Missed

**Pass type:** attack/disconfirmation on our own research corpus (framework §12 applied to the knowledge base itself).
**Method:** keyword audit of all 13 KB/report files + framework checklist vs §3/§6/§9/§14/§19.
**Date:** 2026-09-11

---

## 0. Update log — pass 9 (2026-09-11): verification + unconditional material research

| Gap | Status | Outcome |
|---|---|---|
| B2 (primary benchmark verification) | **CLOSED** | Official leaderboards fetched (V1 swebench.com, V2 tbench.ai, 2026-09-11). Aggregator claims of 88–95% SWE-bench Verified are **NOT supported** by the primary source: official top = 79.2% (Opus 4.5 via agents); mini-SWE-agent harness (Feb 2026): 76.8% Opus-4.5-high @$0.75, 75.8% Gemini-3-Flash-high @$0.36, **75.8% MiniMax-M2.5-high @$0.07**, 72.8% GPT-5.2-high. Terminal-Bench: our TB2.0 citations (Codex 77.3%, Feb 2026) were point-in-time correct for v2.0, but the current leaderboard tops at **58.2%** (GPT-6 Astra + Codex, $3.3k full run) — benchmark version/difficulty changed. Consequence: report-1 `CONTESTED` numbers remain contested; the corpus now carries PRIMARY figures; a new model generation (GPT-6 Astra, Fable 5.1, Opus 5, Sonnet 5) validates the churn re-evaluation trigger. |
| M1 (policy engines) | **CLOSED** | Documented in 07 §7.6 + Rule R15 — Cerbos (sub-1ms PDP, purpose-built for agent/MCP authz), Cedar (typed model, dominates MCP enforcement), OPA (infra policy). |
| M2 (reasoning config) | **CLOSED** | Documented in 02 §2.8 + Rule R14 — thinking tokens billed as output (3–10× per-call cost), per-turn tiered budgets, runaway-loop guard. |
| M4 (RAG depth) | **CLOSED** | Documented in 03 §3.8 + Rule R16 — 2026 baseline pipeline (hybrid + RRF + cross-encoder rerank, 6–8 chunks), chunking defaults, latency budgets, faithfulness-first evaluation, agentic-RAG audit warning. |
| M3, M5–M10 | **NOT IN SCOPE** — user decision 2026-09-11: Path A (no build), scope = research & knowledge work | Browser-agent architecture (M3), voice (M5), multi-user governance (M6), GDPR/non-EU (M7), agent identity (M8), structured-output mechanisms (M9), local serving (M10) are parked; re-open only if scope changes. |
| B1 (scope) | **CLOSED (user)** | Path A · research & knowledge work · audience recommendation: individual researcher / knowledge worker on Windows, web-first (§10.1, 10.7). |
| B3 (git provenance) | **CLOSED (user)** | Commit & push authorized; executed 2026-09-11. |

---

## 1. Process verdict

The corpus is strong on: systems analysis, bug/failure evidence, security, economics, orchestration, evaluation methodology, compliance (EU), UX. It is **weak on implementation-level specifics for some locked decisions**, and it has **zero coverage** of several adjacent product surfaces. This document ranks every gap by decision relevance. Per the stopping rule, gaps that cannot change a decision are **not worth researching** — they are listed for completeness only.

## 2. BLOCKING gaps (mission-level, not research-level)

| # | Gap | Why it blocks | Fix |
|---|---|---|---|
| B1 | **User requirements never collected**: build path (A/B/C), target use cases, audience, budget, platform | Every design choice after D1 depends on it (voice? browser? teams? self-host?) | Decision needed from user — the single true blocker |
| B2 | **Benchmark claims unverified against primary sources** | We flagged C1 (CONTESTED) but never closed it; our "directional" claims rest on aggregators | One verification task: pull SWE-bench/Terminal-Bench official leaderboards directly |
| B3 | **Repo hygiene decisions open**: commit/push policy, PR creation | Work is preserved in-session; provenance not yet in git history | User decision (do not assume) |

## 3. MATERIAL gaps (could change a design decision — worth researching)

| # | Gap | Which decision it could change | Evidence of relevance |
|---|---|---|---|
| M1 | **Deterministic policy-engine implementation** — we assert "deterministic action policy" (D3) but have no implementation research (OPA/Cedar/permit.io, rule languages, latency budgets) | D3 (security layer) — the assertion needs an implementation path | Zero hits in corpus for Cedar; "policy engine" in 1 file only |
| M2 | **Reasoning-model usage patterns** — effort levels, thinking budgets, test-time compute, when extended thinking helps/hurts agents | Model-gateway design (ch. 02): default effort, budget allocation per step; Claude Code's effort levels are a proven surface | 0 hits: effort level, thinking budget, test-time compute |
| M3 | **Browser/computer-use agent architecture** — Playwright-class tooling, screenshot grounding, DOM vs accessibility tree, state management | Use-case scoping: if "do things on the web" is a target task, this is a subsystem; benchmarks covered (OSWorld/WebArena) but not the design | 0 hits: playwright, browser agent; benchmarks only |
| M4 | **RAG/retrieval engineering depth** — chunking, hybrid search, rerankers (Cohere/bge), query rewriting, eval of retrieval itself | If research/knowledge tasks are core to the system, the retrieval pipeline is a subsystem with its own evals | "RAG" mentioned broadly; 0 hits: rerank |
| M5 | **Voice / realtime multimodal agents** — WebSocket audio, VAD, interruption, realtime APIs | 2026's biggest adjacent surface (OpenAI Voice Agents etc.). Changes product scope if voice is a target; currently invisible to our plan | 1 incidental mention |
| M6 | **Team & multi-user governance** — RBAC, shared memory, org policies, audit per user | Product path C: the system's permission model must extend to human roles, not just agent actions | 0 hits: multi-user; RBAC only in MCP/NSA context |
| M7 | **Privacy & non-EU regulation** — GDPR (DPAs, retention, PII in traces), US state laws (Colorado et al.), cross-border data | If the system ships to EU/global users, Art. 50 alone is insufficient; trace content-capture defaults are a GDPR surface | 0 hits: GDPR, PII |
| M8 | **Agent identity & misuse** — agent impersonation ("what does agent X know?" attacks), agent-to-human deception, fraud | Completes the threat model (ch. 07 covers technical injection, not social/misuse vectors) | 1 incidental hit |
| M9 | **Structured-output reliability** — constrained decoding, schema validation, repair strategies | Tool-call reliability is our loop's backbone (ch. 04); we have rules but no mechanism research | 2 shallow hits |
| M10 | **Local/self-hosted serving** — Ollama/vLLM/llama.cpp, NPU/GPU on Windows, serving economics | The Windows-first signature (D6) may include a self-host/offline mode; needs serving-stack research | 0 hits for all three tools |

## 4. LOW / NON-MATERIAL gaps (listed for completeness — do NOT research yet)

| Gap | Why it's non-material |
|---|---|
| Market size / TAM / pricing models | Decision D1 (build harness) does not depend on market projections |
| Agentic fine-tuning research frontier (RLVR, process reward models) | D1 explicitly excludes training models |
| Edge/Cloudflare-class platforms (Durable Objects Agents SDK) | Infrastructure choice; only matters at scale-out, far after v1 |
| llms.txt / agentic-web standards | Nice-to-have for the web tools; changes nothing structural |
| Trajectory datasets (AgentTrek et al.), academic agentic-RL | Research-signal, not decision-signal |
| Accessibility, i18n, payments integration | Product polish; irrelevant until Path C + traction |
| Line-level teardown of one OSS reference (OpenHands/opencode) | Depth gap, not decision gap — we have landscape + licenses + star data; a teardown serves implementation later |

## 5. Framework checklist — what the mission standard required vs. what we did

| Requirement (§) | Status | Note |
|---|---|---|
| Objective/decision/constraints identified (§3) | ✅ | Control-plane + report §3 |
| Task classification (§4) | ✅ | mixed, documented |
| Research architecture & passes (§6–§8) | ✅ | 8 passes, all logged |
| Evidence hierarchy & provenance (§9, §11) | ✅ | K/S/B registers with retrieval dates |
| **Evidence states (§10)** | ✅ | legend in 00-INDEX |
| Disconfirmation of our own conclusions (§12) | ✅→ | This document is the pass; gaps ranked |
| Uncertainty management (§13) | ⚠️ | Classified, but B1 (user inputs) remains open |
| **Data reconciliation (§18)** | ⚠️ | Contradiction register exists; B2 (primary verification) unclosed |
| Change impact / baseline / break-tests (§21, §26, §27) | N/A | Correctly not run — no code authorized yet |
| Monitoring & re-evaluation (§29–§30) | ✅ | control-plane `monitoring` block |

## 6. Recommendation — what to close next, in order

1. **B1 (user decision)** — the only true blocker. Needs: build path A/B/C, target use cases (code? research? browser? voice?), audience, platform.
2. **B2 (verification task)** — pull official SWE-bench Verified + Terminal-Bench leaderboards; close or confirm C1. Small, fast, improves the corpus's weakest evidence.
3. **Material batch gated on B1's use-case answer**: M1 (policy engines) unconditionally; M2 (reasoning config) unconditionally; M3–M10 conditional on scope:
   - code-first product → M3, M9
   - research/knowledge product → M4
   - consumer product → M5, M6, M7, M8
   - self-host/offline → M10
4. **Non-material items:** park (documented here so they are not "missing" silently).

**Authorization state:** unchanged — `NOT_AUTHORIZED` for code. This audit + index update + control-plane update are the only repo changes this turn.
