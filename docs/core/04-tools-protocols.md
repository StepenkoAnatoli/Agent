# 04 — TOOLS & PROTOCOLS: The Agent's Interface to the World

## 4.1 Tool descriptions are the highest-leverage prompt surface

`WELL_SUPPORTED` (K44, K46, K45):
- Vague tool descriptions are the **primary driver of tool-selection errors** (K44).
- **Composio: 10× reduction in tool failures** after ACI-style redesign (K46).
- Anthropic `tool_search` + deferred loading: tool-selection accuracy **Opus 4: 49% → 74%; Opus 4.5: 79.5% → 88.1%** (Nov 2025) (K45).
- SWE-agent's documented ACI choices: 100-line constrained file viewer (stops context loss), filename-only search results, linter-before-edit, explicit empty-output messages (K46).

## 4.2 ACI design rules (our tool-authoring standard)

From K44, K46, K47:

1. Verb–noun names (`get_user`, `send_email`), snake_case, English identifiers.
2. **One atomic action per tool.** Multi-purpose tools create ambiguous selection.
3. Description states **purpose, constraints, and side effects upfront** — hidden side effects cause misuse (K44).
4. **When-not-to-use clause** is the most impactful, most-forgotten component (K45).
5. Strong typed schemas: ranges, patterns, enums — eliminates parameter hallucination (K46).
6. Semantic output: return `name` + `file_type`, not `uuid` + `mime_type`; structure output for the agent's *next decision*, not API completeness (K46).
7. Document failure modes and empty states explicitly ("no matches found in src/") — silent empty returns read as tool bugs (K46).
8. Cap tool returns (~25K tokens Anthropic guideline; hard caps in harness) (K45).
9. Evaluate every tool definition as a context-budget item (K46).

> **Rule R5:** a tool ships only with (a) a description an onboarding engineer could act on without asking questions, (b) schema validation, (c) explicit empty/error states, (d) a when-not-to-use clause. Tool descriptions are versioned with the system prompt and eval-gated (bugs report §11.1 — vendor process fix).

## 4.3 MCP — the connector standard

`ESTABLISHED_FACT` (K10, K13, K14):
- Created by Anthropic (Nov 2024), JSON-RPC 2.0; now governed by the **Agentic AI Foundation under the Linux Foundation** (K10).
- Scale: **97M+ monthly SDK downloads, 10,000+ public servers** (Anthropic, Dec 9, 2025) (K10).
- Primitives: **tools, resources, prompts** (K11). MCP = agent↔tool/data; **A2A** (Google, Apr 2025) = agent↔agent; both co-governed (K10). Also in the survey: ACP and ANP (K12).
- OpenAI migrated from Assistants API toward MCP (2025); function calling is the legacy single-vendor pattern (K10).

**Security posture (the reason MCP is ch. 07 territory):** MCP does **not** enforce authn/authz/input validation at the protocol level (K11). NSA (May 2026): no RBAC at instantiation, weak audit requirements, serialization risks, "security posture depends on implementation discipline rather than protocol guarantees" (K13). Empirical: 7.2% of sampled servers had general vulns, 5.5% MCP-specific (tool poisoning); client defense ranged **0% (Cursor) to 100% (Claude Desktop)** attack success (K14). Full threat detail in ch. 07 §7.3.

> **Rule R6:** we ship an MCP **client** (for interoperability) but every server connection is allowlisted, its tool metadata treated as untrusted input, and its actions pass through our deterministic permission gate. MCP server execution is sandboxed like any other tool.

## 4.4 AGENTS.md / skills / hooks — the knowledge layer

- **AGENTS.md**: OpenAI's counterpart to CLAUDE.md — persistent project instructions (S4).
- **Skills** (SKILL.md folders): passive procedural knowledge loaded on invocation; the composition rule: *MCP gives the ability to call a system; the skill teaches how and when to use it well* (S1). Design principles from Anthropic's reference finance agents (S-source, Medium synthesis): skills are **passive** (no sequencing logic), authored once/syndicated, with deliverables-not-goals in the consuming agent prompt.
- **Hooks**: deterministic scripts on events (post-edit lint, pre-tool policies) — the place where policy lives *outside* the model's negotiation (S1, S5).

## 4.5 AG-UI / A2UI — the frontend protocol layer

For the browser surface: AG-UI event streaming (tool-call events to the UI in real time) is the emerging standard for agent frontends; A2UI for generative UI (K59). Streaming every tool invocation "dramatically improves user trust" (K59) — a requirement for our UX (ch. 08).

## 4.6 Our tool catalog v1 (evidence-derived)

Core (always loaded, ≤7): `read_file`, `write_file`/`edit_file`, `bash` (sandboxed), `web_search`, `fetch_page`, `ask_user`, `todo_write` (state). Deferred/discoverable: git operations, file search, test runner, MCP tools, skill invocations. Each conforms to Rule R5. The permission gate wraps every mutating tool (ch. 07).
