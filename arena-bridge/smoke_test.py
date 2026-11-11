#!/usr/bin/env python3
"""
فحص سريع لجسر LMArena — بدون شبكة وبدون gpt4free.
التشغيل:  python smoke_test.py
"""

import json

from fastapi.testclient import TestClient

import bridge

client = TestClient(bridge.app)

passed = 0


def check(name, fn):
    global passed
    fn()
    passed += 1
    print("PASS —", name)


def t_root():
    r = client.get("/")
    assert r.status_code == 200, r.status_code
    body = r.json()
    assert body["service"] == "jarvis-arena-bridge"
    assert body["openai_base"] == "/v1"


def t_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "has_gpt4free" in body


def t_auth_required():
    old = bridge.BRIDGE_API_KEY
    bridge.BRIDGE_API_KEY = "k-test"
    try:
        assert client.get("/v1/models").status_code == 401
        assert client.get("/v1/models", headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.get("/v1/models", headers={"x-api-key": "k-test"}).status_code == 200
    finally:
        bridge.BRIDGE_API_KEY = old


def t_models_payload():
    payload = bridge._openai_models_payload(["auto", "stealth"])
    assert payload["object"] == "list"
    assert [m["id"] for m in payload["data"]] == ["auto", "stealth"]
    # auto يُضاف دائماً في المقدمة
    models = bridge._arena_models()
    assert models[0] == bridge.DEFAULT_MODEL


def t_completion_payload():
    p = bridge._completion_payload("auto", "أهلاً")
    assert p["object"] == "chat.completion"
    assert p["choices"][0]["message"]["content"] == "أهلاً"
    assert p["choices"][0]["finish_reason"] == "stop"


def t_sse_format():
    chunk = bridge._sse_chunk("auto", "مرحبا")
    assert chunk.startswith("data: ")
    assert chunk.endswith("\n\n")
    data = json.loads(chunk[len("data: "):].strip())
    assert data["object"] == "chat.completion.chunk"
    assert data["choices"][0]["delta"]["content"] == "مرحبا"
    stop = bridge._sse_chunk("auto", "", finish="stop")
    assert json.loads(stop[len("data: "):].strip())["choices"][0]["finish_reason"] == "stop"


def t_validation():
    r = client.post("/v1/chat/completions", json={"messages": []})
    assert r.status_code == 400
    r = client.post("/v1/chat/completions", content=b"not-json", headers={"content-type": "application/json"})
    assert r.status_code == 400


def t_selftest_readiness():
    r = client.get("/arena/selftest")
    assert r.status_code == 200, r.status_code
    body = r.json()
    names = [e["name"] for e in body["engines"]]
    assert names == ["LMArenaBridge", "gpt4free:Arena", "OpenAI-compatible"], names
    assert all("ready" in e for e in body["engines"])
    # /health كمان لازم يعرض المحركات
    h = client.get("/health").json()
    assert isinstance(h["engines"], list) and len(h["engines"]) == 3


def t_env_loading():
    # لا .env حقيقي بالاختبار — نتأكد أن الدالة لا تنفجر بغياب الملف
    bridge._load_dotenv("/tmp/definitely-missing-jarvis.env")


for name, fn in [
    ("GET / يعرّف الخدمة", t_root),
    ("GET /health سليم", t_health),
    ("حماية BRIDGE_API_KEY (Bearer + x-api-key)", t_auth_required),
    ("قائمة النماذج بصيغة OpenAI", t_models_payload),
    ("رد غير بث بصيغة OpenAI", t_completion_payload),
    ("مقاطع البث SSE صحيحة", t_sse_format),
    ("رفض messages الفارغة وJSON الخربان", t_validation),
    ("/arena/selftest يعرض المحركات الثلاثة", t_selftest_readiness),
    ("تحميل .env الغائب آمن", t_env_loading),
]:
    check(name, fn)

print(f"\n{passed}/9 فحوصات ناجحة")
