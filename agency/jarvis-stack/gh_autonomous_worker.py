#!/usr/bin/env python3
"""
J.A.R.V.I.S Autonomous GitHub Actions Worker ($0 Linux Cloud Sandbox)
======================================================================
Runs inside GitHub Actions Ubuntu Linux VM (unlimited free minutes on public repos,
2,000 free min/mo on private repos) when dispatched by Cloudflare Worker or manually.

Capabilities:
- Web search (Tavily or DuckDuckGo) & live webpage fetching/auditing
- Safe file creation/editing under agency/output/ (auto-published to Cloudflare!)
- Sanitized bash/Python execution (secrets stripped from child env)
- 5-Provider Free LLM failover: Gemini -> Mistral -> Groq -> NVIDIA NIM -> OpenRouter
- Reports completion + live URLs directly back to Telegram (+ CallMeBot ring if set)
"""

import html
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, unquote, urlencode, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENCY_DIR = REPO_ROOT / "agency"
OUTPUT_DIR = AGENCY_DIR / "output"

MISSION_GOAL = os.getenv("MISSION_GOAL", "").strip()
MISSION_TAG = re.sub(r"[^A-Za-z0-9_-]", "", os.getenv("MISSION_TAG", "mission"))[:24] or "mission"
WORKER_ORIGIN = os.getenv("WORKER_ORIGIN", "").rstrip("/")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_TELEGRAM_ID = os.getenv("ALLOWED_TELEGRAM_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
CALLMEBOT_TELEGRAM_USER = os.getenv("CALLMEBOT_TELEGRAM_USER", "").strip()

SECRET_ENV_KEYS = {
    "TELEGRAM_BOT_TOKEN",
    "ALLOWED_TELEGRAM_ID",
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
    "GROQ_API_KEY",
    "NVIDIA_API_KEY",
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
    "CALLMEBOT_TELEGRAM_USER",
    "GITHUB_TOKEN",
    "GH_TOKEN",
}


def http_req(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Any] = None,
    form_data: Optional[Dict[str, Any]] = None,
    timeout: int = 40,
) -> Tuple[int, bytes, str]:
    req_headers = {"User-Agent": "JarvisLinuxWorker/1.0"}
    if headers:
        req_headers.update(headers)
    data = None
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


def notify_telegram(text: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and ALLOWED_TELEGRAM_ID):
        return
    full = str(text or "")
    for i in range(0, len(full), 3900):
        try:
            http_req(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                method="POST",
                json_body={"chat_id": ALLOWED_TELEGRAM_ID, "text": full[i:i + 3900]},
                timeout=20,
            )
        except Exception:
            pass


