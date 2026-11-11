#!/usr/bin/env python3
"""
J.A.R.V.I.S 24/7 Autonomous $0 Telegram Voice & Background Task Agent
======================================================================
Runs 24/7 on Render Free (+ UptimeRobot ping, no card) OR Oracle Cloud Always Free (no sleep).
Core runs with Python 3 standard library only! (Optional: `pip install edge-tts` for spoken replies).

100% Free-Tier Stack ($0/month):
- Messaging & Voice Notes: Telegram Bot API (@BotFather)
- Speech-to-Text: Groq Whisper (whisper-large-v3-turbo) or Gemini 2.5 Flash audio
- Text-to-Speech: Microsoft Edge Neural Voices via edge-tts (ar-AE-HamdanNeural / en-US-AndrewNeural)
- Multi-Brain LLM Pool (automatic failover — practically never runs out!):
  1. Google Gemini (gemini-2.5-flash / gemini-2.5-pro)
  2. Mistral AI (~1 Billion tokens/month free: mistral-large-latest -> mistral-small-latest)
  3. Groq (llama-3.3-70b-versatile / openai/gpt-oss-120b)
  4. NVIDIA NIM (meta/llama-3.3-70b-instruct or custom model)
  5. OpenRouter Free Router (openrouter/free)
- Autonomous Background Worker: Give Jarvis a heavy task, keep chatting normally;
  he executes web search + site audits + analysis in a background thread and rings/messages
  you on Telegram when done or when he needs your decision!
- Outbound Telegram Phone Ring: CallMeBot API (free personal setup)
- Optional Cloud Memory Persistence: Private GitHub Gist sync (survives Render free restarts!)
"""

import asyncio
import base64
import csv
import datetime as dt
import html
import http.server
import json
import logging
import os
import re
import socketserver
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, unquote, urlencode, urlparse

try:
    import edge_tts
except ImportError:
    edge_tts = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("jarvis")

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "jarvis_state.json"
STATE_LOCK = threading.Lock()


def load_dotenv_simple(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


load_dotenv_simple(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_TELEGRAM_ID = os.getenv("ALLOWED_TELEGRAM_ID", "").strip()

# Free LLM API Keys (add 1 or all 5 for near-unlimited failover!)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

# Optional free Web Search (Tavily 1,000/mo free; falls back to DuckDuckGo HTML automatically)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

# Optional voice & Telegram ringing
ENABLE_VOICE_REPLIES = os.getenv("ENABLE_VOICE_REPLIES", "true").lower() == "true"
ARABIC_VOICE = os.getenv("ARABIC_VOICE", "ar-AE-HamdanNeural")
ENGLISH_VOICE = os.getenv("ENGLISH_VOICE", "en-US-AndrewNeural")
CALLMEBOT_TELEGRAM_USER = os.getenv("CALLMEBOT_TELEGRAM_USER", "").strip()

# Optional GitHub Gist cloud state persistence (keeps memory safe across Render free restarts)
GITHUB_GIST_ID = os.getenv("GITHUB_GIST_ID", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

# Optional HTTP health server port (Render sets PORT automatically, e.g. 10000)
HEALTH_PORT = os.getenv("PORT", "").strip()

_raw_csv = os.getenv("LEADS_CSV_PATH", str(BASE_DIR.parent / "dubai_high_ticket_leads.csv"))
LEADS_CSV_PATH = Path(_raw_csv)
if not LEADS_CSV_PATH.is_absolute():
    LEADS_CSV_PATH = (BASE_DIR / LEADS_CSV_PATH).resolve()

_GIST_BOOTSTRAPPED = False


# ---------------------------------------------------------------------------
# Stdlib HTTP Helpers
# ---------------------------------------------------------------------------
def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Any] = None,
    form_data: Optional[Dict[str, Any]] = None,
    raw_body: Optional[bytes] = None,
    timeout: int = 35,
) -> Tuple[int, bytes, str]:
    req_headers = {"User-Agent": "JarvisAgent/2.0"}
    if headers:
        req_headers.update(headers)
    data: Optional[bytes] = raw_body
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    elif form_data is not None:
        data = urlencode(form_data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), url


def http_multipart(
    url: str,
    fields: Dict[str, str],
    file_field: str,
    file_path: Path,
    mime_type: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 45,
) -> Tuple[int, bytes]:
    boundary = f"----JarvisBoundary{uuid.uuid4().hex}"
    parts: List[bytes] = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8"))

    file_bytes = file_path.read_bytes()
    parts.append(f"--{boundary}\r\n".encode("utf-8"))
    parts.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8")
    )
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req_headers = dict(headers or {})
    req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    status, resp_bytes, _ = http_request(url, method="POST", headers=req_headers, raw_body=body, timeout=timeout)
    return status, resp_bytes


