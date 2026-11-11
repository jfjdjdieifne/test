# 🌉 JARVIS Arena Bridge — جسر LMArena لجارفس

خدمة Python صغيرة (FastAPI) تكشف **API متوافق مع OpenAI** وتوجّه الطلبات إلى نماذج
LMArena — ومنها النماذج التجريبية/المخفية (stealth) — حتى يستخدمها **جارفس** في تيليجرام.

```
تيليجرام → جارفس (Cloudflare Worker) → arena-bridge (هذي الخدمة) → LMArena
```

## ليش وسيط؟

| المشروع | التقنية | ممكن يشتغل داخل Cloudflare Worker؟ |
|---|---|---|
| [CloudWaddie/LMArenaBridge](https://github.com/CloudWaddie/LMArenaBridge) | Python + FastAPI + Camoufox/Playwright | ❌ لا |
| [Blacklisted-Binary/LMArenaProxy](https://github.com/Blacklisted-Binary/LMArenaProxy) | Python (وكيل عكسي بجلسة المتصفح) | ❌ لا |
| `lianues/lmarenabridge` (نسخة FastAPI + خادم رفع ملفات) | Python + FastAPI | ❌ لا |
| [xtekky/gpt4free](https://github.com/xtekky/gpt4free) — مزود `Arena` | Python + متصفح/CDP + curl_cffi | ❌ لا |

Cloudflare Workers يشغّل JavaScript فقط، بدون متصفح وبدون تخزين كوكيز دائمة —
فالربط الصح هو **خدمة منفصلة** (هذي) وجارفس يناديها كأنها OpenAI.

> 📱 **آيفون؟** دليل مبسّط خطوة بخطوة: [`README_IPHONE_AR.md`](README_IPHONE_AR.md)

> 📱 **معك موبايل بس؟** شوف [`README_DEPLOY_FREE_AR.md`](README_DEPLOY_FREE_AR.md) —
> ٤ طرق مجانية لتشغيل الجسر ٢٤/٧ (Oracle Always Free · Hugging Face Space · Termux · Render).

## التشغيل

```bash
cd arena-bridge
python -m venv .venv && source .venv/bin/activate     # ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # عدّل BRIDGE_API_KEY
python bridge.py              # → http://0.0.0.0:8000
```

أو بـ Docker:

```bash
cp .env.example .env
docker compose up -d
```

فحص ذاتي بدون شبكة (8 فحوصات):

```bash
python smoke_test.py
```

فحص حي للخدمة:

```bash
curl http://127.0.0.1:8000/health
curl -H "Authorization: Bearer <BRIDGE_API_KEY>" http://127.0.0.1:8000/v1/models
curl -H "Authorization: Bearer <BRIDGE_API_KEY>" -H "content-type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"مرحبا"}]}' \
  http://127.0.0.1:8000/v1/chat/completions
```

## المحرّكان

1. **LMArenaBridge محلي (اختياري لكن الأقوى)** — شغّل واحداً من الجسور الأصلية على منفذ
   (مثلاً 8001) واضبط:
   ```
   LMArenaBridge_URL=http://127.0.0.1:8001
   LMArenaBridge_KEY=            # إن كان يدعم مفتاحاً
   ```
   الجسر يضيف `/api/v1/chat/completions` تلقائياً ويمرّر البث (SSE) كما هو.

2. **gpt4free — مزود Arena** (مثبّت عبر `requirements.txt`) — يستخدم
   `g4f.Provider.needs_auth.Arena`، ويتعامل مع محاكاة المتصفح ورموز الجلسة وتجاوز
   Cloudflare. إذا فشل وبـ `G4F_FALLBACK=true` يتراجع لمزودين مجانيين آخرين من g4f.

3. **أي وسيط متوافق مع OpenAI** — لو عندك/لقيت خدمة تصل Arena:
   ```
   OPENAI_COMPAT_URL=https://.../v1
   OPENAI_COMPAT_KEY=...
   ```

الترتيب: LMArenaBridge أولاً (إن وُجد) ← ثم gpt4free/Arena ← ثم الوسيط المتوافق.
أي فشل ينتقل للثاني، والرد النهائي يذكر سبب فشل كل محرك.

### فحص المحركات
`GET /arena/selftest` يعرض المحركات الثلاثة وجاهزيتها، و`/arena/selftest?deep=1`
يجرّب سؤالاً حقيقياً على كل محرك (يستخدمه `/arena test` من تيليجرام).

## متغيرات البيئة

| المتغير | افتراضي | الشرح |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `8000` | عنوان الاستماع |
| `BRIDGE_API_KEY` | فاضي | مفتاح الحماية — جارفس يرسله كـ `Bearer`. **حطه إلزامياً إن كان على الإنترنت** |
| `DEFAULT_MODEL` | `auto` | النموذج الافتراضي |
| `LMArenaBridge_URL` | فاضي | عنوان جسر LMArenaBridge المحلي (بدون `/api/v1`) |
| `LMArenaBridge_KEY` | فاضي | مفتاح الجسر المحلي إن وُجد |
| `G4F_FALLBACK` | `true` | هل يتراجع gpt4free لمزودين آخرين عند فشل Arena |
| `ARENA_COOKIES` / `ARENA_COOKIES_FILE` | فاضي | كوكيز Arena جاهزة (اختياري — لا ترفعها على Git) |
| `OPENAI_COMPAT_URL` | فاضي | أي خدمة متوافقة مع OpenAI تصل Arena (بدون `/chat/completions`) |
| `OPENAI_COMPAT_KEY` / `OPENAI_COMPAT_MODEL` | فاضي / `auto` | مفتاحها ونموذجها |

## النشر المجاني ٢٤/٧
| المنصة | متطلبات | نوم؟ |
|---|---|---|
| **Oracle Cloud Always Free** | بطاقة للتحقق فقط | لا — الأفضل |
| **Hugging Face Docker Space** | بلا بطاقة | تنام بعد ~48 ساعة خمول → `ARENA_BRIDGE_KEEPALIVE=true` |
| **Termux (نفس الموبايل)** | Termux + ngrok | يشتغل وقت ما الموبايل شغّال |
| **Render Free** | GitHub | تنام بعد 15 دقيقة → `ARENA_BRIDGE_KEEPALIVE=true` |

## الربط بجارفس

```bash
cd ../agency-cloudflare
npx wrangler secret put ARENA_BRIDGE_URL   # https://عنوان-الجسر  (بدون /v1)
npx wrangler secret put ARENA_BRIDGE_KEY   # نفس BRIDGE_API_KEY
npx wrangler deploy
```

اختياري: `ARENA_BRIDGE_MODEL`، `ARENA_BRIDGE_FIRST=true` (Arena قبل Gemini)،
`ARENA_BRIDGE_TIMEOUT_MS` (افتراضي 45000 — المتصفح بطيء).

بعدها من تيليجرام: `/arena` ثم `/arena test` ثم `/arena_ask شو أخبار دبي؟`

## نشر الخدمة على VPS (موصى به)

الجسر لازم يشتغل على جهاز دائم التشغيل. أسهل طريقة مع HTTPS:

```bash
# على VPS
git clone <مستودعك> && cd <مستودعك>/arena-bridge
cp .env.example .env && nano .env      # BRIDGE_API_KEY + LMArenaBridge_URL
docker compose up -d
```

خلف Caddy:

```
arena-bridge.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

ثم `ARENA_BRIDGE_URL=https://arena-bridge.example.com`.

## ملاحظات صادقة

- LMArena يحتاج **جلسة تسجيل دخول**؛ الكوكيز (`arena-auth-prod-v1`) تنتهي، وgpt4free
  يجدّدها أحياناً. إذا صار الرد فاشلاً: `/arena test` ثم أعد تشغيل الخدمة أو حدّث الجلسة.
- الاستخدام الآلي قد يخالف شروط استخدام LMArena وقد يُحظر الحساب — على مسؤوليتك،
  وعلى حسابك الشخصي.
- الجسر ما يخزّن أي شيء؛ كل طلب يُمرّر مباشرة. لا تضع كوكيزك في Git (`.gitignore` يغطي `.env`).
- النماذج "المخفية/stealth" تظهر فقط إذا أعادها المزود في `/v1/models` — الأسماء تتغيّر
  باستمرار ولا نضمن ثباتها.
