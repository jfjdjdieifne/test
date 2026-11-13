# 🧰 الـ Stack المجاني للوكالة — كله بمصاري = 0، وبلا بطاقة

> مكتوب: 2026-11-11 · ينطبق على الفرع `arena/749f0c04-test`. أوامر تمهيدية — **مرجع كل مشروع هو README بمستودعه** (التعليمات تتغيّر باستمرار).

## القاعدة الذهبية
كل الريبوهات «مجانية السوفتوير». لا يوجد ما هو «مجاني 100% وموثوق دائماً شغال» بلا اثنين من هذا:
1. **جهازك شغال دائماً** (ولو أثناء الدوام) + **Tailscale مجاني** للوصول إليه من تلفونك، أو
2. **VPS/Oracle Always Free** (يتطلب بطاقة للتحقق فقط — لا يُسحب منها شيء؛ لكنه خيارك وحدك).

الاستضافة المُدارة المجانية (Vercel/Render/Railway) = حدود، نوم، أو شروط استخدام تجاري — لا تُعتمد لحمل العملاء.

---

## المرحلة 1 — اليوم (بلا بطاقة، بلا خادم، بلا Docker)

| الأداة | ماذا تفعل | كيف |
|---|---|---|
| **Cap** | تسجيل تدقيق/عروض للعميل برابط واحد (بدل اجتماع) | حمّل من https://cap.so/download — أو self-host على جهازك (`docker compose up -d`) |
| **VoiceStudio** | استنساخ صوت شامي للإعلانات والفويسوفر — محلي وخاص | GitHub `debpalash/VoiceStudio` → Releases → installer لنظامك |
| **Agent-Reach** | بحث وتتبع سوشيال/منافسين من جهازك بلا رسوم API | `git clone` + README (Python CLI) — بحسابك فقط |
| **Connectors بأرينا** | Gmail/Drive/Calendar/GitHub من داخل المحادثة | زر الأدوات تحت صندوق الإدخال بأرينا ← Sign in بـ OAuth ← toggle كل turn |

## المرحلة 2 — على جهازك (مجاني؛ يعمل وأنت تفتح الجهاز)

```bash
# Docker Desktop أولاً: https://www.docker.com/products/docker-desktop/

# 1) WeKnora — قاعدة معرفة الوكالة (عقود/سياسات/كتالوج) — «اسأل مستنداتك» محلياً
git clone https://github.com/Tencent/WeKnora.git && cd WeKnora
cp .env.example .env        # عدّل .env (نموذج: Gemini بمفتاحك المجاني أو Ollama محلي)
docker compose pull && docker compose up -d   # Web UI: http://localhost · API: :8080

# 2) OmniRoute — «عقل حر» واحد يوصل 150+ مزود مجاني (Kimi/DeepSeek/Gemini/GLM...)
git clone https://github.com/cheaper-inference/OmniRoute.git && cd OmniRoute
# راجع README للتشغيل (Docker) — اربطه بجارفس كمنفذ OpenAI-compatible اختياري
# (جارفس بمشي بسلسلته الحالية بدونه؛ هذا توسيع لما يكون جهازك شغال)

# 3) OpenProject — إدارة مشاريع (فقط لو كبر الفريق) — ثقيل (≥2GB)
docker run -d -p 8080:80 -p 8443:443 -e SECRET_KEY_BASE=$(openssl rand -hex 32) \
  -v openproject-pg:/var/openproject/pgdata -v openproject-data:/var/openproject/assets \
  openproject/community:15

# 4) Cal.diy — صفحة حجز (للتجربة محلي؛ للعملاء انظر المرحلة 3)
git clone https://github.com/calcom/cal.diy.git && cd cal.diy
yarn && cp .env.example .env && yarn dx      # يحتاج Node 18+ وDocker — يفتح http://localhost:3000

# 5) Chatwoot — صندوق موحد (واتساب/تيليجرام/إيميل/ويب) — فقط مع 15–20+ عميل
# docker per README (صورة رسمية + Postgres + Redis) — يحتاج 2GB+ RAM
```

الوصول من تلفونك وأنت برا: ثبّت **Tailscale** (مجاني، بلا بطاقة) على الجهاز والتلفون ← تفتح `http://<جهازك-على-tailscale>` من أي مكان.

## المرحلة 3 — «دائماً شغال» للعملاء (هنا تُدفع الأشياء)

