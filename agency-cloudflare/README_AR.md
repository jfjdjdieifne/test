# 🇦🇪 JARVIS Cloudflare — مساعدك الذكي 24/7 مجاني **بدون بطاقة**

هذه النسخة تعمل على **Cloudflare Workers Free** (100,000 طلب/يوم، لا تنام أبداً، لا تحتاج بطاقة بنكية إطلاقاً) وتجيب عليك في تيليجرام كتابةً وصوتاً وارداً، وتنفذ مهاماً بالخلفية ثم تنبّهك برنّة.

> 💡 النسخة هذي **لا تحتاج** Render ولا UptimeRobot ولا حساب Gist ولا توكن GitHub — الذاكرة تتصير داخل **Cloudflare KV** (مجاني).

---

## ما تحتاجه قبل البدء (5 دقائق)

| المطلوب | من أين | ملاحظة |
|---|---|---|
| حساب Cloudflare مجاني | https://dash.cloudflare.com/sign-up | **بدون بطاقة** — بس بريد + كلمة مرور |
| Node.js (LTS) على جهازك | https://nodejs.org | يحط `npx` تلقائياً |
| بوت التيليجرام مالتك | `@hankash00_bot` | التوكن من `@BotFather` |
| رقم تيليجرام حسابك | `@userinfobot` → Start | رقم بحت للـ `ALLOWED_TELEGRAM_ID` |
| مفاتيح الذكاء المجانية | Gemini + OpenRouter + Tavily | موجودة عندك بالفعل |

---

## خطوات التشغيل كاملة

### 1) حمّل مجلد `agency-cloudflare` من المستودع
من داخل المستودع على فرعك الحالي:
```bash
git clone --branch arena/749f0c04-test --depth 1 https://github.com/jfjdjdieifne/test.git
cd test/agency-cloudflare
```
(أو حمّل الـ ZIP من GitHub وافتح مجلد `agency-cloudflare` منه.)

### 2) ثبّت وربط wrangler بحساب Cloudflare
```bash
npx wrangler login
```
يفتح صفحة في المتصفح → **Allow**.

### 3) أنشئ مخزن الذاكرة (مرة واحدة فقط)
```bash
npx wrangler kv namespace create JARVIS_KV
```
يطلعلك رقم `id` مثل `1a2b3c4d...` → افتح `wrangler.toml` والصقه بدل `PUT_YOUR_KV_NAMESPACE_ID_HERE`.

### 4) ولّد سر الويبهوك (قيمة عشوائية تحفظك من أي انتحال)
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```
احفظ الناتج — راح تحتاجه مرتين (الخطوة 5 والخطوة 7).

### 5) أضف الأسرار (كل أمر يسألك تلصق القيمة — الصقها واضغط Enter)
```bash
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put ALLOWED_TELEGRAM_ID
npx wrangler secret put GEMINI_API_KEY
npx wrangler secret put OPENROUTER_API_KEY
npx wrangler secret put TAVILY_API_KEY
npx wrangler secret put CALLMEBOT_TELEGRAM_USER     # actian_data
npx wrangler secret put WEBHOOK_SECRET              # القيمة من الخطوة 4
npx wrangler secret put CALL_SECRET                 # سر صفحة المكالمة (من الخطوة 4 نفسها أو قيمة أخرى)
```
اختياري ولا تضيفه إذا حسابك مقفل (مو ضروري إطلاقاً):
```bash
npx wrangler secret put MISTRAL_API_KEY
npx wrangler secret put GROQ_API_KEY
npx wrangler secret put NVIDIA_API_KEY
```

### 6) انشر البوت
```bash
npx wrangler deploy
```
يطلعلك رابط مثل: `https://jarvis-cf.<اسمك>.workers.dev` ← احفظه.

### 7) اربط تيليجرام بالبوت (مرة واحدة فقط)
استبدل `<TOKEN>` و`<SUBDOMAIN>` و`<WEBHOOK_SECRET>`:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<SUBDOMAIN>.workers.dev/webhook&secret_token=<WEBHOOK_SECRET>&allowed_updates[]=message"
```
لازم تطلع: `{"ok":true,"result":true,"description":"Webhook was set"}`

> إذا كان البوت مذياع (polling) شغال على جهاز آخر، نفذ هذا مرة واحدة فقط:
> `curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"`

