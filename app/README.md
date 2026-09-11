# Agent — a local AI assistant

A chat agent that runs **on your PC** and looks and feels like Claude or ChatGPT:
clean chat interface, streaming answers, conversation sidebar, dark/light/Claude
themes, and a real agent behind it — it can **search the web** and **read files
from a workspace folder you choose**.

- Works with **Claude** (Anthropic API), **ChatGPT** (OpenAI API or any compatible
  endpoint), or **fully local** models via **Ollama** (no key, no internet needed).
- Everything runs locally; your conversation and settings are stored only on your
  machine. Your API key is sent only to the model provider you pick.

## Run on Windows — 3 steps

1. **Install Python** (once): download from https://www.python.org/downloads/ and
   during install check **"Add python.exe to PATH"**.
2. **Double-click `start.bat`** in this folder.
   - It installs dependencies (first run), starts the server, and opens your
     browser at `http://localhost:8000`.
3. **Configure a provider** — click **Settings** (bottom-left):
   - *Claude:* paste a key from console.anthropic.com (model e.g. `claude-sonnet-4-5`)
   - *ChatGPT:* paste a key from platform.openai.com (model e.g. `gpt-5.2`)
   - *Ollama (free, local):* install Ollama from ollama.com, run
     `ollama pull llama3.1` once, then pick Ollama in Settings — no key needed.

Then just type. The agent answers in the same language you use, can search the web,
and can read files inside the workspace folder (`app/workspace` by default — point
it at any folder, like this repository, in Settings).

## macOS / Linux

```bash
chmod +x start.sh && ./start.sh
```

or manually:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## Expected output / troubleshooting

| You see | What it means | Do this |
|---|---|---|
| Browser opens with the chat | Success — log in via Settings and chat | — |
| `Python was not found` | Python missing or not on PATH | Install from python.org, tick "Add to PATH", run `start.bat` again |
| `Could not install dependencies` | No internet or pip blocked | Check connection; run `pip install -r requirements.txt` in a terminal |
| Red error in chat: "No API key configured" | Provider needs a key | Click **Open Settings** and paste your key |
| Red error: "Could not reach the model server" | Internet down, or (Ollama) Ollama not running | Check connection / start Ollama (`ollama serve`) |
| Port 8000 busy | Another program uses the port | Edit `start.bat`: change `--port 8000` to e.g. `8010` |

## Privacy & security

- Your API key lives in `app/data/settings.json` — **gitignored, never committed**.
  It is only sent to the provider you configured.
- The agent can only read files inside the workspace folder you set; paths outside
  it are refused.
- Web/file content is treated as data, never as instructions (system prompt v1.0).

Design follows the project's research core: `/docs/core/` (tools/ACI, budget
guardrails, provider retry policy, prompt-engineering rules).
