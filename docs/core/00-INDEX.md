# CORE KNOWLEDGE BASE — INDEX & SOURCE REGISTER

**This is the project's core.** The goal is ONE system. Everything below is the consolidated, source-traced research foundation that the system will be designed and built from.

**Status:** `RESEARCH_COMPLETE · IMPLEMENTATION_NOT_AUTHORIZED`
**Retrieved:** 2026-09-11 (web) + live GitHub API data (2026-09-11)

---

## Knowledge Map

```
CORE (one system)
│
├── 01-foundations.md          What an agent system IS · core loop · taxonomy · the build decision
├── 02-models-economics.md     Model landscape · model routing · prompt caching · token economics · cost
├── 03-context-memory.md       Context engineering · 4-tier memory · compaction · memory files
├── 04-tools-protocols.md      Tool design (ACI) · MCP/A2A/AGENTS.md · skills · connectors
├── 05-orchestration-runtime.md Multi-agent patterns · frameworks · durable execution · sandboxes · infra
├── 06-evaluation-quality.md   Benchmarks & contamination · evals · observability · reliability patterns · prompt engineering
├── 07-security-compliance.md  Threat model · prompt injection · MCP security · EU AI Act · governance
├── 08-ux-product.md           Agent UX patterns · HITL/approvals · distribution · OSS reference landscape
├── 09-gaps-disconfirmation.md What we missed — ranked by decision relevance (blocking / material / non-material)
└── 10-operations-pathA.md     Path A playbook: operating the best existing agents for research & knowledge work
```

**Companion artifacts** (earlier passes, still valid core inputs):
- `/DEEP_RESEARCH_REPORT.md` — systems analysis (Claude Code · ChatGPT/Codex · Arena.ai), blueprint, security baseline
- `/BUGS_FIXES_CHALLENGES.md` — documented bugs, vendor postmortems, failure taxonomy
- `/docs/control-plane.json` — machine-readable mission/evidence/validation state

## Evidence-state legend (used throughout)

`ESTABLISHED_FACT` (official/primary) · `WELL_SUPPORTED` (multiple independent sources) · `REASONABLE_INFERENCE` (weaker synthesis, labeled) · `CONTESTED` (sources disagree; disagreement preserved) · `COMMUNITY_REPORT` (forum-level signal) · `UNKNOWN`

---

## Source Register (K-series)

Primary/official marked ★. All retrieved 2026-09-11 unless noted.

