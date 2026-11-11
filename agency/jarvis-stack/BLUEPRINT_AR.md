# المخطط العملي خطوة بخطوة: جارفس 24/7 ببلاش ($0) بأقوى الموديلات وتقريباً لا ينتهي

هذا الدليل مخصص لتشغيل الكود الجاهز في هذا المجلد (`jarvis_telegram_agent.py`) بحيث:
1. يشتغل **24 ساعة على السحابة بـ $0** (حتى ولابتوبك مطفأ تماماً).
2. يستخدم **أقوى الموديلات المجانية في 2026 بالتناوب التلقائي** (فإذا امتلأ حدّ أحدهم ينتقل للثاني فوراً — و**Mistral وحدها تعطيك قرابة مليار توكن شهرياً مجاناً!**).
3. تحاكيه على **تيليجرام بالصوت والكتابة** متى شئت.
4. تعطيه أي مهمة كبيرة فيشتغل عليها **بالخلفية** (`start_background_task`) وأنت تكمل يومك، ثم يراسلك **أو يتصل عليك على تيليجرام عبر CallMeBot** فور انتهائها أو عندما يحتاج قرارك!

---

## الخطوة 1: جهّز المفاتيح المجانية (10 دقائق — بدون بطاقة بنكية)

1. **إنشاء البوت على تيليجرام:**
   - افتح تيليجرام وابحث عن `@BotFather` ← اضغط Start ← أرسل `/newbot`.
   - اختر اسماً (مثلاً `My Jarvis`) واسم مستخدم ينتهي بـ `bot` (مثلاً `ali_jarvis_2026_bot`).
   - انسخ رمز التوكن الطويل (`TELEGRAM_BOT_TOKEN`).
2. **حماية البوت ليسمع كلامك أنت فقط:**
   - ابحث في تيليجرام عن `@userinfobot` ← اضغط Start ← انسخ رقم `Id` الخاص بك (`ALLOWED_TELEGRAM_ID`).
3. **تفعيل أن يتصل بك جارفس ويرنّ جوالك على تيليجرام (مجاني للاستخدام الشخصي):**
   - ابحث في تيليجرام عن `@CallMeBot_txtbot` ← أرسل له `/start` (أو افتح `https://api2.callmebot.com/txt/login.php`).
   - احفظ اسم مستخدمك في تيليجرام مع `@` (مثلاً `CALLMEBOT_TELEGRAM_USER=@yourname`).
   - *ملاحظة تقنية من CallMeBot:* يرنّ تلقائياً وبثبات على أندرويد والكمبيوتر؛ أما على iOS فأحياناً يرن الجوال مع خلل صامت في VoIP تيليجرام (لكن الرسالة الصوتية والنصية تصلك بكل الأحوال).
4. **مفاتيح أقوى موديلات الذكاء المجانية (ضع مفتاحين أو كلّهم للتناوب اللانهائي تقريباً):**
   - **Google AI Studio (`GEMINI_API_KEY`):** من `https://aistudio.google.com/apikey` — يعطيك **Gemini 2.5 Flash / 2.5 Pro** بسياق مليون توكن مجاناً بدون بطاقة.
   - **Mistral AI (`MISTRAL_API_KEY`):** من `https://console.mistral.ai/api-keys` — تحقق برقم الهاتف فقط بدون بطاقة، ويعطيك على باقة Experiment المجانية **`mistral-large-latest` و `mistral-small-latest` بحد يقارب 1 مليار توكن شهرياً (لا ينتهي عملياً!)**.
   - **Groq (`GROQ_API_KEY`):** من `https://console.groq.com/keys` — بدون بطاقة، يشغّل **`llama-3.3-70b-versatile`** بسرعة صاروخية + **تفريغ رسائلك الصوتية عبر `whisper-large-v3-turbo` مجاناً**.
   - **NVIDIA NIM (`NVIDIA_API_KEY`):** من `https://build.nvidia.com/` — بدون بطاقة، يعطيك **1,000 رصيد تجريبي مجاني** لموديلات ثقيلة مثل DeepSeek / Llama 3.3 / Qwen.
   - **OpenRouter (`OPENROUTER_API_KEY`):** من `https://openrouter.ai/keys` — بدون بطاقة، مفتاح احتياط يشغل الموزع المجاني `openrouter/free`.
   - **اختياري للبحث العميق (`TAVILY_API_KEY`):** من `https://tavily.com` — **1,000 بحث ويب شهرياً مجاناً بدون بطاقة** (وإن لم تضعه يستخدم البوت بحث DuckDuckGo مجاناً تلقائياً).

---

## الخطوة 2: تشغيله 24/7 في السحابة مجاناً (اختر الطريقة الأسهل لك)

### الطريقة 1 (الأسهل والأسرع — 0 بطاقة بنكية، 0 نوم): **Cloudflare Workers + ربط GitHub**
لأننا جهّزنا لك ملف `wrangler.jsonc` وملف `agency/jarvis-stack/cf_worker.js` في المستودع مباشرة، فإن ربط GitHub على Cloudflare ينشر لك **موقع الوكالة + جارفس الصوتي + بوت تيليجرام 24/7 + مجدول المهام كل دقيقة** بضغطة واحدة مجاناً (100,000 طلب/يوم ولا ينام أبداً!):