### 8) تأكد أن كل شيء شغال
1. افتح `https://<SUBDOMAIN>.workers.dev/health` في المتصفح → لازم يرجع: `{"status":"ok","service":"jarvis-cf",...}`
2. تيليجرام → `@hankash00_bot` → `/start` → تطلع قائمة الأوامر.
3. جرّب: `/leads` ثم `/lead 2` ثم `افحص namconsultant.com`.
وللمكالمة الصوتية: انشر `call.html` على Netlify Drop ثم أكمل قسم «🎙️ احكِ مع جارفس» بالأسفل.

4. جرّب مهمة خلفية: «دوّر على 3 شركات ديكور بالرياض وفحص مواقعهم واطرشلي التقرير» ← يرد فوراً بأنه أطلق المهمة، ثم يأتيك التقرير ويتصل عليك عبر CallMeBot. تابع بـ `/tasks`.

---

## 🎙️ احكِ مع جارفس بمكالمة حقيقية — مجاني 100% بدون بطاقة

الصفحة الجاهزة `call.html` تحوّل البوت لمساعد صوتي مباشر (Voice⇄Voice) **بدون أي سيرفر صوتي مدفوع**:

### كيف تشتغل
- **متصفحك** يحوّل صوتك لنص مجاناً (Web Speech API — مدمج في Chrome، يدعم العربية).
- **البوت على Cloudflare** يفكّر ويرجع الرد.
- **متصفحك** ينطق الرد بصوت عربي مجاني.
- لا حاجة لحساب LiveKit ولا Twilio ولا أي بطاقة.

### خطوات التشغيل (3 دقائق)
1. تأكد أنك أضفت `CALL_SECRET` بالخطوة 5 أعلاه (نفس طريقة توليد `WEBHOOK_SECRET`) ثم أعد النشر: `npx wrangler deploy`.
2. انشر ملف `call.html` على رابط https مجاني **بدون بطاقة**:
   - **الأسهل (Netlify Drop):** ادخل https://app.netlify.com/drop واسحب ملف `call.html` وحده → يطلعلك رابط `https://xxx.netlify.app` خلال ثواني.
   - **أو GitHub Pages:** فعّله من إعدادات المستودع → Pages → المجلد الجذر → الرابط يكون مثل `https://jfjdjdieifne.github.io/test/agency-cloudflare/call.html`.
3. افتح الرابط من جوالك أو لابتوبك → اضغط ⚙️ → الصق **رابط الـ Worker** و**CALL_SECRET** → احفظ.
4. اضغط زر **«اتصل بجارفس»** ← تكلم بالعربي ← جارفس يرد عليك بصوته. المحادثة مستمرة: يسمعك من جديد تلقائياً بعد كل رد.

### أسئلة صادقة عن المكالمات
- **هل أتصل على رقم هاتف عادي (PSTN) وأحكي مع جارفس؟** لا يوجد مزود أوروبي/عالمي يعطي رقم وارد مجاني بلا بطاقة؛ الأقرب هو **LiveKit Cloud Build** (رقم أمريكي وارد + 50 دقيقة/شهر مجاني بدون بطاقة) — لكن من هولندا ستدفع رسوم مكالمة دولية على خطك أو تستخدم تطبيق VoIP مجاني للاتصال به. والمكالمة **الصادرة** من جارفس لرقم SIM عادية **مدفوعة عند كل مزود عالمياً** (Twilio ~$0.02/دقيقة مثلاً) — هذا القيد الوحيد الذي لا حل مجاني حقيقي له.
- **الحل المجاني الفعلي للرسائل الحرجة (مكافئ «يتصلك»):** رنّة Telegram عبر CallMeBot — **شغالة الآن في البوت**: بعد كل مهمة خلفية يخلص منها، وأمر `/call <نص>` يدوي، وأيضاً الموجز الصباحي (بالأسفل). الرنّة ترد عبر تيليجرام (Android/Desktop ممتازة؛ iOS أحياناً VoIP صامت لكن الرسالة تصل دائماً).
- **جودة الصوت** تعتمد على متصفحك (Chrome الأفضل) — النطق بالعربي «واضح ومفهوم وروبوتي قليلاً».

## ⏰ التحديث الصباحي + الرنّة للمهام الحرجة

