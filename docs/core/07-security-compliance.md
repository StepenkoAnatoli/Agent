# 07 — SECURITY, THREAT MODEL & COMPLIANCE

## 7.1 Threat model (one paragraph)

The system executes model-chosen actions against a filesystem, a network, and external content (web pages, repos, MCP servers, tool outputs). **All external content is untrusted data, never instructions.** The attacker's primary vector is indirect prompt injection; the demonstrated worst case is remote code execution (RCE) on the host (B-report S23: out-of-the-box RCE via a poisoned library reviewed by stock Claude Code/Codex). Therefore the security architecture is **containment-first**: the question is never "can the model be fooled?" (it can — RL attacks achieve 98% bypass of prompt defenses, K44), but "what is the maximum damage when it is?"

## 7.2 The defense stack (in order of evidence strength)

`WELL_SUPPORTED` (S19–S24, K13, K14, K46, report 1 §14.5):

| Layer | Control | Evidence |
|---|---|---|
| 1. OS-enforced sandbox | workspace-scoped filesystem; deny-by-default egress + domain allowlist; **microVM-class isolation** (ch. 05 §5.3); no secrets in env | NVIDIA guidance (S19); escapes are a live CVE class (S22) |
| 2. Deterministic action policy | engine **outside the model's reach**: block destructive commands, sensitive-file reads, config writes; deny writes to implicit-execution paths (git hooks, helper binaries — the 2026 escape class) | Endor (S24); Pillar research (S22) |
| 3. Permission gates | allow/ask/deny per tool+scope; allow-once, never allow-many for boundary crossings; human approval for anything leaving the boundary | NVIDIA (S19); Cursor CVE lesson (S22) |
| 4. Credential broker | short-lived tokens on demand; never long-lived creds in agent env | NVIDIA (S19) |
| 5. MCP hardening | allowlist servers; treat tool metadata as untrusted; gateway architecture; scoped OAuth; audit logs | K10, K13, K14, OWASP |
| 6. Audit logging | every action, tamper-evident, retained (≥6 mo for EU high-risk) | K50, Art. 12 |
| 7. Update discipline | runtimes patched promptly; vendor advisories watched | Cursor 3.0 lesson (S22) |

**Explicit non-goal:** prompt-based self-defense as a security boundary. Instruction hierarchy helps reliability (+63%), not security (98% bypass under RL attack) (K44). The boundary is code, not prose.

## 7.3 MCP-specific threat catalog (peer-reviewed)

`WELL_SUPPORTED` (K12–K14):
- **Tool poisoning**: malicious instructions in tool metadata; 5/7 tested clients lacked static validation; empirical success 0–100% by client (K14).
- **Tool shadowing**: attacker server overrides a legitimate tool name (K10).
- **Config poisoning**: `.mcp/config.json` in a repo auto-connects to attacker servers on project open (K14).
- **Supply chain**: Postmark-impersonating npm MCP server — identical behavior for 15 releases, then one added line exfiltrating every email (K11).
- **Lifecycle threats** (K12): agent-card spoofing, task injection, push-notification hijacking, orphaned resources/credential persistence after termination.
- **Protocol-level gaps** (NSA, K13): no RBAC exchange at instantiation, weak audit spec, serialization/validation gaps, data leakage across servers sharing a client, non-determinism as an attack surface.

## 7.4 Agent-specific attack results (from the bugs pass)

- **Friendly Fire (AI Now, Jul 2026)**: stock Claude Code/Codex reviewing a poisoned library → RCE, no hooks/plugins/MCP required (S23).
- **Cursor CVE-2026-50548**: `working_directory` abuse → writes outside workspace → RCE via overwriting the sandbox helper binary; patched in Cursor 3.0 (S22).
- **Pillar Security (Jul 2026)**: boundary bypasses across Cursor, Codex, Gemini CLI, Antigravity — often sandbox-writes-files-trusted-host-loads (S22).
- **HalluSquatting (Jul 2026)**: hallucinated package/skill names → promptware delivery (S22).
- Our sandbox self-test suite exists precisely to catch these classes in our harness (ch. 06 §6.2).

