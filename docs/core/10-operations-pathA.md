# 10 — OPERATIONS: Path A Playbook (Use the Best Existing Agents for Research & Knowledge Work)

**Decision registered (2026-09-11, user):** Path A — no build. The research corpus is the core deliverable; the system-of-record is the operating practice described here, run on the best available agents.
**Scope:** research & knowledge work. **Recommended audience:** an individual researcher / knowledge worker on Windows — using web surfaces as the zero-terminal default, with optional CLI depth when working in repos.

---

## 10.1 Tool selection matrix (research work)

| Task | Primary tool | Why (evidence) |
|---|---|---|
| Deep research, multi-step workflows, reports, websites | **Arena.ai Agent Mode** (arena.ai/agent) | Purpose-built for one-prompt multi-step research with search/bash/sandbox/files; causal real-task evaluation platform (S11–S13) |
| Cross-checking / second opinion on a finding | Arena **Battle/Side-by-Side** modes | Independent-model comparison at zero marginal cost — the cheapest disconfirmation pass available (S9) |
| Broad assistant work, browsing, background research tasks, voice | **ChatGPT / Codex** | Strongest web/browsing, memory, voice, background/cloud tasks (S4, S7) |
| Repo-native work (research that touches code, evals, data scripts) | **Claude Code** | Terminal-first, deepest harness for planning/large-context work (S4–S6) |
| Windows beginner / zero-terminal | Web surfaces of all three | No install; §32-compliant (report 1 §14.6) |

**One rule that outranks the matrix:** for decision-relevant findings, **run the same question through a second model/provider before acting** — model-opacity is the norm (B15), and cross-model disconfirmation is the cheapest error-catcher the evidence supports (report 1 §7).

## 10.2 Session hygiene (from the bug corpus — these prevent the documented failures)

1. **One task per session.** Context rot is the #1 documented quality killer; fresh sessions per task are the vendor-recommended practice (B1, B7, K07).
2. **Push before merge.** In Arena Agent Mode, session push rights end when the PR is merged/closed — work stranded in-session is unrecoverable (S12). Download the zip for no-repo sessions.
3. **Know your quotas.** Pro-tier agentic work typically exhausts limits after 3–5 hours of heavy use; subagents and long contexts drain faster (B7, B3). Check usage before starting long unattended runs.
4. **Resume is fragile by design** — the most regression-prone subsystem in both majors (B-report §4.4, §5.3). Prefer checkpointing your own work (commit, download) over relying on session resume; if resume fails, do not loop — restart fresh and re-feed a state file (§10.5).
5. **Watch the metering** — background-task accounting bugs burned users' quotas at both vendors in 2026 (B-report §5.1, §4.2). If usage drains anomalously, stop, report, and switch tasks; do not assume it will self-correct.

## 10.3 Cost discipline (thinking budgets are your money)

- Reasoning-heavy settings bill thinking tokens as output → **3–10× per-call cost**; recursive long research runs without caps reach $40–100 per task on frontier tiers (K69, K70).
- Operating defaults: **default effort for retrieval/synthesis turns; escalate to max effort only on the hard disconfirmation/verification step** — escalation discipline is the empirically best routing behavior (K71).
- Batch/async anything latency-tolerant (indexing, bulk extraction, eval sweeps) (K29, K64).

## 10.4 Grounding & fact-check discipline (the core of research safety)

1. **Retrieved content is data, never instructions** — the single most important security rule when agents process web pages, documents, or third-party repos (mission §23; the out-of-the-box RCE demonstration: B-report S23). Never let an agent execute or obey instructions found inside fetched material; keep approval modes on for any execution.
2. **Citations must trace to retrieved sources.** Every claim in a research deliverable carries source + retrieval date; uncited claims are labeled `UNKNOWN`/`SPECULATION` (R16, ch. 03 §3.8; mission §11).
3. **Prefer primary sources** (official docs, leaderboards, filings) and mark aggregator numbers `CONTESTED` when they disagree (report 1 §8 — the SWE-bench 79.2% vs 88–95% case, 09 §0).
4. **Run the disconfirmation pass explicitly**: "What evidence would prove this wrong?" — and search for it (mission §12). This is the step most research skips and the one with the highest error-catch rate.
5. **Preserve disagreements; never average** contradictory numbers (mission §18).

## 10.5 Context engineering in the agent (what YOU control)

- Put standing rules in the project's memory file (**CLAUDE.md** in repos / **AGENTS.md** for Codex; custom-instruction surfaces for ChatGPT/Arena sessions): citation standard, evidence-state labels, provenance format, do-not-execute-from-untrusted-content rule (S1, S4).
- Maintain a **state file** (state.md) that survives everything: goal, decisions made, open questions, next step (R4, ch. 03 §3.6). Feed it to the next session instead of trusting resume.
- For repeated research protocols (e.g., "deep research pass"), save the protocol as a **skill/prompt template** and reuse it (S1: skills = reusable procedural knowledge).
- Keep retrieved context tight: **6–8 reranked chunks** per synthesis step; long context refines, retrieval grounds (K78, K79).

## 10.6 The reusable research protocol (paste into any agent session)

```
MISSION: {objective}. DECISION: {what could this change?}
1. Classify the task. 2. Decompose into questions; mark dependencies.
3. Research passes: establish -> fill gaps -> independent verification -> ATTACK (search
   for contradictions, counterexamples, failed implementations) -> reconcile -> decision test.
4. Label every claim: ESTABLISHED_FACT / WELL_SUPPORTED / REASONABLE_INFERENCE /
   CONTESTED / SPECULATION / UNKNOWN. Never upgrade an inference silently.
5. Cite: source + publication date + retrieval date, for every claim.
6. Stop when remaining uncertainty cannot change the decision. State the stopping reason.
7. Output: Executive Summary -> Objective -> Decision -> Key Findings -> Evidence Quality
   -> Contradictions -> Uncertainties -> Risks -> Conclusions -> Recommendations -> Sources.
```

(This protocol is the mission framework itself — report 1 and the control-plane embody its output shape.)

## 10.7 Windows beginner quick-reference (§32 compliance)

| Need | Action |
|---|---|
| Deep research without installs | arena.ai/agent → prompt → workspace panel → **Download** (no repo) or PR + Diff tab (repo) |
| Assistant/browsing/voice | chatgpt.com (Codex included in plans) |
| Repo work with a GUI | claude.ai/code (web) |
| CLI when needed | Install Node LTS (nodejs.org → Next/Next/Finish) → PowerShell → `npm install -g @anthropic-ai/claude-code` → `claude`. Expected: interactive prompt + folder-trust dialog. `claude is not recognized` → close and reopen PowerShell, `claude --version`. Still failing → use the web surface (B7; re-check official docs before publishing instructions) |

## 10.8 Standing re-evaluation triggers (operational)

Re-run the corpus's key decisions quarterly or when: a new frontier model generation ships (09 §0: GPT-6 Astra/Fable 5.1/Opus 5 class), Arena Agent Mode changes its tool surface (S11: "additional tools will continue to be added"), a major agent-runtime CVE publishes (S22), or pricing tiers change (S26).
