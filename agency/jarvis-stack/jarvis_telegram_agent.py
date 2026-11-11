#!/usr/bin/env python3
"""
J.A.R.V.I.S Autonomous $0 Telegram Voice & Task Agent (Zero-Dependency Core)
===========================================================================
Works with Python 3 standard library only! (Optional: `pip install edge-tts` for spoken MP3 replies).
100% Free-Tier Stack ($0/month):
- Messaging & Voice Notes: Telegram Bot API (@BotFather)
- Speech-to-Text: Groq Whisper (whisper-large-v3-turbo) or Gemini 2.5 Flash multimodal audio
- Text-to-Speech (optional): Microsoft Edge Neural Voices via edge-tts (ar-AE-HamdanNeural / en-US-AndrewNeural)
- LLM Brain (automatic failover): Google Gemini 2.5 Flash -> Groq Llama 3.3 70B -> OpenRouter (openrouter/free)
- Outbound Voice Ring Alerts: CallMeBot Telegram Call API (optional personal setup)
- Built-in Tools: Dubai CRM lead reader/updater, live Website Bug Auditor, Persistent Memory, Proactive Reminders
"""

import asyncio
import base64
import csv
import datetime as dt
import json
import logging
import mimetypes
import os
import re
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlencode, urlparse

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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
ENABLE_VOICE_REPLIES = os.getenv("ENABLE_VOICE_REPLIES", "true").lower() == "true"
ARABIC_VOICE = os.getenv("ARABIC_VOICE", "ar-AE-HamdanNeural")
ENGLISH_VOICE = os.getenv("ENGLISH_VOICE", "en-US-AndrewNeural")
CALLMEBOT_TELEGRAM_USER = os.getenv("CALLMEBOT_TELEGRAM_USER", "").strip()

_raw_csv = os.getenv("LEADS_CSV_PATH", str(BASE_DIR.parent / "dubai_high_ticket_leads.csv"))
LEADS_CSV_PATH = Path(_raw_csv)
if not LEADS_CSV_PATH.is_absolute():
    LEADS_CSV_PATH = (BASE_DIR / LEADS_CSV_PATH).resolve()


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
    req_headers = {"User-Agent": "JarvisAgent/1.0"}
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
# Persistent State (Memory, Reminders, Chat History)
# ---------------------------------------------------------------------------
def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"memories": {}, "reminders": [], "history": [], "lead_notes": {}}


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


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
            headers={"User-Agent": "Mozilla/5.0 (compatible; JarvisAuditor/1.0)"},
            timeout=15,
        )
        raw_html = body.decode("utf-8", errors="replace")
        report = audit_html_content(final_url, raw_html)
        report["http_status"] = status
        return report
    except Exception as e:
        return {"error": f"Failed to fetch {url}: {e}"}


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


def dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "list_leads":
        return tool_list_leads(int(args.get("limit", 12)), str(args.get("status_filter", "")))
    if name == "update_lead":
        return tool_update_lead(str(args.get("business_name", "")), str(args.get("status", "sent")), str(args.get("note", "")))
    if name == "audit_website":
        return tool_audit_website(str(args.get("url", "")))
    if name == "save_memory":
        return tool_save_memory(str(args.get("key", "")), str(args.get("value", "")))
    if name == "get_memories":
        return tool_get_memories()
    if name == "schedule_reminder":
        return tool_schedule_reminder(args.get("minutes_from_now", 60), str(args.get("message", "")), bool(args.get("call_me", False)))
    if name == "call_me_now":
        return trigger_callmebot_telegram_ring(str(args.get("message", "Urgent alert from Jarvis")))
    return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Free LLM Router (Gemini -> Groq -> OpenRouter :free)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are J.A.R.V.I.S, an ultra-capable autonomous AI assistant working at $0 cost for your user.
Respond primarily in clear, crisp Arabic (or English if the user writes in English).
You have real tools! When you need to use a tool, reply ONLY with a valid JSON object (no markdown fences) in this exact shape:
{"tool": "<tool_name>", "args": { ... }}

Available tools:
1. list_leads: {"limit": 12, "status_filter": ""} -> reads Dubai high-ticket prospects CSV and statuses.
2. update_lead: {"business_name": "...", "status": "sent|interested|won|new", "note": "..."} -> saves CRM update.
3. audit_website: {"url": "https://..."} -> fetches a real live website and extracts dead # links, broken wa.me links, emails, phone links, 0-counters, and language gaps.
4. save_memory: {"key": "...", "value": "..."} -> permanently stores facts/preferences.
5. get_memories: {} -> reads saved memories.
6. schedule_reminder: {"minutes_from_now": 2880, "message": "...", "call_me": true} -> sets a timer; when due, Jarvis messages Telegram AND rings via CallMeBot if call_me is true.
7. call_me_now: {"message": "..."} -> immediately rings the user's phone via Telegram CallMeBot (max 250 chars, English ASCII works best with standard TTS).

