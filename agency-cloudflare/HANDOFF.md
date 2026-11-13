# 🤝 JARVIS — هاند أوف كامل لأي ايجنت يستلم المشروع

> اكتبه: 2026-11-11 · آخر تحديث: 2026-11-13 (الفرع `arena/c299d7e2-test`) · النشر الإنتاجي: `arena/749f0c04-test` (Workers Builds)
> الجمهور: ايجنت جديد **ما يعرف شي** عن المشروع. اقرأه كامل قبل أي تعديل. أي شي مكتوب هون أهم من افتراضاتك.

---

## 1) ما هذا المشروع؟

بوت تيليجرام خاص (**@hankash00_bot**) اسمه **«جارفس»** — مساعد شخصي 24/7 لصاحب العمل (وكيل بدبي، يدير 12 عميل مسجل في `LEADS` داخل الكود). يعمل على **Cloudflare Workers Free** — بلا بطاقة، بلا خادم تقليدي، ولا ينام.

المالك يتكلم باللهجة الشامية **دائماً**؛ جارفس مبرمج يرد شامية طبيعية (مو فصحى). القنوات:
- **تيليجرام** (القناة الأساسية: نص + ريكوردات + صور + ملفات)
- **صفحة استدعاء** على `/call` (مكالمة متبادلة من المتصفح — أقرب شي متاح مجاناً لمكالمة صوتية حية)
- **موجز صباحي** كل يوم ~06:00 UTC عبر Cron + طابور مهام بالخلفية بعد موافقة المالك.

### قيود ذهبية لا تكسرها
1. **100% مجاني** — بلا بطاقة، بلا اشتراكات. أي حل يتطلب دفعاً يُرفض حتى لو كان أفضل.
2. **الشامي** في كل ما يقوله جارفس للمستخدم.
3. **لا مهام خلفية بلا موافقة** ✅/❌ عبر بطاقة تيليجرام (consent gate — `start_background_task` لا يبدأ شيئاً بنفسه).
4. **خصوصية**: المستودع خاص؛ الأسرار موجودة في `wrangler.toml [vars]` (نص صريح — انظر القسم 6) وفي `wrangler secret`. **لا تطبع أي قيمة سر في مخرجاتك أو رسائل أو ملفات.**
5. **المالك هو الوحيد** (`ALLOWED_TELEGRAM_ID`)؛ كل غيره يُرفض بـ «⛔ هذا جارفس خاص بالمالك فقط.»
6. النص هو الوضع الافتراضي؛ الصوت opt-in عبر `/voice on`.

---

## 2) بنية المستودع (`/home/user/test/agency-cloudflare/`)

| الملف | الدور |
|---|---|
| `worker.js` (~1450 سطر) | **كل** الكود: الويبهوك، الأوامر، حلقة الوكيل، الأدوات، TTS/STT، قراءة الصور/الملفات |
| `wrangler.toml` | الإعداد: `name = "jarvis-24-7"`، cron `* * * * *`، `[vars]` (انظر §6)، KV `JARVIS_KV`، `[ai] binding = "AI"` |
| `call.html` | صفحة المكالمة (MediaRecorder → `/voice-ask`، و`/ask` للنص، و`speechSynthesis` أو `/tts` للنطق) |
| `live.html` + `livepage.mjs` | صفحة اللايف الحقيقي `/live` — LiveKit WebRTC + توكن من `/livekit-token`. عدّل `live.html` ثم `node -e "…"` لتوليد `livepage.mjs` |
| `livekit-agent/` | Agent Python للّلايف الكامل (Coarena + Edge TTS + Groq Whisper + Silero VAD) — دليله `livekit-agent/README.md` |
| `test.mjs` | 50 اختباراً بلا شبكة حقيقية (fetch وهمي). التشغيل: `node test.mjs` — **يجب أن تبقى 50/50** |
| `apps-script-email.gs` | بوابة Gmail عبر Google Apps Script — **لم ينشرها المالك بعد** |
| `README_AR.md` | دليل الإعداد الأصلي (wrangler login، KV، النشر) |