# ---------------------------------------------------------------------------
# Thread-Safe Persistent State (+ Optional Free GitHub Gist Sync)
# ---------------------------------------------------------------------------
def _default_state() -> Dict[str, Any]:
    return {"memories": {}, "reminders": [], "history": [], "lead_notes": {}, "tasks": []}


def _gist_sync_push(raw_json: str) -> None:
    if not (GITHUB_GIST_ID and GITHUB_TOKEN):
        return
    try:
        http_request(
            f"https://api.github.com/gists/{GITHUB_GIST_ID}",
            method="PATCH",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json_body={"files": {"jarvis_state.json": {"content": raw_json}}},
            timeout=15,
        )
    except Exception as e:
        log.warning("Gist sync push skipped: %s", e)


def _gist_bootstrap_pull() -> Optional[Dict[str, Any]]:
    if not (GITHUB_GIST_ID and GITHUB_TOKEN):
        return None
    try:
        status, body, _ = http_request(
            f"https://api.github.com/gists/{GITHUB_GIST_ID}",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            timeout=15,
        )
        if status == 200:
            content = json.loads(body.decode("utf-8")).get("files", {}).get("jarvis_state.json", {}).get("content")
            if content:
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    return parsed
    except Exception as e:
        log.warning("Gist bootstrap pull failed: %s", e)
    return None


def load_state() -> Dict[str, Any]:
    global _GIST_BOOTSTRAPPED
    with STATE_LOCK:
        if not _GIST_BOOTSTRAPPED:
            _GIST_BOOTSTRAPPED = True
            if not STATE_FILE.exists():
                remote = _gist_bootstrap_pull()
                if remote:
                    STATE_FILE.write_text(json.dumps(remote, ensure_ascii=False, indent=2), encoding="utf-8")
                    return remote
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                for k, v in _default_state().items():
                    data.setdefault(k, v)
                return data
            except Exception:
                pass
        return _default_state()


def save_state(state: Dict[str, Any]) -> None:
    raw = json.dumps(state, ensure_ascii=False, indent=2)
    with STATE_LOCK:
        STATE_FILE.write_text(raw, encoding="utf-8")
    if GITHUB_GIST_ID and GITHUB_TOKEN:
        threading.Thread(target=_gist_sync_push, args=(raw,), daemon=True).start()


# ---------------------------------------------------------------------------
# Built-in Autonomous Tools
# ---------------------------------------------------------------------------
def tool_list_leads(limit: int = 12, status_filter: str = "") -> Dict[str, Any]:
    if not LEADS_CSV_PATH.exists():
        return {"error": f"CSV not found at {LEADS_CSV_PATH}"}
    state = load_state()
    notes = state.get("lead_notes", {})
    rows = []
    with LEADS_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Business Name") or row.get("name") or ""
            st = notes.get(name, {}).get("status", "new")
            if status_filter and st != status_filter:
                continue
            row["local_status"] = st
            rows.append(row)
    return {"total": len(rows), "leads": rows[: max(1, min(limit, 25))]}


