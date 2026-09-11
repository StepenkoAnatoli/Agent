# 06 — EVALUATION, OBSERVABILITY & PROMPT ENGINEERING

## 6.1 The benchmark landscape (and why we mostly ignore it)

`WELL_SUPPORTED` (K15–K19, S15, S18). The six signal benchmarks: **SWE-bench Verified** (coding), **GAIA** (general assistant), **OSWorld** (computer use), **Tau²-Bench** (tool-agent-user policy adherence), **WebArena** (browser), **METR HCAST/Time Horizons** (long-task ability) (K15). Specialist: Terminal-Bench (DevOps), AgentBench (8 environments), ToolSandbox (stateful tools), **AgentDojo** (prompt-injection security), **MCPSecBench/MCPTox** (MCP attacks), SWE-EVO/SWE-CI/SWE-bench Science (long-horizon/maintainability) (K17, K18, B18–B21).

**Why public benchmarks are NOT our eval target** (the disconfirmation pass):
- **Contamination is the default**: 5–15 pts inflation estimated; OpenAI's 2026 audit found 59.4% of the hardest Verified tasks have tests that wouldn't actually catch the bug (K15).
- **Reward hacking at scale**: UC Berkeley RDI (Apr 2026) automated an agent that broke 8 major benchmarks to ~100% (e.g., reading gold answers via `file://` URLs on WebArena); METR found o3/Claude 3.7 reward-hack in 30%+ of eval runs (K19).
- **Harness effects**: scaffolding adds 5–15 pts on SWE-bench; +30 pts on GAIA (HAL); model rankings flip between harnesses (K19, K15, B18); hosting environment alone can move scores **18 points** (K19).
- **Grading brittleness**: LLM-as-judge has position/verbosity bias and false positives; exact-match has false negatives (K16). pass^1 hides reliability; pass^k drops sharply (K16).
- **Snapshot blindness**: ~18% of agent patches regress passing tests; long-horizon collapse 72.8% → 25%; most models <50% on long-term maintenance (B18–B21).

> **Rule R10:** public benchmarks are screening signals only. **Our eval suite is private, hidden-oracle, and harness-specific** — it is the product's control loop (report 1 §14.4), extended per bugs report §11.2: regression cases, long-horizon tasks, harness self-tests (resume/replay, metering, sandbox golden paths + adversarial), and injection cases.

## 6.2 Our eval architecture

`WELL_SUPPORTED` (S14, B18–B22, K19):

| Layer | What | Why |
|---|---|---|
| Unit evals (10+) | small hidden-oracle tasks: add flag X, fix bug Y in fixture repos | fast signal per harness change |
| Regression evals | run existing test suites; **pass-to-fail detector** | ~18% regression rate makes this mandatory |
| Long-horizon (2–3) | multi-step evolution tasks (EvoScore-style) | snapshot benchmarks overstate ~3× |
| Harness self-tests | resume/replay, metering accuracy, sandbox golden paths (git flows, symlinks, hooks) + adversarial cases | the two vendor bug families (bugs report §8) |
| Security evals | injection-laced repos/pages; assert boundary holds | release blocker (ch. 07) |
| A/B harness | same model, different harness versions | harness is part of the system under test |

Environment discipline: every case is containerized from day one (manual env replication costs ~10 h/repo — B22); run evals in the **deployment-shaped** environment (K19: 18-pt environment variance).

## 6.3 Observability — OTel GenAI is the standard

`ESTABLISHED_FACT` (K20–K24): OpenTelemetry **GenAI Semantic Conventions** (SIG since Apr 2024; spec v1.41 by mid-2026) define six layers: LLM client calls, agent orchestration, MCP tool calls, workflow composition, content capture, quality evaluation (K21). Span tree: `invoke_agent` → `chat`/`execute_tool` children; key attributes `gen_ai.request.model`, `gen_ai.usage.*`, `gen_ai.response.finish_reasons`, cost/latency (K21). Real products already emit it: VS Code Copilot (traces/metrics/events), OpenAI Codex (log events + metrics), Claude Code (metrics + logs, trace beta) (K24).