**لا توجد خطوة build ولا package.json ولا npm.** `worker.js` يُنشر كما هو عبر **Workers Builds** المتصل بالمستودع (كل push على `arena/749f0c04-test` → بناء تلقائي). ثلاث خدمات Workers مربوطة بالريبو: `jarvis-24-7` (**الإنتاج**)، `testjarvis` (توأم قديم)، و`test` (**بناء فاشل منذ قبل — رواسب من إعداد سابق، احذفها من اللوحة إذا سمح المالك**).

---

## 3) كيف يعمل الوكيل (معمارية مختصرة)

### تدفق رسالة تيليجرام
```
POST /webhook  (يتحقق من X-Telegram-Bot-Api-Secret-Token)
  → handleUpdate: يتحقق من ALLOWED_TELEGRAM_ID
  → handleCommand (إن بدأت بـ /) — وإلا:
  → agentLoop: يحتفظ بآخر 14 رسالة (MAX_HISTORY)، يستدعي llmComplete،
     يلتقط TOOL_CALL: {"tool":..., "args":...} (حد 6 خطوات MAX_TOOL_STEPS)، ينفذ runTool،
     يحفظ الرد بالذاكرة ويقسمه لرسائل تيليجرام (سقف كل رسالة ~4000)
```

### مسارات HTTP
| المسار | الطريقة | الغرض |
|---|---|---|
| `/health` | GET | فحص حياة (`{"status":"ok"}`) |
| `/` | GET | نبض بسيط |
| `/call` | GET | صفحة المكالمة (HTML) |
| `/webhook` | POST | ويبهوك تيليجرام (سر: `WEBHOOK_SECRET`) |
| `/ask` | POST | جسر نصي لصفحة المكالمة (`x-jarvis-key: CALL_SECRET`) |
| `/voice-ask` | POST | جسر صوتي: base64 audio → STT → agentLoop |
| `/call-end` | POST | ينهي جلسة المكالمة: ملخص LLM → ذاكرة `mem:all` + إشعار تيليجرام (يتجاهل الجلسات بلا كلام) |
| `/tts` | GET/POST | نطق **شامي مجاني** للصفحة (`?key=CALL_SECRET&text=…`)؛ Edge TTS ← Google TTS احتياط |
| `/live` | GET | صفحة اللايف (LiveKit) |
| `/livekit-token` | GET | توكن LiveKit قصير العمر (1–2) للّلايف (`x-jarvis-key: CALL_SECRET`؛ `?project=2` للمشروع الاحتياط) |

### العقل (السلسلة — بالترتيب)
`callGemini (gemini-2.5-flash)` ← `callOpenAICompatible/Mistral` ← `Groq` ← `NVIDIA` ← `OpenRouter (Kimi K2: moonshotai/kimi-k2:free أولاً)` ← `callWorkersAI (@cf/meta/llama-3.3-70b-instruct-fp8-fast)` ← `callPollinations (keyless)`.
منذ 2026-11-13: بوجود `COARENA_API_KEY` (بيئة/[vars]) وKV فاضي → Coarena (Claude Fable 5.2) أساسي تلقائياً؛ عند فشله (429/انقطاع) يكمل على السلسلة بدل `null`. أولوية العقل: KV (`/coarena on|off`) ← `COARENA_API_KEY` ← `arena`. `/coarena limit 50` يعيد تقديم طلب $50/يوم. المالك رفض مستقبلاً GitHub Models وCerebras وGroq كخيارات أولى (لكنها تبقى احتياطاً إن وُجدت مفاتيح). أي مزود x يفشل → التالي تلقائياً. rate-limit شامل → رسالة صادقة («خلصت الحصة» تُعالج بالأعلى فقط).

### STT (تفريغ الريكورد) — سلسلة متجددة
`Groq whisper-large-v3-turbo` (إن وُجد مفتاح) ← `Workers AI @cf/openai/whisper-large-v3-turbo` (حصة يومية تتجدد) ← `Gemini 2.5 Flash` (كوتا محدودة). أي ريكورد واحد **لا** يجب أن يقتل الخدمة. تفريغ الفشل الشامل يبلّغ المالك بالترتيب.

