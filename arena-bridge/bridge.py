#!/usr/bin/env python3
"""
JARVIS Arena Bridge — جسر LMArena لجارفس (تيليجرام)
=====================================================
خدمة Python صغيرة تكشف API متوافق مع OpenAI وتوجّه الطلبات إلى:
  1) gpt4free — مزود Arena (xtekky/gpt4free)  ← المحرك الافتراضي
  2) LMArenaBridge محلي (CloudWaddie/LMArenaBridge · Blacklisted-Binary/LMArenaProxy
     · lianues/lmarenabridge) — إذا شغّلته بنفسك على نفس الجهاز

جارفس (Cloudflare Worker) بينادي هالخدمة كمزود إضافي في سلسلة الـ failover
عنده — عبر متغيرات: ARENA_BRIDGE_URL + ARENA_BRIDGE_KEY (اختياري).

التشغيل:
    pip install -r requirements.txt
    python bridge.py            # أو: uvicorn bridge:app --host 0.0.0.0 --port 8000

Endpoints:
    GET  /health                 — فحص حياة
    GET  /v1/models              — قائمة نماذج Arena المتاحة
    POST /v1/chat/completions    — متوافق مع OpenAI (stream + non-stream)

ملاحظة صادقة: LMArena يتطلب تسجيل دخول (كوكيز arena-auth-prod-v1) وتجاوز
Cloudflare — الكوكيز تنتهي صلاحيتها وتحتاج تجديد. الاستخدام الآلي قد يخالف
شروط استخدام LMArena وقد يُحظر الحساب. استخدمه على حسابك الشخصي وعلى مسؤوليتك.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Optional

# ---------------------------------------------------------------------------
# تحميل .env يدوياً (بدون اعتماد إضافي)
# ---------------------------------------------------------------------------

def _load_dotenv(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(str(Path(__file__).parent / ".env"))

# ---------------------------------------------------------------------------
# الإعدادات (من البيئة)
# ---------------------------------------------------------------------------

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
BRIDGE_API_KEY = os.environ.get("BRIDGE_API_KEY", "").strip()
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "auto").strip() or "auto"
# upstream اختياري: LMArenaBridge محلي (CloudWaddie / Blacklisted-Binary / lianues)
LMArenaBridge_URL = os.environ.get("LMArenaBridge_URL", "").strip().rstrip("/")
LMArenaBridge_KEY = os.environ.get("LMArenaBridge_KEY", "").strip()
# هل نسمح لـ gpt4free بالتراجع لمزودين مجانيين آخرين إذا فشل Arena؟
G4F_FALLBACK = os.environ.get("G4F_FALLBACK", "true").strip().lower() in ("1", "true", "yes", "on")
# كوكيز Arena (اختياري — gpt4free قد يفتح متصفحاً بنفسه عند الحاجة)
ARENA_COOKIES = os.environ.get("ARENA_COOKIES", "").strip()
ARENA_COOKIES_FILE = os.environ.get("ARENA_COOKIES_FILE", "").strip()

try:
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
except ImportError:  # pragma: no cover
    raise SystemExit("نقص اعتماديات — ثبّتها أولاً: pip install -r requirements.txt")

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

# gpt4free اختياري وقت التشغيل (الخدمة تشتغل بدونه إذا كان LMArenaBridge_URL مضبوطاً)
try:
    from g4f.client import Client as G4FClient
    from g4f.Provider.needs_auth.Arena import Arena as G4FArena
    HAS_G4F = True
except Exception as e:  # pragma: no cover
    G4FClient = None  # type: ignore
    G4FArena = None  # type: ignore
    HAS_G4F = False
    print(f"[bridge] تحذير: gpt4free غير متاح ({e}) — سيعمل فقط عبر LMArenaBridge_URL إن وُجد")

app = FastAPI(title="JARVIS Arena Bridge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# أدوات مساعدة
# ---------------------------------------------------------------------------

def _now() -> int:
    return int(time.time())


def _check_auth(authorization: Optional[str] = None, x_api_key: Optional[str] = None) -> None:
    """إذا ضُبط BRIDGE_API_KEY: نطلب Bearer (أو x-api-key). وإلا: مفتوح (شبكة محلية)."""
    if not BRIDGE_API_KEY:
        return
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    token = token or (x_api_key or "").strip()
    if token != BRIDGE_API_KEY:
        raise HTTPException(status_code=401, detail="مفتاح غير صحيح — أرسل Authorization: Bearer <BRIDGE_API_KEY>")


def _read_cookies() -> str:
    """كوكيز Arena من البيئة أو من ملف — تُمرَّر لـ gpt4free عند الحاجة."""
    if ARENA_COOKIES:
        return ARENA_COOKIES
    if ARENA_COOKIES_FILE and Path(ARENA_COOKIES_FILE).exists():
        return Path(ARENA_COOKIES_FILE).read_text(encoding="utf-8").strip()
    return ""


def _arena_models() -> list[str]:
    """قائمة نماذج Arena — من gpt4free إن أمكن، وإلا [auto]."""
    models: list[str] = []
    if HAS_G4F and G4FArena is not None:
        try:
            # get_models قد يفتح الشبكة/المتصفح — يُستدعى داخل thread
            got = G4FArena.get_models()
            if got:
                models = [str(m) for m in got]
        except Exception as e:
            print(f"[bridge] تعذر جلب نماذج Arena: {e}")
    if not models:
        models = ["auto"]
    # أضف النموذج الافتراضي دائماً في المقدمة إن لم يكن موجوداً
    if DEFAULT_MODEL not in models:
        models = [DEFAULT_MODEL] + models
    return models


def _openai_models_payload(models: list[str]) -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {"id": m, "object": "model", "created": _now(), "owned_by": "lmarena-via-gpt4free"}
            for m in models
        ],
    }


def _completion_payload(model: str, text: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex[:24],
        "object": "chat.completion",
        "created": _now(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def _sse_chunk(model: str, delta_text: str, finish: Optional[str] = None) -> str:
    payload = {
        "id": "chatcmpl-" + uuid.uuid4().hex[:24],
        "object": "chat.completion.chunk",
        "created": _now(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": ({"content": delta_text} if finish is None else {}),
                "finish_reason": finish,
            }
        ],
    }
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"


# ---------------------------------------------------------------------------
# المحرك 1: gpt4free (مزود Arena)
# ---------------------------------------------------------------------------

def _g4f_create_sync(model: str, messages: list[dict[str, Any]], stream: bool):
    """إنشاء متزامن عبر gpt4free — يُشغَّل داخل thread حتى لا نحجب حلقة FastAPI."""
    if not HAS_G4F:
        raise RuntimeError("gpt4free غير مثبّت — pip install gpt4free")
    client = G4FClient()
    cookies = _read_cookies()
    base: dict[str, Any] = {"model": model or "auto", "messages": messages, "stream": stream}

    def _call(provider: Any) -> Any:
        kwargs = dict(base)
        if provider is not None:
            kwargs["provider"] = provider
        if cookies:
            try:
                # بعض إصدارات gpt4free تقبل cookies كوسيط إضافي
                return client.chat.completions.create(cookies=cookies, **kwargs)
            except TypeError:
                pass
        return client.chat.completions.create(**kwargs)

    try:
        return _call(G4FArena)
    except Exception:
        if not G4F_FALLBACK:
            raise
        # تراجع: بدون مزود محدد — gpt4free يختار أفضل مزود مجاني متاح
        return _call(None)


def _g4f_text(model: str, messages: list[dict[str, Any]]) -> str:
    resp = _g4f_create_sync(model, messages, stream=False)
    content = getattr(resp.choices[0].message, "content", None) if resp and resp.choices else None
    return (content or "").strip()


def _g4f_deltas(model: str, messages: list[dict[str, Any]]) -> list[str]:
    """يجمع مقاطع البث داخل thread واحد ثم يعيدها — يمنع حجب حلقة الأحداث."""
    resp = _g4f_create_sync(model, messages, stream=True)
    out: list[str] = []
    for chunk in resp:
        try:
            delta = chunk.choices[0].delta.content or ""
        except Exception:
            delta = ""
        if delta:
            out.append(str(delta))
    return out


# ---------------------------------------------------------------------------
# المحرك 2: LMArenaBridge محلي (CloudWaddie / Blacklisted-Binary / lianues)
# ---------------------------------------------------------------------------

async def _LMArenaBridge_text(model: str, messages: list[dict[str, Any]]) -> str:
    """تمرير الطلب إلى LMArenaBridge محلي — يكشف POST /api/v1/chat/completions."""
    if httpx is None:
        raise RuntimeError("httpx غير مثبّت — pip install httpx")
    url = LMArenaBridge_URL + "/api/v1/chat/completions"
    headers = {"content-type": "application/json"}
    if LMArenaBridge_KEY:
        headers["authorization"] = f"Bearer {LMArenaBridge_KEY}"
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(url, headers=headers, json={"model": model, "messages": messages, "stream": False})
        res.raise_for_status()
        data = res.json()
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return (text or "").strip()


async def _LMArenaBridge_stream(model: str, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
    """تمرير البث (SSE) من LMArenaBridge كما هو."""
    if httpx is None:
        raise RuntimeError("httpx غير مثبّت — pip install httpx")
    url = LMArenaBridge_URL + "/api/v1/chat/completions"
    headers = {"content-type": "application/json", "accept": "text/event-stream"}
    if LMArenaBridge_KEY:
        headers["authorization"] = f"Bearer {LMArenaBridge_KEY}"
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, headers=headers, json={"model": model, "messages": messages, "stream": True}) as res:
            res.raise_for_status()
            async for line in res.aiter_lines():
                if line:
                    yield line + "\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """صفحة تعريف سريعة — مفيدة لفحص الوصول من المتصفح."""
    return {
        "service": "jarvis-arena-bridge",
        "openai_base": "/v1",
        "chat": "POST /v1/chat/completions",
        "models": "GET /v1/models",
        "health": "/health",
        "docs": "/docs",
        "auth_required": bool(BRIDGE_API_KEY),
        "engines": {
            "LMArenaBridge": bool(LMArenaBridge_URL),
            "gpt4free_arena": HAS_G4F,
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "jarvis-arena-bridge",
        "has_gpt4free": HAS_G4F,
        "has_LMArenaBridge_upstream": bool(LMArenaBridge_URL),
        "default_model": DEFAULT_MODEL,
        "ts": _now(),
    }


@app.get("/v1/models")
async def list_models(authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(None)):
    _check_auth(authorization, x_api_key)
    models = await asyncio.to_thread(_arena_models)
    return _openai_models_payload(models)


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
):
    _check_auth(authorization, x_api_key)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON غير صالح")
    model = str(body.get("model") or DEFAULT_MODEL)
    messages = body.get("messages") or []
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages مطلوبة (قائمة غير فارغة)")
    stream = bool(body.get("stream", False))

    # ترتيب المحركات: LMArenaBridge المحلي أولاً إن وُجد (أقوى تجاوزاً لـ Cloudflare)،
    # ثم gpt4free/Arena. أي فشل في الأول ينتقل للثاني تلقائياً.
    errors: list[str] = []

    if stream:
        async def gen() -> AsyncIterator[str]:
            # محاولة LMArenaBridge بثاً
            if LMArenaBridge_URL:
                try:
                    async for chunk in _LMArenaBridge_stream(model, messages):
                        yield chunk
                    return
                except Exception as e:
                    errors.append(f"LMArenaBridge: {e}")
            # ثم gpt4free بثاً (التجميع داخل thread حتى لا نحجب الحلقة)
            try:
                deltas = await asyncio.to_thread(_g4f_deltas, model, messages)
                for delta in deltas:
                    yield _sse_chunk(model, delta)
                yield _sse_chunk(model, "", finish="stop")
                yield "data: [DONE]\n\n"
                return
            except Exception as e:
                errors.append(f"gpt4free: {e}")
            yield _sse_chunk(model, "تعذر الوصول لكل محركات Arena: " + " | ".join(errors), finish="stop")
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream", headers={"cache-control": "no-cache", "x-accel-buffering": "no"})

    # غير بث: LMArenaBridge أولاً
    if LMArenaBridge_URL:
        try:
            text = await _LMArenaBridge_text(model, messages)
            if text:
                return JSONResponse(_completion_payload(model, text))
            errors.append("LMArenaBridge: رد فارغ")
        except Exception as e:
            errors.append(f"LMArenaBridge: {e}")

    # ثم gpt4free
    try:
        text = await asyncio.to_thread(_g4f_text, model, messages)
        if text:
            return JSONResponse(_completion_payload(model, text))
        errors.append("gpt4free: رد فارغ")
    except Exception as e:
        errors.append(f"gpt4free: {e}")

    raise HTTPException(status_code=502, detail="فشل كل محركات Arena: " + " | ".join(errors))


if __name__ == "__main__":
    import uvicorn

    print(f"[bridge] JARVIS Arena Bridge على http://{HOST}:{PORT} — النموذج الافتراضي: {DEFAULT_MODEL}")
    print(f"[bridge] gpt4free: {'متاح' if HAS_G4F else 'غير متاح'} | LMArenaBridge upstream: {LMArenaBridge_URL or 'غير مضبوط'}")
    uvicorn.run(app, host=HOST, port=PORT)
