# DEEP RESEARCH REPORT
## Claude Code · ChatGPT/Codex · Arena.ai — and how to build the best such system

**Prepared:** 2026-09-11 · **Mode:** Deep research + research architecture + security analysis (no code changes authorized)
**Artifact:** `/DEEP_RESEARCH_REPORT.md` + machine-readable state in `/docs/control-plane.json`

---

## 1. Executive Summary

1. **Claude Code, ChatGPT/Codex, and Arena.ai Agent Mode are three different answers to the same architecture.** All three are an **LLM-driven agent loop**: a harness repeatedly asks a frontier model "what next?", executes the tool calls the model emits (shell, file edit, web), appends the real observed result to context, and repeats until the model declares completion. The differences are in *where the loop runs* (terminal vs. cloud vs. browser sandbox), *what context it carries* (CLAUDE.md / AGENTS.md / session memory), *how permissions are enforced* (approval gates vs. OS-level sandboxing), and *what the product is for* (repo-native engineering vs. general-purpose assistant with an agent attached vs. model evaluation).
2. **Claude Code** (terminal-first, repo-native) is the deepest *harness*: agent loop, subagents, skills, MCP, hooks, checkpoints, and an Agent SDK for building your own. **ChatGPT** is the broadest *product surface* (chat, memory, voice, image, search, canvas), with **Codex** as its coding agent — winning on cloud/background tasks, computer use, and UX polish. **Arena.ai** is the *measurement layer*: 2+ years of crowdsourced model Elo, and since June 2026 an Agent Mode that runs agents with real tools (search, image gen, sandboxed bash, GitHub PRs) and ranks them on real-world task outcomes.
3. **"Making the best" is mostly engineering, not model choice.** The strongest evidence — Anthropic's own agent-engineering guidance, NVIDIA/OWASP security research, and the 2026 wave of agent exploits — converges on four levers, in order: **(a) eval-driven development** (your own hidden tests beat any leaderboard), **(b) containment-first security** (OS-enforced sandbox + deterministic action-level policy; prompt injection cannot currently be fully prevented, only bounded), **(c) context engineering** (context is a budget; subagents/skills/compaction discipline it), **(d) model selection with fallbacks**, since model rankings churn monthly.
4. **Recommendation:** Do not try to build a frontier model. Build the **harness** on top of frontier APIs (start with Claude Sonnet-class API + a sandbox + a tool loop + evals ≈ a weekend MVP), then layer skills, subagents, MCP, and permissions as needs are demonstrated — exactly the order the incumbents themselves evolved.
5. **Evidence honesty:** benchmark numbers in this space conflict across aggregator sites (same model, 5–7 pt spreads). Those numbers are marked `CONTESTED` below and should be treated as directional only. Structural facts come from official documentation and are marked `ESTABLISHED_FACT`.

---

## 2. Objective

Produce accurate, decision-useful understanding of **Claude Code**, **ChatGPT (incl. Codex)**, and **Arena.ai**, and derive a **reliable blueprint for building the best such agent system** — suitable for the owner of this (currently empty) `Agent` repository.

## 3. Decision

| Field | Value |
|---|---|
| **Decision under study** | Whether/how the project owner should build their own agent system, on what foundation, and in what order |
| **Decision-maker** | Repo owner (user) |
| **Constraints** | Empty starter repo; no stated budget or team; likely Windows environment (§32 of brief); frontier training is out of scope for any individual builder |
| **Success criteria** | A correct, source-traced description of the three systems + an actionable, correctly-ordered build path that avoids known failure modes |
| **Acceptable uncertainty** | Exact benchmark scores, vendor-internal architecture details, Arena's unpublished roadmap |
| **Unacceptable uncertainty** | What the core loop *is*; where the security boundaries must sit; which components are worth building vs. buying |
| **Consequence of being wrong** | Building the wrong component (e.g., a model) or an insecure harness (prompt-injection RCE) wastes months and exposes users |

**Authorization status:** `NOT_AUTHORIZED` for code changes. Only research artifacts (this report + control-plane JSON) were added to the repo. Nothing else was modified.

---

## 4. Scope

**In scope:** architecture and mechanism of the three systems; their differentiation; the shared engineering core; security/failure modes; the 2026 model landscape (as background); a build blueprint, sequencing, and validation plan.

**Out of scope:** legal/export analysis; detailed API pricing tables (volatile); exhaustive framework survey (OpenHands, Aider, Goose, Cline, etc.); model training.

---

## 5. Research Architecture

Six adaptive passes were executed (sources listed in §16):