### TTS (النطق)
`edgeTtsMp3` — **Edge TTS مجاني بلا مفتاح** (نفس صوت Read Aloud): WebSocket إلى `wss://speech.platform.bing.com/edge/v1` مع `Sec-MS-GEC` = SHA-256 uppercase لـ `(filetime rounded to 5min) + TrustedClientToken`، الصوت الافتراضي **`ar-SY-LaithNeural`** (شاركي رجل؛ `ar-SY-AmanyNeural` أنثى؛ تغيير عبر `EDGE_TTS_VOICE` في `[vars]`). عند فشل/نقص بايتات (>500 مطلوبة) ← `googleTtsMp3` احتياط ضمن `ttsArabicMp3`. `tgSendVoice` يرسل `sendVoice` وإن رفض تيليجرام يرجع `sendAudio`.
ملاحظة معمارية: `Sec-MS-GEC-Version` ثابت حالياً (`1-143.0.3650.75`) — لو مايكروسوفت عدّلت Read Aloud يوماً ما قد تظهر 403؛ الترتيب الاحتياطي يتكفل.

### قراءة الصور والملفات (أُضيفت 2026-11-11)
- **صور** ← `visionDescribe`: Workers AI `@cf/meta/llama-3.2-11b-vision-instruct` (مجاني يومياً) ← Gemini vision احتياطاً. النتيجة تُغذّى إلى agentLoop كنص «[المستخدم بعت صورة — تفريغها الآلي: …]».
- **ملفات** ← `extractDocumentText` (تحميل عبر `getFile`؛ سقف 10MB): نصوص/CSV/JSON/XML مباشرة؛ **xlsx/xlsm** عبر قارئ ZIP مصغّر (`readZipMap` + `DecompressionStream("deflate-raw")`) مع `sharedStrings.xml` حتى 4 ورقات × 150 صفاً؛ **docx** عبر `word/document.xml`. PDF **غير مدعوم** (لا بناء/لا مكتبات) — تُطلب كصور أو Word.
- **التعديل الفعلي**: لو كان الـ caption فيه إشارة تعديل («عدّل/ترجملي/نظّف/ارجعلي ملف…») ← `llmComplete` يرجع CSV فقط ← `tgSendDocument` باسم `*-jarvis.csv`.

### الأدوات (RUN عبر `TOOL_CALL:`)
`search_web` (Tavily ثم DuckDuckGo fallback) · `audit_website` · `list_leads` · `get_lead` · `update_lead` · `start_background_task` (**بطاقة موافقة فقط**) · `remember` · `recall_memory` · `forget_memory` · `send_email` (بطاقة ✅/❌) · `call_me_now`.

### المهام الخلفية (طابور)
`/tasks` يعرض، `/clear_tasks` يمسح، `processTaskQueue` كل دقيقة (`STEPS_PER_TICK = 3`، حد صلب `MAX_TASK_STEPS = 60`). الموافقة عبر `approvals` في KV؛ أنواع البطاقات: `task` (خلفية) و`email` (Gmail). عند 3 إخفاقات متتالية ← تُغلق المهمة تلقائياً (لا حرق للكوتا). أحداث غير قابلة للتفويض: ما تعمله يبقيه المالك بوعيه.

### مفاتيح KV المستخدمة
`history` (14 رسالة) · `mem:all` (الذاكرة، سقف 500) · `tasks` · `approvals` · `owner_chat_id` · `leads_overlay` · `voice_replies` (bool) · `call_transcripts` (آخر 10) · `owner_chat_id` يُضبط مع أول رسالة. الذاكرة تُدوَّر آلياً بسقف.

---

## 4) النشر والتحقق (الدورة الإلزامية لأي ايجنت)

