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
MAX_TOKENS = int(os.environ.get("CEO_MAX_TOKENS", "1200"))
DAILY_TOKEN_CAP = os.environ.get("DAILY_TOKEN_CAP", "200000")


def _keys():
    raw = os.environ.get("COARENA_API_KEYS") or os.environ.get("COARENA_API_KEY", "")
    keys = [k.strip() for k in raw.split(",") if k.strip()]
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


def chat(messages, temperature=0.7, max_tokens=None):
    """messages: قائمة {role, content} — يرجع النص الخام من المساعد."""
    if db_spent_exceeded():
        raise BrainError("خلص سقف إنفاق اليوم — راجعني بكرة أو زيد DAILY_TOKEN_CAP")
    body = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or MAX_TOKENS,
        }
    ).encode("utf-8")

    last_err = None
    for _ in range(len(_keys())):
        key = _next_key()
        req = urllib.request.Request(
            BASE_URL + "/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
        )
        try:
            resp = urllib.request.urlopen(req, timeout=60)
            payload = json.loads(resp.read().decode("utf-8"))
            msg = ((payload.get("choices") or [{}])[0].get("message") or {})
            content = (msg.get("content") or "").strip()
            usage = payload.get("usage") or {}
            if not content:
                # رد فاضي من النموذج — سجّل مفاتيح الـ payload للتشخيص وجرّب المفتاح التالي
                print(f"brain empty: msg_keys={list(msg.keys())} usage={usage} raw={json.dumps(payload, ensure_ascii=False)[:400]}")
                last_err = "العقل رجّع جواب فاضي من النموذج (رد فارغ)"
                if isinstance(msg.get("tool_calls") or msg.get("reasoning") or msg.get("reasoning_content"), (list, str)):
                    last_err += " — النموذج بيحكي بقناة الاستدلال/الأدوات مو المحتوى العادي"
                continue
            used = int(usage.get("total_tokens") or max(1, len(content) // 4))
            try:
                import db
                db.add_tokens(used)
            except Exception:
                pass
            return content
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:200] if e.fp else str(e)
            last_err = f"HTTP {e.code}: {detail}"
            if e.code in (401, 403, 429):
                continue  # المفتاح التالي
            raise BrainError(last_err) from None
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            continue
    raise BrainError(f"فشلت كل المفاتيح — آخر خطأ: {last_err}")


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


def system_prompt():
    return (
        "أنت «جارفس» — المدير التنفيذي لطاقم وكلاء الدكتور، وتحكي معه على تيليجرام.\n"
        "- احكِ باللهجة الشامية السورية كبشر حقيقي، بجمل قصيرة وطبيعية. ممنوع Markdown وقوائم ميتة.\n"
        "- أنت القلب والقرار: تفهم المقصد، ترد بإيجاز، ولا تطوّل بلا سبب.\n"
        "- إذا كان السؤال يعرفه أي أحد (سعر، خبر، معلومة) — جاوب مباشرة بسرعة.\n"
        "- إذا طلب مهمة تحتاج موافقة/تصرّف على عالم خارجي (إيميل، شراء، بيع، نشر، حذف نهائي) — "
        "لا تنفّذها بدون إذن صريح محدد من الدكتور.\n"
        "- إذا طُلب منك تعديل «نفسك» أو «الكود» — فهمت، حوّلها لأمر مستقل كـ action=edit_code.\n"
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
    )