def trigger_callmebot(msg: str) -> Dict[str, Any]:
    if not CALLMEBOT_TELEGRAM_USER:
        return {"ok": False, "error": "CALLMEBOT_TELEGRAM_USER not set"}
    clean = re.sub(r"\s+", " ", msg).strip()[:240]
    url = (
        f"https://api.callmebot.com/start.php?user={quote_plus(CALLMEBOT_TELEGRAM_USER)}"
        f"&text={quote_plus(clean)}&lang=en-US-Standard-B&rpt=2&cc=yes"
    )
    try:
        st, body, _ = http_req(url, timeout=15)
        return {"ok": st == 200, "status": st, "body": body.decode("utf-8", errors="replace")[:160]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Autonomous Tools inside Linux Runner
# ---------------------------------------------------------------------------
def safe_resolve_agency_path(rel_path: str, write_mode: bool = False) -> Path:
    raw = str(rel_path or "").strip().lstrip("/")
    if not raw or ".." in Path(raw).parts:
        raise ValueError("Invalid relative path")
    target = (OUTPUT_DIR / raw).resolve() if write_mode and not raw.startswith("output/") else (AGENCY_DIR / raw).resolve()
    if write_mode:
        if not (target == OUTPUT_DIR.resolve() or OUTPUT_DIR.resolve() in target.parents):
            raise ValueError("Writes are restricted to agency/output/ only")
    else:
        if not (target == AGENCY_DIR.resolve() or AGENCY_DIR.resolve() in target.parents):
            raise ValueError("Reads are restricted to agency/ directory")
    return target


def tool_web_search(query: str, max_results: int = 6) -> Dict[str, Any]:
    q = str(query or "").strip()
    if not q:
        return {"error": "Empty query"}
    if TAVILY_API_KEY:
        try:
            st, body, _ = http_req(
                "https://api.tavily.com/search",
                method="POST",
                json_body={"api_key": TAVILY_API_KEY, "query": q, "max_results": max_results},
                timeout=25,
            )
            if st == 200:
                res = json.loads(body.decode("utf-8")).get("results", [])
                return {
                    "source": "tavily",
                    "results": [{"title": r.get("title"), "url": r.get("url"), "snippet": (r.get("content") or "")[:400]} for r in res],
                }
        except Exception:
            pass
    try:
        st, body, _ = http_req(
            "https://html.duckduckgo.com/html/",
            method="POST",
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"},
            form_data={"q": q},
            timeout=25,
        )
        if st != 200:
            return {"error": f"DuckDuckGo HTTP {st}"}
        raw = body.decode("utf-8", errors="replace")
        blocks = re.findall(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?(?:class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div)>)',
            raw,
            flags=re.DOTALL | re.IGNORECASE,
        )
        items = []
        for href_raw, title_raw, snip_raw in blocks[:max_results]:
            href = html.unescape(href_raw)
            if "uddg=" in href:
                qs = parse_qs(urlparse(href).query)
                if "uddg" in qs:
                    href = unquote(qs["uddg"][0])
            items.append({
                "title": re.sub(r"<[^>]+>", "", html.unescape(title_raw)).strip(),
                "url": href,
                "snippet": re.sub(r"<[^>]+>", "", html.unescape(snip_raw)).strip()[:300],
            })
        return {"source": "duckduckgo", "results": items}
    except Exception as e:
        return {"error": str(e)}


def tool_fetch_and_audit(url: str) -> Dict[str, Any]:
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {"error": "Invalid URL"}
    host = (parsed.hostname or "").lower()
    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or host.startswith(("10.", "192.168.", "169.254.")):
        return {"error": "Private network host blocked"}
    try:
        st, body, final_url = http_req(
            parsed.geturl(),
            headers={"User-Agent": "Mozilla/5.0 (compatible; JarvisWorker/1.0)"},
            timeout=20,
        )
        raw = body.decode("utf-8", errors="replace")[:180000]
        title_m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
        links = re.findall(r'<a\b[^>]*href=["\']([^"\']{1,300})["\'][^>]*>(.*?)</a>', raw, re.IGNORECASE | re.DOTALL)
        dead_hash = []
        wa_links = []
        broken_wa = []
        for href, label in links[:200]:
            low = href.lower().strip()
            lbl = re.sub(r"<[^>]+>", " ", label).strip()[:50]
            if href.strip() in ("#", "/#", "/en/#") and lbl:
                dead_hash.append({"text": lbl, "href": href})
            if "wa.me/" in low or "whatsapp.com/send" in low:
                wa_links.append(href)
                if "wa.me/00" in low or "wa.me/+" in low or "%20" in low or " " in href:
                    broken_wa.append(href)
        emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,12}", raw)))[:8]
        text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", " ", raw, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()
        return {
            "http_status": st,
            "url": final_url,
            "title": title[:160],
            "has_arabic": bool(re.search(r"[\u0600-\u06FF]", text)),
            "dead_hash_ctas": dead_hash[:8],
            "whatsapp_links": wa_links[:6],
            "broken_whatsapp_links": broken_wa[:6],
            "emails": emails,
            "text_preview": text[:1600],
        }
    except Exception as e:
        return {"error": str(e)}


