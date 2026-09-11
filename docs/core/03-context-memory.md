# 03 — CONTEXT & MEMORY: The Window Is a Budget, Not a Bucket

## 3.1 Core facts

- LLMs remember **nothing between API calls**; memory is a layer we build explicitly (K05).
- Context is the **dominant cost and quality variable**: turns slow from ~1.1 s (fresh) to ~5 s (500K tokens) in Claude Code (B8); context bugs masquerade as model regressions (bugs report §4.1 — the April 2026 postmortem).
- Two named failure modes (K08): **context rot** (quality degrades as the window grows) and **context collapse** (repeated rewriting erodes detail).

## 3.2 The four memory tiers

`WELL_SUPPORTED` (K05, K09):

| Tier | Storage | Latency | Use |
|---|---|---|---|
| In-context (working) | context window | ~0 | system prompt, current task, tool results |
| External KV (warm) | Redis/Dragonfly/DB | ~ms | session state, conversation buffer, pinned facts |
| Episodic log (cold, structured) | SQL/Postgres/SQLite | ~ms | "what happened when", entity tracking, audit |
| Semantic vector (cold, fuzzy) | Pinecone/Qdrant/pgvector/Chroma | 50–200 ms | "find me similar", cross-session recall |

**Choosing the wrong tier is the most common architectural mistake in agent projects** (K05). In-context for <2K tokens needed every turn; KV for hot state; vector only for fuzzy recall. Vector-only memory "kept missing obvious connections" — structured + semantic combined is the working pattern (K06).

## 3.3 "The log is the agent"

The append-only message log **is** the agent's state: persisting it enables crash recovery, resume, and debugging (K05). This is the foundation of session/resume as a tested subsystem (bugs report §9 C3, Decision D5). Everything durable-execution (ch. 05 §5.4) hangs off this.

## 3.4 The write/select/compress/isolate framework

`WELL_SUPPORTED` (K45, K44, K07):

1. **Write** — persist info *outside* the window: scratchpads, todo/state files, memory store. The single most reliable upgrade for long-running agents: **let the agent write durable notes** (K08). External memory must be **written at decision time**, not extracted retroactively at compaction — retroactive extraction is fragile (K07).
2. **Select** — bring only the right tokens in per step: RAG, semantic tool filtering, sub-agent dispatch.
3. **Compress** — summarize old turns into a compressed state; replace raw history (Anthropic productized automatic compaction).
4. **Isolate** — split context across subagents and schema fields.

## 3.5 Compaction — techniques and tradeoffs

`WELL_SUPPORTED` (K07, K08, K05):

| Strategy | Mechanism | Notes |
|---|---|---|
| Truncation | drop oldest messages | simple, lossy |
| Summarization | LLM condenses old turns | token cost + latency; quality must be **monitored as a rolling metric** (K07) |
| Sliding window + pinned | last N + pinned important messages | best balance for most cases (K05) |
| Anchored iterative | persistent section templates | converging field pattern (K07) |
| External offload | MemGPT/Letta OS-virtual-memory analogy | tool calls move memory in/out |
| Retrieval-augmented episodic | embed turns, retrieve top-K on demand | cross-session continuity |

**Practical production settings** (K07, K05): compact at **≈75% threshold**; after every 10–20 turns run a summarization pass (cuts hot-tier tokens 60–70%); compaction **invalidates prompt-cache prefixes** (ch. 02 §2.4) — design them together; **artifact tracking (which files were modified) is uniformly weak across all production methods (2.19–2.45/5)** — so make file-change tracking a first-class harness feature, not a compaction afterthought.

## 3.6 Memory files pattern (adopted by all majors)

`WELL_SUPPORTED` (S1, K06): CLAUDE.md / AGENTS.md = always-on project context; a NOW.md-style **state file that always survives compaction** (200-line lifeline); MEMORY.md curated by the agent for long-term facts; git itself as history/knowledge graph (`git log`, `git grep`) is a viable low-tech memory store (K06).