| Pass | Purpose | What was done |
|---|---|---|
| 1 — Establish | Official/primary evidence | Anthropic Claude Code docs; Arena.ai official blog, help center, launch post; Wikipedia (Arena); NVIDIA security guidance |
| 2 — Fill gaps | Secondary technical analyses | Architecture deep-dives (Claude Code harness, agent-loop tutorials), product comparisons (Codex vs Claude Code, feature matrices) |
| 3 — Independent verification | Cross-source confirmation | Multiple independent aggregators/analysts for benchmarks and feature claims; the author also holds **direct primary evidence**: this report was produced by an Arena Agent Mode session running the very tooling analyzed |
| 4 — Attack | Failure & contradiction search | Prompt-injection research (AI Now RCE PoC, Pillar Security sandbox escapes, Cursor CVE, HalluSquatting), negative results ("when NOT to build agents") |
| 5 — Reconcile | Disagreement resolution | Contradiction register in §8; conflicting claims preserved rather than averaged |
| 6 — Decision test | Residual-uncertainty check | Remaining uncertainty (exact scores, vendor internals) does **not** change the recommendation (build harness, not model; eval + sandbox first). Research stopped here — per the expected-decision-value rule. |

---

## 6. Key Findings

### 6.1 Claude Code — the deepest open harness

**What it is.** Anthropic's repo-native coding agent: terminal-first, also VS Code/JetBrains extensions, desktop, web (claude.ai/code), iOS; included with Claude Pro/Max subscriptions (`ESTABLISHED_FACT`, [S1](https://code.claude.com/docs/en/features-overview), [S4](https://www.askglitch.com/blog/claude-code-vs-codex)).