```bash
cd /home/user/test
git fetch origin
git status --short --branch        # تأكد 0 0 مع origin واكتشاف أي تغيّر خارجي
# عدّل، ثم:
node --check agency-cloudflare/worker.js   # أو import عبر node -e
node agency-cloudflare/test.mjs            # يجب: 50/50
git add -A && git commit -m "…" && git push origin arena/749f0c04-test
sleep ~150
gh api repos/jfjdjdieifne/test/commits/<SHA>/check-runs --jq '.check_runs[] | select(.name=="Workers Builds: jarvis-24-7") | {status, conclusion}'
# /health عبر fetch_page (إن كانت الخدمة تعمل — حالياً معطلة ضد workers.dev: تحقق من تلفونك: jarvis-24-7.jfjdjdieifne.workers.dev/health)
```

- **لا تثق بالحالة المحلية**: سبق وأن كان المجلد المحلي متأخراً عن origin — لذا `fetch` أمر إلزامي قبل أي تعديل.
- `node test.mjs` بمفرده يمسك أخطاء الأدوات والأوامر؛ للمسارات الجديدة **اكتب هارنس في /tmp** (fetch وهمي + بناء ZIP يدوي بإدخالات stored لاختبار xlsx) كما فُعل في 2026-11-11 (8/8).
- بعد كل deploy: افحص check-run واحد على الأقل + اطلب من المالك تجربة حية (ريكورد واحد، صورة، Excel، `/call`).
- سجل الحالة عبر git فقط — لا تنشر أي فرع آخر.

---

## 5) جدول المتغيرات والأسرار (بدون قيم — لا تكتب القيم!)

كلها اليوم في `wrangler.toml [vars]` (نص صريح — أسوأ حالة) باستثناء روابط Apps Script التي يجب `wrangler secret put`:

| الاسم | الغرض | ملاحظة |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | توكن البوت من @BotFather | مكشوف بالريبو — **يتطلب تدويراً** |
| `ALLOWED_TELEGRAM_ID` | هوية المالك الوحيدة | رقم تيليجرام — حساس قليلاً |
| `GEMINI_API_KEY` | Gemini (عقل + STT + رؤية احتياط) | مكشوف |
| `OPENROUTER_API_KEY` | سكة OpenRouter (Kimi K2 وغيرها) | مكشوف |
| `TAVILY_API_KEY` | بحث الويب | مكشوف |
| `CALLMEBOT_TELEGRAM_USER` | اسم مستخدم المالك في CallMeBot (**بدون @**) — على المالك تأكيد أنه مطابق لاسمه بالضبط | قيمة خاطئة = لا رنّات |
| `WEBHOOK_SECRET` | سر الويبهوك | مكشوف |
| `CALL_SECRET` | مفتاح صفحة `/call` و`/tts` | مكشوف |
| `CALL_ON_BRIEF` | `true` = رنّة مع الموجز الصباحي | عام |
| `GROQ_API_KEY` · `APPS_SCRIPT_URL` · `APPS_SCRIPT_SECRET` · `OWNER_CHAT_ID` · `EDGE_TTS_VOICE` · `MISTRAL_API_KEY` · `NVIDIA_API_KEY` | اختيارية — تُضاف كـ vars أو secrets عند الحاجة | — |
| `COARENA_API_KEY` · `COARENA_MODEL` | العقل المجاني (Coarena) — صاروا ب `[vars]` 2026-11-13 | مكشوف — يتطلب تدويراً |
| `LIVEKIT_WS_URL` · `LIVEKIT_API_KEY` · `LIVEKIT_API_SECRET` | LiveKit المشروع 1 (اللايف) | مكشوف — يتطلب تدويراً |
| `LIVEKIT_ALT_WS_URL` · `LIVEKIT_ALT_API_KEY` · `LIVEKIT_ALT_API_SECRET` | LiveKit المشروع 2 (احتياط، `?project=2`) | مكشوف — يتطلب تدويراً |
| `LINPHONE_API_KEY` · `LINPHONE_SIP_URI` | هوية SIP (مقيدة IP 89.124.8.30 — لا تعمل من Cloudflare) | مكشوف |

