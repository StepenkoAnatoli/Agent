# Agent

One system. The research is the core.

## Core Knowledge Base

- **[docs/core/00-INDEX.md](docs/core/00-INDEX.md)** — knowledge map + source register (start here)
- **[docs/core/01-foundations.md](docs/core/01-foundations.md)** — what the system is; the core loop; build decision
- **[docs/core/02-models-economics.md](docs/core/02-models-economics.md)** — models, routing, caching, cost engineering
- **[docs/core/03-context-memory.md](docs/core/03-context-memory.md)** — context engineering, memory tiers, compaction
- **[docs/core/04-tools-protocols.md](docs/core/04-tools-protocols.md)** — tool design (ACI), MCP/A2A, skills
- **[docs/core/05-orchestration-runtime.md](docs/core/05-orchestration-runtime.md)** — multi-agent, frameworks, durable execution, sandboxes
- **[docs/core/06-evaluation-quality.md](docs/core/06-evaluation-quality.md)** — benchmarks, evals, observability, reliability, prompt engineering
- **[docs/core/07-security-compliance.md](docs/core/07-security-compliance.md)** — threat model, injection, MCP security, EU AI Act
- **[docs/core/08-ux-product.md](docs/core/08-ux-product.md)** — agent UX, HITL, distribution, OSS landscape
- **[docs/core/09-gaps-disconfirmation.md](docs/core/09-gaps-disconfirmation.md)** — what we missed, ranked by decision relevance
- **[docs/core/10-operations-pathA.md](docs/core/10-operations-pathA.md)** — Path A playbook: operating the best existing agents for research work

## Companion Research (earlier passes)

- **[DEEP_RESEARCH_REPORT.md](DEEP_RESEARCH_REPORT.md)** — Claude Code · ChatGPT/Codex · Arena.ai analysis + build blueprint
- **[BUGS_FIXES_CHALLENGES.md](BUGS_FIXES_CHALLENGES.md)** — documented bugs, vendor postmortems, failure taxonomy
- **[docs/control-plane.json](docs/control-plane.json)** — machine-readable mission/evidence/validation state

## Status

`RESEARCH_COMPLETE · BUILD_DELIVERED` — on 2026-09-11 the user reversed Path A and directed a build:
*"i want this agent to work on my local pc and it needs to look like claude or chat gpt the simplicity of the design."*
The agent now exists under **[app/](app/)** — a local-PC chat agent with a Claude/ChatGPT-style UI. See **[app/README.md](app/README.md)** for the 3-step Windows setup (or `start.sh` on macOS/Linux).

## The App (app/)

A single system that runs on your computer: Python + FastAPI serving a clean
one-page chat UI at `http://localhost:8000`. Works with **Claude** (Anthropic
API), **ChatGPT** (OpenAI API), or **fully local models** (Ollama, no key). It
streams answers, searches the web, reads files in a workspace folder you pick,
keeps chats in a local SQLite file, and shows token usage and cost per answer.
Everything — settings, keys, chats — stays on your machine. `data/` and
`workspace/` are gitignored, so your key is never committed.
