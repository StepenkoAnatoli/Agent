"""Agent tools: web search and workspace-scoped file access.

Tool descriptions follow the ACI rules from the research core (docs/core/04):
one atomic action each, stated side effects, when-not-to-use clauses,
explicit empty/error states, capped outputs.
"""

import html as html_mod
import re

import httpx

from config import get_workspace

MAX_FILE_CHARS = 60_000
MAX_FILE_LINES = 1000

TOOL_DEFS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for current information. Returns up to 5 results with "
            "title, URL and a short snippet. Use this when you need up-to-date facts, "
            "news, prices, or anything beyond your training data. Do NOT use it for "
            "common knowledge, pure reasoning, or code questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query, 2-8 words."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": (
            "Read a text file from the user's workspace folder. Returns the file "
            "content (truncated if very large). Use when the user asks about a file "
            "or when you need its contents. Do NOT use for files outside the workspace — "
            "you cannot access them."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file, relative to the workspace folder or absolute inside it.",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_dir",
        "description": (
            "List files and folders in a directory of the user's workspace. Use to "
            "explore what files exist before reading them. Do NOT use outside the workspace."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to the workspace. Use '.' for the workspace root.",
                }
            },
            "required": ["path"],
        },
    },
]


def _resolve_in_workspace(path: str):
    """Resolve a user-supplied path and enforce it stays inside the workspace."""
    ws = get_workspace()
    try:
        p = (ws / path).resolve()
    except Exception:
        raise PermissionError("Invalid path.")
    if p != ws and ws not in p.parents:
        raise PermissionError(
            f"Access denied: '{path}' is outside the workspace ({ws}). "
            "You can change the workspace folder in Settings."
        )
    return p


def _strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


async def web_search(query: str) -> dict:
    """Keyless search via DuckDuckGo Lite HTML endpoint. Graceful on failure."""
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=12.0) as client:
            resp = await client.post(url, data={"q": query}, headers=headers)
        if resp.status_code != 200:
            return {
                "ok": False,
                "summary": "Search failed",
                "result": f"Search returned HTTP {resp.status_code}. Try again later.",
            }
        page = resp.text
    except Exception as e:
        return {
            "ok": False,
            "summary": "Search failed",
            "result": f"Could not reach the search engine ({type(e).__name__}). "
            "Check your internet connection and try again.",
        }

    link_matches = re.findall(
        r'<a[^>]*class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S
    )
    snippet_matches = re.findall(
        r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>', page, re.S
    )
    results = []
    for i, (href, title) in enumerate(link_matches[:5]):
        snippet = _strip_tags(snippet_matches[i]) if i < len(snippet_matches) else ""
        results.append({"title": _strip_tags(title), "url": href, "snippet": snippet[:280]})

    if not results:
        return {
            "ok": True,
            "summary": "No results found",
            "result": f"No search results for: {query}. Try rewording the query.",
        }

    text = "\n\n".join(f"{i+1}. {r['title']}\n   {r['url']}\n   {r['snippet']}" for i, r in enumerate(results))
    return {
        "ok": True,
        "summary": f"{len(results)} results for “{query}”",
        "result": f"Search results for “{query}”:\n\n{text}",
    }


def read_file(path: str) -> dict:
    try:
        p = _resolve_in_workspace(path)
    except PermissionError as e:
        return {"ok": False, "summary": "Access denied", "result": str(e)}
    if not p.exists():
        return {"ok": False, "summary": "File not found", "result": f"No file at: {path}"}
    if p.is_dir():
        return {"ok": False, "summary": "Is a directory", "result": f"'{path}' is a directory. Use list_dir instead."}
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "summary": "Read failed", "result": f"Could not read {path}: {e}"}
    lines = content.splitlines()
    if len(lines) > MAX_FILE_LINES or len(content) > MAX_FILE_CHARS:
        content = "\n".join(lines[:MAX_FILE_LINES])[:MAX_FILE_CHARS]
        content += "\n\n[... file truncated — it is larger than the readable limit ...]"
    return {
        "ok": True,
        "summary": f"Read {p.name} ({len(lines)} lines)",
        "result": content,
    }


def list_dir(path: str) -> dict:
    try:
        p = _resolve_in_workspace(path)
    except PermissionError as e:
        return {"ok": False, "summary": "Access denied", "result": str(e)}
    if not p.exists():
        return {"ok": False, "summary": "Not found", "result": f"No directory at: {path}"}
    if not p.is_dir():
        return {"ok": False, "summary": "Not a directory", "result": f"'{path}' is a file. Use read_file instead."}
    entries = []
    for child in sorted(p.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            entries.append(f"[dir]  {child.name}/")
        else:
            try:
                size = child.stat().st_size
            except OSError:
                size = 0
            entries.append(f"       {child.name}  ({size:,} bytes)")
    if not entries:
        return {"ok": True, "summary": "Empty directory", "result": f"'{path or '.'}' is empty."}
    return {
        "ok": True,
        "summary": f"{len(entries)} entries in “{path or '.'}”",
        "result": "\n".join(entries),
    }


TOOL_EXECUTORS = {
    "web_search": web_search,
    "read_file": read_file,
    "list_dir": list_dir,
}


async def execute_tool(name: str, args: dict) -> dict:
    executor = TOOL_EXECUTORS.get(name)
    if executor is None:
        return {"ok": False, "summary": "Unknown tool", "result": f"No tool named '{name}'."}
    try:
        result = executor(**args)
        if hasattr(result, "__await__"):
            result = await result
        return result
    except TypeError as e:
        return {"ok": False, "summary": "Bad arguments", "result": f"Invalid arguments for {name}: {e}"}
    except Exception as e:
        return {"ok": False, "summary": "Tool error", "result": f"{name} failed: {type(e).__name__}: {e}"}