def tool_update_lead(business_name: str, status: str, note: str = "") -> Dict[str, Any]:
    state = load_state()
    state.setdefault("lead_notes", {})[business_name] = {
        "status": status,
        "note": note,
        "updated_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    save_state(state)
    return {"ok": True, "business_name": business_name, "status": status}


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_h1 = False
        self.skip_tag = False
        self.title_parts: List[str] = []
        self.h1_parts: List[str] = []
        self.h1s: List[str] = []
        self.cur_a_href: Optional[str] = None
        self.cur_a_text: List[str] = []
        self.links: List[Tuple[str, str]] = []
        self.text_parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        attr_map = dict(attrs)
        if t in ("script", "style", "noscript"):
            self.skip_tag = True
        elif t == "title":
            self.in_title = True
        elif t == "h1":
            self.in_h1 = True
            self.h1_parts = []
        elif t == "a" and "href" in attr_map:
            self.cur_a_href = (attr_map["href"] or "").strip()
            self.cur_a_text = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in ("script", "style", "noscript"):
            self.skip_tag = False
        elif t == "title":
            self.in_title = False
        elif t == "h1":
            self.in_h1 = False
            h = " ".join("".join(self.h1_parts).split())
            if h:
                self.h1s.append(h)
        elif t == "a" and self.cur_a_href is not None:
            label = " ".join("".join(self.cur_a_text).split())[:60]
            self.links.append((self.cur_a_href, label))
            self.cur_a_href = None

    def handle_data(self, data: str) -> None:
        if self.skip_tag:
            return
        if self.in_title:
            self.title_parts.append(data)
        if self.in_h1:
            self.h1_parts.append(data)
        if self.cur_a_href is not None:
            self.cur_a_text.append(data)
        self.text_parts.append(data)


def audit_html_content(url: str, raw_html: str) -> Dict[str, Any]:
    parser = AuditParser()
    parser.feed(raw_html)
    title = " ".join("".join(parser.title_parts).split())[:160]
    body_text = " ".join(" ".join(parser.text_parts).split())

    dead_hash_ctas = []
    wa_links = []
    broken_wa_links = []
    tel_links = []
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw_html)))[:8]

    for href, label in parser.links:
        low = href.lower()
        if href in ("#", "/#", "/en/#") or low.endswith("/#"):
            if label:
                dead_hash_ctas.append({"text": label, "href": href})
        if "wa.me/" in low or "whatsapp.com/send" in low:
            wa_links.append(href)
            if "wa.me/00" in low or "wa.me/+" in low or "%20" in low or " " in href:
                broken_wa_links.append(href)
        if low.startswith("tel:"):
            tel_links.append(href)

    zero_counters = re.findall(r"(?:0\+|Years[^0-9]{0,15}0\b|Rating[^0-9]{0,10}0\b)", body_text, re.IGNORECASE)
    has_arabic = bool(re.search(r"[\u0600-\u06FF]", body_text))

    return {
        "url": url,
        "title": title,
        "h1": parser.h1s[:5],
        "has_arabic_content": has_arabic,
        "dead_hash_ctas": dead_hash_ctas[:8],
        "whatsapp_links": wa_links[:6],
        "broken_whatsapp_links": broken_wa_links[:6],
        "tel_links": tel_links[:6],
        "emails_found": emails,
        "suspicious_zero_counters": zero_counters[:6],
        "snippet": body_text[:700],
    }


def tool_audit_website(url: str) -> Dict[str, Any]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {"error": "Invalid URL. Must start with http:// or https://"}
    host = (parsed.hostname or "").lower()
    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or host.startswith(("10.", "192.168.", "169.254.")):
        return {"error": "Refused private/local network address."}
    try:
        status, body, final_url = http_request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; JarvisAuditor/2.0)"},
            timeout=15,
        )
        raw_html = body.decode("utf-8", errors="replace")
        report = audit_html_content(final_url, raw_html)
        report["http_status"] = status
        return report
    except Exception as e:
        return {"error": f"Failed to fetch {url}: {e}"}