def tool_write_output_file(filename: str, content: str) -> Dict[str, Any]:
    try:
        path = safe_resolve_agency_path(filename, write_mode=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        rel = path.relative_to(AGENCY_DIR).as_posix()
        live_url = f"{WORKER_ORIGIN}/{rel}" if WORKER_ORIGIN else rel
        return {"ok": True, "saved_path": f"agency/{rel}", "live_url": live_url, "bytes": len(content.encode("utf-8"))}
    except Exception as e:
        return {"error": str(e)}


def tool_read_agency_file(rel_path: str) -> Dict[str, Any]:
    try:
        path = safe_resolve_agency_path(rel_path, write_mode=False)
        if not path.exists():
            return {"error": f"File not found: {rel_path}"}
        if path.is_dir():
            return {"files": [p.name for p in sorted(path.iterdir())][:50]}
        return {"path": f"agency/{path.relative_to(AGENCY_DIR).as_posix()}", "content": path.read_text(encoding="utf-8", errors="replace")[:8000]}
    except Exception as e:
        return {"error": str(e)}


def tool_run_sanitized_python(code: str) -> Dict[str, Any]:
    """Runs Python snippet inside agency/output with all API secret env vars stripped."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    clean_env = {k: v for k, v in os.environ.items() if k not in SECRET_ENV_KEYS}
    try:
        proc = subprocess.run(
            ["python3", "-c", str(code)],
            cwd=str(OUTPUT_DIR),
            env=clean_env,
            capture_output=True,
            text=True,
            timeout=25,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout[:3000],
            "stderr": proc.stderr[:1500],
        }
    except Exception as e:
        return {"error": str(e)}


def dispatch_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "web_search":
        return tool_web_search(args.get("query", ""), int(args.get("max_results", 6)))
    if name == "fetch_and_audit":
        return tool_fetch_and_audit(args.get("url", ""))
    if name == "write_output_file":
        return tool_write_output_file(args.get("filename", ""), args.get("content", ""))
    if name == "read_agency_file":
        return tool_read_agency_file(args.get("path", ""))
    if name == "run_python":
        return tool_run_sanitized_python(args.get("code", ""))
    if name == "call_me_now":
        return trigger_callmebot(args.get("message", "Jarvis mission completed"))
    return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# 5-Provider Free LLM Router
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are J.A.R.V.I.S Autonomous Linux Execution Agent running inside a free GitHub Actions cloud VM.
Your job is to execute the user's mission completely, step by step, producing real files/research/HTML deliverables under agency/output/ when asked.
Note: Any HTML/CSV/MD file you save with `write_output_file` is automatically pushed to GitHub and deployed live on Cloudflare!

To call a tool, respond ONLY with raw valid JSON (no markdown fences):
{"tool": "<name>", "args": {...}}

Tools:
1. web_search: {"query": "...", "max_results": 6}
2. fetch_and_audit: {"url": "https://..."} -> fetches live HTML/text, finds dead # links, broken wa.me links, emails, Arabic presence.
3. read_agency_file: {"path": "dubai_high_ticket_leads.csv"} -> reads files or lists directory in agency/.
4. write_output_file: {"filename": "report.html", "content": "..."} -> writes file inside agency/output/ and returns its live URL!
5. run_python: {"code": "print(1+1)"} -> runs Python script inside agency/output/ (useful for data analysis, CSV generation, HTML syntax check).
6. call_me_now: {"message": "..."} -> rings user on Telegram via CallMeBot (short English ASCII <=240 chars).

When finished, output ONLY the clear final Arabic summary (mentioning any saved file paths & live URLs)."""


def call_gemini(msgs: List[Dict[str, str]]) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    convo = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in msgs)
    for model in ("gemini-2.5-flash", "gemini-2.5-pro"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        st, body, _ = http_req(
            url,
            method="POST",
            json_body={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": convo}]}],
                "generationConfig": {"temperature": 0.35},
            },
            timeout=60,
        )
        if st == 200:
            txt = json.loads(body.decode("utf-8")).get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
            if txt:
                return txt
    return None


def call_openai_compat(url: str, key: str, model: str, msgs: List[Dict[str, str]], extra: Optional[Dict[str, str]] = None) -> Optional[str]:
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}"}
    if extra:
        headers.update(extra)
    st, body, _ = http_req(
        url,
        method="POST",
        headers=headers,
        json_body={
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + msgs,
            "temperature": 0.35,
        },
        timeout=60,
    )
    if st != 200:
        return None
    return json.loads(body.decode("utf-8")).get("choices", [{}])[0].get("message", {}).get("content")