Backends: Langfuse (OSS, OTLP endpoint), LangSmith (LangGraph depth), Phoenix/Arize, Laminar, Datadog LLM, Braintrust (evals) (K22, K23).

**Privacy default: content capture is OFF in production; ON in dev/staging** (K21). "Observability is necessary; evaluation is sufficient" — traces show the decision, eval scores tell whether it was correct (K21).

> **Rule R11:** every component emits OTel GenAI spans from v0.1. Telemetry must classify errors into model / context / orchestration / metering / sandbox / capacity — otherwise misdiagnosis (the April 2026 lesson, bugs report §4.1).

## 6.4 Reliability patterns — LLM calls are not REST calls

`WELL_SUPPORTED` (K64–K67, B8):
- **Latency**: P50/P99 ratio 1:8–1:15 (vs 1:2–1:3 for REST); P99 >30 s happens (K64).
- **Error mix**: ~5% of all spans error; **60% of LLM errors are 429s** (K65). 86.7% of Claude Code API errors were local connection failures (B8) — measure before blaming the provider.
- **Retry only transient**: 429, 5xx, timeouts/network. **Never retry 400/401/403/content-policy** — deterministic, retrying burns money (K66).
- Exponential backoff + jitter: base 1–2 s, ×2, jitter 0–base, cap 30–120 s, max 5–7 attempts; honor `Retry-After` (K66, K67). Jitter cuts retry storms 60–80% (K67).
- **Circuit breakers** on provider + fallback chain; open-trip in <30 s (K64). Monitor: retry rate >10%, breaker open >5 min, retries exhausted >5%, loop stuck >30 min (K67).
- Validation gates catch ~70% of hallucinated outputs before tool execution; schema + business + safety layers (K65).

> **Rule R12:** the model gateway implements the full pattern (retry policy, jitter, breakers, fallback chain, budget enforcement, deprecation via config). This is one module with its own tests.

## 6.5 Agent failure taxonomy (what our telemetry must label)

`WELL_SUPPORTED` (B18): strong models fail on **instruction following** (misreading requirements); weak models on **tool use + syntax**; older models **loop** or **terminate early**. Detection: loop detectors (no-progress N turns), early-stop detectors, scaffold-sensitivity tests (B18).

## 6.6 Prompt engineering — system prompts are software

`WELL_SUPPORTED` (K44, K45, K48):
- Treat system prompts as **conditionally assembled code**: version control, testing, gradual rollout. Claude Code's 110+ instruction strings are individually testable units (K44). (This is exactly the vendor process fix from bugs report §4.1.)
- Static vs dynamic split: identity/rules/tool-defs/security = static prefix (cacheable); RAG, summaries, current file, skills = just-in-time injection (K44).
- **Instruction hierarchy** (system > user > tool output) is trained into models: +63% defense vs prompt extraction — but RL-based attacks still achieve 98% bypass (K44). Conclusion: hierarchy helps; it is **not** the security boundary (that's ch. 07).
- Reasoning models invert classic prompting: **no chain-of-thought prescriptions**; specify goal, constraints, output contract (K45).
- 12 system-prompt modules (K45): role, goal, constraints, tool instructions, output format, examples, error handling, reflection, memory, escalation, stop criteria, safety. Our system prompt = these modules, each versioned + eval-gated.
- "Find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome" (K45) — the compactness principle behind Rules R2/R4.

## 6.7 Quality loop (the meta-process)

Build → eval → trace → classify error (model/context/harness) → fix the right layer → re-eval. Eval results and traces live in the same event store (K21). Reading **20 real traces weekly** is the practitioner habit (K45). This loop IS the "monitoring & re-evaluation" requirement from the mission control plane — and it is how the one system stays correct over time (control-plane `monitoring` block).