**ثوابت بنيوية**: KV `JARVIS_KV` (id موجود في `wrangler.toml`)، `[ai] binding = "AI"`، cron كل دقيقة، `compatibility_date 2024-11-01`.

**قاعدة أي ايجنت**: عند استلام المشروع، **الخطوة صفر** هي تدوير كل ما في `[vars]` عبر BotFather/Google AI Studio/OpenRouter/Tavily/Cloudflare (`wrangler secret put` أو تعديل `[vars]` بعد تنظيف التاريخ). هذا الإجراء معلّق منذ أيام ولم ينفذه المالك.

---

## 6) مشاكل وقرارات وأحداث (لا تكرر الأخطاء)

1. **تسريب أسرار بالريبو**: `wrangler.toml [vars]` فيها كل المفاتيح بصيغة صريحة (وسبق تسريب `cfut_` API token في محادثة). التنظيف مضاف لقائمة المالك؛ **أي ايجنت لا يعيد إدخال أسرار ولا يطبعها**.
2. **«خلصت الحصة» بـ STT**: كانت `transcribeGeminiAudio` بلا احتياط — أُصلحت 2026-11-11 بسلسلة Groq←Workers AI←Gemini. **لا تعُد لاختبار ريكورد واحد فقط.**
3. **جوجل ترانسليت TTS** رفضه المالك لسماحة «مكسر» — مصدر الشامي الآن Edge TTS (غير رسمي؛ إذا كسرته مايكروسوفت فجأة، الاحتياطي Google يكمل).
4. **CallMeBot**: الرنّة لا تصل إذا لم يضغط المالك **Start** عند `@CallMeBot_txtbot`، أو إذا كان `CALLMEBOT_TELEGRAM_USER` ليس اسم مستخدم المالك حرفياً. الكود الآن يقرأ رد CallMeBot ويقول الحقيقة بدل «تم الإرسال». **هذا سبب الشكوى «ولا رنّة ولا اتصال» الأكثر احتمالاً.**
5. **مكالمة هاتف/واتساب حقيقية مجانية = غير موجودة**. لا PSTN مجاني (Twilio يطلب بطاقة + أرقام موثقة)، ولا WhatsApp Business Calling مفتوح، و**تيليجرام لا يسمح للبوتات بإجراء مكالمات صوتية إطلاقاً**. البديل المعتمد: صفحة `/call` (صوت متبادل عبر المتصفح + `/tts` الشامي) وريكوردات تيليجرام. لا تعد المالك بشيء آخر.
6. **طلب «كوكيز ارينا من تحت الارض ليدير ارينا لوحده»** — طلب المالك مرتين ورفض مرتين (2026-11-11). الأسباب: لا API عام لجلسات Agent Mode؛ Connectors رسمية لكل turn فقط؛ الكوكي = سيطرة كاملة على الحساب في Worker على الإنترنت (يتناقض مع حرائق الأسرار)؛ هشاشة ضد أي تغيير UI = ضد «اشغلو وانساه». **أي ايجنت يستلم المشروع لا ينفذ هذا الطلب ولا «حيلة» مثلها. البديل المعتمد**: Connectors داخل ارينا (Gmail/Drive/Sheets/Calendar/GitHub — مجانية، OAuth، لكل turn) + طابور المهام بالخلفية بعد ✅ هنا في المشروع + GitHub Actions كرون لمهام مجدولة بديلة.
7. **مهام وهمية تستهلك الكوتا**: كانت المهام الخلفية تنطلق بلا إذن — أُغلق ذلك بـ consent gate (`queueApprovedTask` فقط بعد ✅). **لا تربط أي أداة بمسألة `startBackgroundTask` مباشرة.**
8. **ذاكرة تحتوي قمامة**: «ملخص مكالمة (11-11-2026): المحادثة ما في فيها محتوى حقيقي» (المعرف يبدأ/ينتهي بـ `3pzx` تقريباً) محفوظة قبل حاجز الملخصات الفارغة — المالك لم ينفذ `/forget 3pzx` بعد. **لا تحذفها نيابة عنه عبر KV دون علمه؛ اطلب منه الأمر.**
9. **حدود Cloudflare Workers الحقيقية**: مجاني = 100k طلب/يوم، 10ms CPU (لا شيء ثقيل متزامن؛ الملفات تعالج ≤10MB)، KV 1k كتابة/يوم مجاناً، Workers AI آلاف neurons/يوم. **التجميع والتلخيص يجب أن يقتصرا على حدود الرسائل** (14 تاريخ، 150 صف/ورقة، 12k حرف/ملف، 500 ذاكرة).
10. **fetch_page معطلة ضد workers.dev حالياً** (2026-11-11 ~23:00) — موثوقيتها متذبذبة؛ اعتمد check-runs + فحص المالك الحي.
11. **بناء `test`** (خدمة Workers ثانية على نفس الريبو) فاشل في كل commit — مسبق، منفصل عن الإنتاج.
12. **اختبارات test.mjs** تتحقق من الأدوات والأوامر عبر fetch وهمي — أي تغيير سلوكي يتطلب تحديثها؛ لا «تصلح» الاختبارات لتمرير كود معطل، بل العكس.
13. **قرارات 2026-11-13 (بطلب المالك)**: (أ) `COARENA_API_KEY` ب `[vars]` = Coarena أساس تلقائياً؛ عند فشله يكمل على السلسلة. (ب) LiveKit: مشروعان مجانيان — JWT يُوقَّع بالبوت (`/livekit-token`، HS256 بـ WebCrypto — بلا تبعيات)؛ صفحة `/live` تحتاج `livekit-agent/` على جهاز المالك (Groq STT + Coarena LLM + Edge TTS + Silero VAD، كله مجاني). (ج) Linphone: هوية SIP فقط — لا PSTN — ومفتاحها مقيد IP ولا يعمل من Cloudflare؛ مخزنة للتوثيق/الاستخدام من جهاز المالك. (د) Edge TTS قرار معتمد للـ Agent (نفس صوت البوت `ar-SY-LaithNeural`).