## 7.5 Compliance baseline (EU AI Act — binding since Aug 2, 2026)

`ESTABLISHED_FACT` (K49–K53, EU AI Office K51):

| Obligation | Requirement | Applies |
|---|---|---|
| Art. 5 | prohibitions (harmful manipulation etc.) | now |
| **Art. 50 transparency** | disclose AI interaction; label generated content; CoP published | **Aug 2, 2026** (marking/detection compliance deadline Dec 2, 2026 for pre-existing systems) |
| Chapter III (high-risk) | risk mgmt (Art. 9), data governance (Art. 10), tech docs (Art. 11), **tamper-evident logs ≥6 months (Art. 12)**, deployer transparency (Art. 13), **human oversight (Art. 14)**, accuracy monitoring (Art. 15) | Aug 2, 2026, for high-risk sectors (HR, credit, health, education, infrastructure) |
| GPAI obligations | on the underlying model provider, not us | now |
| Fines | up to **€35M or 7%** global turnover | — |

**Roles**: provider (develops/places on market) vs deployer (integrates) vs **orchestrator** (runs multi-agent pipelines — obligations span both) (K49). We are provider if we ship the system; deploying a third-party model does **not** transfer compliance (K49, K53).

**What auditors ask for** (K52): agent inventory + owners; risk assessment per system; 90-day audit trail; named human-override path with evidence of use; pre-interaction disclosure; data-processing records; accuracy monitoring with detected-regression history.

> **Rule R13:** the design includes Art. 12/14-compatible logging (tamper-evident, ≥6 months) and human-oversight paths **from the architecture**, not retrofitted — plus an AI-disclosure element in every user-facing surface (Art. 50). Audit-readiness is a feature of the activity log (ch. 08 §8.2), not a filing exercise.

## 7.6 Policy-engine implementation (M1 — closed 2026-09-11)

`WELL_SUPPORTED` (K72, K73, K74, K75):

- **Principle**: "LLMs cannot make enforcement decisions" — authorization must be deterministic, versioned, auditable, and explainable after the fact (K75).
- **Engine options**:
  - **Cerbos** — open-source PDP (Go); YAML policies in git; **sub-1ms decisions**; purpose-built for AI-agent/MCP tool-call authorization; RBAC/ABAC/PBAC; agent **kill-switch** (instant revocation); 8 language SDKs; structured decision logs with policy-version lineage; v0.51 (Feb 2026) (K72, K75).
  - **Cedar** — application-level authorization language (AWS); typed entity model → compile-time branch elimination → lower p99 under concurrent multi-tenant load (measured class: ~12 ms vs ~60 ms for OPA-style untyped walks); **dominant policy language in the MCP-enforcement ecosystem** (ToolHive, ScopeBlind protect-mcp, Cedar-for-Agents, IBM ContextForge) (K73, K74).
  - **OPA/Rego** — CNCF-graduated, general-purpose (K8s Gatekeeper); untyped JSON → full-tree walks unless hand-optimized; right for infra policy, heavier for the per-tool-call hot path (K72, K73).
- **Deployment pattern**: policy check on **every tool call** with principal (delegating user) + action (tool + args) + resource (path/scope) + environment signals (cost, risk class); latency budget sub-1ms–few ms on the hot path; every decision logged with policy-version lineage (feeds Art. 12/14, §7.5) (K72, K75).
- **MCP-specific**: enforcement gateways exist that evaluate Cedar/Cerbos policy per MCP tool call and sign decisions as cryptographic receipts (K74).

> **Rule R15:** the permission gate (D3) is implemented as a **Cerbos-class PDP with YAML policies versioned in git**, evaluated on every tool call before sandbox execution — not as prompt text and not as ad-hoc if-statements.

## 7.7 Residual risks (accepted, monitored)

1. Injection can't be fully prevented — accepted, bounded by containment (S22, OWASP).
2. Novel sandbox escapes — mitigated by update discipline + microVM tier + egress allowlists (K54–K58).
3. Compliance interpretation drift (Art. 50 CoP is new) — monitor EU AI Office guidance (K51).
4. Supply-chain attacks via dependencies — pin, verify, sandbox installs (S22).