1. في لوحة **Cloudflare (`dash.cloudflare.com`)** ← **Workers & Pages** ← **Create application**:
   - **لا تختر** `Upload your static files` (لأنها للملفات فقط بدون سيرفر البوت).
   - اختر **Import a repository (GitHub)** وسجّل/اربط حسابك في GitHub.
2. اختر مستودعك **`jfjdjdieifne/test`** واضبط الإعدادات هكذا:
   - **Project/Worker name:** `jarvis-24-7`
   - **Git branch / Production branch:** غيّره من `main` إلى **`arena/00d98017-test`** ⚠️ *(مهم جداً)*
   - **Build command:** اتركه **فارغاً**
   - **Deploy command:** اتركه الافتراضي **`npx wrangler deploy`**
   - **Root directory:** اتركه الافتراضي **`/`**
3. اضغط **Save and Deploy** وانتظر ~40 ثانية حتى يظهر رابطك مثل `https://jarvis-24-7.xxx.workers.dev`.
4. من داخل المشروع في Cloudflare ادخل **Settings → Variables and Secrets → Add** وأضف:
   - `TELEGRAM_BOT_TOKEN` (من `@BotFather`)
   - `ALLOWED_TELEGRAM_ID` (من `@userinfobot`)
   - مفتاحاً أو أكثر من مفاتيح الذكاء (`GEMINI_API_KEY`، `MISTRAL_API_KEY`، `GROQ_API_KEY`، `NVIDIA_API_KEY`، `OPENROUTER_API_KEY`)
   - *(اختياري)* `CALLMEBOT_TELEGRAM_USER` + `GITHUB_GIST_ID` + `GITHUB_TOKEN` (لتفعيل الذاكرة والمهام المجدولة في الخلفية كل دقيقة).
   - اضغط **Deploy / Save** لحفظ المتغيرات.
5. افتح رابط موقعك متبوعاً بـ **`/setup`** (مثلاً `https://jarvis-24-7.xxx.workers.dev/setup`) ← اكتب رقم الـ Telegram ID الخاص بك واضغط **🔗 ربط بوت تيليجرام الآن**.
6. مبروك! افتح تيليجرام وأرسل `/start` للبوت — يعمل 24/7 بلا توقف وبـ $0!

---

### الطريقة 2 (بديل بالبايثون الكامل بدون بطاقة): **Render Free + UptimeRobot**
خطة **Render Free Web Service** تعطيك **750 ساعة شهرياً مجاناً بدون بطاقة بنكية** (الشهر فيه 720–744 ساعة، يعني تغطي الشهر كله 24/7!).
ولكي لا ينام السيرفر بعد 15 دقيقة خمول، أضفنا في `jarvis_telegram_agent.py` منفذ فحص `/health`؛ فقط تجعل موقع مجاني مثل UptimeRobot ينكز الرابط كل 10 دقائق!

1. ارفع هذا المستودع على حسابك في GitHub (أو اعمل Fork لـ `jfjdjdieifne/test` واختر فرع الكود).
2. *(اختياري لحفظ الذاكرة للأبد حتى لو أعاد Render تشغيل الحاوية):*
   - أنشئ في GitHub ملف **Secret Gist** سري اسمه `jarvis_state.json` ومحتواه `{}`، وانسخ `GITHUB_GIST_ID` من الرابط + أنشئ **Personal Access Token** بصلاحية `gist` فقط (`GITHUB_TOKEN`).
3. ادخل `https://render.com` وسجّل مجاناً عبر حسابك في GitHub (**لا يطلب بطاقة**).
4. اضغط **New +** ← **Web Service** ← اختر المستودع، وأدخل الإعدادات التالية بالضبط:
   - **Name:** `my-jarvis-24-7`
   - **Branch:** `arena/00d98017-test` (أو الفرع الذي نسخت إليه)
   - **Root Directory:** `agency/jarvis-stack`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 jarvis_telegram_agent.py`
   - **Instance Type:** `Free`
5. في خانة **Environment Variables** أضف مفاتيحك:
   `TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_ID`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `GROQ_API_KEY`, `CALLMEBOT_TELEGRAM_USER` (وباقي المفاتيح التي تريدها).
6. اضغط **Deploy Web Service** وانتظر دقيقة حتى يظهر رابطك مثل `https://my-jarvis-24-7.onrender.com`.
7. **لمنع النوم 24/7:** افتح `https://uptimerobot.com` (مجاني بدون بطاقة) ← **Add New Monitor** ← النوع **HTTP(s)** ← الرابط `https://my-jarvis-24-7.onrender.com/health` ← كل **10 minutes** ← حفظ!
   - انتهينا! الآن البوت مستيقظ **24/7 بتكلفة $0 وبدون بطاقة بنكية**!

---

