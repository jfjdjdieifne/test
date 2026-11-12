---
title: JARVIS Arena Bridge
emoji: 🌉
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# جسر LMArena لجارفس (Space)

خدمة FastAPI متوافقة مع OpenAI توجّه الطلبات إلى LMArena (gpt4free/Arena).

## الملفات المطلوبة بهذا الـ Space
- `README.md` (هذا الملف)
- `Dockerfile`
- `bridge.py` (من `arena-bridge/bridge.py`)
- `requirements.txt` (من `arena-bridge/requirements.txt`)

## الأسرار (Settings → Variables and secrets)
| الاسم | القيمة |
|---|---|
| `BRIDGE_API_KEY` | مفتاح طويل عشوائي (نفسه بجارفس) |
| `DEFAULT_MODEL` | `auto` |
| `LMArenaBridge_URL` | فارغ إلا إذا شغّلت جسراً محلياً |
| `G4F_FALLBACK` | `true` |

## بعد ما يبني
- الرابط: `https://<user>-<space>.hf.space`
- الفحص: `https://<user>-<space>.hf.space/health`
- بجارفس: `ARENA_BRIDGE_URL` = نفس الرابط، و`ARENA_BRIDGE_KEY` = قيمة `BRIDGE_API_KEY`
- شغّل `ARENA_BRIDGE_KEEPALIVE=true` — HF تنوّم الـ Space المجاني بعد ~48 ساعة خمول،
  والـ cron تبع جارفس يضربه كل 10 دقائق فيضل صاحي.

> ⚠️ الـ Space المجاني **عام** (الكود ظاهر للجميع). لا تحط كوكيز أو مفاتيح داخل الكود —
> استخدم Secrets فقط، وخلي `BRIDGE_API_KEY` إلزامياً.