| ID | Source | Topic |
|---|---|---|
| K01 | [uvik.net — Agentic AI Frameworks 2026](https://uvik.net/blog/agentic-ai-frameworks/) | Framework comparison (15 frameworks, tiers) |
| K02 | [Langfuse — Comparing open-source agent frameworks](https://langfuse.com/blog/2025-03-19-ai-agent-comparison) | Framework comparison (13 frameworks) |
| K03 | [Arize — AI agent frameworks handbook](https://arize.com/guides/ai-agent-handbook/agent-frameworks/) | Framework taxonomy (SDK/runtime/harness/platform) |
| K04 | [MorphLLM — AI agent frameworks 2026](https://www.morphllm.com/ai-agent-framework) | Provider SDK vs independent framework split |
| K05 | [Kunal Ganglani — 4-tier agent memory](https://www.kunalganglani.com/blog/ai-agent-memory-state-management) | Memory tiers, "log is the agent", hot/warm/cold |
| K06 | [r/LocalLLaMA — memory system](https://www.reddit.com/r/LocalLLaMA/comments/1qrbs69/memory_system_for_ai_agents_that_actually/) | NOW.md/MEMORY.md pattern (community) |
| K07 | [Zylos — agent context compaction](https://zylos.ai/research/2026-04-21-agent-context-compaction-long-running-sessions/) | Compaction strategies, caching tension, artifact tracking gap |
| K08 | [AyAutomate — context engineering](https://www.ayautomate.com/blog/context-engineering) | Context rot vs collapse; memory hierarchy; tool scoping |
| K09 | [StartupHub — memory tools 2026](https://www.startuphub.ai/ai-news/insights/2026/ai-agent-memory-tools-2026) | Vector DB landscape (Pinecone, Qdrant, pgvector, MongoDB) |
| K10 | [NeuralCoreTech — MCP became the standard](https://neuralcoretech.com/model-context-protocol-mcp-2026-agentic-ai-standard/) | MCP adoption stats, governance, A2A relationship |
| K11 | [Zenity — MCP security](https://zenity.io/academy/model-context-protocol-explained) | MCP threat classes, Postmark supply-chain incident |
| K12 | [arXiv 2505.02279 — protocol survey](https://arxiv.org/html/2505.02279v1) | MCP/ACP/A2A/ANP survey, lifecycle threats |
| K13 | [NSA — MCP Security Design Considerations ★](https://www.nsa.gov/Portals/75/documents/Cybersecurity/CSI_MCP_SECURITY.pdf) | Official NSA guidance (May 2026): no RBAC/authz in spec, audit gaps |
| K14 | [arXiv 2603.22489 — MCP threat modeling](https://arxiv.org/html/2603.22489v1) | Tool poisoning; client defense variance 0–100% |
| K15 | [DecodeTheFuture — benchmarks 2026](https://decodethefuture.org/en/ai-agent-benchmarks-2026/) | GAIA/SWE/OSWorld/Tau²/WebArena/METR + contamination figures |
| K16 | [IoTDigitalTwinPLM — benchmark comparison](https://iotdigitaltwinplm.com/ai-agent-benchmarks-swe-bench-gaia-tau-bench-2026/) | Grading brittleness, pass^k vs pass^1 |
| K17 | [BenchmarkingAgents — benchmark table](https://benchmarkingagents.com/agent-benchmarks/) | Task counts, leak risk per benchmark |
| K18 | [arXiv 2605.20530 — AgentAtlas](https://arxiv.org/html/2605.20530v1) | Benchmark coverage audit rubric |
| K19 | [RapidClaw — benchmark hacking](https://rapidclaw.dev/blog/ai-agent-benchmarks-2026) | Reward-hacking ~100% (UCB RDI), METR 30%, env effects |
| K20 | [dev.to — agent observability stack](https://dev.to/chunxiaoxx/ai-agent-observability-in-2026-openai-agents-sdk-langsmith-and-opentelemetry-3ale) | SDK traces + LangSmith + OTel layering |
| K21 | [Twistag — OTel + Langfuse pattern](https://twistag.com/thinking/ai-agent-observability) | OTel GenAI semconv v1.41, six layers, content-capture privacy |
| K22 | [Laminar — observability platforms ranked](https://laminar.sh/article/2026-04-23-top-6-agent-observability-platforms) | Laminar/Langfuse/LangSmith/Phoenix/Braintrust/Weave |
| K23 | [QASkills — Langfuse guide](https://qaskills.sh/blog/langfuse-llm-observability-guide-2026) | Langfuse capabilities, OSS vs LangSmith |
| K24 | [OpenTelemetry blog — GenAI observability ★](https://opentelemetry.io/blog/2026/genai-observability/) | Real products emitting OTel (Copilot, Codex, Claude Code) |
| K25 | [FutureAGI — cost optimization](https://futureagi.com/blog/llm-cost-optimization-2025/) | 30-day wins; routing/caching/batching savings ranges |
| K26 | [MyEngineeringPath — cost pipeline](https://myengineeringpath.dev/genai-engineer/llm-cost-optimization/) | Routing 40–60% savings, caching 70–90%, combined 80–95% |
| K27 | [DataAIHub — cost guide](https://www.dataaihub.co/learn/cost-optimization) | Router + escalation + token budgets (code example) |
| K28 | [Zylos — token economics](https://zylos.ai/research/2026-02-19-ai-agent-cost-optimization-token-economics/) | Agent cost 3–10× chat; cascade routing 87% |
| K29 | [Wavect — token costs](https://wavect.io/blog/reduce-llm-token-costs-2026/) | RouteLLM numbers; priority order cache→batch→route |
| K30 | [SinghAjit — multi-agent swarms](https://singhajit.com/multi-agent-ai-swarms-system-design/) | 5 patterns; failure modes at handoffs |
| K31 | [DevelopersDigest — multi-agent TS](https://www.developersdigest.tech/blog/multi-agent-systems) | Swarm/supervisor/pipeline/debate patterns |
| K32 | [DigitalApplied — 5 patterns](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work) | Pattern×framework compatibility matrix |
| K33 | [Focused.io — supervisor vs swarm](https://focused.io/lab/multi-agent-orchestration-in-langgraph-supervisor-vs-swarm-tradeoffs-and-architecture) | Measured: routing 94% vs 91%, latency, swarm ping-pong |
| K34 | [DecodeTheFuture — multi-agent topologies](https://decodethefuture.org/en/multi-agent-systems-explained/) | Orchestrator-worker ≈70% of deployments |
| K35 | [Zylos — checkpointing & resumability](https://zylos.ai/research/2026-03-04-ai-agent-workflow-checkpointing-resumability/) | Checkpoint granularity, replay, idempotency, continue-as-new |
| K36 | [MatthewSWong — durable execution](https://www.matthewswong.com/en/blog/durable-execution-ai-agent-workflows/) | Temporal/Restate/DBOS/Inngest state models |
| K37 | [Zylos — durable execution patterns](https://zylos.ai/research/2026-02-17-durable-execution-ai-agents/) | Temporal $300M/$5B (Feb 2026), 9.1T executions; event sourcing |
| K38 | [Callsphere — Temporal for agents](https://callsphere.ai/blog/temporal-ai-agent-workflows-durable-execution-workflow-as-code/) | When to use durable execution |
| K39 | [Zylos — agent runtimes](https://zylos.ai/research/2026-04-24-durable-execution-agent-runtimes/) | LangGraph checkpoints, Dapr Agents, MS Durable Task |
| K40 | [ArtificialAnalysis — coding agents comparison](https://artificialanalysis.ai/agents/coding) | Category map of all coding agents |
| K41 | [Kunal Ganglani — OSS Claude Code alternatives](https://www.kunalganglani.com/blog/claude-code-alternatives-open-source) | Aider/OpenHands/Cline/Goose tested |
| K42 | [AIFoss — OSS coding agents state 2026](https://aifoss.dev/blog/open-source-coding-agents-state-2026/) | SWE-bench scores by harness; token efficiency |
| K43 | [Frontman — OSS tools table](https://frontman.sh/blog/best-open-source-ai-coding-tools-2026/) | Stars/licenses/status table |
| K44 | [Zylos — prompt engineering for agents](https://zylos.ai/research/2026-03-30-prompt-engineering-ai-agent-systems-instruction-hierarchies/) | System prompts as software; tool-description engineering |
| K45 | [BlckAlpaca — prompt engineering agents](https://blckalpaca.at/en/knowledge-base/ai-agents/prompt-engineering-for-agents) | tool_search accuracy gains; reasoning-model inversion |
| K46 | [AgentPatterns — ACI](https://agentpatterns.ai/tool-engineering/agent-computer-interface/) | HCI→ACI mapping; Composio 10× failure reduction; SWE-agent choices |
| K47 | [ApXML — tool selection prompts](https://apxml.com/courses/prompt-engineering-agentic-workflows/chapter-3-prompt-engineering-tool-use/prompting-agent-tool-selection-operation) | Tool name/description/schema conventions |
| K48 | [GetMaxim — practitioner prompt guide](https://www.getmaxim.ai/articles/a-practitioners-guide-to-prompt-engineering-in-2025/) | Structured outputs, guardrail blueprints |
| K49 | [EyrEact — EU AI Act & agents](https://eyreact.com/ai-agents-eu-ai-act/) | Provider/deployer/orchestrator roles, Art 5/50 timing |
| K50 | [Salt — EU AI Act compliance](https://salt.security/eu-ai-act-compliance) | Art 12 tamper-evident logs ≥6 months; fines €35M/7% |
| K51 | [EU AI Office — FAQ ★](https://ai-act-service-desk.ec.europa.eu/en/faq) | Enforcement timeline Aug 2, 2026 (official) |
| K52 | [Centurian — auditor checklist](https://centurian.ai/blog/eu-ai-act-compliance-2026) | What auditors ask for (Arts 9–15) |
| K53 | [Suntec — enterprise governance](https://www.suntecindia.com/blog/eu-ai-act-august-2026-enterprise-ai-agent-governance/) | Provider vs deployer accountability |
| K54 | [Beam — sandbox guide 2026](https://www.beam.cloud/blog/2026-sandbox-guide) | E2B/Modal/CodeSandbox/Daytona/Beam comparison |
| K55 | [VietAnh — agent sandboxes](https://www.vietanh.dev/blog/2026-02-02-agent-sandboxes) | gVisor vs Firecracker vs containers vs Wasm |
| K56 | [Spheron — sandbox GPU](https://www.spheron.network/blog/ai-agent-code-execution-sandbox-e2b-daytona-firecracker/) | Firecracker VMM ~50K LoC Rust; GPU passthrough via VFIO |
| K57 | [LogRocket — sandbox platforms measured](https://blog.logrocket.com/comparing-ai-agent-sandbox-platforms-e2b-modal-daytona-and-more/) | Measured cold starts (717ms E2B etc.) |
| K58 | [Grigio — sandbox tech comparison](https://grigio.org/ai-agent-sandbox-technologies-a-complete-2026-comparison/) | Memory overhead per isolation tech |
| K59 | [Zylos — agentic UX](https://zylos.ai/research/2026-05-28-agentic-ux-frontend-design-patterns-ai-agents/) | Approval gates, progressive delegation, activity panel, AG-UI |
| K60 | [Agentic-Patterns — HITL framework](https://www.agentic-patterns.com/patterns/human-in-loop-approval-framework/) | Risk classification, multi-channel approvals, timeout deny |
| K61 | [Heym — agentic design patterns](https://heym.run/blog/agentic-design-patterns) | 7 patterns; symptom→pattern mapping |
| K62 | [Agentic-Design — ambient agents](https://agentic-design.ai/patterns/ui-ux-patterns/ambient-agent-patterns) | Notify/Question/Review; event streams |
| K63 | [Hatchworks — agent UX patterns](https://hatchworks.com/blog/ai-agents/agent-ux-patterns/) | Build order: controls→receipts→logs→approvals→memory→eval |
| K64 | [GroovyWeb — LLM production integration](https://www.groovyweb.co/blog/llm-integration-rate-limiting-caching-fallbacks-2026/) | P50/P99 1:8–1:15; semantic cache 40–60% hit rate |
| K65 | [ValueStreamAI — error handling 2026](https://valuestreamai.com/blog/ai-error-handling-patterns-2026) | Error stats: 60% of LLM errors are 429; budget guardrails −40% |
| K66 | [LearnWithParam — retry patterns](https://www.learnwithparam.com/blog/retry-patterns-llm-api-errors-production) | Retryable vs not; jitter math |
| K67 | [Fast.io — retry guide](https://fast.io/resources/ai-agent-retry-patterns/) | Backoff parameters; monitoring thresholds |
| GH-OSS | Live GitHub API, 2026-09-11 (stars/issues): OpenHands 87,271★/MIT · Cline 67,801★/Apache-2.0 · Goose 54,100★/Apache-2.0 · Aider 48,889★/Apache-2.0 · LangGraph 41,413★/MIT · openai-agents-python 29,337★/MIT · qwen-code 27,758★/Apache-2.0 · pydantic-ai 19,856★/MIT | Primary |
| K68 | [APIScout — Claude extended thinking 2026](https://apiscout.dev/guides/claude-api-extended-thinking-mode-2026) | Thinking budgets, pricing, adaptive thinking |
| K69 | [Chiraghasija — reasoning models & test-time compute](https://chiraghasija.cc/posts/reasoning-models-test-time-compute-2026/) | Thinking-token economics (7.3× example), Claude vs o-series |
| K70 | [TokenFence — extended thinking cost explosion](https://tokenfence.dev/blog/extended-thinking-cost-explosion-claude-o3-budget-controls-2026) | Recursive-agent runaway ($40–100), tiered enforcement |
| K71 | [Ian Paterson — 15 models on 38 real tasks](https://ianlpaterson.com/blog/llm-benchmark-2026-38-actual-tasks-15-models-for-2-29/) | Real-task routing tiers, escalation discipline |
| K72 | [AppSecSanta — Cerbos review](https://appsecsanta.com/cerbos) | Cerbos: sub-1ms PDP for agents/MCP |
| K73 | [Zop.dev — OPA vs Cedar at scale](https://zop.dev/resources/blogs/opa-vs-cedar-when-policy-as-code-hits-500-accounts) | Cedar typed-model latency under concurrency |
| K74 | [Chatforest — authorization policy MCP servers](https://chatforest.com/reviews/authorization-policy-engine-mcp-servers/) | Cedar dominance in MCP enforcement ecosystem |
| K75 | [Cerbos — agentic authorization](https://www.cerbos.dev/features-benefits-and-use-cases/agentic-authorization) | Deterministic eval, kill switch, policy lifecycle |
| V1 | [SWE-bench official leaderboard](https://www.swebench.com/) ★ | Primary verification (fetched 2026-09-11) |
| V2 | [Terminal-Bench official leaderboard](https://www.tbench.ai/) ★ | Primary verification (fetched 2026-09-11) |
| K76 | [FutureAGI — RAG architecture 2026](https://futureagi.com/blog/rag-architecture-llm-2025/) | 2026 RAG baseline, latency budgets, complexity ladder |
| K77 | [AWS — RAG hallucination detection](https://aws.amazon.com/blogs/machine-learning/reducing-hallucinations-in-large-language-models-with-custom-intervention-using-amazon-bedrock-agents/) | RAGAS-based hallucination detector + HITL remediation |
| K78 | [Inexture — advanced RAG](https://www.inexture.ai/blog/advanced-rag-techniques-for-reliable-ai-architecture/) | Hierarchical reranking; 6–8 chunks max |
| K79 | [CallMissed — RAG best practices 2026](https://www.callmissed.com/en/blog/rag-best-practices-2026) | Hybrid always; rerank = highest ROI; long-context-vs-RAG rule; eval |
| K80 | [Starmorph — RAG techniques compared](https://blog.starmorph.com/blog/rag-techniques-compared-best-practices-guide) | Chunking table, +25–40% precision, decision tree, over-engineering warning |
| K81 | [Scadea — RAG evaluation metrics](https://scadea.com/evaluating-rag-quality-hallucination-detection-and-answer-accuracy-metrics/) | Faithfulness etc.; framework comparison table |
| K82 | [ResearchGate — RAGAs paper](https://www.researchgate.net/publication/393020278_RAGAs_Automated_Evaluation_of_Retrieval_Augmented_Generation) | Recall × granularity govern hallucination; metric definitions |

**Carry-over registers:** DEEP_RESEARCH_REPORT.md §16 (S1–S26) · BUGS_FIXES_CHALLENGES.md §12 (B1–B22).

---

## Core Architecture Decisions (locked by evidence, pending user authorization to build)

| # | Decision | Evidence basis | Status |
|---|---|---|---|
| D1 | One system = **harness on frontier APIs**, never a trained model | Report 1 §14.1 | LOCKED (research) |
| D2 | Build order: **eval → sandbox → loop → context → product** | Report 1 §14.2 | LOCKED (research) |
| D3 | **Containment-first security** (OS-enforced sandbox + deterministic action policy) | Report 1 §14.5; ch. 07 | LOCKED (research) |
| D4 | **Eval-driven development**; own hidden tests over leaderboards | Report 1 §14.4; ch. 06 | LOCKED (research) |
| D5 | Session state & metering are **tested subsystems from day one** | Bugs report §8–§9; ch. 05 | LOCKED (research) |
| D6 | Windows-first distribution as signature surface (§32) | Report 1 §14.6; ch. 08 | PROPOSED (user-dependent) |