def parse_duckduckgo_html(raw_html: str, max_results: int = 5) -> List[Dict[str, str]]:
    results = []
    blocks = re.findall(
        r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?(?:<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>|<div[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</div>)',
        raw_html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for raw_href, raw_title, snip1, snip2 in blocks[:max_results]:
        href = html.unescape(raw_href)
        if "uddg=" in href:
            qs = parse_qs(urlparse(href).query)
            if "uddg" in qs:
                href = unquote(qs["uddg"][0])
        title = re.sub(r"<[^>]+>", "", html.unescape(raw_title)).strip()
        snippet = re.sub(r"<[^>]+>", "", html.unescape(snip1 or snip2 or "")).strip()
        results.append({"title": title, "url": href, "snippet": snippet[:300]})
    return results


def tool_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    q = query.strip()
    if not q:
        return {"error": "Empty query"}
    if TAVILY_API_KEY:
        try:
            status, body, _ = http_request(
                "https://api.tavily.com/search",
                method="POST",
                json_body={"api_key": TAVILY_API_KEY, "query": q, "max_results": max_results},
                timeout=20,
            )
            if status == 200:
                res = json.loads(body.decode("utf-8")).get("results", [])
                return {
                    "source": "tavily",
                    "results": [{"title": r.get("title"), "url": r.get("url"), "snippet": (r.get("content") or "")[:350]} for r in res],
                }
        except Exception as e:
            log.warning("Tavily search error: %s", e)

    try:
        status, body, _ = http_request(
            "https://html.duckduckgo.com/html/",
            method="POST",
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"},
            form_data={"q": q},
            timeout=20,
        )
        if status == 200:
            parsed = parse_duckduckgo_html(body.decode("utf-8", errors="replace"), max_results=max_results)
            return {"source": "duckduckgo", "results": parsed}
        return {"error": f"Search status {status}"}
    except Exception as e:
        return {"error": f"Web search error: {e}"}


def tool_save_memory(key: str, value: str) -> Dict[str, Any]:
    state = load_state()
    state.setdefault("memories", {})[key.strip()] = {
        "value": value.strip(),
        "saved_at": dt.datetime.utcnow().isoformat() + "Z",
    }
    save_state(state)
    return {"ok": True, "key": key}


def tool_get_memories() -> Dict[str, Any]:
    return load_state().get("memories", {})


def tool_schedule_reminder(minutes_from_now: float, message: str, call_me: bool = False) -> Dict[str, Any]:
    mins = max(0.1, float(minutes_from_now))
    due_ts = time.time() + mins * 60.0
    state = load_state()
    state.setdefault("reminders", []).append({
        "id": f"rem_{int(time.time()*1000)}",
        "due_ts": due_ts,
        "message": message.strip(),
        "call_me": bool(call_me),
        "done": False,
    })
    save_state(state)
    due_str = dt.datetime.fromtimestamp(due_ts).strftime("%Y-%m-%d %H:%M:%S")
    return {"ok": True, "due_local_time": due_str, "call_me": bool(call_me)}


def trigger_callmebot_telegram_ring(text: str) -> Dict[str, Any]:
    if not CALLMEBOT_TELEGRAM_USER:
        return {"ok": False, "error": "CALLMEBOT_TELEGRAM_USER not configured in .env"}
    clean = re.sub(r"\s+", " ", text).strip()[:250]
    url = (
        f"http://api.callmebot.com/start.php?user={quote_plus(CALLMEBOT_TELEGRAM_USER)}"
        f"&text={quote_plus(clean)}&lang=en-US-Standard-B&rpt=2&cc=yes"
    )
    try:
        status, body, _ = http_request(url, timeout=20)
        return {"ok": status == 200, "status": status, "response": body.decode("utf-8", errors="replace")[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_list_tasks() -> Dict[str, Any]:
    return {"tasks": load_state().get("tasks", [])[-10:]}


# ---------------------------------------------------------------------------
# Background Autonomous Task Runner
# ---------------------------------------------------------------------------
def _background_task_worker(task_id: str, goal: str, call_when_done: bool, chat_id: int) -> None:
    log.info("Background worker started %s: %s", task_id, goal)
    state = load_state()
    for t in state.get("tasks", []):
        if t.get("id") == task_id:
            t["status"] = "running"
    save_state(state)

    memories = state.get("memories", {})
    worker_prompt = (
        f"[BACKGROUND MISSION {task_id}]\n"
        f"Saved Memories: {json.dumps(memories, ensure_ascii=False)}\n"
        f"Mission from user: {goal}\n"
        "Execute this completely using your tools (web_search, audit_website, list_leads, save_memory, etc.). "
        "If you genuinely hit a point where you need the user's permission or decision before proceeding, explain clearly what you need and call `call_me_now` too. "
        "Otherwise finish the task thoroughly and return a crisp Arabic report."
    )
    msgs = [{"role": "user", "content": worker_prompt}]
    final_report = ""
    had_error = False

    try:
        for _ in range(6):
            reply = ask_free_llm(msgs, system_prompt=WORKER_SYSTEM_PROMPT)
            tool_call = extract_tool_call(reply)
            if not tool_call:
                final_report = reply
                break
            t_name = str(tool_call.get("tool", ""))
            t_args = tool_call.get("args") or {}
            log.info("[%s] Tool %s(%s)", task_id, t_name, t_args)
            res = dispatch_tool(t_name, t_args, chat_id=chat_id, allow_bg=False)
            msgs.append({"role": "assistant", "content": reply})
            msgs.append({
                "role": "user",
                "content": f"[TOOL RESULT for {t_name}]: {json.dumps(res, ensure_ascii=False)[:6500]}\nContinue your background mission or produce the final Arabic summary.",
            })
        else:
            final_report = ask_free_llm(msgs, system_prompt=WORKER_SYSTEM_PROMPT)
    except Exception as e:
        had_error = True
        final_report = f"توقفت المهمة {task_id} بسبب خطأ تقني: {e}"

    state = load_state()
    for t in state.get("tasks", []):
        if t.get("id") == task_id:
            t["status"] = "failed" if had_error else "done"
            t["finished_at"] = dt.datetime.utcnow().isoformat() + "Z"
            t["summary"] = final_report[:500]
    save_state(state)

    if TELEGRAM_BOT_TOKEN and chat_id:
        header = f"🤖 **انتهت مهمة الخلفية ({task_id})**:\n{goal}\n\n"
        send_telegram_reply(chat_id, header + final_report, want_voice=True)
        if call_when_done and CALLMEBOT_TELEGRAM_USER:
            trigger_callmebot_telegram_ring(f"Jarvis finished task {task_id}. Check Telegram for the full report.")


def tool_start_background_task(goal: str, call_when_done: bool = True, chat_id: int = 0) -> Dict[str, Any]:
    task_id = f"task_{int(time.time()) % 100000}"
    state = load_state()
    state.setdefault("tasks", []).append({
        "id": task_id,
        "goal": goal.strip(),
        "status": "queued",
        "call_when_done": bool(call_when_done),
        "created_at": dt.datetime.utcnow().isoformat() + "Z",
    })
    state["tasks"] = state["tasks"][-25:]
    save_state(state)

    if chat_id:
        threading.Thread(
            target=_background_task_worker,
            args=(task_id, goal.strip(), bool(call_when_done), chat_id),
            daemon=True,
        ).start()
    return {"ok": True, "task_id": task_id, "status": "started_in_background", "call_when_done": bool(call_when_done)}


def dispatch_tool(name: str, args: Dict[str, Any], chat_id: int = 0, allow_bg: bool = True) -> Dict[str, Any]:
    if name == "list_leads":
        return tool_list_leads(int(args.get("limit", 12)), str(args.get("status_filter", "")))
    if name == "update_lead":
        return tool_update_lead(str(args.get("business_name", "")), str(args.get("status", "sent")), str(args.get("note", "")))
    if name == "audit_website":
        return tool_audit_website(str(args.get("url", "")))
    if name == "web_search":
        return tool_web_search(str(args.get("query", "")), int(args.get("max_results", 5)))
    if name == "save_memory":
        return tool_save_memory(str(args.get("key", "")), str(args.get("value", "")))
    if name == "get_memories":
        return tool_get_memories()
    if name == "list_tasks":
        return tool_list_tasks()
    if name == "schedule_reminder":
        return tool_schedule_reminder(args.get("minutes_from_now", 60), str(args.get("message", "")), bool(args.get("call_me", False)))
    if name == "call_me_now":
        return trigger_callmebot_telegram_ring(str(args.get("message", "Jarvis needs your attention on Telegram")))
    if name == "start_background_task":
        if not allow_bg:
            return {"error": "Already inside background task"}
        return tool_start_background_task(str(args.get("goal", "")), bool(args.get("call_when_done", True)), chat_id=chat_id)
    return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Multi-Provider Free LLM Router (Gemini -> Mistral 1B/mo -> Groq -> NIM -> OpenRouter)
# ---------------------------------------------------------------------------
BASE_TOOLS_DOC = """Available tools (to call one, reply ONLY with a valid raw JSON object: {"tool": "<name>", "args": {...}}):
1. web_search: {"query": "...", "max_results": 5} -> searches the live internet via Tavily/DuckDuckGo.
2. audit_website: {"url": "https://..."} -> fetches live site HTML and inspects broken # links, broken wa.me links, emails, tel links, 0-counters, and Arabic support.
3. list_leads: {"limit": 12, "status_filter": ""} -> reads Dubai high-ticket prospects CSV and statuses.
4. update_lead: {"business_name": "...", "status": "sent|interested|won|new", "note": "..."} -> saves CRM update.
5. save_memory: {"key": "...", "value": "..."} -> permanently stores facts/preferences.
6. get_memories: {} -> reads saved memories.
7. schedule_reminder: {"minutes_from_now": 2880, "message": "...", "call_me": true} -> sets a proactive timer; messages Telegram and rings via CallMeBot if call_me=true.
8. call_me_now: {"message": "..."} -> immediately rings the user's Telegram via CallMeBot (use short English ASCII text <=240 chars so TTS reads cleanly).
9. list_tasks: {} -> lists recent background tasks."""

SYSTEM_PROMPT = f"""You are J.A.R.V.I.S, a 24/7 autonomous AI co-pilot working at $0 cost.
Respond in clear, crisp Arabic (or English if the user writes in English).
{BASE_TOOLS_DOC}
10. start_background_task: {{"goal": "...", "call_when_done": true}} -> use this whenever the user gives a multi-step / heavy / research / "work in the background and call me" task so it runs asynchronously without blocking chat!

Once you have all facts (or after launching a background task), answer directly in clean plain text without JSON."""

WORKER_SYSTEM_PROMPT = f"""You are J.A.R.V.I.S Background Worker executing a multi-step autonomous mission.
{BASE_TOOLS_DOC}
Execute tools step by step until complete, then produce a sharp Arabic report. If you truly require a user decision, say so clearly and optionally invoke call_me_now."""


def call_gemini(messages: List[Dict[str, str]], system_prompt: str, model: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    convo_text = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": convo_text}]}],
        "generationConfig": {"temperature": 0.4},
    }
    status, body, _ = http_request(url, method="POST", json_body=payload, timeout=55)
    if status != 200:
        log.warning("Gemini (%s) failed (%s): %s", model, status, body.decode("utf-8", errors="replace")[:200])
        return None
    data = json.loads(body.decode("utf-8"))
    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")


def call_openai_compatible(url: str, key: str, model: str, messages: List[Dict[str, str]], system_prompt: str, extra_headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}"}
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.4,
    }
    status, body, _ = http_request(url, method="POST", headers=headers, json_body=payload, timeout=55)
    if status != 200:
        log.warning("Provider %s (%s) failed (%s): %s", url, model, status, body.decode("utf-8", errors="replace")[:200])
        return None
    data = json.loads(body.decode("utf-8"))
    return data.get("choices", [{}])[0].get("message", {}).get("content")


def ask_free_llm(messages: List[Dict[str, str]], system_prompt: str = SYSTEM_PROMPT) -> str:
    providers = [
        lambda: call_gemini(messages, system_prompt, GEMINI_MODEL),
        lambda: call_gemini(messages, system_prompt, "gemini-2.5-flash") if GEMINI_MODEL != "gemini-2.5-flash" else None,
        lambda: call_openai_compatible("https://api.mistral.ai/v1/chat/completions", MISTRAL_API_KEY, MISTRAL_MODEL, messages, system_prompt),
        lambda: call_openai_compatible("https://api.mistral.ai/v1/chat/completions", MISTRAL_API_KEY, "mistral-small-latest", messages, system_prompt) if MISTRAL_MODEL != "mistral-small-latest" else None,
        lambda: call_openai_compatible("https://api.groq.com/openai/v1/chat/completions", GROQ_API_KEY, GROQ_MODEL, messages, system_prompt),
        lambda: call_openai_compatible("https://integrate.api.nvidia.com/v1/chat/completions", NVIDIA_API_KEY, NVIDIA_MODEL, messages, system_prompt),
        lambda: call_openai_compatible(
            "https://openrouter.ai/api/v1/chat/completions",
            OPENROUTER_API_KEY,
            "openrouter/free",
            messages,
            system_prompt,
            {"X-Title": "Jarvis 24/7 Agent"},
        ),
    ]
    for fn in providers:
        try:
            ans = fn()
            if ans:
                return ans.strip()
        except Exception as e:
            log.warning("LLM provider error: %s", e)
    return "لم ينجح أي مزود ذكاء حالياً — أضف مفتاحاً واحداً على الأقل في المتغيرات (GEMINI_API_KEY / MISTRAL_API_KEY / GROQ_API_KEY / NVIDIA_API_KEY / OPENROUTER_API_KEY)."


def extract_tool_call(text: str) -> Optional[Dict[str, Any]]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()
    if not (cleaned.startswith("{") and cleaned.endswith("}")):
        return None
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "tool" in obj:
            return obj
    except Exception:
        return None
    return None


def run_agent_turn(user_text: str, chat_id: int) -> str:
    state = load_state()
    memories = state.get("memories", {})
    history = state.get("history", [])[-10:]

    mem_prefix = ""
    if memories:
        mem_prefix = "[Saved Memories: " + json.dumps(memories, ensure_ascii=False) + "]\n"

    working_msgs = list(history) + [{"role": "user", "content": mem_prefix + user_text}]
    final_reply = ""

    for _ in range(4):
        reply = ask_free_llm(working_msgs, system_prompt=SYSTEM_PROMPT)
        tool_call = extract_tool_call(reply)
        if not tool_call:
            final_reply = reply
            break
        t_name = str(tool_call.get("tool", ""))
        t_args = tool_call.get("args") or {}
        log.info("Executing tool %s with args %s", t_name, t_args)
        result = dispatch_tool(t_name, t_args, chat_id=chat_id, allow_bg=True)
        working_msgs.append({"role": "assistant", "content": reply})
        working_msgs.append({
            "role": "user",
            "content": f"[TOOL RESULT for {t_name}]: {json.dumps(result, ensure_ascii=False)[:6000]}\nNow synthesize a helpful final answer for the user (or call another tool if needed).",
        })
    else:
        final_reply = ask_free_llm(working_msgs, system_prompt=SYSTEM_PROMPT)

    state = load_state()
    state.setdefault("history", []).extend([
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": final_reply},
    ])
    state["history"] = state["history"][-20:]
    save_state(state)
    return final_reply


# ---------------------------------------------------------------------------
# Voice STT & TTS ($0)
# ---------------------------------------------------------------------------
def transcribe_audio_file(file_path: Path) -> Optional[str]:
    if GROQ_API_KEY:
        try:
            status, body = http_multipart(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                fields={"model": "whisper-large-v3-turbo"},
                file_field="file",
                file_path=file_path,
                mime_type="audio/ogg",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            )
            if status == 200:
                txt = json.loads(body.decode("utf-8")).get("text", "").strip()
                if txt:
                    return txt
        except Exception as e:
            log.warning("Groq Whisper error: %s", e)

    if GEMINI_API_KEY:
        try:
            b64 = base64.b64encode(file_path.read_bytes()).decode("ascii")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"text": "Transcribe this voice message verbatim in its original language (Arabic or English). Output ONLY the transcription."},
                        {"inlineData": {"mimeType": "audio/ogg", "data": b64}},
                    ],
                }]
            }
            status, body, _ = http_request(url, method="POST", json_body=payload, timeout=45)
            if status == 200:
                return json.loads(body.decode("utf-8")).get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        except Exception as e:
            log.warning("Gemini STT fallback error: %s", e)
    return None


