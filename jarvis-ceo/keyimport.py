#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
وضعية «احفظ كل المفاتيح» — الدكتور بيلصق كل مفاتيحه مرة واحدة (مع كتابات زيادة حواليهم)
والنظام:
  1) يمسح رسالته فوراً (خصوصية) — ما بيضل شي بالشات.
  2) يفهم السطور محلياً فقط — **ولا مفتاح بيروح لفابل/Coarena أو أي خدمة خارجية**.
  3) يشيل الكلام الزيادة (Bearer، علامات، شروحات) ويحدد الاسم تلقائياً.
  4) يحفظ كل شي بملف الأسرار (chmod 600) وبصحتحه لك: شو انحفظ و شو ناقصك.
كل المعالجة هنا بـ Python محلي — صفر توكنز، صفر إرسال خارجي.
"""
import re

import integrations

# ---------- خرائط الأسماء ----------

LABEL_MAP = {
    "coarena": "COARENA_API_KEY",
    "كوارنيا": "COARENA_API_KEY",
    "كوارنياا": "COARENA_API_KEY",
    "كوائرنا": "COARENA_API_KEY",
    "كوارين": "COARENA_API_KEY",
    "coarenapool": "COARENA_API_KEYS",
    "coarena_pool": "COARENA_API_KEYS",
    "coarena keys": "COARENA_API_KEYS",
    "جيميناي": "GEMINI_API_KEY",
    "جيميني": "GEMINI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "جيميني tts": "GEMINI_TTS_API_KEYS",
    "جيميناي فويس": "GEMINI_TTS_API_KEYS",
    "gemini tts": "GEMINI_TTS_API_KEYS",
    "gemini pool": "GEMINI_TTS_API_KEYS",
    "tavily": "TAVILY_API_KEY",
    "تافيلي": "TAVILY_API_KEY",
    "taviliy": "TAVILY_API_KEY",
    "github": "GITHUB_TOKEN",
    "جيتهاب": "GITHUB_TOKEN",
    "git": "GITHUB_TOKEN",
    "gmail": "GMAIL_APP_PASSWORD",
    "جيميل": "GMAIL_APP_PASSWORD",
    "app password": "GMAIL_APP_PASSWORD",
    "باسوورد التطبيق": "GMAIL_APP_PASSWORD",
    "باسوورد جيميل": "GMAIL_APP_PASSWORD",
    "x api": "X_API_KEY",
    "تويتر": "X_API_KEY",
    "twitter": "X_API_KEY",
    "x secret": "X_API_SECRET",
    "x access": "X_ACCESS_TOKEN",
    "telegram": "TELEGRAM_BOT_TOKEN",
    "تيليجرام": "TELEGRAM_BOT_TOKEN",
    "botoken": "TELEGRAM_BOT_TOKEN",
    "bot token": "TELEGRAM_BOT_TOKEN",
}

PREFIX_MAP = [
    (re.compile(r"^coa_[A-Za-z0-9]{8,}$"), "COARENA_API_KEYS"),
    (re.compile(r"^AIza[0-9A-Za-z_-]{20,}$"), "GEMINI_API_KEY"),
    (re.compile(r"^github_pat_[0-9A-Za-z_]{20,}$"), "GITHUB_TOKEN"),
    (re.compile(r"^ghp_[0-9A-Za-z]{20,}$"), "GITHUB_TOKEN"),
    (re.compile(r"^gho_[0-9A-Za-z]{20,}$"), "GITHUB_TOKEN"),
    (re.compile(r"^xox[baprs]-[0-9A-Za-z-]{10,}$"), None),  # لسنسناكو — نتجاهل
]

_SPACEY = re.compile(r"[\s«»„“”\"'(){}\[\]<>،؛:;!؟،—–\-_*|/\\.]+")
_NAME_PAT = re.compile(r"([A-Za-z][A-Za-z0-9_]{2,39})")

def _clean_value(v):
    v = v.strip()
    v = re.sub(r"^(bearer|token|api[-_ ]?key|key)\s*[:=]?\s*", "", v, flags=re.I)
    v = v.strip().strip("'\"“”‘’«»„”")
    # شيل علامات الزائد من الطرفين
    v = v.strip("،؛,.;|/\\()[]{}<>`* ")
    return v.strip()


def _classify_name(name):
    name = name.upper()
    if name in integrations.ALL_KEYS or name in integrations.EXTRA_KEYS:
        return name
    return None


def _unmask(v):
    """كشف جزئي آمن: أول ٤ رموز + … + طول — عشان دردش بدون كشف."""
    v = v or ""
    return f"{v[:4]}… ({len(v)} حروف)" if len(v) > 4 else "…"


def _add(mapping, env, value):
    if env in POOL_KEYS:
        mapping.setdefault(env, []).append(value)
    else:
        mapping[env] = value


def parse_bulk_text(text):
    """يرجع (mapping, skipped_values). mapping: {ENV_NAME: value أو [values] للمجموعات} — كلشي محلي."""
    text = text or ""
    mapping = {}
    skipped = []

    # ---------- 1) NAME = value (سمير بالعربية أو الإنجليزية) ----------
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(?:[^\s=:：،]{1,30}[:：]\s*)?([A-Za-z][A-Za-z0-9_]{2,39})\s*[=:：]\s*(\S+)", line)
        if m:
            name, value = m.group(1), _clean_value(m.group(2))
            env = _classify_name(name)
            if env and len(value) >= 8 and not any(c.isspace() for c in value):
                _add(mapping, env, value)
                continue
        # ---------- 2) تسمية عربية/إنجليزية بدون اسم متغير («جيميني: VALUE») ----------
        lower = line.lower()
        for label, env in LABEL_MAP.items():
            if label in lower:
                m2 = re.search(r"([A-Za-z0-9_\-./+=]{8,})", line)
                if m2:
                    value = _clean_value(m2.group(1))
                    if len(value) >= 8:
                        _add(mapping, env, value)
                        break

    # ---------- 3) حالة values بلا اسم (معرّفة بالبادئة فقط) ----------
    leftover = []
    for tok in re.split(r"[\s,؛،]+", text):
        tok = _clean_value(tok)
        if len(tok) < 8 or re.fullmatch(r"[A-Z][A-Z0-9_]{2,39}", tok):
            continue
        used = [v for vals in mapping.values() for v in (vals if isinstance(vals, list) else [vals])]
        if any(tok in v for v in used):
            continue  # صارت مستعمله
        guessed = None
        for pat, env in PREFIX_MAP:
            if pat.fullmatch(tok):
                guessed = env
                break
        if guessed:
            _add(mapping, guessed, tok)
        else:
            leftover.append(tok)

    # ---------- 4) القيم اللي ما عرفنا شو هي ----------
    for tok in leftover:
        if re.search(r"[0-9A-Za-z_\-+/=]{8,}", tok) and not tok.lower().startswith(("http", "www.")):
            skipped.append(("قيمة بلا اسم معروف", _unmask(tok)))

    return mapping, skipped


POOL_KEYS = {"COARENA_API_KEYS", "GEMINI_API_KEYS", "GEMINI_TTS_API_KEYS"}

CRITICAL = ("TELEGRAM_BOT_TOKEN", "COARENA_API_KEY", "GEMINI_API_KEY")


def apply_bulk(chat_id, text, delete_fn=None):
    mapping, skipped = parse_bulk_text(text)
    saved, failed = [], []
    saved_total = 0
    for name, value in mapping.items():
        if isinstance(value, list):
            ok_all = True
            for v in value:
                ok, _ = integrations.store_pool_value(name, v)
                ok_all = ok_all and ok
                if ok:
                    saved_total += 1
            (saved if ok_all else failed).append(name)
        else:
            ok, _note = integrations.store_env_var(name, value)
            if ok:
                saved_total += 1
            (saved if ok else failed).append(name)

    lines = []
    if saved:
        lines.append(f"✅ حفظت {saved_total} مفتاح: {', '.join(saved)}")
    if failed:
        lines.append(f"❌ ما قدرت أحفظ: {', '.join(failed)}")
    if skipped:
        lines.append("🤔 لقيت قيم ما عرفت اسمها:")
        for _label, masked in skipped[:8]:
            lines.append(f"   • {masked} — اعطيني اسمها (مثال: «احفظ مفتاح GEMINI_API_KEY=…»)")
    if not saved and not skipped and not failed:
        lines.append("ما لقيت ولا مفتاح بالسطور هدي — جرّب مرة تانية (بتقدر تلصقهم بأي ترتيب)")
    if delete_fn:
        try:
            delete_fn()
        except Exception:  # noqa: BLE001
            lines.append("⚠️ حاولت امسح رسالتك وما قدرت — احذفها بيدك (فيها مفاتيح!)")

    return "\n".join(lines), saved


def final_report():
    ok = [k for k in CRITICAL if integrations.key_state(k)]
    missing = [k for k in CRITICAL if not integrations.key_state(k)]
    lines = ["خلصت الاستلام 👍"]
    lines.append(f"✅ موجود: {', '.join(ok) if ok else 'ولا إشي أساسي بعد'}")
    if missing:
        lines.append(f"❌ ناقص الأساسي: {', '.join(missing)}")
        lines.append("بالذات COARENA_API_KEY — العقل ما بيقدر يرد بدونها.")
    else:
        lines.append("كل الأساسيات موجودة — جاهز للانطلاق 🚀")
    return "\n".join(lines)


_UNAMBIGUOUS = (re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
                re.compile(r"github_pat_[0-9A-Za-z_]{20,}"),
                re.compile(r"ghp_[0-9A-Za-z]{20,}"),
                re.compile(r"gho_[0-9A-Za-z]{20,}"),
                re.compile(r"sk-[A-Za-z0-9]{16,}"),
                re.compile(r"coa_[A-Za-z0-9]{16,}"))
_ASSIGN = re.compile(r"([A-Za-z][A-Za-z0-9_]{2,39})\s*[=:]")
_TOKENISH = re.compile(r"[A-Za-z0-9_\-./+=]{8,}")


def looks_like_bulk(text):
    """هل النص فيه ≥2 لمحة واضحة عن مفاتيح؟ (للتعرف التلقائي) — محلي 100%."""
    if not text:
        return False
    hits = 0
    for pat in _UNAMBIGUOUS:
        if pat.search(text):
            hits += 1
    for m in _ASSIGN.finditer(text):
        env = _classify_name(m.group(1))
        if env:
            hits += 1
        if hits >= 2:
            return True
    # أسطر بتسمية عربية/إنجليزية معروفة («جيميني: قيمة») + قيمة طويلة على نفس السطر
    if hits < 2:
        for line in text.splitlines():
            low = line.lower()
            if any(lbl in low for lbl in LABEL_MAP) and _TOKENISH.search(line):
                # نتأكد إنو القيمة نفسها طويلة بما يكفي (مو مجرد شرح قصير)
                toks = _TOKENISH.findall(line)
                if any(len(t) >= 12 for t in toks):
                    hits += 1
                    if hits >= 2:
                        return True
    return hits >= 2
