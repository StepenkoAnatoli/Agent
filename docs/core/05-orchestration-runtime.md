# 05 — ORCHESTRATION, RUNTIME & INFRASTRUCTURE

## 5.1 Multi-agent patterns — when and which

`WELL_SUPPORTED` (K30–K34). Five patterns: **supervisor**, pipeline (sequential), fan-out (parallel), swarm (peer), debate. Measured tradeoffs (K33):

| Metric | Supervisor | Swarm |
|---|---|---|
| Latency (handoff needed) | ~9.1 s | ~5.4 s |
| LLM calls per request | 2 (route + specialist) | 1 |
| Avg tokens/request | ~2,800 | ~1,900 |
| Routing accuracy | **94%** | 91% |
| Failure mode | bottleneck | **swarm ping-pong loops** until recursion limit |

- **Supervisor is the 2026 production default**; orchestrator–worker ≈70% of production deployments (K34, K32).
- Debate costs ~2.5× a single model — only when stakes justify (K32).
- **Most multi-agent failures happen at handoffs, not inside agents** (K30): infinite loops, context drift, budget explosion, handoff data loss, conflicting actions.
- **Skip multi-agent entirely** with <3 distinct domains or no per-agent evals — "without them, you're debugging in production" (K33).

> **Rule R7:** v1 is single-agent with subagents for parallel context isolation only (the Claude Code model, S1). Multi-agent orchestration is adopted only when a demonstrated failure mode (ch. 06 evals) demands it.

## 5.2 Framework landscape (15 frameworks surveyed)

`WELL_SUPPORTED` (K01–K04). Tiered production picture:

| Tier | Frameworks | Fit |
|---|---|---|
| 1 — production-hardened | **LangGraph** (stateful graphs, checkpointing, HITL), CrewAI, Microsoft Agent Framework, OpenAI Agents SDK, Google ADK | regulated/enterprise/multi-agent |
| 2 — strong niches | **Claude Agent SDK** (production-tested harness as a library: files/shell/MCP/hooks/permissions/subagents), Pydantic AI (type-safe, durable execution), LlamaIndex, Mastra, Agno | coding/research; typed Python; RAG; TS stacks |
| 3 — specialized | DSPy (prompt compilation), Letta/MemGPT (persistent memory), Haystack, mcp-agent, AG2 | research/prototyping |

Key splits (K04): provider-native vs independent; **graph-based (explicit control) vs model-driven loop (simplicity)**. Our decision: the harness is small enough that we **build the loop on a typed SDK layer** (Pydantic-AI-style type safety, K02: "type-safe, testable agent logic") rather than adopting a heavy graph runtime in v1 — consistent with Anthropic's "start with direct APIs; frameworks hide prompts and encourage over-engineering" (S16). LangGraph-class checkpointing becomes relevant only at the durable-orchestration stage (§5.4).

## 5.3 Execution sandboxes — the isolation decision

`WELL_SUPPORTED` (K54–K58, S20). Isolation ladder:

| Tech | Startup | Isolation | Density/memory | Use |
|---|---|---|---|---|
| Docker container | ~200 ms–2 s | process (shared kernel) | 5–10 MB/instance | trusted workloads, dev |
| gVisor (Sentry) | ~300 ms | syscall interception | 15–30 MB | multi-tenant, high density (Modal, Beam, Cloud Run) |
| **Firecracker microVM** | ~150 ms (snapshot resume 5–30 ms) | hardware (own kernel) | 30–50 MB | **untrusted code, production** (E2B, CodeSandbox, AWS Lambda MicroVMs, Vercel) |
| Kata Containers | ~200 ms+ | hardware | 50–100 MB | regulated, zero-trust |
| Wasm/V8 isolates | <1 ms | high but limited | tiny | edge, real-time |

- Firecracker VMM ≈ **50K lines of Rust**, deliberately small device model (K56); escaping requires a hypervisor exploit, not a syscall bug (K56).
- gVisor blocks GPU PCIe passthrough; Firecracker supports **VFIO GPU passthrough** (K56) — relevant only if the system ever runs ML inside sandboxes.
- Measured cold starts differ from vendor claims (E2B: 717 ms create / 662 ms resume measured; Modal 2.4 s) — test, don't trust (K57).
- Platform options (K54–K58): E2B (managed, ~$0.05/vCPU-hr; OSS Apache-2.0 self-host), Modal (gVisor, GPU), Daytona (persistent workspaces, Docker/Kata), Northflank (Kata/gVisor, BYOC), CubeSandbox (self-host KVM <60 ms), Google Agent Sandbox (gVisor on GKE), AWS Lambda MicroVMs (Firecracker snapshots).

> **Rule R8:** dev sandboxes = Docker; **production execution of model-generated code = Firecracker-class microVM**, workspace-scoped filesystem, deny-by-default egress with domain allowlist (S19, report 1 §14.5). Container-only is not acceptable for untrusted code (S20).

## 5.4 Durable execution — resume as infrastructure

`WELL_SUPPORTED` (K35–K39). The market validation: **Temporal raised $300M at $5B (Feb 2026)**; 9.1T lifetime executions, 1.86T from AI-native companies (K37). Four runtime models (K36):

| Runtime | State lives in | How resume works |
|---|---|---|
| Temporal | event history (service) | replay history, skip completed activities |
| Restate | journal + KV (server) | re-invoke handler, replay journal |
| DBOS | **Postgres checkpoints** | re-run pending workflow, return checkpointed outputs |
| Inngest | managed step state | re-invoke with memoised step results |

Core concepts (K35–K39):
- **Determinism is the price of replay** — LLM calls, shell, RNG, wall-clock **must be Activities/steps** (recorded durable results), never inline workflow logic (K36). Pydantic AI's Temporal integration enforces exactly this split (K39).
- **Idempotency keys** on every external write — otherwise replay = duplicate side effects (two charges, two emails) (K35).
- **Continue-as-new** for long histories; **Saga pattern** adapted for compensating rollbacks (K37).
- **Event sourcing** for agent state: `tool_called`/`llm_responded` events give a complete audit trail, **time travel** (rewind and re-execute), and agent versioning (replay old conversations against new logic) (K37).
- LangGraph checkpoints (PostgresSaver/SqliteSaver) = agent-native checkpoints + human-in-the-loop interrupts (K39).

> **Rule R9:** our agent run = a **durable workflow from day one** (Postgres-backed — zero new infra, DBOS-style or LangGraph-class checkpointing). This directly implements Decision D5 and kills the session/resume bug class that plagued both majors (bugs report §4.4, §5.3).

## 5.5 Runtime topology (the one system, sketched)

```
Client (TUI → web → IDE)  ─▶  API/orchestrator
                                 ├─ session store (Postgres: transcript, state.md, checkpoints, budgets)
                                 ├─ model gateway (default + fallbacks, caching, retry policy — ch. 02)
                                 ├─ permission gate (deterministic — ch. 07)
                                 ├─ sandbox manager (microVM pool, egress allowlist)
                                 ├─ tool registry (ch. 04 catalog + MCP clients)
                                 ├─ skill/memory loader (ch. 03)
                                 └─ telemetry (OTel — ch. 06)
```