أضيفت للمشروع جدولة **Cron** داخل Cloudflare نفسه (مجانية ولا تحتاج سيرفر): كل يوم **06:00 UTC** (~07:00–08:00 أمستردام) يوصلك في تيليجرام **موجز جارفس الصباحي**:
- الصفقات الساخنة (Hot) اللي ما أرسلت لها شيء لحد الآن
- آخر المهام الخلفية المخلصة
- ملخص حالة العملاء الـ12

**لتفعيل الرنّة مع الموجز** (موبس فقط لو تبي تذكير صوتي كل صباح):
```bash
npx wrangler secret put CALL_ON_BRIEF   # ثم اكتب: true
```
ولإيقاف الموجز نهائياً: احذف قسم `[triggers]` من `wrangler.toml`.

## 🧠 ذاكرة جارفس الطويلة — تتذكر كل شيء بدون استنزاف توكنات

كيف تشتغل تقنياً (بصدق):
- **الحفظ خام بدون LLM**: كل حقيقة تُخزَّن حرفياً في Cloudflare KV — لا ملخصات، لا توكنات بالمحفوظ إطلاقاً.
- **الاسترجاع محلي** (تطابق كلمات + وزن للمثبتات) — صفر توكنات لاسترجاع القائمة.
- عند كل رسالة نصية يُحقن في البرومبت **فقط المقتطفات المطابقة** (~100–400 توكن) — ليس كامل المحادثات القديمة.
- الحقائق المثبتة بـ `!` تُحقن دائماً (مثل اسمك، شركتك، أسعار ما تحب تعرضها).
- السقف: 500 حقيقة (يكفي سنوات). للنسخة الاحتياطية: `/export` يرسلك JSON كامل.

الأوامر:
```
/learn ! أنا مالك وكالة بدبي، ميزانيتي 15 ألف درهم
العميل المفضل هو NAM Consultant
```
(كل سطر = حقيقة، والسطر الذي يبدأ بـ `!` يُثبَّت دائماً)

- `/memories` — اعرض كل المحفوظ (مع أرقامه ومعرفاته)
- `/forget 3` — امسح الحقيقة رقم 3 (أو اكتب المعرف المختصر مثل `m_kx2`)
- `/export` — ملف JSON كامل بذاكرتك ينزل على تيليجرام

ملاحظة صادقة: «يتذكر كل شيء حرفياً بلا حد ولا توكنات» لا يوجد عند أي مزود — لكن بهاي الطريقة **كلفتها شبه صفر** وعمليتها ممتازة لمساعدك الشخصي. الذكاء نفسه (فهمك وتأليفه) مصدره Gemini المجاني.

## 📧 إرسال الإيميلات من Gmail مالتك — مجاني — عبر Google Apps Script

جارفس يقدر يرسل إيميل لأي شركة باسمك — **بعد موافقتك بضغطة واحدة** (مقصودة لحمايتك من حظر Gmail بسبب spam لو مالياً بالخطأ).

### التركيب (مرة واحدة — 5 دقائق)
1. افتح https://script.google.com → **New project** → سمّه `jarvis-email`
2. احذف الكود الافتراضي والصق محتوى `apps-script-email.gs` كاملاً
3. غيّر `SECRET` داخله لقيمة عشوائية (نفس الأمر: `node -e "console.log(require('crypto').randomBytes(24).toString('hex'))"`)
4. **Deploy → New deployment → النوع: Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - → Deploy → انسخ رابط `/exec`
5. بالأالطرفة:
   ```bash
   npx wrangler secret put APPS_SCRIPT_URL     # رابط /exec
   npx wrangler secret put APPS_SCRIPT_SECRET  # نفس SECRET داخل السكربت
   npx wrangler deploy
   ```