> **Rule R4:** the harness maintains `state.md` at each milestone (goal, decisions, next step, known issues) — written by the agent, never compacted away, versioned in git. This is our defense against context rot and against resume regressions (bugs report §4.4).

## 3.7 Tool scoping as context engineering

Expose only phase-relevant tools (K08); 31 always-on tools ≈ 4,500 tokens/query (K44); production pattern: **3–7 always-loaded tools + dynamic discovery** (K45, ch. 04). Skills load descriptions at start, full content on invocation (S1) — same principle applied to knowledge.

## 3.8 RAG & retrieval engineering (M4 — closed 2026-09-11; scope: research & knowledge work)

`WELL_SUPPORTED` (K76–K80):

**The 2026 production baseline pipeline** (K76, K79):

```
query → [query rewrite, optional] → hybrid retrieval (BM25 + dense, RRF fusion, top-50 each)
      → cross-encoder reranker → top 5–8 chunks → context builder (metadata + citations)
      → LLM with structured output (citations required)
```

**Component rules:**

| Stage | Evidence-based choice | Notes |
|---|---|---|
| Chunking | **recursive 300–500 tokens, 10–15% overlap** as default; document-aware (markdown headers/functions) for structured docs; semantic chunking only if quality insufficient (~70% lift but costly) (K80) | "Chunking is where most quality is won or lost" (K79) |
| Retrieval | **hybrid always** — dense is weak on exact names/SKUs/error codes; BM25 is the inverse (K79) | hybrid+rerank: +25–40% precision over naive (K80) |
| Reranking | **highest-ROI step**; cross-encoder (Cohere/Voyage managed; ColBERT self-hosted) (K76, K79) | reranking dramatically reordering results = initial retrieval noisy (K80) |
| Query handling | rewrite/expand (HyDE, step-back, decomposition) only when intent ambiguous; 1 extra LLM call + 200–400 ms (K76) | multi-query + RRF for hard queries |
| Context size | **6–8 chunks max**; larger increases hallucination risk (K78) | "RAG retrieves, long context refines" — 5–20 chunks in a 16–64K prompt (K79) |
| Complexity ladder | classic → hybrid+rerank → query rewriting → multi-hop → agentic → graph RAG; **escalate only when metrics prove the need** (K80) | most common mistake is over-engineering (K80) |

**Latency budget (production chat RAG)** (K76): rewrite 200–400 ms · hybrid retrieval 50–150 ms · rerank 50–150 ms · first token 200–500 ms · full generation 500–1500 ms · groundedness eval 1–2 s out-of-band.

**Evaluation — the part most teams skip** (K79): retrieval quality = recall@k / MRR / nDCG against a ~100-query golden set with ground-truth chunks; generation = **faithfulness (most critical: decompose answer into atomic claims, verify each against retrieved context)** + answer relevance + context precision/recall; citation faithfulness explicitly penalizes hallucinated citations (K79). Frameworks: RAGAS (reference-free LLM metrics), DeepEval (pytest CI), TruLens, Arize Phoenix (OTel) (K81, K82). Hallucination is governed jointly by **retrieval recall and chunk granularity** (K82).

**Two standing warnings** (K76, r/LangChain synthesis):
1. **Agentic RAG creates an audit problem** — once retrieval is multi-step and agent-directed, you must trace exactly which chunks entered the prompt; provenance is a design feature, not an afterthought (feeds ch. 06 telemetry + Art. 12).
2. Cascade failures: a bad query rewrite tanks everything downstream — keep rewrites cached and cheap (K76).

> **Rule R16 (operations, Path A):** any research deliverable produced through retrieval must ship with **citations traced to retrieved sources**; uncited claims are treated as `UNKNOWN`/`SPECULATION` per the evidence-state discipline (00-INDEX legend). This is the same provenance standard the mission framework (§11) applies to the corpus itself.
