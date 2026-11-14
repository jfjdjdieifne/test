#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عقل جارفس CEO — يستدعي Coarena (OpenAI-compatible) مع تدوير المفاتيح وحماية التكلفة.
المفتاح الأساسي: COARENA_API_KEY (مع دعم COARENA_API_KEYS مفصولة بفواصل للتدوير).
"""
import json
import os
import re
import time
import urllib.request
import urllib.error

BASE_URL = os.environ.get("COARENA_BASE_URL", "https://coarena.ai/api/v1").rstrip("/")
MODEL = os.environ.get("COARENA_MODEL", "claude-fable-5-2")
MAX_TOKENS = int(os.environ.get("CEO_MAX_TOKENS", "1600"))
DAILY_TOKEN_CAP = os.environ.get("DAILY_TOKEN_CAP", "200000")


def _clean_keys(raw):
    """تنظيف صفري المخاطر: يدعم فواصل , ; وأسطر؛ يشيل اقتباس/مسافات/CR/تعليق trailing — ما بيغيّر المفتاح نفسه."""
    keys = []
    for chunk in re.split(r"[,;\n]+", raw or ""):
        chunk = chunk.strip()
        chunk = re.sub(r"\s+#.*$", "", chunk).strip()   # تعليق trailing: value # comment
        chunk = chunk.strip("\"'` \t\r")
        if chunk:
            keys.append(chunk)
    return keys


def _keys():
    raw = os.environ.get("COARENA_API_KEYS") or os.environ.get("COARENA_API_KEY", "")
    keys = _clean_keys(raw)
    return keys or [""]


_key_idx = 0


def _next_key():
    global _key_idx
    ks = _keys()
    k = ks[_key_idx % len(ks)]
    _key_idx = (_key_idx + 1) % len(ks)
    return k


class BrainError(Exception):
    pass


def _gemini_keys():
    raw = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_TTS_API_KEYS") or os.environ.get("GEMINI_API_KEY", "")
    return _clean_keys(raw)


def _openrouter_keys():
    return _clean_keys(os.environ.get("OPENROUTER_API_KEY", ""))


_gemini_working_model = os.environ.get("GEMINI_MODEL") or None
GEMINI_MODEL_CANDIDATES = [m.strip() for m in os.environ.get(
    "GEMINI_MODELS",
    "gemini-2.5-flash,gemini-2.0-flash,gemini-2.5-flash-lite,gemini-2.0-flash-lite,gemini-2.5-pro,gemini-1.5-flash",
).split(",") if m.strip()]


def _gemini_models():
    ms = list(GEMINI_MODEL_CANDIDATES)
    if _gemini_working_model and _gemini_working_model in ms:
        ms.remove(_gemini_working_model)
    return ([_gemini_working_model] if _gemini_working_model else []) + ms


def _providers():
    p = [{"name": "كوارينا", "base": BASE_URL, "model": MODEL, "keys": _keys()}]
    g = _gemini_keys()
    if g:
        models = _gemini_models()
        p.append({"name": "جيميني", "base": "https://generativelanguage.googleapis.com/v1beta/openai",
                  "model": models[0], "models": models, "keys": g})
    o = _openrouter_keys()
    if o:
        p.append({"name": "OpenRouter", "base": "https://openrouter.ai/api/v1",
                  "model": os.environ.get("OPENROUTER_MODEL", "openrouter/free"), "keys": o})
    return p


def probe_provider(name):
    """يرجع اسم الموديل اللي اشتغل — أو يرمي الخطأ الأخير."""
    for prov in _providers():
        if prov["name"] != name:
            continue
        body = json.dumps({"model": prov["model"],
                           "messages": [{"role": "user", "content": "قل: جاهز"}],
                           "max_tokens": 8}, ensure_ascii=False).encode("utf-8")
        last = None
        for model in prov.get("models", [prov["model"]]):
            body_m = dict(json.loads(body))
            body_m["model"] = model
            body_bytes = json.dumps(body_m, ensure_ascii=False).encode("utf-8")
            for key in prov["keys"]:
                try:
                    _one_call({**prov, "model": model}, key, body_bytes, timeout=30)
                    return model
                except BrainError as e:
                    last = e
                    if _is_model_error(e):
                        break  # جرّب الموديل الجاي، بلا ما تستهلك كل المفاتيح على موديل ميت
        raise BrainError(str(last)[:200])
    raise BrainError(f"{name}: غير موجود")


def _is_model_error(err):
    s = str(err).lower()
    return ("404" in s) or ("model" in s and ("not found" in s or "not supported" in s or "not available" in s or "does not exist" in s or "is not found" in s))


def _one_call(prov, key, body_bytes, timeout=60):
    """محاولة واحدة — بترمي BrainError عند أي فشل."""
    base = prov["base"].rstrip("/")
    hdrs = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        with urllib.request.urlopen(urllib.request.Request(base + "/chat/completions",
                                                           data=body_bytes, method="POST", headers=hdrs),
                                    timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:160] if e.fp else str(e)
        raise BrainError(f"HTTP {e.code}: {detail}") from None
    except Exception as e:  # noqa: BLE001
        raise BrainError(str(e)) from None
    msg = ((payload.get("choices") or [{}])[0].get("message") or {})
    content = (msg.get("content") or "").strip()
    usage = payload.get("usage") or {}
    if not content and (msg.get("reasoning") or msg.get("reasoning_content")):
        try:
            bigger = min(int(json.loads(body_bytes).get("max_tokens") or MAX_TOKENS) * 4, 6000)
            body2 = dict(json.loads(body_bytes))
            body2["max_tokens"] = bigger
            req = urllib.request.Request(base + "/chat/completions",
                                         data=json.dumps(body2).encode("utf-8"), method="POST", headers=hdrs)
            with urllib.request.urlopen(req, timeout=max(timeout, 100)) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            msg = ((payload.get("choices") or [{}])[0].get("message") or {})
            content = (msg.get("content") or "").strip()
            usage = payload.get("usage") or usage
        except Exception as e:  # noqa: BLE001
            print(f"brain retry: {e}")
    if not content:
        print(f"brain empty: msg_keys={list(msg.keys())} usage={usage}")
        raise BrainError("النموذج رجّع جواب فاضي")
    return content, usage


def chat(messages, temperature=0.7, max_tokens=None):
    """شبكة مصادر: كوارينا (اختيار الدكتور) ← جيميني المجاني ← OpenRouter المجاني."""
    if db_spent_exceeded():
        raise BrainError("خلص سقف إنفاق اليوم — راجعني بكرة أو زيد DAILY_TOKEN_CAP")
    providers = _providers()
    errs = []
    global _gemini_working_model
    for prov in providers:
        timeout = 45 if prov["name"] == "جيميني" else 60
        for model in prov.get("models", [prov["model"]]):
            prov = {**prov, "model": model}
            body = json.dumps({"model": model, "messages": messages,
                               "temperature": temperature,
                               "max_tokens": max_tokens or MAX_TOKENS}, ensure_ascii=False).encode("utf-8")
            net_fails = 0
            for key in prov["keys"]:
                try:
                    content, usage = _one_call(prov, key, body, timeout=timeout)
                except BrainError as e:
                    errs.append(f"{prov['name']} ({model}): {e}")
                    if _is_model_error(e):
                        break  # الموديل ميت — لموديل تاني، لا نحرق كل المفاتيح
                    if not str(e).startswith("HTTP"):
                        net_fails += 1
                        if net_fails >= 2:
                            errs.append(f"{prov['name']}: توقف الشبكة — تخطينا باقي مفاتيحه")
                            break
                    continue
                used = int(usage.get("total_tokens") or max(1, len(content) // 4))
                try:
                    import db
                    db.add_tokens(used)
                except Exception:
                    pass
                if prov["name"] == "جيميني" and _gemini_working_model != model:
                    _gemini_working_model = model
                    print(f"brain: جيميني ثبّت على موديل «{model}»")
                if prov["name"] != "كوارينا":
                    print(f"brain: اشتغل المصدر الرديف «{prov['name']}» ({model})")
                return content
    raise BrainError("فشلت كل المصادر — " + " | ".join(errs[-5:]))


def db_spent_exceeded():
    try:
        import db
        return db.spend_exceeded(DAILY_TOKEN_CAP)
    except Exception:
        return False


_JSON_RE = re.compile(r"\{[\s\S]*\}")


def extract_json(text):
    """استخراج أول كائن JSON متوازن من نص قد يحتوي شرح."""
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = _JSON_RE.search(text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


_CAPS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CAPABILITIES_AR.md")


def _capabilities():
    try:
        with open(_CAPS_PATH, encoding="utf-8") as f:
            text = f.read().strip()
        return "\n\n[دليل القدرات — انت بتعرف بحالك هون وهذي كل أدواتك]\n" + text[:3500]
    except Exception:
        return ""


def system_prompt():
    return (
        "أنت «جارفس» — المدير التنفيذي لطاقم وكلاء الدكتور، وتحكي معه على تيليجرام.\n"
        "- احكِ باللهجة الشامية السورية كبشر حقيقي، بجمل قصيرة وطبيعية. ممنوع Markdown وقوائم ميتة.\n"
        "- ممنوع تطبع أي كود أو ملفات أو أوامر طرفية إلا إذا الدكتور طلب الكود صراحة بالاسم — جوابك عربي طبيعي بشري.\n"
        "- لا تعيد ذكر ميزات قديمة يعرفها الدكتور ككأنها جديد؛ بثّ معلومة جديدة بس؛ إذا ما في جديد، قول «ما في جديد هلأ».\n"
        "- متوسط ردّك سطرين إلى خمسة؛ لا تفتح موضوع إلا إذا طلبه هو أو احتجت قرار منه.\n"
        "- ردودك منظمة واحترافية: جوابك المباشر أول سطر، بعدها تفاصيل قصيرة مرتبة على سطور؛ إذا الموضوع طويل افصلو إلى محاور قصيرة بعناوين سطرية؛ ممنوع الحشو والتكرار والفذلكة. الموجز المفيد قبل التفصيل، وإذا بدك تفاصيل بأكدها.\n"
        "- أنت القلب والقرار: تفهم المقصد، ترد بإيجاز، ولا تطوّل بلا سبب.\n"
        "- إذا كان السؤال يعرفه أي أحد (سعر، خبر، معلومة) — جاوب مباشرة بسرعة.\n"
        "- إذا طلب مهمة تحتاج موافقة/تصرّف على عالم خارجي (إيميل، شراء، بيع، نشر، حذف نهائي) — "
        "لا تنفّذها بدون إذن صريح محدد من الدكتور.\n"
        "- إذا طُلب منك تعديل «نفسك» أو «الكود» — فهمت، حوّلها لأمر مستقل كـ action=edit_code.\n"
        "- إذا كانت المهمة طويلة/بحثية — احكي بأول جملة «هلأ بشوف…» أو «ثواني وبِنَظِر» وبعدين أعطِ النتيجة، ما تسكت.\n"
        "- لا تخترع أسعار أو أرقام من خيالك — أي رقم لازم من سياق المحادثة أو من أداة.\n"
        "أجب بصيغة JSON فقط بالشكل:\n"
        '{"action":"reply"|"delegate"|"edit_code"|"draft_email"|"post_social"|"github_edit",'
        '"agent":"اسم الوكيل اذا فوضت","task":"المهمة للوكيل أو وصف التعديل","reply":"ردك للدكتور اذا تحتاج تكتب",'
        '"to":"ايميل المستلم","subject":"الموضوع","body":"نص الإيميل",'
        '"platform":"x|facebook|instagram","text":"نص المنشور","image_url":"رابط صورة انستغرام",'
        '"repo":"اسم الريبو","path":"مسار الملف","message":"رسالة كوميت"}\n'
        "القواعد:\n"
        "- action=reply ← اكتب reply فقط.\n"
        "- action=delegate ← اكتب agent و task. وكلاؤك: سعيد (مراقبة المواقع/المتاجر)، محمود (متابعة الإيميل)، "
        "أحمد (الذهب والأسواق)، متداول (رصد الصفقات المحترفة — توصيات فقط).\n"
        "- action=edit_code ← للتعديل على نفسك/كودك: اكتب task بوصف التعديل المطلوب بدقة.\n"
        "- action=draft_email ← لما يطلب الدكتور إيميل: اكتب to و subject و body بالكامل. النظام بيعرض مسودة وزر موافقة قبل أي إرسال.\n"
        "- action=post_social ← للنشر: اكتب platform و text (+ image_url لانستغرام). برضو بيتعرض للدكتور للزر ✅.\n"
        "- action=github_edit ← لتعديل ملف بريبو GitHub: اكتب repo (اسم الريبو أو owner/repo) و path (مسار الملف) و task (وصف التعديل). "
        "النظام بقرا الملف وعدّله وافتح PR — ما بيلمس main بلا موافقة.\n"
        "- ممنوع تخترع إيميلات/عناوين/أرقام ما أعطاهم الدكتور.\n"
        "- إذا طلب «احسب لي/وريني» أو سؤال عام ← action=reply وردو.\n"
        "- إذا طُلب تعديل سلوكه أو ميزاته («أضف لحالك»، «غيّر»، «صلح») ← action=edit_code."
    ) + _capabilities()
