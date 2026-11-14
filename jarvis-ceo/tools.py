#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات جارفس — الأيدي: ملفات Excel، صوت، أسعار، مواقع.
المبدأ: كل قرار «فهم» يتخذه فابل — الأدوات تفحص وتنفذ فقط.
"""
import asyncio
import base64
import json
import os
import re
import time
import urllib.request
import urllib.error
import urllib.parse

import edge_tts
import openpyxl

GEMINI_STT_MODEL = os.environ.get("GEMINI_STT_MODEL", "gemini-3-flash-preview")
EDGE_TTS_VOICE = os.environ.get("EDGE_TTS_VOICE", "ar-SY-LaithNeural")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()


# ---------- قراءة المواقع (Jina Reader — مجاني بلا مفتاح) ----------

def read_url(url, max_chars=3500):
    """يقرا أي رابط عبر r.jina.ai — يرجع نص نظيف (بلا مفتاح)."""
    u = (url or "").strip()
    if not u:
        raise ValueError("الرابط فاضي")
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    target = "https://r.jina.ai/" + u
    req = urllib.request.Request(target, headers={"User-Agent": "jarvis-ceo", "Accept": "text/plain"})
    with urllib.request.urlopen(req, timeout=25) as r:
        text = r.read().decode("utf-8", errors="ignore")
    return text.strip()[:max_chars]


# ---------- Excel ----------

def excel_report(path, max_rows=12):
    """ملخص نصي عن ملف Excel — يزود فابل بالبنية عشان يقرر."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    parts = []
    for ws in wb.worksheets:
        dims = f"{ws.max_row}x{ws.max_column}"
        rows = list(ws.iter_rows(values_only=True, max_row=min(ws.max_row, max_rows)))
        sample = []
        for r in rows:
            sample.append([str(c)[:40] if c is not None else "" for c in r])
        parts.append(f"ورقة «{ws.title}» ({dims}):\n" + "\n".join(str(r) for r in sample))
    wb.close()
    return "\n\n".join(parts)[:6000]


_FORBIDDEN = re.compile(
    r"(__import__|\bimport\s+os\b|\bimport\s+sys\b|\bimport\s+subprocess|\bopen\s*\(|\bexec\s*\(|\beval\s*\(|\bcompile\s*\(|\binput\s*\(|\bshutil\b|\bsocket\b|\burllib\b|\brequests\b|\bctypes\b|\bglobals\s*\()"
)


def apply_excel_code(path, code, log_limit=2000):
    """ينفذ كود فابل على ملف Excel ببيئة مقيدة — بيرجع (نجح؟, نص النتيجة)."""
    if _FORBIDDEN.search(code):
        return False, "الكود فيه امتداد ممنوع (os/open/import…) — ما بنفذ شي"
    backup = path + ".bak"
    try:
        with open(path, "rb") as f:
            data = f.read()
        with open(backup, "wb") as f:
            f.write(data)
    except Exception as e:  # noqa: BLE001
        return False, f"ما قدرت أعمل نسخة احتياطية: {e}"

    wb = openpyxl.load_workbook(path)
    logs = []

    def log(*args):
        logs.append(" ".join(str(a) for a in args))

    safe_builtins = {
        "len": len, "range": range, "enumerate": enumerate, "zip": zip,
        "str": str, "int": int, "float": float, "bool": bool,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
        "enumerate": enumerate, "sorted": sorted, "reversed": reversed,
        "any": any, "all": all, "print": log, "True": True, "False": False, "None": None,
        "openpyxl": openpyxl,
    }
    sandbox = {"wb": wb, "ws": wb.active, "log": log, "openpyxl": openpyxl}
    try:
        exec(code, {"__builtins__": safe_builtins}, sandbox)  # noqa: S102 — بيئة مقيدة بتصميم
        wb.save(path)
        return True, ("\n".join(logs)[:log_limit] or "تم التعديل بنجاح").strip()
    except Exception as e:  # noqa: BLE001
        try:
            with open(backup, "rb") as f:
                back = f.read()
            with open(path, "wb") as f:
                f.write(back)
            return False, f"فشل التنفيذ — رجّعت النسخة الاحتياطية: {type(e).__name__}: {e}"
        except Exception:
            return False, f"فشل التنفيذ: {type(e).__name__}: {e}"


# ---------- الصوت ----------

def gemini_transcribe(path, mime="audio/ogg"):
    """تفريغ ملف صوت عبر Gemini (نفس المفتاح المُثبت بالتجارب)."""
    raw = os.environ.get("GEMINI_TTS_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("لا يوجد مفتاح Gemini على السيرفر")
    audio_b64 = base64.b64encode(open(path, "rb").read()).decode()
    body = json.dumps({
        "contents": [{"role": "user", "parts": [
            {"text": "فرّغ هذا التسجيل بدقة كما هو منطوق باللهجة الشامية أو الفصحى — النص فقط بدون أي شرح. إذا كان صامتاً أو غير مفهوم أجب بكلمة واحدة: صمت"},
            {"inlineData": {"mimeType": mime, "data": audio_b64}},
        ]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 512},
    }).encode("utf-8")
    for key in keys:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_STT_MODEL}:generateContent",
            data=body, method="POST",
            headers={"x-goog-api-key": key, "content-type": "application/json"},
        )
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            payload = json.loads(resp.read().decode("utf-8"))
            parts = (((payload.get("candidates") or [{}])[0].get("content") or {}).get("parts")) or []
            text = "".join(p.get("text", "") for p in parts).strip()
            return "" if text == "صمت" else text
        except Exception:
            continue
    raise RuntimeError("تعذر تفريغ الصوت عبر Gemini")


async def _tts_save(text, path):
    await edge_tts.Communicate(text, EDGE_TTS_VOICE).save(path)


def speak_to_file(text, path):
    asyncio.run(_tts_save(text, path))
    return path


# ---------- الأسواق & الطقس (مجاني بلا مفاتيح) ----------

def _get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (JarvisBot)"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read().decode("utf-8"))


def gold_usd():
    """سعر أونصة الذهب بالدولار عبر CoinGecko (PAX Gold ≈ سعر الذهب)."""
    data = _get_json("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd")
    return float(data["pax-gold"]["usd"])


def crypto_usd(symbol="bitcoin"):
    data = _get_json(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd")
    return float(data[symbol]["usd"])


def weather(city="Vilnius"):
    req = urllib.request.Request(
        f"https://wttr.in/{urllib.parse.quote(city)}?format=3&lang=ar",
        headers={"User-Agent": "curl/8"},
    )
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore").strip()


# ---------- فحص المواقع ----------

def check_site(url, timeout=12):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (JarvisBot)"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read(300000).decode("utf-8", "ignore")
        ms = int((time.time() - start) * 1000)
        m = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else "(بدون عنوان)"
        return {"ok": True, "status": resp.status, "ms": ms, "title": title, "url": url}
    except Exception as e:  # noqa: BLE001
        ms = int((time.time() - start) * 1000)
        return {"ok": False, "error": str(e)[:200], "ms": ms, "url": url}


# ---------- بحث Tavily (اختياري — مفتاح عند الدكتور أصلاً) ----------

def web_search(query, max_results=5):
    if not TAVILY_API_KEY:
        return ""
    body = json.dumps({"api_key": TAVILY_API_KEY, "query": query, "max_results": max_results}).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search", data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=25)
        data = json.loads(resp.read().decode("utf-8"))
        out = []
        for r in (data.get("results") or [])[:max_results]:
            out.append(f"- {r.get('title','')}: {r.get('content','')[:220]}")
        return "\n".join(out)
    except Exception:
        return ""