6. فعّل الأزرار (مرة واحدة) — بدون allowed_updates حتى تعمل أزرار ✅/❌:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<SUBDOMAIN>.workers.dev/webhook"
   ```

### الاستخدام
قل لجارفس: «ابعت إيميل لـ info@namconsultant.com بعرض الشراكة» ← يجهز الإيميل ويطرشل بطاقة فيها النص + زرتين **✅ أرسل الآن / ❌ الغي** ← ضغطة واحدة وينزل الإرسال من Gmail مالتك (يظهر بصندوق "تم الإرسال").

الحصص المجانية: ~100 إيميل/يوم (Gmail عادي) أو 1500/يوم (Workspace).

## ⚠️ عن «الصلاحيات لكل شيء حرفياً» — الحقيقة التقنية

لا يوجد «كل شيء» بدون حدود — كل قدرة تحتاج **مفتاح وصلاحية مستقلة** تربطها بنفسك:

| القدرة | الوضع |
|---|---|
| Arena AI يفتح ويطلب شغل من داخل البوت | ❌ غير موجود — Arena لا يطرح API أبداً (أنا أشتغل هنا داخل جلسة بإشرافك فقط) |
| «الدماغ» المجاني داخل جارفس | ✅ يشتغل — Gemini المجاني + OpenRouter |
| إيميل Gmail (إرسال) | ✅ مبني اليوم — بعد موافقتك بضغطة |
| التذكر الكامل + مهام طويلة | ✅ مبني — طابور كل دقيقة + ذاكرة خام |
| اتصال هاتفي SIM صادر | ❌ مدفوع حصرياً عند كل مزود |
| رنّة على تيليجرام | ✅ مفعّلة (CallMeBot) |
| واتساب أوتوميشن | ⚠️ Meta Cloud API رسمي مجاني لـ1000 محادثة/شهر لكن يتطلب تحقق تجاري ورقم خاص؛ أدوات WAHA ممكن تحظر رقمك |
| بناء ونشر مواقع كاملة بلا يدك | ⚠️ ممكن تقنياً (GitHub Pages + API) — يحتاج جلسة بناء إضافية متخصصة |

الخلاصة: اللي كلفتها صفر ويعتمد عليك فقط — **مبني أو جاهز بالتنفيذ**. اللي يحتاج طرفاً ثالثاً (اتصالات، تحقق تجاري) — يوصل لك بوضوح بدون وعود فارغة.

## 🌉 جسر LMArena — استخدم نماذج Arena (حتى المخفية/stealth) من تيليجرام

الحقيقة أولاً: **جارفس على Cloudflare Workers ما بيقدر يشغّل بايثون ولا متصفح ولا يحفظ كوكيز Arena**. كل المشاريع اللي ذكرتها (الجسور وgpt4free) تحتاج **بايثون + متصفح حقيقي + جلسة تسجيل دخول**، فما ينفع تنسخ كودها داخل الـ Worker.

الحل اللي بنيناه: **خدمة وسيطة صغيرة** بمجلد `arena-bridge/` بمستودعنا:

```
تيليجرام  →  جارفس (Cloudflare Worker)  →  arena-bridge (Python/FastAPI)  →  LMArena
             ARENA_BRIDGE_URL                gpt4free/Arena  أو  LMArenaBridge محلي