### الطريقة B: إذا عندك بطاقة بنكية للتحقق فقط (لا يُخصم منها شيء) — Oracle Cloud Always Free (الأقوى للأبد)
- ستحصل على سيرفر Linux كامل **2 OCPUs + 12 GB RAM + 200 GB SSD** مجاناً للأبد بدون نوم وبدون حاجة لـ UptimeRobot أو Gist!
- داخل السيرفر:
  ```bash
  git clone -b arena/00d98017-test https://github.com/jfjdjdieifne/test.git
  cd test/agency/jarvis-stack
  cp .env.example .env
  nano .env   # ضع مفاتيحك هنا واحفظ
  pip install -r requirements.txt
  nohup python3 jarvis_telegram_agent.py > jarvis.log 2>&1 &
  ```
- ولإبقائه شغالاً تلقائياً بعد أي إعادة تشغيل للسيرفر، شغّله كخدمة `systemd` (أو داخل Docker).

---

## الخطوة 3: كيف تستخدمه في حياتك اليومية؟

1. افتح بوتك في تيليجرام وأرسل `/start`.
2. **حاكيه صوت أو كتابة في أي وقت:** أرسل رسالة صوتية باللهجة العربية أو الإنجليزية؛ سيفرّغها بـ Whisper ويرد عليك كتابة + مقطع صوتي عربي طبيعي!
3. **أعطه مهمة تشتغل بالخلفية وأنت تقفل التطبيق:**
   - مثال: *"ابحث لي في الويب عن 5 عيادات تجميل جديدة في أبوظبي، افحص مواقعهم واستخرج الثغرات، وجهز لي رسائل واتساب جاهزة، واشتغل بالخلفية ورن عليّ تيليجرام بس تخلص أو إذا احتجت قراري."*
   - سيجاوبك فوراً أنه بدأ المهمة برقمها (مثلاً `#task_12345`) ويترك الشات حراً، ويعمل بالخلفية عدة خطوات بحث وفحص وتحليل، ثم يرسل لك التقرير الكامل **ويرن على تيليجرام جوالك ليخبرك أنه جاهز**!
4. أرسل `/tasks` في أي وقت لمعرفة حالة المهام الشغالة في الخلفية.

---

## التحديث الجديد: المكالمة الصوتية الحية (`/call`) + التنفيذ البرمجي المستقل (`/mission`) بدون Arena.ai

### 1. حل مشكلة المكالمات نهائياً — مكالمة صوتية ثنائية حية (`/call`)
- بدل الاعتماد على CallMeBot وحده (الذي يعاني من انقطاع الصوت على iOS وحد 256 حرف إنجليزي)، أضفنا شاشة **`/call.html`** المدعومة بتقنية **Gemini 3.8 Live WebSocket** مع نظام تحويل احتياطي تلقائي لـ Groq/Mistral:
  1. افتح بوتك في تيليجرام وأرسل **`/call`** ← سيظهر لك زر **`📞 افتح المكالمة الصوتية الحية`** موقعاً برمز حماية مؤقت.
  2. اضغطه وتحدّث بالصوت مباشرة ذهاباً وإياباً (ويمكنك مقاطعته بأي وقت وتكليفه بالبحث أو إرسال مهام للخلفية!).

### 2. تنفيذ المهام الثقيلة على خادم Linux مستقل مجاني (`/mission`) — البديل الشرعي لـ Arena.ai
- بما أن `arena.ai` لا يوفر API للمطورين، وأدوات سحب الكوكيز (`gpt4free` / `LMArenaBridge`) تتوقف باستمرار برموز `401/403` وتحديات Cloudflare Turnstile وتعرّض حسابك للحظر:
  - بنينا بديلاً رسمياً بـ **$0** يعمل داخل **GitHub Actions Linux VM** (دقائق مجانية غير محدودة على المستودعات العامة، أو 2,000 دقيقة مجانية/شهر للخاص): `.github/workflows/jarvis_worker.yml` + `gh_autonomous_worker.py`.
  - يمتلك العامل صلاحية البحث في الويب، فحص المواقع، تشغيل Python، بناء صفحات HTML/CSV تحت `agency/output/`، ثم رفعها تلقائياً لتنشر فوراً على رابط Cloudflare وإرسال النتيجة لك على تيليجرام!
  - **لتفعيله في 30 ثانية:**
    1. اقبل دمج الفرع **`arena/00d98017-test`** إلى **`main`** على GitHub (لأن GitHub يشترط وجود ملف `jarvis_worker.yml` في الفرع الافتراضي `main` للسماح بتشغيله عن بُعد).
    2. من إعدادات المستودع في GitHub (**Settings → Secrets and variables → Actions**) أضف مفاتيحك (`TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_ID`, `GEMINI_API_KEY` ...).
    3. تأكد أن `GITHUB_TOKEN` في **Cloudflare Secrets** يملك صلاحية `Actions: Read and write` + `Contents: Read and write` (وفي `Classic Token`: `repo` + `workflow` + `gist`).
    4. بعدها أرسل في تيليجرام: `/mission افحص موقع ... وابنِ له صفحة عرض HTML` — وسيعمل كأنه وكيل مستقل بالكامل!

