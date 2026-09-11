"""Central configuration: paths, provider metadata, model defaults, pricing."""

from pathlib import Path
import json
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WORKSPACE_DIR = BASE_DIR / "workspace"
SETTINGS_FILE = DATA_DIR / "settings.json"
DB_FILE = DATA_DIR / "agent.db"

DEFAULT_PORT = 8000

# ---------------------------------------------------------------------------
# Provider registry (shown in the Settings UI)
# ---------------------------------------------------------------------------
PROVIDERS = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "needs_key": True,
        "env_key": "ANTHROPIC_API_KEY",
        "base_url_placeholder": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-5",
        "models": [
            "claude-sonnet-4-5",
            "claude-sonnet-4-6",
            "claude-opus-4-6",
            "claude-haiku-4-5",
        ],
        "key_hint": "Get a key at console.anthropic.com",
    },
    "openai": {
        "label": "OpenAI-compatible (ChatGPT)",
        "needs_key": True,
        "env_key": "OPENAI_API_KEY",
        "base_url_placeholder": "https://api.openai.com/v1",
        "default_model": "gpt-5.2",
        "models": [
            "gpt-5.2",
            "gpt-5.2-codex",
            "gpt-5-mini",
            "o3",
        ],
        "key_hint": "Get a key at platform.openai.com — any OpenAI-compatible endpoint works (e.g. OpenRouter)",
    },
    "ollama": {
        "label": "Ollama (fully local — no key)",
        "needs_key": False,
        "env_key": "",
        "base_url_placeholder": "http://127.0.0.1:11434",
        "default_model": "llama3.1",
        "models": [
            "llama3.1",
            "qwen2.5:7b",
            "llama3.2",
            "mistral",
        ],
        "key_hint": "Install Ollama from ollama.com, then run: ollama pull llama3.1",
    },
}

DEFAULT_SETTINGS = {
    "provider": "anthropic",
    "api_key": "",
    "base_url": "",
    "model": "",
    "workspace": str(WORKSPACE_DIR),
    "max_iterations": 6,
    "theme": "light",
    "tavily_key": "",
}

# $ per 1M tokens: (input, output) — estimates for the usage footer
PRICING = [
    (("anthropic",), "sonnet", (3.0, 15.0)),
    (("anthropic",), "opus", (5.0, 25.0)),
    (("anthropic",), "haiku", (1.0, 5.0)),
    (("openai",), "gpt-5-mini", (0.5, 2.0)),
    (("openai",), "o3", (10.0, 40.0)),
    (("openai",), "gpt-5", (2.5, 15.0)),
    (("openai",), "gpt-4o", (2.5, 10.0)),
    (("ollama",), "", (0.0, 0.0)),
]


def load_settings() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            saved = {}
        merged = dict(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in saved.items() if k in merged})
        return merged
    return dict(DEFAULT_SETTINGS)


def save_settings(updates: dict) -> dict:
    settings = load_settings()
    for k, v in updates.items():
        if k in settings and v is not None:
            if k == "api_key" and v == "":
                continue  # keep existing key when field left blank
            settings[k] = v
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return settings


def effective_key(provider: str) -> str:
    settings = load_settings()
    key = settings.get("api_key", "")
    if key:
        return key
    env_name = PROVIDERS.get(provider, {}).get("env_key", "")
    if env_name:
        return os.environ.get(env_name, "")
    return ""


def effective_model(provider: str) -> str:
    settings = load_settings()
    return settings.get("model") or PROVIDERS.get(provider, {}).get("default_model", "")


def effective_base_url(provider: str) -> str:
    settings = load_settings()
    return settings.get("base_url") or PROVIDERS.get(provider, {}).get("base_url_placeholder", "")


def get_workspace() -> Path:
    settings = load_settings()
    p = Path(settings.get("workspace") or WORKSPACE_DIR).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


def estimate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    m = (model or "").lower()
    for providers, prefix, (pin, pout) in PRICING:
        if provider in providers and (not prefix or prefix in m):
            return (input_tokens * pin + output_tokens * pout) / 1_000_000
    return 0.0
