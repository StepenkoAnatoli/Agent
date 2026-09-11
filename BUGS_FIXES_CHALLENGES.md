# BUGS, FIXES & CHALLENGES
## Deep-research addendum — Claude Code · ChatGPT/Codex · Arena.ai + build-path implications

**Prepared:** 2026-09-11 · **Mode:** Deep research (bug/failure-mode pass) · **Status:** `RESEARCH_COMPLETE · IMPLEMENTATION_NOT_AUTHORIZED`
**Companion to:** `/DEEP_RESEARCH_REPORT.md` (§10 Failure Modes expanded with documented cases) and `/docs/control-plane.json` (updated).

---

## 1. Executive Summary

1. **Every system in this space ships real bugs, and the biggest ones are invisible from outside.** The most consequential documented incident is Anthropic's April 2026 postmortem: three separate bugs (reasoning-depth reduction, a caching bug that wiped reasoning history *every turn* — the "context rot" users experienced — and a verbosity-limiting system prompt that cost ~3% quality) shipped together and were perceived by users as "the model got dumber." All three were harness/infra bugs; **the model API was unaffected.** Fix: v2.1.116 (Apr 20) + mandatory model-specific eval suites for every system-prompt change + usage resets.
2. **The two most common bug classes are (a) context/caching bugs masquerading as model regressions, and (b) metering/background-task accounting bugs** (usage drained in minutes). Both vendors hit both: Claude Code (subagent-multiplication quota drain, June 2026) and Codex (auto-review/helper subagents running twice + phantom dashboard charges, June 2026, fixed in a "warroom" with cap resets + new monitoring).
3. **Scale of the problem:** `anthropics/claude-code` has **12,513 open issues** (Sept 2026, primary API data); Codex's single most-commented open bug has **1,123 comments** (#28756, backend 404 errors); OpenAI logged **~166 incidents in ~9 months (~18/month)** through July 2026 with measured uptime of 99.94% (APIs) / 99.62% (ChatGPT) / 99.98% (Codex). Claude Code's most-commented issues are usage-limit bugs (#16157: 1,494 comments).
4. **Capacity and rate limits are the dominant end-user failure mode**, ahead of correctness bugs: "model at capacity," 429/529s, usage-limit exhaustion (typically after 3–5 h of agentic work on a $20 plan).
5. **Session/resume is a recurring correctness minefield** — dozens of shipped regressions across both tools (resume sandbox-gate bug, crash-on-resume, worktree state loss, "invalid transport" for WSL threads, subagents never woken). If you build an agent, treat **session persistence as a first-class subsystem with its own tests**, not an afterthought.
6. **Arena.ai Agent Mode** has thinner public bug data: community-reported issues (chat deletion bug, large-file truncation, request-rejected hangs, model identity opacity, thumbs-only feedback) + design constraints (PR-merge session lockout). No public Arena status/incident history was found (`UNKNOWN`). The closest open-source reference — **Qwen Code's Agent Arena** — documents the same engineering challenges honestly: silently dropped config, no diff preview, no session resumption, worktree cleanup bugs.
7. **For our own build, the research sharpens the blueprint:** agents fail most often on *instruction following* (strong models) and *tool-use/syntax* (weak models); ~**18% of agent patches regress previously passing tests**; snapshot benchmarks hide maintainability — long-horizon benchmarks cut pass rates from ~73% (SWE-bench) to **25%** (SWE-EVO). Conclusion: our eval suite must include **regression tests, long-horizon tasks, and harness-specific cases** (resume, metering, sandbox) — not just one-shot fixes.

---

## 2. Scope, Method, Evidence Quality

**Method:** Pass 7 (bug-focused) added to the research plan: primary GitHub issue-tracker data (via GitHub API, retrieved live), vendor changelogs, official postmortems/status pages via secondary reporting, community reports (Reddit), and peer-reviewed failure-mode analyses (arXiv). Evidence classes: `ESTABLISHED_FACT` (vendor-acknowledged), `WELL_SUPPORTED` (multiple consistent sources), `COMMUNITY_REPORT` (user forum — plausible, unverified), `UNKNOWN`.

**Honesty notes:** community reports are treated as signals, not facts; changelog mirrors (gradually.ai, claudelog) were cross-checked against GitHub issues and match; OpenAI incident numbers come from its public status history as reported by tech press — internal root causes are vendor-confidential.

---

## 3. Bug Taxonomy (what "bugs" exist in agent systems)

| Class | Definition | Examples (this pass) |
|---|---|---|
| **Model-behavior** | model itself misbehaves (fixed upstream) | verbosity, "dumb" outputs — often *not* actually this |
| **Context/caching** | context assembly, compaction, prompt caching | reasoning-history wipe (CC), cache-miss quota drain (CC) |
| **Orchestration** | loop logic, subagents, retries, notifications | subagent multiplication (CC), double-running helpers (Codex) |
| **Metering/accounting** | usage, quotas, billing display | phantom charges (Codex), Max-plan fast drain (CC) |
| **Session/resume** | persistence, replay, state restoration | sandbox-gate regression, crash-on-resume, WSL transport |
| **Sandbox/policy** | isolation false positives/negatives | git checkout blocked on `.vscode/` (CC), sandbox escape (CVE, report 1) |
| **Tooling/integration** | editors, OS shells, installers | Windows desktop relaunch locks, JetBrains/VS Code breakage |
| **Capacity/platform** | provider infra, rate limits, outages | "model at capacity," 429/529, ~18 incidents/month (OpenAI) |
| **UX/product** | UI state, feedback, affordances | terminal flicker, 60s auto-resolve, thumbs-only feedback (Arena) |
| **Evaluation** | benchmark/env harness defects | pass-to-fail tests, env replication ~10 h/repo |

**Key insight:** users attribute most failures to "the model got worse" — vendor postmortems show the cause is usually **harness or infrastructure**. Design implication: your agent's telemetry must be able to *distinguish* model errors from harness errors, or you will fix the wrong thing.

---

## 4. Claude Code — Documented Bugs & Fixes

### 4.1 The April 2026 quality incident (`ESTABLISHED_FACT` — official postmortem)

Users reported a broad quality drop over ~a month. Anthropic's postmortem identified **three independent bugs, none in the model API**:

| Bug | Shipped | Effect | Fix |
|---|---|---|---|
| Lowered reasoning depth (internal change) | ~Mar | Shallow reasoning on complex tasks | Reverted/restored |
| **Caching optimization** (delete old reasoning after 1 h idle) | Mar 26 | Coding error → reasoning history wiped **every turn**; "context rot": forgetfulness, repetition, contradictory edits; cache misses burned quota | Fixed Apr 10 |
| System-prompt verbosity limit ("≤25 words between tool calls") aimed at Opus 4.7 | Apr 16 | Later eval showed **−3% quality**; rolled back | Rolled back Apr 20 |

**Process fixes** (the "fix" worth copying): all three fixed by **v2.1.116 (Apr 20)**; usage limits reset for all subscribers; **every system-prompt change must now pass a broad, model-specific eval suite**; employees dogfood the exact public build. *Lesson for us: system-prompt changes are code changes — gate them on evals.*

### 4.2 June 2026 subagent-multiplication / quota-drain bug (`WELL_SUPPORTED`, acknowledged)

Subagents dispatching repeatedly without progress, corrupting sessions, burning "hundreds of thousands of tokens on simple operations"; Pro/Max quotas exhausted in minutes. Anthropic acknowledged elevated errors (Opus + Sonnet), shipped a fix, and issued emergency quota resets. User workarounds in the interim: fresh sessions, limit parallel tasks, avoid resume during bad runs.

### 4.3 Top open issue themes (primary API data, Sept 2026 — 12,513 open issues)

| Issue | Comments | Class | Status |
|---|---|---|---|
| #16157 Instantly hitting usage limits on Max | 1,494 | Metering | OPEN |
| #38335 Max sessions exhausted abnormally fast (since Mar 23) | 843 | Metering/caching | OPEN (same root cause class as 4.1 bug #2) |
| #34229 Phone verification failures | 742 | Auth/platform | OPEN |
| #41447 "Open source Claude Code" | 234 | Product | OPEN |
| #84352 False cyber-safeguard blocks on approved orgs | 199 | Policy | OPEN |
| #46987 "Stream idle timeout — partial response" | 184 | Capacity/network | OPEN |
| #42776 Windows Desktop fails to relaunch (orphaned process file lock) | 173 | Tooling/OS | OPEN |
| #24055 32k output-token cap error | 135 | Model limits | OPEN |
| #26224 Hanging/freezing 5–20 min | 131 | Capacity | OPEN |
| #826 / #769 / #1913 Terminal flicker/scrolling | 354/307/187 | UX | OPEN (long-lived) |

### 4.4 Session/resume — a documented regression factory

Changelog fix history shows this class recurs almost every release: resume failed when a worktree lost git metadata (2.1.260); subagent resumed via SendMessage never woken (2.1.260); **5 MB transcript → "No transcript found"** on resume (2.1.257); resume picking wrong sessions by path similarity (2.1.239); `--continue` broken by sandbox gate regression in **2.1.120** (#53085 — user settings `sandbox.enabled=false` not honored on the resume path; workaround: pin 2.1.119); crash-on-resume `UKH is not a function` (#53315); PDF-too-large permanently locking sessions (2.1.31); resume requiring re-read of created files (2.0.15/2.0.17). **Lesson: session state (files created, worktree, transcript, permission mode) must be captured, versioned, and replayed with its own regression suite.**

### 4.5 Sandbox/worktree correctness bugs

Linux sandbox broke sandboxed git in repos with `extensions.worktreeConfig` (2.1.239); worktree-isolated sessions refused bash loops/`$()`/heredocs as "too complex to verify" (2.1.257); sandbox blocked `git checkout`/`worktree add` on repos tracking `.vscode/` (#51303, hardcoded blocklist) leaving **stale branches/worktrees**; plan mode auto-ran file-modifying bash without prompts (2.1.212); worktree creation followed a symlinked `.claude/worktrees` **outside the repo** (2.1.212 — security-adjacent). *Pattern: sandboxes over-block legitimate git workflows and under-block rare malicious paths — both need dedicated tests.*

### 4.6 User-environment issues + fixes (documented workarounds)

| Symptom | Cause | Fix |
|---|---|---|
| Usage limit reached | Pro-plan caps (~3–5 h agentic work) | fewer parallel subagents; smaller context; upgrade |
| npm install fails | Node <18, permissions, cache | update Node LTS; clear npm cache |
| Auth/API key errors | expired session/rotated key | re-login; check status.anthropic.com |
| Hangs | network during long runs; context overflow | restart session; `/compact` |
| Wrong-file edits | context confusion | `/compact`, re-state task, shorter sessions |
| VS Code/JetBrains breakage | CLI-extension version mismatch | update both; check PATH |
| Slowness (measured) | context size dominates | fresh: ~1.1 s/turn; 150K ctx: ~3.5 s; 500K+: ~5 s; **86.7% of API errors = local connection failures** |
| 429/529 errors | rate limits / provider overload | retry later; switch model; `/status` |
| Windows | native support limited | use WSL2 |

---

## 5. Codex (OpenAI) — Documented Bugs & Fixes

### 5.1 The usage-metering bug (`ESTABLISHED_FACT` — vendor-acknowledged)

**June 28–30, 2026:** users hit weekly limits in 2–3 days. Engineering lead Sottiaux: a Sunday **warroom** found auto-review and helper **subagents running more often than intended, running twice, or retrying too aggressively**; the dashboard also showed **activity that was never charged**. Fixes deployed + all user caps reset + "more detailed monitoring to detect background-usage regressions sooner." A similar incident was logged Mar 6–7, 2026 on the official status page. *Same bug class as Claude Code's — background/subagent accounting. Twice. This is a hard problem, not a one-off.*

### 5.2 Capacity & platform incidents (`WELL_SUPPORTED` — official status history via press)

- **Jun 16, 2026:** "model at capacity" — GPT-5.5 unavailable, users forced to older models; recovered ~3 h later.
- **Jul 22–25, 2026:** fourth incident in four days; 503s (`biscuit_baker_service_me_circuit_open` internal label) across APIs + ChatGPT + Codex simultaneously.
- **Sep 3, 2026:** elevated errors across **19 components** (ChatGPT group: 15 incl. Agent, Deep Research, Codex-in-Desktop; Codex group: web, API, CLI, VS Code).
- **Cumulative:** ~166 incidents in ~9 months (avg ~18/month, pattern "since autumn 2025"); 90-day uptime: APIs 99.94%, ChatGPT 99.62%, Codex 99.98%.
- **Structural context:** OpenAI merged ChatGPT + Codex + API into one platform (May 2026) to concentrate engineering — single-platform incidents now have blast radius across all surfaces.

### 5.3 Top open issue themes (primary API data, Sept 2026)

| Issue | Comments | Class |
|---|---|---|
| #28756 "unexpected status 404" from backend API | 1,123 | Platform/backend |
| #19464 Request 1M-token context for GPT-5.5 | 132 | Model limits |
| #20214 Windows app freezes/stutters on capable hardware | 111 | Tooling/OS |
| #25719 macOS `syspolicyd`/`trustd` CPU+memory runaway | 89 | Tooling/OS |
| #40752 Windows desktop fails to start after update 26.820 | 87 | Updater/OS |
| #38350 Scheduled tasks **self-disable** after successful runs | 66 | Orchestration |
| #40819/#40715 WSL-thread resume fails — "invalid transport in mcp_servers.codex_app" | 68/71 | Session/resume |
| #37403 macOS regression: cannot resume Remote Control/CLI thread | 60 | Session/resume |
| #31606 "Reset failed, did not apply and 1 reset is wasted" | 58 | Metering/UX |
| #18960 Websocket reconnect loop (closed before response.completed) | 58 | Network |
| #13993 Request standalone **Windows installer** | 84 | Distribution |
| #9203 "/undo" removed | 77 | Product regression |

**Windows distribution gap** (#13993, #20214, #40752): Codex on Windows remains the weakest surface — relevant to our §32 Windows-first product thesis: *a robust, standalone Windows installer is a genuine differentiator nobody has nailed.*

---

## 6. Arena.ai Agent Mode — Reported Issues & Constraints

### 6.1 Community-reported bugs (`COMMUNITY_REPORT`, May–Jun 2026, r/lmarena)

- **Chat deletion bug**: cannot delete an agent-mode chat.
- **Large-file truncation**: built-in file-reading tool returns only the beginning and end of large files, silently omitting the middle — a data-integrity hazard for code work.
- **Mid-project failures**: "service request rejected," file issues, and indefinite "loading" states that stalled multi-hour projects.
- **Model opacity**: users cannot see which model/provider executes their agent task — hard to calibrate expectations or compare.
- **Feedback model mismatch**: thumbs-up/down is insufficient for agentic iteration (users want edit-upload-repeat, i.e., a real work loop).

### 6.2 Design constraints (official, from report 1 — by design, not bugs)

GitHub sessions end their push rights when the PR is merged/closed; post-merge work is stranded in-session (official help doc warns "make sure your work is pushed before merging"). No-repo sessions deliver via zip download. Workspace panel is the only file interface.

### 6.3 Open-source reference: Qwen Code "Agent Arena" (`ESTABLISHED_FACT` — official docs)

Qwen Code's multi-model competitive arena (git-worktree isolation, max 5 agents) documents its own known limitations — a real engineering map of arena-building challenges: `maxRoundsPerAgent`/`timeoutSeconds` in settings **silently dropped** by the CLI; **no diff preview** before choosing a winner; **no session resumption** (closing the terminal strands worktrees → manual `git worktree prune`); worktree creation/cleanup failures and stale worktrees; applying the winner's diff can conflict with concurrent working-directory changes; requires a git repo.

### 6.4 Unknowns

No public Arena status/incident history or official bug tracker was found in this pass (`UNKNOWN`). Internal bug/fix data for Arena Agent Mode is not public; treat 6.1 as a lower-confidence snapshot.

---

## 7. Why Agents Fail — Evaluation Research (`WELL_SUPPORTED`, arXiv 2026)

| Finding | Source | Implication for our build |
|---|---|---|
| **Long-horizon collapse**: best model solves 25% of SWE-EVO tasks vs 72.8% on SWE-bench Verified | SWE-EVO (2512.18470) | Ship long-horizon eval tasks; snapshot benchmarks overstate capability ~3× |
| **Failure taxonomy**: strong models fail on *instruction following*; weak models on *tool use + syntax*; older models loop or terminate early | SWE-EVO | Tailor harness/UX to your model tier; add loop & early-stop detection |
| **Scaffold sensitivity**: model rankings flip between harnesses (SWE-agent vs OpenHands) | SWE-EVO | The harness is part of the system under test — eval your harness, not just your model |
| **~18% pass-to-fail**: ~1 in 5 agent patches breaks a previously passing test | SWE-bench-secret (UWaterloo) | CI-style regression evals mandatory; hidden tests must include existing tests |
| **Logic deviation dominates failures** (66.7–73%) | SWE-bench-secret | Surface diff review before merge; human checkpoint at consequential changes |
| **Maintainability invisible in snapshots**: regressions compound over evolution; most models <50% long-term solved rate | SWE-CI (2603.03823) | Eval must include multi-step evolution tasks (EvoScore-style) |
| **Even best agent <50% on scientific SWE**; poorly-aligned guidance causes anchoring | SWE-bench Science (2608.19799) | RAG/context injection can *hurt*; measure it |
| **Env replication is the practical bottleneck** (~10 h/repo manually) | Toloka SWE-bench audit | Containerize every eval case from day one |

---

## 8. Cross-System Patterns (the five recurring bug families)

1. **Context/caching bugs masquerade as model regressions** — Claude Code Apr 2026; users cannot distinguish; vendors now gate prompt changes on evals. *Mitigation: telemetry that separates model, context, and harness errors.*
2. **Background-task & subagent metering** — Claude Code Jun 2026, Codex Jun 2026 *and* Mar 2026. *Mitigation: usage accounting per task/subagent with anomaly detection before billing/limits are touched.*
3. **Session/resume state machines** — dozens of regressions in both tools; the single most-churned bug area. *Mitigation: serialize full session state (files, worktree, transcript, permissions, mode), version it, replay-test every release.*
4. **Sandbox correctness at the edges** — false blocks on legitimate git flows vs. rare malicious paths slipping through. *Mitigation: golden-path tests (clone, checkout, worktree, symlinks, hooks) + adversarial cases, both in CI.*
5. **Capacity as UX** — rate limits, "at capacity," and outages dominate real-world complaints more than correctness. *Mitigation: graceful degradation (queue, fallback model, checkpoint-and-resume), honest quota UX.*

---

## 9. Challenges & Risks for Our Own Build (with fixes)

| # | Challenge | Evidence basis | Fix / design response | Severity |
|---|---|---|---|---|
| C1 | Context rot (long sessions contradict themselves) | CC postmortem, dev reports | budgets + `/compact`-style compaction + session-scoped task state + subagents for parallel exploration | CRITICAL |
| C2 | Subagent/loop cost runaway | CC + Codex metering bugs | per-task token/cost budgets, loop detectors, no unbounded auto-retry, anomaly alarms | CRITICAL |
| C3 | Session/resume correctness | CC/Codex regression history | session state as first-class subsystem; replay tests; pin/rollback via versioned binaries | HIGH |
| C4 | Sandbox false positives (blocks legit git) and negatives (escapes) | CC #51303, CVE-2026-50548 (report 1) | allowlist design + golden-path CI + adversarial suite; microVM isolation in prod | HIGH |
| C5 | Evaluation blind spots (regression, long-horizon, scaffold) | SWE-EVO, SWE-CI, SWE-bench-secret | hidden-oracle tasks incl. existing tests + multi-step evolution + harness A/B | HIGH |
| C6 | Model/vendor incidents and churn | ~18 OpenAI incidents/month; capacity events | multi-provider fallback, graceful degradation, honest status UX | MEDIUM |
| C7 | Metering correctness (phantom charges kill trust) | Codex warroom | metering is a tested subsystem, not bookkeeping | MEDIUM |
| C8 | Windows distribution (installer, updater, desktop bugs) | Codex #13993/#20214/#40752; CC #42776 | standalone installer, updater with rollback; WSL and native paths both tested (matches §32 brief) | MEDIUM |
| C9 | Model opacity in multi-model products | Arena community reports | disclose model identity + per-model stats in any arena-style product | LOW |

---

## 10. Risk Register (updated — addendum to report 1 §11)

| Risk | Δ from report 1 | Notes |
|---|---|---|
| Prompt injection / RCE | unchanged CRITICAL | see report 1 §14.5 |
| Cost blowup | confirmed HIGH→CRITICAL for subagent-heavy designs | two independent vendor incidents in 2026 |
| Context degradation | new CRITICAL | vendor postmortem shows it's fixable but recurring |
| Session-state corruption | new HIGH | most-churned bug class in both majors |
| Provider incidents/capacity | new MEDIUM-HIGH | 18/month cadence observed |
| Eval blind spots (regression, long-horizon) | sharpened HIGH | ~18% pass-to-fail; 25% long-horizon |
| Windows distribution immaturity | new OPPORTUNITY + risk | nobody has nailed it; first-mover with polish wins |

---

## 11. Recommendations & Next Actions

1. **Adopt the vendor process fix as our own rule:** any system-prompt, context-assembly, or metering change is gated on a model-specific eval suite + dogfooding the exact shipped build (Anthropic's Apr 2026 fix).
2. **Eval suite additions** (build this before the loop, per report 1 §14.4): (a) regression cases with existing tests (pass-to-fail detector), (b) ≥2 long-horizon/evolution tasks, (c) harness self-tests: resume/replay, metering accuracy, sandbox golden paths + adversarial cases, (d) injection cases (report 1).
3. **Telemetry must classify errors** into model / context / orchestration / metering / sandbox / capacity — otherwise you will misdiagnose (the April 2026 lesson).
4. **Session state is a subsystem:** version it, replay-test it, make it the first thing covered by CI.
5. **Capacity honesty:** budget for fallback models and checkpoint-and-resume; do not let quota UX repeat Codex's "wasted reset" (#31606) or CC's Max-plan drain (#16157).
6. **Windows-first distribution remains the open differentiator** (§32): standalone installer, updater rollback, no terminal for the happy path.
7. **Authorization unchanged:** `NOT_AUTHORIZED` for code. This addendum and the control-plane update are the only repo changes. Blocking decision still: which build path (A/B/C) — now with the bug data in hand, Path B's Phase 2 should absorb the C1–C9 mitigations above.

## 12. Sources

Retrieved 2026-09-11 (live GitHub API queries included). Official/primary marked ★; vendor-acknowledged facts marked VA.

| # | Source | Type |
|---|---|---|
| [B1](https://the-decoder.com/anthropic-confirms-claude-code-problems-and-promises-stricter-quality-controls/) | Anthropic postmortem coverage (3 bugs, v2.1.116, process changes) ★VA | Primary |
| [B2](https://www.cybersecurityintelligence.com/blog/claude-code-has-a-bug--9442.html) | June 2026 subagent-multiplication incident | Secondary (vendor-acknowledged) |
| [B3](https://github.com/anthropics/claude-code/issues) | anthropics/claude-code tracker — 12,513 open; top issues by comments (API, live) ★ | Primary |
| [B4](https://www.gradually.ai/en/changelogs/claude-code/) | Claude Code changelog mirror (387 releases; fix history 2.1.31→2.1.260) | Primary-derived |
| [B5](https://github.com/anthropics/claude-code/issues/53085) | #53085 sandbox-gate resume regression | Primary |
| [B6](https://github.com/anthropics/claude-code/issues/51303) | #51303 sandbox blocks git on `.vscode`-tracked repos | Primary |
| [B7](https://claude-code-alternatives.com/blog/claude-code-not-working/) | 9 common CC issues + fixes | Community/how-to |
| [B8](https://www.aakashx.com/blog/claude-code-slow-causes-fixes/) | CC slowness: measured baselines, error taxonomy | Analysis |
| [B9](https://github.com/openai/codex/issues) | openai/codex tracker — top issues by comments (API, live) ★ | Primary |
| [B10](https://www.businessinsider.com/openai-codex-usage-limit-warroom-fix-issue-2026-6) | Codex usage-bug warroom + fixes ★VA | Primary (vendor statements) |
| [B11](https://status.openai.com/incidents/01KK26XE1W536H7DQV2EXM3GHE) | Mar 2026 Codex usage-rate incident ★ | Primary |
| [B12](https://www.businessinsider.com/openai-codex-elevated-errors-at-capacity-2026-6) | Jun 16, 2026 "model at capacity" ★VA | Primary (vendor statements) |
| [B13](https://thenextweb.com/news/openai-outage-chatgpt-codex-api-july-2026) | Jul 2026 4-in-4-days; ~166 incidents/9mo; uptime figures | Secondary (official status history) |
| [B14](https://www.unite.ai/openai-confirms-service-degradation-hitting-chatgpt-and-codex-users/) | Sep 3, 2026 19-component degradation ★VA | Secondary (official status) |
| [B15](https://www.reddit.com/r/lmarena/comments/1tm949b/tried_the_agent_mode/) | Arena Agent Mode user reports (chat deletion, truncation, opacity) | Community |
| [B16](https://www.reddit.com/r/lmarena/comments/1svzd5h/arena_ai_changed/) | Arena mid-project failures, model availability | Community |
| [B17](https://qwenlm.github.io/qwen-code-docs/en/users/features/arena/) | Qwen Code Agent Arena official docs — documented limitations ★ | Primary |
| [B18](https://arxiv.org/html/2512.18470v5) | SWE-EVO — long-horizon benchmark + failure taxonomy | Academic |
| [B19](https://arxiv.org/abs/2608.19799) | SWE-bench Science — <50% pass@1; anchoring | Academic |
| [B20](https://dspacemainprd01.lib.uwaterloo.ca/server/api/core/bitstreams/4945e946-05ee-424b-9255-1f9110d9485e/content) | SWE-bench-secret — pass-to-fail ~18% | Academic |
| [B21](https://arxiv.org/html/2603.03823v4) | SWE-CI — regressions in long-term maintenance | Academic |
| [B22](https://toloka.ai/blog/fixing-swe-bench-a-smarter-way-to-evaluate-coding-ai/) | Benchmark env-replication bottleneck (~10 h/repo) | Analysis |

*Limitations: vendor-internal root causes beyond public postmortems are unknown; community reports unverified; changelog mirrors cross-checked but not word-for-word official; Arena has no public bug tracker found.*