async def _make_tts_mp3(text: str, out_path: Path) -> None:
    has_arabic = bool(re.search(r"[\u0600-\u06FF]", text))
    voice = ARABIC_VOICE if has_arabic else ENGLISH_VOICE
    clean = re.sub(r"[*_`#<>]", "", text)[:1200]
    comm = edge_tts.Communicate(clean, voice)
    await comm.save(str(out_path))


def synthesize_speech(text: str) -> Optional[Path]:
    if not ENABLE_VOICE_REPLIES or edge_tts is None:
        return None
    try:
        tmp = Path(tempfile.gettempdir()) / f"jarvis_tts_{int(time.time()*1000)}.mp3"
        asyncio.run(_make_tts_mp3(text, tmp))
        if tmp.exists() and tmp.stat().st_size > 100:
            return tmp
    except Exception as e:
        log.warning("edge-tts failed: %s", e)
    return None


# ---------------------------------------------------------------------------
# Telegram Bot Transport + Proactive Reminder Loop
# ---------------------------------------------------------------------------
def tg_api(method: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    _, body, _ = http_request(url, method="POST", form_data=data or {}, timeout=35)
    return json.loads(body.decode("utf-8"))


def send_telegram_reply(chat_id: int, text: str, want_voice: bool = True) -> None:
    for chunk_start in range(0, len(text), 3900):
        tg_api("sendMessage", data={"chat_id": str(chat_id), "text": text[chunk_start:chunk_start + 3900]})
    if want_voice:
        mp3 = synthesize_speech(text)
        if mp3:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio"
                http_multipart(
                    url,
                    fields={"chat_id": str(chat_id), "title": "JARVIS"},
                    file_field="audio",
                    file_path=mp3,
                    mime_type="audio/mpeg",
                )
            finally:
                mp3.unlink(missing_ok=True)


def check_due_reminders() -> None:
    if not TELEGRAM_BOT_TOKEN or not ALLOWED_TELEGRAM_ID:
        return
    state = load_state()
    now = time.time()
    changed = False
    for rem in state.get("reminders", []):
        if not rem.get("done") and float(rem.get("due_ts", 0)) <= now:
            rem["done"] = True
            changed = True
            msg = f"⏰ تذكير من جارفس:\n{rem['message']}"
            try:
                send_telegram_reply(int(ALLOWED_TELEGRAM_ID), msg, want_voice=True)
                if rem.get("call_me"):
                    trigger_callmebot_telegram_ring(f"Jarvis reminder: {rem['message']}")
            except Exception as e:
                log.warning("Reminder send failed: %s", e)
    if changed:
        save_state(state)


# ---------------------------------------------------------------------------
# Optional HTTP Health Server (keeps Render Free awake via UptimeRobot ping)
# ---------------------------------------------------------------------------
class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        payload = json.dumps({"status": "ok", "agent": "JARVIS 24/7", "time": dt.datetime.utcnow().isoformat() + "Z"})
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        return


def start_health_server_if_needed() -> None:
    if not HEALTH_PORT:
        return
    port = int(HEALTH_PORT)

    class ReuseTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    def _serve() -> None:
        with ReuseTCPServer(("0.0.0.0", port), HealthHandler) as httpd:
            log.info("Health server listening on 0.0.0.0:%s", port)
            httpd.serve_forever()

    threading.Thread(target=_serve, daemon=True).start()


def poll_forever() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("ERROR: Set TELEGRAM_BOT_TOKEN before running.")
    if not ALLOWED_TELEGRAM_ID:
        raise SystemExit("ERROR: Set ALLOWED_TELEGRAM_ID (get your numeric ID from @userinfobot).")

    start_health_server_if_needed()
    log.info("J.A.R.V.I.S 24/7 Agent active (owner=%s). Listening...", ALLOWED_TELEGRAM_ID)
    offset = 0
    while True:
        try:
            check_due_reminders()
            res = tg_api("getUpdates", data={"timeout": "20", "offset": str(offset)})
            for upd in res.get("result", []):
                offset = max(offset, upd["update_id"] + 1)
                msg = upd.get("message") or {}
                chat_id = msg.get("chat", {}).get("id")
                user_id = str(msg.get("from", {}).get("id", ""))
                if not chat_id or user_id != ALLOWED_TELEGRAM_ID:
                    continue

                text = msg.get("text", "").strip()
                voice_obj = msg.get("voice") or msg.get("audio")
                is_voice = False

                if voice_obj:
                    is_voice = True
                    f_info = tg_api("getFile", data={"file_id": voice_obj["file_id"]})
                    file_path = f_info.get("result", {}).get("file_path")
                    if file_path:
                        _, dl_bytes, _ = http_request(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}", timeout=30)
                        tmp_ogg = Path(tempfile.gettempdir()) / f"in_{int(time.time()*1000)}.ogg"
                        tmp_ogg.write_bytes(dl_bytes)
                        try:
                            text = transcribe_audio_file(tmp_ogg) or ""
                        finally:
                            tmp_ogg.unlink(missing_ok=True)
                        if text:
                            tg_api("sendMessage", data={"chat_id": str(chat_id), "text": f"🎙️ سمعتك: «{text}»"})
                        else:
                            tg_api("sendMessage", data={"chat_id": str(chat_id), "text": "لم أتمكن من تفريغ الصوت — تأكد من إضافة GROQ_API_KEY أو GEMINI_API_KEY."})
                            continue

                if not text:
                    continue

                if text == "/start":
                    send_telegram_reply(
                        chat_id,
                        "أهلاً بك! أنا جارفس (نسخة 24/7 المجانية). أرسل لي نصاً أو رسالة صوتية — أستطيع البحث بالويب، فحص المواقع، العمل على مهمات ثقيلة بالخلفية (/tasks)، وتذكيرك والاتصال بك عبر تيليجرام.",
                        want_voice=True,
                    )
                    continue

                if text == "/tasks":
                    tasks = tool_list_tasks().get("tasks", [])
                    if not tasks:
                        send_telegram_reply(chat_id, "لا توجد مهام خلفية مسجلة بعد.", want_voice=False)
                    else:
                        lines = [f"• {t['id']} [{t['status']}]: {t['goal'][:80]}" for t in tasks[-5:]]
                        send_telegram_reply(chat_id, "📋 آخر المهام الخلفية:\n" + "\n".join(lines), want_voice=False)
                    continue

                tg_api("sendChatAction", data={"chat_id": str(chat_id), "action": "typing"})
                reply = run_agent_turn(text, chat_id=int(chat_id))
                send_telegram_reply(chat_id, reply, want_voice=(is_voice or ENABLE_VOICE_REPLIES))
        except KeyboardInterrupt:
            log.info("Shutting down cleanly.")
            break
        except Exception as e:
            log.error("Loop error: %s", e)
            time.sleep(4)


# ---------------------------------------------------------------------------
# Offline Self-Test
# ---------------------------------------------------------------------------
def run_selftest() -> None:
    leads_res = tool_list_leads(limit=3)
    assert leads_res.get("total", 0) >= 1, f"Expected CSV leads, got {leads_res}"

    sample_html = """
    <html><head><title>Test Clinic</title></head>
    <body>
      <h1>Best Clinic</h1>
      <a href="/en/#">Book Consultation</a>
      <a href="https://wa.me/00971501234567">WhatsApp</a>
      <p>0+ Years Experience | info@example.com</p>
    </body></html>
    """
    audit = audit_html_content("https://example.com", sample_html)
    assert len(audit["dead_hash_ctas"]) == 1, audit
    assert len(audit["broken_whatsapp_links"]) == 1, audit
    assert "info@example.com" in audit["emails_found"], audit

    ddg_sample = '<a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.ae%2F">Dubai <b>Clinic</b></a><a class="result__snippet">Best clinic in Dubai</a>'
    ddg_parsed = parse_duckduckgo_html(ddg_sample)
    assert ddg_parsed and ddg_parsed[0]["url"] == "https://example.ae/", ddg_parsed

    assert extract_tool_call('```json\n{"tool": "start_background_task", "args": {"goal": "research"}}\n```')["tool"] == "start_background_task"
    print("SELFTEST OK:", json.dumps({"leads_found": leads_res["total"], "audit_ok": True, "ddg_parser_ok": True, "bg_parser_ok": True}))


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        poll_forever()
