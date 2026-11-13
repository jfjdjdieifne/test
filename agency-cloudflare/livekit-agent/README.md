# 🎙️ جارفس — مكالمة اللايف الحقيقية (LiveKit) — كل شي مجاني

هاي أكمل نسخة مجانية لمكالمة **كاملة الازدواجية (Full-Duplex)** مع جارفس: تحكي طبيعي، وتقاطعه متى بدك، ويرد عليك بصوت شامي بشري خلال ~1–2 ثانية — **بدون بطاقة وبدون أي اشتراك**.

## المعمارية (كل حلقة مجانية 100%)

```
مايك جهازك ─► LiveKit Cloud (WebRTC مجاني) ─► هذا الـ Agent (Python، شغال على جهازك)
                                                │
                                                ├─ STT ← Groq Whisper large-v3-turbo (حصة مجانية يومية)
                                                ├─ العقل ← Coarena Model API (Claude Fable 5.2 — $5/يوم مجاناً)
                                                ├─ TTS ← Microsoft Edge Neural TTS (ar-SY-LaithNeural — بلا حدود، بلا مفتاح)
                                                └─ VAD ← Silero (محلياً على جهازك)
مكبر الصوت ◄─ نفس البث الراجع
```

- **LiveKit Cloud**: عندك مشروعان مجانيان → حصة مضاعفة (الـ Worker يصدر توكن لأي واحد — `?project=1` أو `?project=2`).
- **Coarena**: $5/يوم مجاناً (+ طلب $50/يوم معلّق للمراجعة عندهم). تجدد الساعة 3:00 AM.
- **Edge TTS**: لا مفتاح ولا حدود — أصوات Microsoft العصبية (نفس صوت Read Aloud).
- **Groq Whisper**: حصة مجانية سخية يومياً للتفريغ الصوتي.
- **Silero VAD**: كشف بداية/نهاية كلامك محلياً — صفر توكنات.

## التشغيل (مرة واحدة — 10 دقائق)

### 1) استلزام واحد: Python 3.10+ على جهازك
من https://www.python.org/downloads أو `python3 --version` — إذا ≥ 3.10 كمل.

### 2) ثبّت المكتبات (داخل مجلد `livekit-agent`)
```bash
cd agency-cloudflare/livekit-agent
python3 -m venv .venv && source .venv/bin/activate   # ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3) حضّر المتغيرات
```bash
export LIVEKIT_URL=wss://المشروع-مالتك.livekit.cloud   # من wrangler.toml [vars] أو لوحة LiveKit
export LIVEKIT_API_KEY=...                             # API key
export LIVEKIT_API_SECRET=...                          # API secret
export COARENA_API_KEY=coa_...                         # نفس COARENA_API_KEY ب [vars]
export GROQ_API_KEY=gsk_...                            # https://console.groq.com — مجاني، بدون بطاقة
```
(القيم الحقيقية عندك — ما في شي هون، فقط أسماء المتغيرات. أو انسخ `.env.example` → `.env` واملأه.)

### 4) شغّل الـ Agent
```bash
python agent.py start
```
بيطبع سجلات الاتصال بـ LiveKit. خليه شغال (نافذة ترمينال مفتوحة).

### 5) افتح صفحة اللايف
```
https://<عنوان-الـ-Worker>/live
```
- اضغط ⚙️ واكتب الـ Worker URL + **CALL_SECRET** (نفس تبع /call) — بتخزن محلياً على جهازك بس.
- اضغط **«اتصل بجارفس لايف»** → اختر المشروع 1 (أو 2 لو الأول استنفد حصته).
- احكِ طبيعي — جارفس يرد بصوته الشامي. **قاطِعه** أي وقت — بيسكت ويسمعك.

## لما ما يشتغل — تشخيص سريع

| العَرَض | السبب | الحل |
|---|---|---|
| «LiveKit المشروع 1 مو مضبوط» (503) | `[vars]` ناقصها LIVEKIT_* | أضفها ب `wrangler.toml [vars]` أو `wrangler secret put` |
| الصفحة تتصل والروم يضل صامت | الـ Agent مو شغال | شغّل `python agent.py start` وشوف السجلات |
| «GROQ_API_KEY مو مضبوط» | ناقص مفتاح Groq | مجاني من console.groq.com خلال دقيقتين |
| جارفس يرد بالإنجليزي/فصحى | النموذج تجاهل التعليمات | جرّب `COARENA_MODEL=kimi-k3` أو `gemini-3-8-flash` |
| صوت روبوتي كثير | هذا أفضل صوتي سوري عند Edge | جرّب `EDGE_TTS_VOICE=ar-SA-HamedNeural` (سعودي) أو `ar-EG-SalmaNeural` |
| خلصت حصة Coarena اليوم | $5 استُهلكت | البوت يكمل تلقائياً على الاحتياط (Arena/Gemini…) — بـ اللايف: انتظر 3:00 AM أو بدّل `COARENA_MODEL` |
| قاطعت وما سكت | VAD حسّ إنك صوت خلفي | زوّد ضجيج الخلفية أو غيّر `min_silence_duration` بـ `silero.VAD.load()` |

## حدود صادقة
- الـ Agent يحتاج **جهاز شغال** (لابتوب/PC). للتشغيل 24/7 بلا جهاز: **`AWS_EC2_AR.md`** (دليل خطوة بخطوة — المالك عنده AWS بقيمة $100 رصيد مجاني ينتهي 2027-05-13) — أو Oracle Always Free (يتطلب بطاقة للتحقق فقط).
- تريد «كل شي محلي/على AWS وببلاش» (صوت Nabra/Polly بدل Edge TTS، وضع Hermes التجريبي، حساب الرصيد)؟ **`LOCAL_VOICE_AWS_AR.md`** — المعمارية الكاملة مع المقارنة والحسابات.
- LiveKit Cloud المجاني يعطيك (Bandwidth محدودة شهرياً) — مشروعان = ضعف. للمكالمة الشخصية هذا أكثر من كافٍ.
- Edge TTS بروتوكول غير رسمي — إذا Microsoft غيّرته يوم ممكن يكسر؛ البديل: صوت المتصفح بالصفحة، أو Workers AI TTS داخل البوت.
- Groq Whisper حصة يومية محدودة لكنها تتجدد — وتفريغ 10 دقائق كلام/يوم يكفي لمكالمة شخصية.

## ما هو **ليس** هذا المشروع
- **مكالمة هاتف حقيقية على رقم جوال (PSTN)** — غير موجودة مجاناً عند أي مزود. أقرب بديل مجاني: SIP (Linphone) بين تطبيقين — انظر README_AR.md قسم Linphone.
- **مكالمة على واتساب** — Meta ما بتتيحها مجاناً للبوتات.