---

## 7) قائمة أفعال المالك (لم تُنفذ — لا تنفذها نيابة عنه)

1. `/forget 3pzx` — حذف ذاكرة «ملخص مكالمة» الفارغة
2. `/clear_tasks` — تصفير أي مهام عالقة
3. تدوير كل أسرار `[vars]` (BotFather: `/revoke`؛ Google AI Studio؛ OpenRouter؛ Tavily؛ WEBHOOK_SECRET/CALL_SECRET عشوائياً) + **حذف توكن `cfut_…` من أنا هون ومن أي مكان** + تنظيف تاريخ git إن أمكن (filter-repo) — المستودع خاص لكن لا يكفي
4. الضغط **Start** عند `@CallMeBot_txtbot` + تأكيد `CALLMEBOT_TELEGRAM_USER`
5. نشر `apps-script-email.gs` كـ Web App ووضع `APPS_SCRIPT_URL`/`APPS_SCRIPT_SECRET` لتفعيل إرسال الإيميل بعد ✅
6. حذف/فصل خدمة `test` من ريبو GitHub + فصل `testjarvis` إن لم تُستخدم
7. اختياري: `EDGE_TTS_VOICE=ar-SY-AmanyNeural` للصوت النسائي

---

## 8) قواعد أي ايجنت يستلم (مختصرة وملزمة)