Once you have all facts needed, answer the user directly in plain text without JSON tool wrappers."""


def call_gemini(messages: List[Dict[str, str]]) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    convo_text = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": convo_text}]}],
        "generationConfig": {"temperature": 0.4},
    }
    status, body, _ = http_request(url, method="POST", json_body=payload, timeout=45)
    if status != 200:
        log.warning("Gemini failed (%s): %s", status, body.decode("utf-8", errors="replace")[:200])
        return None
    data = json.loads(body.decode("utf-8"))
    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")


def call_openai_compatible(url: str, key: str, model: str, messages: List[Dict[str, str]], extra_headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}"}
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "temperature": 0.4,
    }
    status, body, _ = http_request(url, method="POST", headers=headers, json_body=payload, timeout=45)
    if status != 200:
        log.warning("Provider %s failed (%s): %s", model, status, body.decode("utf-8", errors="replace")[:200])
        return None
    data = json.loads(body.decode("utf-8"))
    return data.get("choices", [{}])[0].get("message", {}).get("content")


def ask_free_llm(messages: List[Dict[str, str]]) -> str:
    for fn in (
        lambda: call_gemini(messages),
        lambda: call_openai_compatible("https://api.groq.com/openai/v1/chat/completions", GROQ_API_KEY, "llama-3.3-70b-versatile", messages),
        lambda: call_openai_compatible(
            "https://openrouter.ai/api/v1/chat/completions",
            OPENROUTER_API_KEY,
            "openrouter/free",
            messages,
            {"X-Title": "Jarvis Telegram Agent"},
        ),
    ):
        try:
            ans = fn()
            if ans:
                return ans.strip()
        except Exception as e:
            log.warning("LLM provider error: %s", e)
    return "لم ينجح أي مزود ذكاء حالياً — تأكد من إضافة GEMINI_API_KEY أو GROQ_API_KEY أو OPENROUTER_API_KEY في ملف .env."


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


def run_agent_turn(user_text: str) -> str:
    state = load_state()
    memories = state.get("memories", {})
    history = state.get("history", [])[-10:]

    mem_prefix = ""
    if memories:
        mem_prefix = "[Saved Memories: " + json.dumps(memories, ensure_ascii=False) + "]\n"

    working_msgs = list(history) + [{"role": "user", "content": mem_prefix + user_text}]
    final_reply = ""

    for _ in range(4):
        reply = ask_free_llm(working_msgs)
        tool_call = extract_tool_call(reply)
        if not tool_call:
            final_reply = reply
            break
        t_name = str(tool_call.get("tool", ""))
        t_args = tool_call.get("args") or {}
        log.info("Executing tool %s with args %s", t_name, t_args)
        result = dispatch_tool(t_name, t_args)
        working_msgs.append({"role": "assistant", "content": reply})
        working_msgs.append({
            "role": "user",
            "content": f"[TOOL RESULT for {t_name}]: {json.dumps(result, ensure_ascii=False)[:6000]}\nNow synthesize a helpful final answer for the user (or call another tool if needed).",
        })
    else:
        final_reply = ask_free_llm(working_msgs)

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


def poll_forever() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("ERROR: Set TELEGRAM_BOT_TOKEN in .env before running.")
    if not ALLOWED_TELEGRAM_ID:
        raise SystemExit("ERROR: Set ALLOWED_TELEGRAM_ID in .env (get your numeric ID from @userinfobot).")

    log.info("J.A.R.V.I.S Telegram Agent active (owner=%s). Listening...", ALLOWED_TELEGRAM_ID)
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
                    send_telegram_reply(chat_id, "أهلاً بك! أنا جارفس (نسخة $0 الكاملة). أرسل لي نصاً أو رسالة صوتية: مثلاً 'اعطني أول 3 عملاء في دبي' أو 'افحص موقع https://namconsultant.com' أو 'ذكرني بعد دقيقة أتصل بالعميل'.", want_voice=True)
                    continue

                tg_api("sendChatAction", data={"chat_id": str(chat_id), "action": "typing"})
                reply = run_agent_turn(text)
                send_telegram_reply(chat_id, reply, want_voice=(is_voice or ENABLE_VOICE_REPLIES))
        except KeyboardInterrupt:
            log.info("Shutting down cleanly.")
            break
        except Exception as e:
            log.error("Loop error: %s", e)
            time.sleep(4)


# ---------------------------------------------------------------------------
# Offline Self-Test (verifies tools & parsers without network/tokens)
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
    assert len(audit["suspicious_zero_counters"]) >= 1, audit
    assert extract_tool_call('```json\n{"tool": "list_leads", "args": {"limit": 5}}\n```')["tool"] == "list_leads"
    print("SELFTEST OK:", json.dumps({"leads_found": leads_res["total"], "audit_ok": True, "tool_parser_ok": True}))


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        poll_forever()