| الأداة | الطريق | التكلفة الحقيقية |
|---|---|---|
| **OpenSEO** | انشر على **Cloudflare مجاناً** (كوماند واحد؛ docs/SELF_HOSTING_CLOUDFLARE.md على حسابك المجاني) — بلا خادم | السوفتوير **مجاني**؛ **البيانات تحتاج DataForSEO** (دفع حسب الاستعمال، بلا اشتراك) — بدونها التطبيق فاضية |
| **Cal.diy للعملاء** | VPS صغير أو Oracle Always Free — ليس «مجاني بلا شروط» | يتطلب خادماً؛ البديل الفوري: Google Calendar + Connector بأرينا |
| **OmniRoute 24/7** | جهازك أو VPS | السوفتوير مجاني؛ الاستضافة المُدارة ليست مجانية |
| **Cap للعملاء بمساحة أكبر** | Cap Cloud أو self-host + S3 | السوفتوير مجاني |

## ❌ ما لا تشتريه بأي حال
- **OpenWhisper**: مكرر — جارفس أصلاً يفرغ (Groq/Workers AI/Gemini) وصفحة `/call` شغالة.
- **OpenHiggsfield**: واجهة مجانية؛ **التوليد مدفوع** (platform key) — لا تضع مفاتيح دفع فيها.
- **WeKnora/Chatwoot/OpenProject للعملاء على استضافة مجانية نوم/حدود**: ستنهار في أول ضغط — إما جهازك أو خادم حقيقي.

## ترتيب التنفيذ المقترح للوكالة (هذا الأسبوع)
1. Cap ← أول فيديو تدقيق لعميل اليوم. 2. Connectors بأرينا (Gmail/Drive/Calendar). 3. VoiceStudio (صوت شامي). 4. WeKnora (قاعدة معرفة للمكتب).
5. (قرار) OpenSEO على Cloudflare + كريديت DataForSEO صغير ← تدقيقات SEO مدفوعة فعلياً.
6. (لاحقاً) OmniRoute على جهازك؛ Chatwoot/OpenProject لما يكبر الفريق.

## تذكير أمان
- أي مفاتيح أو بيانات عملاء: على جهازك فقط، لا ترفعها لتطبيقات hosted مجانية «للفضول».
- لا تستخدم Agent-Reach على حسابات غيرك (تحتفظ كوكيز جلستك بيدك).

## المرحلة 2.5 — صوت جارفس اللايف (أُضيفت 2026-11-13)

المكالمة اللايف الحقيقية بجودة مكالمة كاملة الازدواجية صارت **مبنية وجاهزة بالمستودع** — كل حلقة مجانية، بلا بطاقة:

| الحلقة | الأداة المجانية |
|---|---|
| النقل (WebRTC) | **LiveKit Cloud — مشروعان مجانيان** (حصة مضاعفة) — التوكن يصدر من البوت `/livekit-token` |
| STT (صوت→نص) | **Groq whisper-large-v3-turbo** — حصة مجانية يومية، حساب من console.groq.com بلا بطاقة |
| العقل | **Coarena — Claude Fable 5.2** ($5/يوم مجاناً؛ + طلب $50/يوم و300 req/min معلّق للمراجعة) |
| TTS (نص→صوت شامي) | **Microsoft Edge Neural TTS** (`ar-SY-LaithNeural`) — بلا مفتاح وبلا حدود |
| VAD | **Silero** — يعمل محلياً على جهازك ولا يستهلك حصة |
| المكالمة من الهاتف/المتصفح | صفحة `/live` بالمستودع (`live.html`) على أي رابط https مجاني (GitHub Pages/Netlify Drop) |
| المكالمة بدون تثبيت | `/live` — صوت Neural عربي عبر EC2، شغّال دايماً بدون أي خطوة عندك |

التشغيل على جهازك: `agency-cloudflare/livekit-agent/README.md` — 10 دقائق مرة واحدة + نافذة ترمينال مفتوحة أثناء المكالمات.
وللتشغيل **24/7 بلا جهازك**: `livekit-agent/AWS_EC2_AR.md` — دليل EC2 كامل على حساب AWS المجاني للمالك ($100 رصيد، حتى 2027-05-13).

**Linphone SIP** (`sip:moudy.moray@sip.linphone.org`): SIP↔SIP مجاني بين تطبيقين — مفيد كخط داخلي مجاني؛ **ليس** بديلاً عن PSTN ولا عن مكالمات الجوال، ومفتاح الـ API مالتك مقيد على IP محدد (89.124.8.30) فلا يعمل من Cloudflare.
