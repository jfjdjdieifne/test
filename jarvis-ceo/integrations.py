#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مركز الوصلات — جارفس يعرف شو مربوط، شو ناقص، وكيف يربط بنفسه.
الدكتور ما بيحتاج يتعلم ولا خطوة تقنية: بيقول «ربط X» وبيمشي خطوة خطوة،
وأي مفتاح بيكرر عليه الزر، بيصرح جارفس: ما حدا يشوفه غير السيرفر.
"""
import os
import re

ENV_PATH = os.environ.get("CEO_ENV_PATH", os.path.expanduser("~/jarvis-ceo.env"))

SERVICES = {
    "github": {
        "name": "GitHub",
        "keys": ["GITHUB_TOKEN"],
        "optional": ["GITHUB_OWNER"],
        "howto": [
            "افتح github.com/settings/tokens/new (حسابك بتاعه)",
            "Fine-grained token → اسم: jarvis-ceo → Expires: سنة",
            "الصلاحيات تحت Repository permissions: Contents (Read and write) + Pull requests (Read and write) + Administration (Read and write)",
            "Generate → انسخ التوكن (github_pat_...)",
            "ارجع تلغرام واكتب: احفظ مفتاح GITHUB_TOKEN=<التوكن>",
        ],
    },
    "gmail": {
        "name": "جيميل",
        "keys": ["GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"],
        "optional": [],
        "howto": [
            "افتح myaccount.google.com/security وفعّل التحقق بخطوتين (إذا مو مفعّل)",
            "افتح myaccount.google.com/apppasswords",
            "التطبيق: «Mail» → «Other» → اكتب jarvis → إنشاء",
            "انسخ كلمة المرور 16 حرف",
            "ارجع تلغرام واكتب: احفظ مفتاح GMAIL_ADDRESS=ايميلك وبعدين احفظ مفتاح GMAIL_APP_PASSWORD=كلمةالمرور",
        ],
    },
    "x": {
        "name": "X (تويتر)",
        "keys": ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"],
        "optional": [],
        "howto": [
            "افتح developer.x.com بحسابك واعمل Project + App مجاني",
            "User authentication settings → OAuth 1.0a → Read and Write",
            "Keys and tokens → انسخ: API Key, API Secret, Access Token, Access Token Secret",
            "ارجع تلغرام واكتبهم: احفظ مفتاح X_API_KEY=... وهكذا",
            "ملاحظة: النشر المجاني محدود شهرياً — بقلك لما تخلص",
        ],
    },
    "facebook": {
        "name": "فيسبوك (صفحة)",
        "keys": ["META_PAGE_ID", "META_PAGE_TOKEN"],
        "optional": [],
        "howto": [
            "لازم عندك صفحة Facebook (مو حسابك الشخصي) — افتح facebook.com/pages",
            "افتح developers.facebook.com واعمل App نوع Business",
            "أضف منتج «Facebook Login for Business» → لحاله بيطلعلك Page Access Token",
            "ارجع تلغرام: احفظ مفتاح META_PAGE_ID=... وبعدين احفظ مفتاح META_PAGE_TOKEN=...",
        ],
    },
    "instagram": {
        "name": "انستغرام (Business)",
        "keys": ["META_IG_USER_ID", "META_PAGE_TOKEN"],
        "optional": [],
        "howto": [
            "حوّل حساب انستغرام لـ Professional/Business (من التطبيق → Settings → Account)",
            "اربط انستغرام بصفحة الفيسبوك تبعتك (نفس إعدادات الحساب)",
            "من developers.facebook.com خذ نفس الـ META_PAGE_TOKEN اللي عملته لفيسبوك",
            "احصل على Instagram Business Account ID من الـ Graph API Explorer",
            "ارجع تلغرام: احفظ مفتاح META_IG_USER_ID=...",
            "ملاحظة: انستغرام بدها صورة مع كل منشور",
        ],
    },
    "gemini": {
        "name": "Gemini (للصوت)",
        "keys": ["GEMINI_API_KEY"],
        "optional": ["GEMINI_STT_MODEL"],
        "howto": [
            "عندك المفتاح أصلاً بالتجارب — الصقه: احفظ مفتاح GEMINI_API_KEY=<المفتاح>",
        ],
    },
    "tavily": {
        "name": "بحث الويب Tavily",
        "keys": ["TAVILY_API_KEY"],
        "optional": [],
        "howto": [
            "افتح tavily.com بحسابك (الحصة المجانية 1000 بحث بالشهر)",
            "API Keys → انسخ المفتاح",
            "ارجع تلغرام: احفظ مفتاح TAVILY_API_KEY=<المفتاح>",
        ],
    },
}

ALL_KEYS = {k for s in SERVICES.values() for k in s["keys"] + s["optional"]}
EXTRA_KEYS = {"COARENA_API_KEY", "COARENA_BASE_URL", "COARENA_MODEL", "DAILY_TOKEN_CAP", "CEO_CHAT_ID",
              "TELEGRAM_BOT_TOKEN", "BROWSERLESS_TOKEN", "VERCEL_TOKEN", "CLOUDFLARE_TOKEN"}


def key_state(name):
    return bool(os.environ.get(name, "").strip())


def service_ok(svc_id):
    svc = SERVICES.get(svc_id)
    if not svc:
        return False
    return all(key_state(k) for k in svc["keys"])


def status_lines():
    try:
        import github
        gh = github.whoami() if github.configured() else None
        gh_line = f"✅ {gh.get('login')}" if gh and gh.get("ok") else ("⚠️ التوكن موجود بس ما قبلو" if gh else "❌ ناقص")
    except Exception:
        gh_line = "❌ ناقص"
    lines = []
    for sid, svc in SERVICES.items():
        ok = service_ok(sid)
        missing = [k for k in svc["keys"] if not key_state(k)]
        if sid == "github" and ok and gh_line.startswith(("✅", "⚠️")):
            lines.append(f"• GitHub: {gh_line}")
        else:
            lines.append(f"• {svc['name']}: {'✅ جاهز' if ok else '❌ ناقص: ' + ', '.join(missing)}")
    return lines


def missing_list():
    out = []
    for sid, svc in SERVICES.items():
        missing = [k for k in svc["keys"] if not key_state(k)]
        if missing:
            out.append(f"• {svc['name']} — {', '.join(missing)}")
    return out


def steps_for(query):
    q = (query or "").strip().lower()
    mapping = {
        "github": "github", "جيتهاب": "github", "جتهاب": "github",
        "جيميل": "gmail", "gmail": "gmail", "ايميل": "gmail", "الإيميل": "gmail",
        "x": "x", "تويتر": "x", "twitter": "x",
        "فيسبوك": "facebook", "facebook": "facebook", "فيس بوك": "facebook",
        "انستغرام": "instagram", "انستا": "instagram", "instagram": "instagram", "انستحرام": "instagram",
        "gemini": "gemini", "جيميني": "gemini",
        "tavily": "tavily", "بحث": "tavily", "Tavily": "tavily".lower(),
    }
    sid = mapping.get(q) or mapping.get(q.replace(" ", ""))
    if not sid:
        # مطابقة جزئية
        for key, val in mapping.items():
            if key and key in q:
                sid = val
                break
    if not sid:
        return None, None
    svc = SERVICES[sid]
    steps = [f"ربط {svc['name']} — الخطوات:"]
    steps += [f"{i + 1}. {s}" for i, s in enumerate(svc["howto"])]
    steps.append("وإذا ضاعت: اكتب «شو لازم اضيف» وانا بوريك شو ناقص.")
    return sid, "\n".join(steps)


def env_var_allowed(name):
    return name in ALL_KEYS or name in EXTRA_KEYS


def store_env_var(name, value, path=None):
    """يخزّن مفتاح بـ .env — يستبدل الموجود أو يضيف. بلا طباعة القيمة أبداً."""
    path = path or ENV_PATH
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,40}", name or ""):
        return False, "اسم المتغير مش صالح (حروف إنجليزية كبيرة وأرقام و _ بس)"
    if not value or len(value) > 500 or any(ch in value for ch in "\n\r"):
        return False, "القيمة فاضية أو فيها أسطر — ما بنحفظ هيك"
    lines = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    replaced = False
    out_lines = []
    for line in lines:
        if line.strip().startswith(f"{name}="):
            out_lines.append(f"{name}={value}")
            replaced = True
        else:
            out_lines.append(line)
    if not replaced:
        out_lines.append(f"{name}={value}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out_lines).rstrip("\n") + "\n")
    os.chmod(path, 0o600)
    return True, ("انحفظ واستبدلت القديم" if replaced else "انحفظ")