1. اقرأ هذا الملف + `README_AR.md` قبل أي سطر كود.
2. `git fetch` أولاً؛ لا تعتمد على النسخة المحلية؛ لا تعيد تسمية الفرع؛ لا push لغير `arena/749f0c04-test`.
3. تحقق من كل deploy (check-run + `/health` مع المالك) — «بناء نجح» وحدها لا تكفي أن البوت حي.
4. لا أسرار في المخرجات أو الكود أو الذاكرة؛ لا تكتب قيمًا في HANDOFF/README.
5. لا مهام خلفية بلا ✅؛ لا tool تنفذة علناً بلا موافقة؛ لا «كوكيز/جلسات» أي خدمة، أعذار مهما كانت.
6. لا تعد بقدرات لا يملكها (PDF حقيقي، مكالمات هاتفيه حقيقية، «وكيل كامل ينفذ كل شي بلا موافقتك»).
7. عند الغموض: اسأل المالك بسؤال واحد محدد؛ لا تنفذ «الأصلحك» وأنت لا تراه (خاصة مع إرسالات للخارج / إيميلات / اتصالات).
8. عند أي شك في تسريب سر جديد: أوقف وبلّغ المالك فوراً ولا تكمل.

---

## 9) كيف تضيف ميزة (وصفات جاهزة)

- **أمر جديد (`/x`)**: `case "/x"` داخل `handleCommand` (و`return true`) + سطر في `WELCOME` + اختبار في `test.mjs`.
- **أداة جديدة للوكيل**: سطر في `TOOL_DOC` + `case` في `runTool` + `parseToolCall` يلتقطها تلقائياً؛ إن كانت حساسة → بطاقة ✅/❌ عبر `approvals` أولاً.
- **مسار HTTP جديد**: فرع في `fetch()` قبل `/health` + `jsonResponse` + CORS عند الحاجة؛ لا تعتمد على بناء/تبعيات.
- **نموذج احتياط جديد في العقل**: دالة `callXxx` تتبع نفس شكل `llmComplete` وأدخلها في السلسلة بـ `llmComplete` — لا تسبق خيارات المالك دون إذنه.
- **صوت شامي آخر**: `EDGE_TTS_VOICE` في `[vars]` (لا تعديلات كود).
- **حالة الوكيل لكلturn**: `opts.ctx.waitUntil` للمهام الطويلة؛ `agentLoop(text, env, chatId, { ctx })`.

---

## 10) Backlog مقترح (بموافقة المالك فقط)

1. **PDF حقيقية**: تتطلب خطوة build أو مكتبة wasm — الخيار العملي الحالي: «PDF → صور» ويقرأها جارفس بصرياً اليوم.
2. **GitHub Actions كرون** كمهام 24/7 إضافية (بحث + تقرير Telegram) — تكمل طابور المهام الحالي بلا أي كوكيز.
3. إرجاع الملف بصيغته الأصلية (xlsx معدّل بدلاً من CSV) — يتطلب كاتب ZIP؛ حالياً CSV كافٍ وفتحه في Sheets متاح.
4. تحسين تفريغ Excel للجداول الضخمة (Streaming) إن لزم.
5. تنظيف `test` Worker + تقرير موحّد GitHub→Cloudflare (الأوامر الجاهزة في §3).
6. Connectors الرسمية في ارينا (Gmail/Drive/Sheets) لتعويض «بوابة Gmail» بدل Apps Script.

---

## 11) ملخص الـ commit الحالية المهمة

- `6f6af53` Consent gate + `/tasks` + `/clear_tasks` + skill 3-ضربات.
- `77679f1` عقل مجاني متجدد (Workers AI + Kimi K2 + Pollinations) + عبرة Groq/Gemini + حارس الملخصات الفارغة.
- `d7fd690` رؤية وصور + قارئ xlsx/docx + STT متجدد + TTS شامي عبر Edge TTS + CallMeBot بصراحة.
- **الحالي (2026-11-13)** `feat(live)`: Coarena أساس تلقائي عبر `COARENA_API_KEY` + سقوط سلس للاحتياط + `/coarena status|off|limit` + `/livekit-token` (JWT HS256 WebCrypto) + `/live` + `livekit-agent/` (Coarena←Edge TTS←Groq Whisper←Silero) + Linphone/LiveKit ب `[vars]` + 50/50 اختباراً.

أي تعارض بين هذا الملف والكود: **الكود هو الحَكم**، وحدّث هذا الملف معه في نفس الـ commit.