def ask_free_llm(msgs: List[Dict[str, str]]) -> str:
    for fn in (
        lambda: call_gemini(msgs),
        lambda: call_openai_compat("https://api.mistral.ai/v1/chat/completions", MISTRAL_API_KEY, "mistral-large-latest", msgs),
        lambda: call_openai_compat("https://api.mistral.ai/v1/chat/completions", MISTRAL_API_KEY, "mistral-small-latest", msgs),
        lambda: call_openai_compat("https://api.groq.com/openai/v1/chat/completions", GROQ_API_KEY, "llama-3.3-70b-versatile", msgs),
        lambda: call_openai_compat("https://integrate.api.nvidia.com/v1/chat/completions", NVIDIA_API_KEY, "meta/llama-3.3-70b-instruct", msgs),
        lambda: call_openai_compat("https://openrouter.ai/api/v1/chat/completions", OPENROUTER_API_KEY, "openrouter/free", msgs, {"X-Title": "Jarvis Actions Worker"}),
    ):
        try:
            ans = fn()
            if ans and ans.strip():
                return ans.strip()
        except Exception:
            pass
    raise RuntimeError("No free LLM API key succeeded inside GitHub Actions Secrets.")


def extract_tool_call(text: str) -> Optional[Dict[str, Any]]:
    clean = str(text or "").strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", clean, flags=re.DOTALL).strip()
    if not (clean.startswith("{") and clean.endswith("}")):
        return None
    try:
        obj = json.loads(clean)
        if isinstance(obj, dict) and isinstance(obj.get("tool"), str):
            return obj
    except Exception:
        return None
    return None


def execute_mission() -> None:
    if not MISSION_GOAL:
        raise SystemExit("MISSION_GOAL is empty")

    print(f"Starting autonomous mission tag={MISSION_TAG}")
    msgs: List[Dict[str, str]] = [{"role": "user", "content": f"MISSION ({MISSION_TAG}):\n{MISSION_GOAL}"}]
    final_answer = ""

    for step in range(1, 13):
        reply = ask_free_llm(msgs)
        tc = extract_tool_call(reply)
        if not tc:
            final_answer = reply
            break
        t_name = tc["tool"]
        t_args = tc.get("args") or {}
        print(f"Step {step}: executing tool {t_name}")
        res = dispatch_tool(t_name, t_args)
        msgs.append({"role": "assistant", "content": reply})
        msgs.append({
            "role": "user",
            "content": f"[TOOL RESULT {t_name}]: {json.dumps(res, ensure_ascii=False)[:7500]}\nContinue mission or deliver final Arabic summary.",
        })
    else:
        final_answer = ask_free_llm(msgs + [{"role": "user", "content": "Produce final Arabic report now."}])

    report = f"🚀 اكتملت المهمة المستقلة ({MISSION_TAG}):\n\n{final_answer}"
    if WORKER_ORIGIN:
        report += f"\n\n📞 افتح مكالمة صوتية مباشرة لمناقشة النتيجة:\n{WORKER_ORIGIN}/call.html"
    notify_telegram(report)
    if CALLMEBOT_TELEGRAM_USER:
        trigger_callmebot(f"Jarvis finished GitHub mission {MISSION_TAG}. Check Telegram.")
    print("Mission finished successfully.")


def run_selftest() -> None:
    res = tool_write_output_file("selftest_probe.txt", "ok-test")
    assert res.get("ok"), res
    read_back = tool_read_agency_file("output/selftest_probe.txt")
    assert read_back.get("content") == "ok-test", read_back
    (OUTPUT_DIR / "selftest_probe.txt").unlink(missing_ok=True)
    py_res = tool_run_sanitized_python("import os; print('KEY_LEAK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'SAFE_OK')")
    assert "SAFE_OK" in py_res["stdout"], py_res
    assert extract_tool_call('{"tool":"web_search","args":{"query":"dubai"}}')["tool"] == "web_search"
    print("GH_WORKER SELFTEST OK")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        execute_mission()