**How it works — the agent loop.** A cycle: assemble context → model emits tool calls → harness executes (built-in tools or MCP servers) → results appended → repeat until the model finishes. The orchestration code does not decide *what* to do; the model does. Planning is emergent, not architectural — each turn is a fresh decision informed by observed results ([S2](https://callsphere.ai/blog/inside-claude-code-s-architecture-how-the-agent-loop-works)).

**Context is a budget, not a bucket** (up to 1M tokens in 2026): each turn layers system prompt + tool definitions + `CLAUDE.md` + auto-memory + loaded skill descriptions + history + tool results. Long sessions use **compaction**; parallel exploration uses **subagents** (fresh isolated context windows returning only summaries) ([S2](https://callsphere.ai/blog/inside-claude-code-s-architecture-how-the-agent-loop-works), [S5](https://www.penligent.ai/hackinglabs/inside-claude-code-the-architecture-behind-tools-memory-hooks-and-mcp/)).

**Five layers** (synthesis consistent across official docs and [S5](https://www.penligent.ai/hackinglabs/inside-claude-code-the-architecture-behind-tools-memory-hooks-and-mcp/)):

| Layer | Controls | Key elements |
|---|---|---|
| Agent loop | what happens next | tool calls, retries, worktrees, checkpoints |
| Context & memory | what the model knows | CLAUDE.md, auto memory, skills, MCP tool names, history |
| Execution surface | blast radius | Read/Edit/Bash/WebFetch; **sandboxed Bash** with OS-enforced filesystem + network-proxy boundaries |
| Governance | what is permitted | permission modes (allow/ask/deny), hooks, trust verification, managed settings |
| Extensibility | how capability arrives | **Skills** (SKILL.md folders, loaded on demand), **MCP** servers, **plugins**, **Agent SDK** |

**Extension mechanisms** ([S1](https://code.claude.com/docs/en/features-overview), [S3](https://colinmcnamara.com/blog/understanding-skills-agents-and-mcp-in-claude-code)): `CLAUDE.md` = always-on rules; **Skill** = instructions/knowledge/workflow loaded on invocation; **Subagent** = isolated parallel context; **Hook** = deterministic script fired on events (e.g., lint after every edit); **MCP** = external tools via a standard protocol (Anthropic, Nov 2024); **Agent SDK** = export the same loop to your own application. Skills and MCP compose: *MCP gives the ability to call a system; the skill teaches how and when to use it well* ([S1](https://code.claude.com/docs/en/features-overview)).

**What it is best at** (consistent across independent comparisons): planning, architecture, long-horizon reasoning over large existing codebases ([S6](https://explainx.ai/blog/codex-vs-claude-code-ai-agent-comparison-2026), [S4](https://www.askglitch.com/blog/claude-code-vs-codex)). **Weaknesses:** no first-class browser/computer-use (terminal-native), less polished UI, more restrictive consumer rate limits, weaker at background/cloud tasks ([S6](https://explainx.ai/blog/codex-vs-claude-code-ai-agent-comparison-2026)).

### 6.2 ChatGPT / Codex — the broadest product surface

**ChatGPT** is the general assistant: automatic memory, Bing web browsing, voice, image generation, Canvas, GPTs; free / Go / Plus ($20) / Pro tiers ([S7](https://www.nxcode.io/resources/news/claude-vs-chatgpt-2026-which-ai-to-use), [S4](https://www.askglitch.com/blog/claude-code-vs-codex)).

**Codex** is OpenAI's coding agent — CLI (open-source), IDE extension, desktop app, **cloud tasks that run in parallel/background**, GitHub issue→PR flow, **browser and computer use**, mobile remote control; `AGENTS.md`, skills, MCP. OpenAI reported **4M weekly users** as of June 2026 ([S6](https://explainx.ai/blog/codex-vs-claude-code-ai-agent-comparison-2026), [S4](https://www.askglitch.com/blog/claude-code-vs-codex)). It leads **Terminal-Bench 2.0** (Codex CLI + GPT-5.x: 77.3%, Feb 2026) and **OSWorld computer-use** (GPT-5.4: 75%) ([S15](https://smartscope.blog/en/generative-ai/chatgpt/llm-coding-benchmark-comparison-2026/), [S18](https://iternal.ai/llm-selection-guide)).

**Positioning:** Codex wins on execution speed, UI polish, cloud/background delegation, and "feeling of agency"; Claude Code wins on planning depth and large-codebase reasoning. The developer consensus reported across 2026 comparisons: serious users subscribe to both and chain them ([S6](https://explainx.ai/blog/codex-vs-claude-code-ai-agent-comparison-2026), [S4](https://www.askglitch.com/blog/claude-code-vs-codex)).

### 6.3 Arena.ai — the measurement layer, now with agents

**Lineage.** Arena (formerly LMArena / Chatbot Arena) launched April 2023 from UC Berkeley (Chiang, Angelopoulos, Stoica): anonymous head-to-head model battles feeding a crowdsourced Elo leaderboard ([S9](https://en.wikipedia.org/wiki/LMArena)).

**Agent Mode** launched **June 4, 2026** ([S10](https://x.com/arena/status/2062565126600114484)): an agent loop with **web search, image generation, file tools, and sandboxed bash**, running frontier models (GPT-5.5, Claude Opus 4.7, Gemini 3.1 Pro + open models) on real multi-step tasks — "build a website, debug code, do deep research" in one prompt ([S11](https://arena.ai/blog/agent-mode), [S12](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode)). GitHub integration: the agent works in a **copy of your repo, commits to a working branch, and opens a pull request** with a diff view; session push rights end when the PR is merged/closed ([S12](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode)).

**Agent Arena** — Arena's methodological contribution: instead of static benchmarks, it derives leaderboards from **causal evaluation of millions of in-the-wild agent sessions** doing real work. One 7-day slice: **160,480 tasks** — code writing 17.5%, research/lookup 10.8%, planning/brainstorming 10.6%, multimodal 10.2%, documents 9.1%, debugging 8.9% ([S13](https://arena.ai/blog/agent-arena-methodology)).

**Direct primary observation** (this report was produced inside Arena Agent Mode): sessions run in a cloud sandbox tied to a git branch; tools include shell, file read/write/edit, web search/fetch, image generation, speech, an ask-the-user dialog, and live previews of running dev servers proxied to the user's browser; work is auto-saved per turn. This is direct evidence of the platform's tool surface — though its internal architecture (isolation tech, model routing, evaluation internals) is **not publicly documented** (`UNKNOWN`).

### 6.4 The common core — anatomy of every modern coding agent

All three systems are the same skeleton ([S2](https://callsphere.ai/blog/inside-claude-code-s-architecture-how-the-agent-loop-works), [S14](https://www.decodingai.com/p/building-a-coding-agent-from-scratch-system-design)):

```
User request ─▶ [Context assembly] ─▶ Model ─▶ tool call(s) ─▶ [Permission gate] ─▶ [Sandbox] ─▶ observation ─▶ back to context
                                              (reason → act → observe, until the model stops calling tools)
```

Every serious implementation adds, in roughly this order: **tools** (read/edit/shell/web) → **sandbox** → **permission gates** → **memory files** (CLAUDE.md/AGENTS.md) → **context discipline** (subagents, compaction) → **skills** (on-demand procedural knowledge) → **connectors** (MCP) → **hooks** (deterministic policy) → **evals + telemetry**. That ordering is itself a finding: it is the path the incumbents followed, and it is the correct build order for a new entrant (`REASONABLE_INFERENCE` from [S1](https://code.claude.com/docs/en/features-overview), [S14](https://www.decodingai.com/p/building-a-coding-agent-from-scratch-system-design), [S16](https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/)).

### 6.5 What "best" means — the evidence

**6.5.1 Simplicity is a feature, not a compromise.** Anthropic's agent-infrastructure guidance (Dec 2024, still the industry reference in 2026): find the simplest pattern that passes evaluation; most production systems need a **workflow**, not an autonomous agent; use an agent only where the path can't be hardcoded **and** progress is verifiable (tests, environment state). Reserve autonomy for verifiable-feedback tasks ([S16](https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/), [S17](https://patmcguinness.substack.com/p/design-patterns-for-effective-ai)).

**6.5.2 Security is the #1 differentiator of a *trustworthy* best-in-class system.** The 2026 evidence is unambiguous:

- NVIDIA's AI Red Team names **indirect prompt injection as the primary threat** to coding agents; recommends OS-level sandbox controls (block egress to unknown destinations, block writes outside workspace, block writes to agent config), allow-once-per-action approvals, and credential-broker secret injection ([S19](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/)).
- **Real RCE, out of the box:** AI Now's "Friendly Fire" PoC achieved remote code execution with stock Claude Code and Codex just by having the agent *review* a third-party library seeded with prompt injections — no plugins, hooks, or MCP required ([S23](https://ainowinstitute.org/publications/friendly-fire-exploit-brief)).
- **Sandbox escapes are a live class of bug:** Cursor CVE-2026-50548 (write outside workspace → RCE, patched in Cursor 3.0); Pillar Security's July 2026 "Week of Sandbox Escapes" found boundary bypasses across Cursor, Codex, Gemini CLI, and Antigravity — often by making the sandbox **write files that trusted host-side processes later load or execute** ([S22](https://www.developersdigest.tech/blog/securing-ai-coding-agents)).
- **Supply chain:** "HalluSquatting" (July 2026) — hallucinated package/skill names become promptware delivery paths ([S22](https://www.developersdigest.tech/blog/securing-ai-coding-agents)).
- Consensus defense posture (OWASP-aligned): **containment, not detection** — injection can't be fully prevented, so cap blast radius with OS-enforced sandboxes + domain allowlists + deterministic action-level policy + approval gates on anything leaving the boundary ([S22](https://www.developersdigest.tech/blog/securing-ai-coding-agents), [S24](https://www.endorlabs.com/learn/prompt-injection-against-coding-agents-the-attack-surface-nobody-owns), [S20](https://northflank.com/blog/how-to-sandbox-ai-agents)).
- Isolation tiers for untrusted execution: hardened containers < gVisor < **Firecracker/Kata microVMs** (hardware boundary, ~125–200ms boot) ([S20](https://northflank.com/blog/how-to-sandbox-ai-agents)).

**6.5.3 Model landscape (background for "best").** As of mid-2026, secondary aggregators agree on direction but not numbers: Claude's Opus line leads coding Elo and SWE-bench-class results; GPT-5.5/Codex leads terminal/computer-use benchmarks; Gemini 3.x is strong on context/multimodal/value; open-weight models (MiniMax, GLM, Qwen, DeepSeek) are within a few points of frontier at far lower cost ([S15](https://smartscope.blog/en/generative-ai/chatgpt/llm-coding-benchmark-comparison-2026/), [S18](https://iternal.ai/llm-selection-guide), [S25](https://ofox.ai/blog/llm-leaderboard-best-ai-models-ranked-2026/), [S26](https://localaimaster.com/blog/lmarena-chatbot-arena-leaderboard)). The landscape churns monthly — hence the standing rule: **evaluate on your own tasks; treat any leaderboard as a screening tool, not a verdict** (consistent with [S13](https://arena.ai/blog/agent-arena-methodology)'s own thesis).

**6.5.4 Product lessons.** Independent 2026 comparisons identify what users actually feel as "best": Codex's polish, cloud tasks, and phone remote-control; Claude Code's depth, scripting, and automation surfaces (SDK, hooks, GitHub Actions) ([S4](https://www.askglitch.com/blog/claude-code-vs-codex), [S6](https://explainx.ai/blog/codex-vs-claude-code-ai-agent-comparison-2026)). The durable insight: **winners pair a tight core loop with one or two signature surfaces, not feature parity** (`REASONABLE_INFERENCE`).

---

## 7. Evidence Quality

| Source class | Quality | Used for |
|---|---|---|
| Official docs/blogs (Anthropic, Arena.ai, NVIDIA, OpenAI-reported) | High — primary | Architecture, features, launch facts, security guidance |
| Independent technical deep-dives (harness analyses, tutorial series) | Medium-high | Mechanism, build patterns |
| Independent product comparisons (4+ 2026 sources, mutually consistent) | Medium | Differentiation, UX |
| Benchmark aggregator sites | **Low-medium** — conflicts observed | Model landscape (directional only) |
| Security research (AI Now, Pillar via secondary, CVE reports) | High for threat claims | Failure modes, defenses |
| Direct observation of Arena Agent Mode (this session) | Primary | Tool surface, workflow |

**Provenance note:** all structural claims above trace to sources listed in §16 with retrieval date 2026-09-11. Where sources conflicted, conflicts are preserved (§8), not averaged.

## 8. Contradictions

| # | Conflict | Resolution |
|---|---|---|
| C1 | SWE-bench scores for the same model differ 5–7 pts across aggregators (e.g., Opus 4.8: 82.0% vs 88.6%; "Fable 5": 95% with conflicting withdrawal/restoration stories) | Unresolved. Treat all aggregator numbers as `CONTESTED`; they are secondary, unverifiable against primary benchmark repos here. Recommendation unchanged. |
| C2 | "Claude Code has no browser use" vs. "preview/browser verification in Desktop and web workflows" | Likely definitional (built-in computer-use vs. preview verification). Marked `UNKNOWN`. |
| C3 | "ChatGPT is better/worse than Claude" | Resolution is task-dependent and consistent across sources: Claude for planning/large codebases; ChatGPT/Codex for speed, computer use, cloud tasks, multimodal. |
| C4 | Consumer pricing tiers beyond $20/mo ($100/200 tiers) vary by source | Noted as approximate; irrelevant to core decision. |
| C5 | Whether frontier benchmarks translate to real task outcomes | Arena's causal-evaluation methodology exists precisely because they don't always; aligns with eval-your-own-tasks recommendation ([S13](https://arena.ai/blog/agent-arena-methodology)). |

## 9. Uncertainties

| Uncertainty | Class | Impact on decision |
|---|---|---|
| Exact benchmark/leaderboard values | **Non-material** | Direction is consistent across sources |
| Arena Agent Mode internals (isolation tech, routing, eval pipeline) | **Material** (for replicating Arena specifically) | Does not change "build harness" recommendation; flagged in blueprint as a design choice |
| Rate of model release/churn | **Material** (for vendor lock-in) | Mitigate with provider-agnostic harness + fallbacks |
| User's budget, team, and target audience for their own build | **Blocking** for final product scoping | Report provides three conditional build paths (§14.3); user decision needed before implementation |
| Vendor security posture changes (new CVEs monthly) | **Material** | Mitigate with update discipline + re-evaluation trigger (§15.2) |

## 10. Failure Modes

**Agent-loop failures:** divergence from task; context bloat → compaction loss; premature stopping; wrong tool/wrong arguments; infinite loops without budgets; retry storms; silent state corruption.

**Security failures (documented in the wild, 2026):** prompt-injection RCE via reviewed code ([S23](https://ainowinstitute.org/publications/friendly-fire-exploit-brief)); sandbox escape via path/`working_directory` abuse (CVE-2026-50548); host-side handoff attacks (sandbox writes → trusted host process loads → RCE) ([S22](https://www.developersdigest.tech/blog/securing-ai-coding-agents)); supply-chain poisoning via hallucinated names; secret exfiltration through unfiltered egress; context poisoning (RAG/history tampering) ([S20](https://northflank.com/blog/how-to-sandbox-ai-agents)).

**Decision-layer failure (the subtle one):** a system can be technically correct while producing a wrong decision — e.g., an agent that "successfully" completes a task against a stale or wrong assumption. Countermeasure: verify outcomes, not just tool success; compare against baseline; require humans at consequential checkpoints.

## 11. Risks

| Risk | Likelihood | Impact | Notes |
|---|---|---|---|
| Prompt injection / RCE in an agent product | High (demonstrated) | Critical | Containment-first design is mandatory, not optional |
| Cost blowup (subagent token multiplication, loops) | High | High | Budgets, stop conditions, token caps per task |
| Model/vendor churn invalidating tuning | High (monthly releases) | Medium | Provider-agnostic harness, eval suite as the moat |
| Overbuilding before demand exists | High (classic) | Medium | Workflow-first; ship the MVP harness |
| Unverified benchmark-driven decisions | Medium | Medium | Own-task eval suite (§14.4) |
| Unverified export/legal claims in aggregator blogs (e.g., "Fable 5 export controls") | Unknown | Unknown | Not relied upon anywhere in this report |

## 12. Gaps

1. No public architecture documentation for Arena Agent Mode internals (isolation, routing, eval scoring).
2. No independent verification of aggregator benchmark numbers against primary benchmark repos (SWE-bench/Terminal-Bench) — flagged rather than trusted.
3. No cost model computed for a self-built harness (depends on model choice + usage; needs user input).
4. No user-side requirements gathered (budget, audience, Windows vs. cloud deployment) — blocking only for final scoping, not for the blueprint.

## 13. Conclusions

1. `ESTABLISHED_FACT` — All three systems are the same core loop (model + tools + sandbox + context + permissions). The loop is simple; the differentiation is in context engineering, enforcement, and product surface.
2. `WELL_SUPPORTED` — The path to "best" is eval-driven engineering, containment-first security, context discipline, and simplicity-first design — in that priority order.
3. `WELL_SUPPORTED` — Building the *harness* (on frontier APIs) is feasible for an individual or small team; building the *model* is not the winning move.
4. `WELL_SUPPORTED` — Prompt injection cannot be fully prevented today; the correct posture is to bound blast radius with deterministic, OS-enforced controls — and to design for it from day one, not bolt it on.
5. `REASONABLE_INFERENCE` — A new entrant should compete on one signature surface (e.g., a Windows-friendly "download → install → open → run" experience, per §32 of the brief) rather than feature parity with Claude Code/Codex.
6. `CONTESTED` — Specific benchmark rankings; directional picture only.

## 14. Recommendations

### 14.1 Decision recommendation

**Build a harness, not a model. Build it in the order the evidence says matters: eval → sandbox → loop → context → product.** Do not start with UI polish, multi-agent orchestration, or model fine-tuning — none of those are the bottleneck; all are the classic over-build traps.

### 14.2 Reference architecture for "your own Arena/Claude Code/ChatGPT-style agent"

```
┌──────────────┐   ┌─────────────────────────────────────────────┐
│ Client (TUI/ │──▶│ Orchestrator: session state, context        │
│  Web/IDE)    │   │ assembly, budgets, stop conditions           │
└──────────────┘   └───────┬───────────────────────┬─────────────┘
                           │ model calls           │ tool calls
                 ┌─────────▼─────────┐   ┌─────────▼─────────────────────┐
                 │ Model gateway     │   │ Permission gate (deterministic)│
                 │ (multi-provider,  │   │ allow/ask/deny per tool+scope │
                 │ fallback, caching)│   └─────────┬─────────────────────┘
                 └───────────────────┘   ┌─────────▼─────────────────────┐
                                         │ Sandbox (Dev: Docker;         │
                                         │  Prod: Firecracker/Kata μVM)  │
                                         │  · filesystem: workspace-only │
                                         │  · network: egress allowlist  │
                                         │  · no secrets in env          │
                                         └───────────────────────────────┘
  Cross-cutting: telemetry/traces · eval runner (hidden tests per task)
  · memory files (project.md) · skills (on-demand) · MCP (later) · checkpoints
```

**Component build-vs-buy** (evidence: [S2](https://callsphere.ai/blog/inside-claude-code-s-architecture-how-the-agent-loop-works), [S14](https://www.decodingai.com/p/building-a-coding-agent-from-scratch-system-design), [S19](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/), [S20](https://northflank.com/blog/how-to-sandbox-ai-agents)):

| Component | Buy/Reuse | Build |
|---|---|---|
| Model | **Buy** — frontier API (Sonnet-class default; fallback GPT/Gemini) | — |
| Tool-calling protocol | Use API-native tool calls / MCP SDK | thin wrapper |
| Sandbox | **Reuse** — Docker (dev), Firecracker/Kata or a sandbox PaaS (prod) | image + egress policy |
| Permission gate | — | **Build** (deterministic; cannot be talked past — it executes outside the model's reach) |
| Eval runner | Reuse harness patterns (SWE-bench style) | **Build** your own task cases — this is the moat |
| Context/memory files, skills | Reuse the *pattern* (CLAUDE.md/SKILL.md are openly documented) | build |
| UI | Reuse TUI libs / plain web | build minimal |

### 14.3 Three conditional build paths

**Path A — You want a personal/practical tool (fastest value):** Don't build anything. Use Arena Agent Mode for evaluation and Claude Code or Codex for daily work; encode your rules in `CLAUDE.md`/`AGENTS.md` and skills. Windows-friendly: all three have browser surfaces — zero install.

**Path B — You want to learn by building (recommended for this repo):** Phase 1 (≈1–2 weekends): ReAct loop + file/shell tools + Docker sandbox + 10 eval cases. Phase 2: permission gate + egress allowlist + memory file + budgets. Phase 3: skills + subagents + MCP client. Phase 4: web UI + GitHub PR flow + telemetry. *Gate every phase on passing your eval suite.* This is the demonstrated evolution order of the incumbents.

**Path C — You intend a product:** Path B first; then differentiators ranked by evidence: (1) trust (best-in-class sandboxing + audit logs), (2) one signature surface (e.g., a genuinely beginner-friendly Windows app per §32: "Download → Install → Open → Run" with zero terminal), (3) eval-transparency. Compete where Claude Code (terminal depth) and Codex (cloud tasks) are weak, not where they are strong.

### 14.4 Evaluation strategy (the "make it the best" lever #1)

Your own hidden-oracle task cases predict usefulness better than any leaderboard ([S14](https://www.decodingai.com/p/building-a-coding-agent-from-scratch-system-design)). Build: ~10 small task cases (add flag X, fix bug Y in fixture repos) with hidden tests; 2–3 end-to-end scenarios (issue → PR). Run on every harness change. Add security cases: malicious files in the repo, injected instructions in fetched pages — assert the sandbox/permission layer holds. Track: pass rate, tokens/cost, wall-clock, and **escape/injection failures = release blocker**.

### 14.5 Security baseline (lever #2 — non-negotiable)

1. OS-enforced sandbox: workspace-scoped filesystem, deny-by-default network egress with domain allowlist ([S19](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/)).
2. Deterministic action-level policy engine (block destructive commands, sensitive-file reads, config writes) — enforced where the model cannot negotiate ([S24](https://www.endorlabs.com/learn/prompt-injection-against-coding-agents-the-attack-surface-nobody-owns)).
3. No secrets in agent environments; short-lived credential broker if needed ([S19](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/)).
4. Deny writes to implicit-execution paths (git hooks, helper binaries) — the 2026 escape class ([S22](https://www.developersdigest.tech/blog/securing-ai-coding-agents)).
5. Human approval for anything crossing the boundary; audit log of every action.
6. Treat all retrieved content as untrusted data, never as instructions (this project's §23 — matches OWASP guidance).

### 14.6 Windows beginner experience (per §32)

- **Zero-command start:** use the browser surfaces — arena.ai/agent, claude.ai/code, chatgpt.com (Codex). Nothing to install; this is the correct default for a beginner.
- **When a terminal is needed** (Claude Code CLI on Windows): open PowerShell (Start → type "PowerShell"); install: `npm install -g @anthropic-ai/claude-code` (requires Node.js — install the LTS from nodejs.org, "Next → Next → Finish"); run: `claude`. Expected output: an interactive prompt and trust dialog for your folder. Failure: `claude is not recognized` → close and reopen PowerShell, then `claude --version`. Still failing → use the web surface instead and re-check the official docs at code.claude.com. *(Command verified against current official docs at retrieval time; re-check before publishing instructions.)*

## 15. Next Actions

1. **User decision:** confirm which Path (A/B/C) and constraints (budget, Windows vs cloud, audience) — this unlocks implementation scoping.
2. **Repo:** on authorization, Phase-1 MVP per Path B; update `README.md` to describe the project and link this report.
3. **Evaluation:** build the 10-case eval suite before any further harness features.
4. **Watchlist (re-evaluation triggers):** model releases, agent-runtime CVEs (update runtimes promptly — the Cursor lesson), Arena Agent Mode feature changes, benchmark methodology updates. Re-run this research or a delta-audit quarterly or on any trigger.

## 16. Sources

Retrieved 2026-09-11 unless noted. Primary/official marked ★.

| # | Source | Date | Type |
|---|---|---|---|
| [S1](https://code.claude.com/docs/en/features-overview) | Anthropic — Extend Claude Code (official docs) ★ | 2026-07 | Primary |
| [S2](https://callsphere.ai/blog/inside-claude-code-s-architecture-how-the-agent-loop-works) | Callsphere — Inside Claude Code's architecture | 2026-06 | Analysis |
| [S3](https://colinmcnamara.com/blog/understanding-skills-agents-and-mcp-in-claude-code) | C. McNamara — Skills, Agents, Subagents, MCP | 2025-10 | Analysis |
| [S4](https://www.askglitch.com/blog/claude-code-vs-codex) | AskGlitch — Codex vs Claude Code 2026 | 2026-07 | Comparison |
| [S5](https://www.penligent.ai/hackinglabs/inside-claude-code-the-architecture-behind-tools-memory-hooks-and-mcp/) | Penligent — Claude Code architecture layers | 2026-04 | Analysis |
| [S6](https://explainx.ai/blog/codex-vs-claude-code-ai-agent-comparison-2026) | ExplainX — Codex vs Claude Code | 2026-09 | Comparison |
| [S7](https://www.nxcode.io/resources/news/claude-vs-chatgpt-2026-which-ai-to-use) | Nxcode — Claude vs ChatGPT 2026 | 2026-03 | Comparison |
| [S8](https://www.iwoszapar.com/p/chatgpt-codex-claude-gemini-antigravity) | Iwos Zapar — feature matrix | 2026-09 | Comparison |
| [S9](https://en.wikipedia.org/wiki/LMArena) | Wikipedia — Arena (LMArena) | upd. 2026-09 | Reference |
| [S10](https://x.com/arena/status/2062565126600114484) | Arena.ai — Agent Mode launch ★ | 2026-06 | Primary |
| [S11](https://arena.ai/blog/agent-mode) | Arena.ai — Agent Mode blog ★ | 2026-08 | Primary |
| [S12](https://help.arena.ai/articles/5432423882-how-to-use-agent-mode) | Arena.ai — How to use Agent Mode ★ | 2026-08 | Primary |
| [S13](https://arena.ai/blog/agent-arena-methodology) | Arena.ai — Agent Arena methodology ★ | 2026-08 | Primary |
| [S14](https://www.decodingai.com/p/building-a-coding-agent-from-scratch-system-design) | DecodingAI — coding agent harness design | 2026-08 | Analysis |
| [S15](https://smartscope.blog/en/generative-ai/chatgpt/llm-coding-benchmark-comparison-2026/) | Smartscope — benchmark comparison | 2026-03 | Benchmarks (contested) |
| [S16](https://mer.vin/2026/05/when-not-to-build-ai-agents-anthropics-workflow-vs-agent-playbook/) | Mer.vin — Anthropic workflow-vs-agent playbook | 2026-05 | Analysis of ★ Anthropic guidance (Dec 2024) |
| [S17](https://patmcguinness.substack.com/p/design-patterns-for-effective-ai) | P. McGuinness — Design patterns for effective agents | 2025-03 | Analysis |
| [S18](https://iternal.ai/llm-selection-guide) | Iternal — LLM selection guide | 2026-09 | Benchmarks (contested) |
| [S19](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/) | NVIDIA — sandboxing agentic workflows ★ | 2026-03 | Security |
| [S20](https://northflank.com/blog/how-to-sandbox-ai-agents) | Northflank — sandboxing AI agents 2026 | 2026-02 | Security |
| [S21](https://ai-sdk.dev/docs/agents/building-agents) | Vercel AI SDK — building agents | 2026 | Docs |
| [S22](https://www.developersdigest.tech/blog/securing-ai-coding-agents) | Developers Digest — threat model (CVE-2026-50548, Pillar, HalluSquatting) | 2026-07 | Security |
| [S23](https://ainowinstitute.org/publications/friendly-fire-exploit-brief) | AI Now Institute — Friendly Fire RCE PoC ★ | 2026-07 | Security |
| [S24](https://www.endorlabs.com/learn/prompt-injection-against-coding-agents-the-attack-surface-nobody-owns) | Endor Labs — prompt injection attack surface | 2026-09 | Security |
| [S25](https://ofox.ai/blog/llm-leaderboard-best-ai-models-ranked-2026/) | Ofox — leaderboard snapshot | 2026-06 | Benchmarks (contested) |
| [S26](https://localaimaster.com/blog/lmarena-chatbot-arena-leaderboard) | LocalAI Master — Arena leaderboard | 2026-08 | Benchmarks (contested) |

---

### Evidence-state legend used in this report

`ESTABLISHED_FACT` (official/primary source) · `WELL_SUPPORTED` (multiple consistent independent sources) · `REASONABLE_INFERENCE` (synthesis of weaker signals, labeled as such) · `CONTESTED` (sources disagree; disagreement preserved) · `SPECULATION` · `UNKNOWN` (no adequate source found).

*Limitations: web retrieval was the primary evidence channel (no direct API access to benchmark repos or vendor internals). Aggregator benchmark values are unverified against primary repositories. Arena Agent Mode internal architecture is undocumented. All conclusions are time-sensitive to the 2026-09 model/security landscape; re-evaluate quarterly or on trigger events (§15.2).*
