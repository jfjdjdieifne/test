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
4. جرّب مهمة خلفية: «دوّر على 3 شركات ديكور بالرياض وفحص مواقعهم واطرشلي التقرير» ← يرد فوراً بأنه أطلق المهمة، ثم يأتيك التقرير ويتصل عليك عبر CallMeBot. تابع بـ `/tasks`.

---

## التحديث والتدوير لاحقاً

- **أي مفتاح تريد تغيّره** (مثلاً بعد تدوير مفاتيح مالتك القديمة): أعد نفس أمر `npx wrangler secret put <NAME>` بالقيمة الجديدة — يتحدّث تلقائياً بدون deploy جديد.
- **لوجات البوت الحية:** `npx wrangler tail`
- **قائمة كل المفاتيح المضافة:** `npx wrangler secret list`
- **اختبارات المطور (بدون شبكة):** `node test.mjs` — 10 اختبارات تغطي الويبهوك، الصلاحيات، الأدوات، الخلفية، والتقسيم.

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
- **الردود الصوتية غير مفعّلة في النسخة الأولى** — استماع رسائلك الصوتية **شغال** (تفريغ عبر Gemini أو Groq Whisper إذا أضفته لاحقاً).
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

تم الفحص: **10/10 اختبارات ناجحة** (`node test.mjs`).
الملفات: `worker.js` (كل شيء في ملف واحد مستقل) + `wrangler.toml` + `test.mjs` + هذا الدليل.