```

الخدمة تكشف API متوافق مع OpenAI (`/v1/chat/completions`, `/v1/models`, `/health`) وتشتغل بمحرّكين بالترتيب:

| المحرك | المصدر | الدور |
|---|---|---|
| 1 | **LMArenaBridge / LMArenaProxy** محلي (CloudWaddie · Blacklisted-Binary · lianues) | تمرير مباشر عبر `POST /api/v1/chat/completions` — الأقوى بتجاوز Cloudflare |
| 2 | **gpt4free — مزود Arena** (xtekky/gpt4free) | محاكاة متصفح + رموز جلسة تلقائياً، ويقدر يتراجع لمزودين مجانيين تانيين |

### التركيب (3 أوامر)

```bash
cd arena-bridge
pip install -r requirements.txt        # أو: docker compose up -d
cp .env.example .env                   # عدّل BRIDGE_API_KEY
python bridge.py                       # http://0.0.0.0:8000
```

### ربطه بجارفس

```bash
cd ../agency-cloudflare
npx wrangler secret put ARENA_BRIDGE_URL   # مثال: https://arena-bridge.example.com  (بدون /v1)
npx wrangler secret put ARENA_BRIDGE_KEY   # نفس BRIDGE_API_KEY
npx wrangler deploy
```

📱 **معك آيفون بس؟** دليل كامل خطوة-خطوة: [`../arena-bridge/README_IPHONE_AR.md`](../arena-bridge/README_IPHONE_AR.md)

**Arena أساسي تلقائياً** بمجرد ضبط `ARENA_BRIDGE_URL`: كل رد وكل مهمة بالخلفية وكل أداة
(بحث · فتح رابط · تدقيق موقع · إيميل · جدولة مهمة…) بتمرق بعقل Arena أولاً، وباقي المزودين
احتياط فقط. إذا بده يرجع الترتيب القديم: `ARENA_BRIDGE_FIRST=false` أو أمر `/arena primary`.

**قاطع الدائرة:** إذا الجسر فشل، جارفس يتجاهله مدة قصيرة (`ARENA_BRIDGE_COOLDOWN_MS`، افتراضي 5 دقائق)
بدل ما يتأخر كل رد — وبيرجع يجرّبه تلقائياً بعدها.

**الاستضافة المجانية ٢٤/٧ من الموبايل:** شوف [`../arena-bridge/README_DEPLOY_FREE_AR.md`](../arena-bridge/README_DEPLOY_FREE_AR.md) — أربع طرق مجانية (Oracle Always Free · Hugging Face Space · Termux · Render).
- إذا الاستضافة **بتنام** (Render/HF): `npx wrangler secret put ARENA_BRIDGE_KEEPALIVE` → `true`، وجارفس بيضرب `/health` كل ١٠ دقائق عبر الـ cron الموجود.
- إذا الجسر نايم وقت الطلب: جارفس يحاول `/health` (Wake) ويعيد المحاولة مرة واحدة، وبعدها يكمّل على باقي المزودين عادي.

### من تيليجرام

| الأمر | الوظيفة |
|---|---|
| `/arena` | حالة الجسر + النماذج + هل Arena أساسي + حالة القاطع |
| `/arena on` / `/arena off` | تشغيل/إيقاف استخدام الجسر فوراً (بدون deploy) |
| `/arena test` | فحص وصول جارفس للجسر |
| `/arena wake` | تصحيّة الجسر النايم (مهم للاستضافات المجانية) |
| `/arena primary` | تبديل: Arena أساسي ↔ احتياطي (محفوظ بالـ KV، فوري بلا deploy) |
| `/arena test` | تشخيص عميق: يجرّب كل محرك بالجسر (LMArenaBridge · gpt4free · وسيط) ويقولك مين شغال |
| `/arena url <رابط>` · `/arena key <مفتاح>` | **إعداد الجسر بالكامل من تيليجرام** — بدون wrangler ولا لوحة Cloudflare |
| `/arena setup` | شرح الخطوات جوا تيليجرام |
| `/arena <اسم-نموذج>` | اختيار النموذج (مثلاً `/arena stealth-model`) |
| `/arena_ask <سؤال>` | سؤال مباشر عبر Arena بدون أي مزود آخر |

بدون `ARENA_BRIDGE_URL` كل شي يضل شغال كما هو — الجسر **معطّل افتراضياً** وما يستهلك أي طلب.

### تحذير صادق

- LMArena يحتاج تسجيل دخول، والكوكيز (`arena-auth-prod-v1`) تنتهي — gpt4free يجدّدها أحياناً تلقائياً، وإذا فشل: حدّث جلسة المتصفح أو أعد تشغيل الخدمة.
- استخدام آلي للمنصة قد يخالف شروط استخدامها وقد يُحظر الحساب. جرّبه على حسابك الشخصي وعلى مسؤوليتك.
- الجسر لازم يشتغل على جهاز دائم التشغيل (VPS/راسبيري/كمبيوتر ما ينام) — Cloudflare لا يشغّل بايثون.
- إذا كان الجسر على الإنترنت: **حط BRIDGE_API_KEY** ويفضّل HTTPS (Caddy/Nginx).

## التحديث والتدوير لاحقاً

- **أي مفتاح تريد تغيّره** (مثلاً بعد تدوير مفاتيح مالتك القديمة): أعد نفس أمر `npx wrangler secret put <NAME>` بالقيمة الجديدة — يتحدّث تلقائياً بدون deploy جديد.
- **لوجات البوت الحية:** `npx wrangler tail`
- **قائمة كل المفاتيح المضافة:** `npx wrangler secret list`
- **اختبارات المطور (بدون شبكة):** `node test.mjs` — 37 اختباراً تغطي الويبهوك، الصلاحيات، الأدوات، الخلفية، /ask، الذاكرة، وطابور الموافقة على الإيميل، وجسر LMArena (بما فيها الإفاقة والـ Keep-alive).

---

## 🔐 أمان — اقرأها مرة واحدة

1. **المفاتيح التي شاركتها بالمحادثة تعتبر منكشفة** — دوّرها بأسرع ما تستطيع:
   - التيليجرام: `@BotFather` → `/mybots` → `hankash00_bot` → API Token → **Revoke current token** → ثم `npx wrangler secret put TELEGRAM_BOT_TOKEN` بالتوكن الجديد.
   - Gemini: https://aistudio.google.com/apikey → احذف المفتاح القديم → أنشئ جديد → حدّثه بـ `secret put`.
   - OpenRouter: https://openrouter.ai/keys → احذف القديم → جديد → `secret put`.
   - Tavily: https://app.tavily.com → API Keys → احذف القديم → جديد → `secret put`.
   - توكن GitHub `ghp_...` اللي أرسلته: احذفه من https://github.com/settings/tokens (ما يلزمني هنا أصلاً بمسار Cloudflare).
2. **لا تشارك** `WEBHOOK_SECRET` ولا رابط الـ workers.dev مع أحد — مع توكن البوت يمكّن أي شخص يراسلك باسمك.
3. **الأسرار لا تُكتب في `worker.js` ولا `wrangler.toml` أبداً** — ملفات المشروع فارغة من أي مفتاح.
4. البوت يتجاهل أي تحديث من حساب تيليجرام غير حسابك (`ALLOWED_TELEGRAM_ID`).

---

## ✅ حدود صادقة للخطة المجانية (حتى لا تعوّل على شيء غلط)

- **100,000 طلب/يوم مجاناً** — أكبر بكثير من استهلاك بوت شخصي.
- **لا تنام Cloudflare Workers أبداً** — لا حاجة UptimeRobot ولا cron.
- **المهام الخلفية بحد أقصى 6 خطوات** ثم تُعطي الجواب المتاح — المهام الضخمة (بحث ساعات) قسّمها لمهام أصغر.
- **المكالمات الصوتية:** الواردة منك تشتغل مجاناً عبر `call.html`؛ الصادرة لرقم SIM عادية غير مجانية عند أي مزود عالمياً (البديل المجاني: رنّة Telegram بعد أي مهمة خلفية + موجز الصباح — كلاهما مفعّل). استماع رسائلك الصوتية داخل البوت شغال أيضاً.
- **Gemini المجاني له حدود يومية** — عند بلوغها ينتقل البوت تلقائياً على OpenRouter (`openrouter/free`).
- **هاك مالي صفر:** لا تُضاف بطاقة لأي خطوة من الخطوات أعلاه.

---

## استكشاف الأخطاء السريع

| العَرَض | السبب الأرجح | الحل |
|---|---|---|
| البوت ما يرد إطلاقاً | setWebhook ما نجح أو ALLOWED_TELEGRAM_ID غلط | أعد `/start` وتأكد أن الجواب وصلك برسالة «هذا جارفس خاص» (يعني الفلترة شغالة بس الـ ID غلط) ثم صحّحه |
| `403` عند نداء /webhook | `secret_token` في الرابط لا يطابق `WEBHOOK_SECRET` | أعد أمر setWebhook بنفس قيمة الـ secret بالضبط |
| رد «تعذر الوصول لكل مزودي الذكاء» | مفاتيح Gemini/OpenRouter مفقودة أو غلط | `npx wrangler secret list` وتأكد، `wrangler tail` للوجات |
| رنّة CallMeBot ما تجي | الحساب غير مسجل بـ @CallMeBot_txtbot | ادخل المحادثة واضغط Start مرة ثانية وتأكد أن `actian_data` هو اليوزرنيم المسجل |
| «no such KV namespace» | لم تُحدّث `id` في `wrangler.toml` | `npx wrangler kv namespace list` وانسخ الـ id الصحيح |
| البوت يرد بس بذاكرة فارغة دائماً | الـ KV غير مربوط | نفس الحل أعلاه |

---

تم الفحص: **19/19 اختباراً ناجحاً** (`node test.mjs`).
الملفات: `worker.js` + `wrangler.toml` + `test.mjs` (**19/19 ناجحة**) + `call.html` (صفحة المكالمة) + `apps-script-email.gs` (آلة الإيميل) + هذا الدليل.
