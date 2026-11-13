# HANDOFF — جارفس CEO (Jarvis CEO) — دليل كامل ومفصّل

> **لمن هذا الملف:** للمعالج/الوكيل القادم اللي حيكمل مع الدكتور من وين ما وصلنا.
> **متى كُتب:** 2026-11-13 (الليل UTC) على البرانش `arena/e3e2c397-test`، الكوميت الأخير `b37341e`.
> **اقرأ هذا الملف كاملاً قبل أي فعل.** الدكتور **مبتدئ بالمطلق** — ما عنده خلفية برمجة. خاطبتو بلغته (شامية)، خطوة واحدة كل مرة، ما تشاركشتو أي مفتاح/توكن أبداً.

---

## 0. الخلاصة في 60 ثانية

المشروع: **بوت تلغرام شخصي اسمه «جارفس» (jarvis v1)** على سيرفر AWS t4g.micro قائم (مجاني، ما منعمل استقرار/Upgrade).

- العقل: **Fable 5.2 عبر Coarena** (OpenAI-compatible) — نفس العقل لكل الوكلاء، الفرق بس بالشخصية (persona).
- الدكتور بيحكيلو بالشامية **نص أو فويس** (Gemini STT)، بيرد نص + صوت (edge-tts عربي مجاني).
- كل وكيل = فابل + شخصية. الوكلاء: **سعيد** (مواقع/متاجر/مراقبة)، **محمود** (إيميل)، **أحمد** (ذهب/أسواق)، **متداول** (صفقات المحترفين — توصيات فقط) + أي وكيل جديد بكلمة من الدكتور.
- **قدرات كاملة جاهزة بالكود**: تعديل ذاتي من تلغرام (مع فحص + رجعة تلقائية + «تراجع»)، Excel بصوت المديل، GitHub تحكم كامل، Gmail قراءة/مسودة بموافقة، X/فيسبوك/انستغرام نشر بموافقة، صور مجانية، ذاكرة معرفة (احفظ/تذكر)، تذكيرات (كل يوم/أسبوع)، محكمة ذكية (متفائل/متشائم/قاضي)، تقرير صباحي 06:00، نسخة احتياطية تلقائية على GitHub لكل تعديل ذاتي.
- **الاختبارات: 27/27 ✅** (على Python 3.11 بالـ sandbox، offline).
- **الحالة الفعلية: الكود خلص ومفحوص ومُرفوع على GitHub — لكنه لسا ما اشتغل على السيرفر.** الباقي = خطوة نشر على EC2.

---

## 1. الوضع الحالي — وين وصلنا بالزبط

### البرانش والكوميتات (repo `jfjdjdieifne/test` — private)

```
b37341e jarvis-ceo: key drop, reminders, second brain wiring, images, self-awareness
0df45c1 jarvis-ceo: second brain (FTS5), debate arena, opportunity brief, auto GitHub backup
3fb5b58 jarvis-ceo: GitHub/Gmail/social integrations, approval flow
b26836c jarvis-ceo: jarvis-ceo Telegram multi-agent executive (البنية الأولى)
```
نسخة كامل لكل ملفات `jarvis-ceo/` على GitHub ضمن البرانش أعلاه.

### الـ tests
`cd /home/user/test/jarvis-ceo && python3 -W ignore::ResourceWarning -m unittest test_agent -v` → **Ran 27 tests … OK**

### الملفات الجاهزة داخل `jarvis-ceo/`
| الملف | شو فيه |
|---|---|
| `agent.py` (~970 سطر) | بوت تلغرام long-polling بلا مكتبات — كل السيرفر والميزات والأوامر |
| `brain.py` | عميل Coarena (OpenAI-compatible) + تدوير مفاتيح + سقف إنفاق + system prompt |
| `db.py` | SQLite: messages / agents / tasks / kv / notes(FTS5) / reminders + سقف توكن يومي |
| `tools.py` | Excel (report + تنفيذ مقيد بـ backup/restore)، Gemini STT، edge-tts، أسعار (CoinGecko)، طقس (wttr.in)، مواقع |
| `github.py` | GitHub REST: whoami / list_repos / get_file / put_file (فرع + PR فقط، **ما بيلمس main**) / create_repo |
| `gmail.py` | IMAP+SMTP بـ App Password — قراءة/مسودات/إرسال بعد زر ✅ |
| `social.py` | X (OAuth 1.0a) + Facebook Page feed + Instagram Business (يحتاج صورة + Business حساب) |
| `integrations.py` | مركز الوصلات: حالة كل خدمة، خطوات الربط، تخزين مفاتيح **بلا طباعة** + chmod 600 |
| `project.py` | وعي ذروة بالمشروع: قراءة/بحث/ملخص مجلد المشروع (PROJECT_DIR) |
| `images.py` | Pollinations — صور مجانية بلا مفتاح |
| `selfedit.py` | **التعديل الذاتي**: فابل بيكتب كود → py_compile + كل الاختبارات → بغير الـactivate بلا رجعة، رجعة تلقائية + `تراجع` |
| `test_agent.py` | 27 اختبار offline (CEO_DB مؤقت) |
| `README_AR.md` | دليل المستخدم (أوامر + الإعداد + القادم) |
| `requirements.txt` | edge-tts, openpyxl فقط |
| `jarvis-ceo.service` | systemd: Restart=always, MemoryMax=350M |
| `run.sh` | تشغيل + تحميل `~/jarvis-ceo.env` |

### ما خلص بالكامل ✅
كل المطروح بالأعلى + الذاتي التعديل + الموافقات بضغطة + التصويت «تراجع».

### نصف-مبني / محتاج تحقق حي على السيرفر ⚠️
- **ما حدا شغل جارفس فعلياً لسا.** كل شي ما ترأى على EC2 ولا حرف خارجي.
- Coarena «Fable 5.2» — شكل الردود الفعلي مع payload حقيقي **لسا ما تظبط بالتجربة** (في احتمال content:null / حدود tool-calling).
- الصفحة العربية للأوامر في README مفصحة — بس لازم تجربة «هلا» حقيقية.

### ما بدأ لسا (مقصود — مو نسيان)
- Vercel/Cloudflare Auto-Deploy — يحتاج حساب الدكتور (مجاني) — بعد ما يربط.
- Lemon Squeezy/Stripe — هويتك المالية؛ الدكتور يفتح لحساب نفسه — ما منفتح حساب دفع.
- سبام بارد / إرسال جماعي بدون موافقة — **لن نبنيه أبداً** (قانوناً وأخلاقياً والدومين المدمر).
- CRM تلقائي من الإيميل، نسب أسعار بين منصات — لاحقاً بعد استقرار الإيميل.
- ChromaDB / Playwright / n8n — **ممنوع** على 1GB RAM. البديل المبني: FTS5 (أخف بكثير) + Python عادي.

---

## 2. المهمة الوحيدة الباقية الآن: نشر جارفس على EC2 من آيفون

**الظرف:** الدكتور هلأ على **iPhone** (تلفونه). الكمبيوتر بدون كهرباء لفترات طويلة. كونسوّل AWS على الآيفون **ما بيسمح باللصق في الترمنال العادي** (المشكلّة اللي وصلناها هلأ).

**الهدف:** تشغيل جارفس على السيرفر t4g.micro القائم — بدون لمس البوت القديم (`jarvis-live`) نهائياً.

**معلومات مؤكدة:**
- EC2 عندو إنترنت صادر (بينفع اتصال APIs خارجية — مثبت تجريبياً مع Gemini على البوت القديم).
- AWS Console على الآيفون: صفحة البحث والقوائم بينفع التعامل معها، والمربعات النصية (textarea) بينفع اللصق فيها عادةً — (مربع "Commands" بصفحة Run a command هو textarea، وبينفع فيه لصق).
- Systems Manager ← الدكتور ما لقاه بالـ UI على الآيفون (Phase: «مالقيتها…»). **الحل الأفضل: هلأ** رابط مباشر يعمل لصق URL بالكونسول من الآيفون:
  `https://console.aws.amazon.com/systems-manager/run-command/instances?region=REGION#`
  أو افتح EC2 → Instances → الجهاز → Connect → **Session Manager** tab.
  - **REGION لازم نعرفه** (من الزاوية بالفوق يمين باللون البرتقالي بالكونسول — مثلاً `eu-north-1` أو `eu-central-1`). الدكتور لازم يلاقي اسمه.
  - **Instance ID** (i-xxxxxxxx) بصفحة الجهاز.
- **إذا Run Command ما بيضيف الـ Instance كـ target** → معناتو الـ Instance ما تجهزة SSM (عادة لابّدو بتغلب setup). الحل الوحيد الباقي: كهربا/كمبيوتر (10 دقيقة بكل شي) أو أي جهاز ثاني. ما في حل سحري من آيفون للمشكلّة هاي.

### السيناريو الجاهز للتنفيذ (بالترتيب — خطوتين لصق ما خربانين)

**Command A (التثبيت + الذخائر) — يلزقه بمربع Commands بدون أي توكن:**
> يلزم GITHUB_TOKEN_NEW إلا إذا فهمتو إن الإيزار حتى يجيب الكود لازم مصادقة. إلك مناسكين صيغة آمنة باستعمال توكن الدكتور الشخصي (اللي عملو اليوم، صلاحية Admin+Contents+PRs على ريبو `test`): يلزق توكنه **بنفسه** وإحنا ما نشيلو. إذا عامل جديد masterfully بروح بجرب بالأوضة العامة معه، يخصصه لساعتها.

التعديل العملي المنجز كالتالي — توكن الدكتور **ما بيجي عن طريق المحادثة ولا عن طريقنا فيه:**

```sh
set -e
RUSER=$(id -nu 1000 2>/dev/null || id -nu 1001)
RHOME=$(eval echo ~$RUSER)
echo "user=$RUSER home=$RHOME"
# يلزم توكن github_pat_ تبع الدكتور: يبدّل TOKEN بعتو بنفسه باللصق
git clone --depth 1 --branch arena/e3e2c397-test https://x-access-token:TOKEN@github.com/jfjdjdieifne/test.git /tmp/jarvis-src
mkdir -p "$RHOME/jarvis-ceo"
cp -r /tmp/jarvis-src/jarvis-ceo/. "$RHOME/jarvis-ceo/"
rm -rf /tmp/jarvis-src
chown -R "$RUSER:$RUSER" "$RHOME/jarvis-ceo"
python3 -m venv "$RHOME/jarvis-ceo/.venv"
"$RHOME/jarvis-ceo/.venv/bin/pip" install -q -r "$RHOME/jarvis-ceo/requirements.txt"
```

**قائمة مفاتيح فقط (ما بلاش قيم) — آمنة للصق بالكونسول:**
```sh
echo "--- يلي بـ .env القديم (أسماء بس):"
(grep -oE '^[A-Z0-9_]+=' "$RHOME/jarvis.env" 2>/dev/null || true) | tr -d '=' | sort | tr '\n' ' '; echo
echo FILES-OK
```
(أو إذا ممنوعة: يكفي يسأله الدكتور «شو بدك؟» وبعطيه الوصفة كسطر.)

**Command B (ملفات البيئة + service — الدكتور يلزق توكن jarvis v1 بيدو):**
```sh
set -e
RUSER=$(id -nu 1000 2>/dev/null || id -nu 1001); RHOME=$(eval echo ~$RUSER)
(grep -E '^(GEMINI_API_KEY|TAVILY_API_KEY)=' "$RHOME/jarvis.env" >> "$RHOME/jarvis-ceo.env" 2>/dev/null || true)
cat >> "$RHOME/jarvis-ceo.env" <<'EOF'
TELEGRAM_BOT_TOKEN=TOKEN_GOES_HERE_BY_THE_DOCTOR
COARENA_BASE_URL=PASTE_FROM_OLD_ENV
COARENA_MODEL=PASTE_FROM_OLD_ENV
COARENA_API_KEY=PASTE_FROM_OLD_ENV
DAILY_TOKEN_CAP=200000
GITHUB_OWNER=jfjdjdieifne
PROJECT_DIR=/home/RUSER/jarvis-ceo
EOF
chmod 600 "$RHOME/jarvis-ceo.env"; chown "$RUSER:$RUSER" "$RHOME/jarvis-ceo.env"
sed -e "s#REPLACE_USER#$RUSER#g" -e "s#REPLACE_HOME#$RHOME#g" -e "s#/usr/bin/python3#$RHOME/jarvis-ceo/.venv/bin/python#g" "$RHOME/jarvis-ceo/jarvis-ceo.service" > /etc/systemd/system/jarvis-ceo.service
systemctl daemon-reload && systemctl enable --now jarvis-ceo
sleep 3
systemctl status jarvis-ceo --no-pager
```
> ملاحظة للمبرمج: محتوى `jarvis-ceo.env` — أسماء المتغيرات بالـ README_AR.md؛ التوكن الصحيح هو توكن البوت الجديد فقط، وأي قيمة من ملف `jarvis.env` القديم. لا يصير عرض أي قيمة بـ logs أو بالشات طول العمل.

**Command C (التحقق):** `journalctl -u jarvis-ceo -n 40 --no-pager` — لازم يشوف: `جارفس CEO شغال كـ @<username>…`.

**أول رسالة على تلغرام:** الدكتور يكتب «هلا» للبوت الجديد من تلفونه — **لازم يكون أول مين يحكي مع البوت** (claim_or_check بيقفل المحادثة عليه لحاله).

---

## 3. الموارد والحسابات — شو موجود وين

| الشيء | الحالة | الملحوظة |
|---|---|---|
| AWS | $100 credits، expire **2027-05-13**، **free plan** — لما تستهلك الخدمات لا تمنح فاتوراً | **ممنوع Upgrade**؛ Budget alerts مرفوضة من الدكتور؛ t4g.micro فقط |
| السيرفر | t4g.micro 1GB RAM، Ubuntu/Amazon Linux (غير معروف بدقة) | بوت قديم `jarvis-live` شغال عليه — **ما تلمسه** |
| ملف الأسرار القديم | `~/jarvis.env` على السيرفر | فيه مفاتيح Gemini (مثبت استعماله من البوت القديم) — **لا نعرض محتواه أبداً؛ أسمائها بس** |
| Coarena / Fable 5.2 | موصول عبر البوت القديم (`/arena connect`) — مكان التخزين الدقيق **لسا مو معروف** (غالباً في KV/ملف إعدادات البوت القديم) | بالـ 11 مفتاح × $5 = $55 متاحة |
| Gemini API key | **موجود على السيرفر** بالتجربة القديمة مع Gemini STT `gemini-3-flash-preview` (مو 2.5 — جاب 404) | بيتقاد من `tools.gemini_transcribe` |
| Telegram البوت القديم | `jarvis-live` — LiveKit/Gemini voice | لا تلمسه؛ token مختلف عن الجديد |
| Telegram بوت «jarvis v1» | **التوكن عند الدكتور** (BotFather، إنشاء 2026-11-13) — لسا **ما انحط على السيرفر** | مطلوب للتشغيل؛ ممنوع يكتوب بالشات |
| GitHub | حساب `jfjdjdieifne`؛ repo `test` (private) — البرانش متستعمل | الدكتور فتح **repo عام فارغ** اسمو `jarvis-ceo` (2026-11-13) — my push له أعطي 403؛ الكوميت الرئيسي يفضل على `test`؛ ممكن الدكتور يحذفه أو يتجاهله |
| Gmail / X / Facebook / Instagram | **مو موصولة** | خطوات الربط جاهزة بـ README_AR.md و integrations.py؛ الدكتور يفتح الحسابات + يجيب المفاتيح بنفسه، بعدين «احفظ مفتاح …» من تلغرام (بيرح الرسالة تلقائياً) |
| Vercel / Cloudflare / Lemon Squeezy / Stripe | مو موصولة ولا بدأت | لاحقاً؛ هويتك المالية/الشخصية بيده |
| Tavily | **مفتاح موجود على السيرفر** (بالبوت القديم كان مستعمل) | يفعنا ببحث Tavily + «فرصة اليوم» |
| Voice STT | `gemini-3-flash-preview` | مطابق للتجربة الناجحة |

---

## 4. القواعد الحمراء — لا تُخرق (وراثة من كل الجلسة)

1. **ممنوع Upgrade / ممنوع إنشاء Instances** — t4g.micro فقط؛ Budget alerts مرفوضة من صراحة الدكتور.
2. **ممنوع لمس البوت القديم** (jarvis-live) بأي شكل.
3. **ممنوع مشاركة مفتاح/توكن/كلمة مرور بأي شات** — ولا بطلب. مكانهم **حصرياً** `~/jarvis-ceo.env` على السيرفر، chmod 600، ما بينطبعوا لا باللجات ولا بـ README.
4. **الدفعة على GitHub للمستودع**: ما منبعت بلا إذن صريح من الدكتور («ابعت»). البرانش الوحيد اللي بنشتغل عليه: `arena/e3e2c397-test`.
5. **قرارات المال/النشر/الرسائل الخارجية**: بدون موافقة الدكتور **ما بتنفذ** — ولا باتفاق مسبق ولا «ما راح يصير شي». بالأزرار ✅/❌ بالمسودة.
6. **ممنوع سبام / إرسال جماعي بدون تفويض صريح محدد**؛ ممنوع فتح حسابات هوية؛ ممنوع تداول بفلوس حقيقية بدون إذن صريح لكل صفقة (متداول = توصيات فقط).
7. **لا n8n / CrewAI / LangGraph / OpenHands / ChromaDB / Playwright** على 1GB.
8. **IETF**: Telegram ما بيسمح باثنين على نفس التوكن — البوت الجديد لازم توكنه منفصل.
9. **الفرع** `arena/e3e2c397-test`؛ لا ننشر فرع تاني ولا نمسح/نبدل شي به (ولا نكتب على `main` مباشرة).
10. **كل تعديل ذاتي على جارفس لازم يعدي: py_compile + كل الاختبارات → وإلا رجعة تلقائية.** حتى الكود الجديد نفسه لما يتعدل.
11. الدكتور **يرفض** أي حل فيه: بطاقة ائتمان، دفعات احتيالية، سكرابر يخرق ToS، E2E بمعلاق هويته.

---

## 5. خارطة الطريق بالترتيب (بعد النشر)

**الآن (اليوم):**
1. النشر على EC2 (Commands A→B→C فوق) + تأكيد systemd + «هلا» من الدكتور.
2. اختبار فويس: رسالة صوتية فيها سؤال بسيط → رد صوتي (edge-tts ar-SY-LaithNeural).
3. اختبار Excel: يرفع ملف فيه أعمدة + على كل صف ملاحظة تُملأ بطلبه (مثلاً: «عبي ملاحظة كل صف من التسجيل المرفق»).
4. اختبار التعديل الذاتي: «أضف ميزة: إذا قلت لك «وقت» تعطيني التاريخ والساعة» → لازم يعدي الاختبارات وينجح؛ بعدها «تراجع» → رجعة.
5. أول backup فرع على GitHub (لما يطلب تعديل: `backups/<ts>` بريبو jarvis-ceo-backup — يحتاج صلاحية Administration+Contents بالـ PAT).

**القريب (خلال يومين):**
6. ربط الجيميل بالـ App Password (بتلغرام: «ربط الجيميل» → الخطوات؛ بعدها «شو لازم اضيف» → «احفظ مفتاح GMAIL_ADDRESS=…» + «احفظ مفتاح GMAIL_APP_PASSWORD=…») — أوامر «ايميلاتي» وتقرير الصباح.
7. ربط GitHub (موجود): «ربيوزاتي»، «شو موصول».
8. Tavily: إذا Tavily موجود بالسيرفر → «فرصة اليوم» بتشوف بالتقرير الصباحي 06:00 (حد استثمر توكن ~350/يوم).
9. قائمة مراقبة سعيد: «راقب <URL>» — تنبيه إذا الموقع طاح.

**اللاحق (أسبوعي):**
10. X: مفاتيح + أول منشور بموافقة → بوت ينشر لما توافق.
11. انستغرام Business (الأصعب — خطوات Meta قيد التحقق) + فيسبوك Page.
12. Lemon Squeezy/Stripe (هويتك هو) → بوت يدير المدفوعات بس هو بموافقة.
13. CRM: تتبع من الإيميل + تنبيهات «صار إسبوع بلا تواصل مع فلان».
14. فرصة اليوم → عروض فعلية بضغطة موافقة.

**أبدي (ممنوع):** أي سبام، أي تنفيذ صفقة مالية بدون إذن، أي Upgrade AWS، أي كشف مفاتيح.

---

## 6. أين كل شي وكيف ترجع تكمل بجلسة جديدة

- **الريبو والبرانش:** `jfjdjdieifne/test` @ `arena/e3e2c397-test` — آخر كوميت `b37341e`.
- **النسخة المحلية (لهذا الـ sandbox):** `/home/user/test/jarvis-ceo/`
- **الذاكرة المؤقتة من المحادثات السابقة** في هذا الـ sandbox: ذات `/home/user/test/jarvis-ceo/` بالكود — أي تعديل جديد بيكمل من هناك.
- **README_AR.md** — دليل المستخدم النهائي (الأوامر + الأسرار + نظام الصيانة).
- **للمعالج الجديد — أول رسالة يرسلها الدكتور:**
  > «أنت بتكمل مشروع جارفس — اقرأ jarvis-ceo/HANDOFF_AR.md بالكامل قبل أي فعل، واكمل معي من وين ما وقفنا.»
- **الاختبارات:** `cd /home/user/test/jarvis-ceo && python3 -W ignore::ResourceWarning -m unittest test_agent -v`
- **تشغيل التطوير:** أي تعديل → شغّل الاختبارات → ما بنرفع بلا نجاح الكل.

---

## 7. أخطاء وملحوظات يعرفها المعالج الجديد (تحفظ)

1. **Coarena F** — رد متوقع `content: null` في بعض الردود؛ `brain.extract_json` بيحاول الأفضل JSON embedded. لو فيه null دائم — جرب `COARENA_API_KEYS` (تدوير) وحاول على الـ proxy بإعدادات مختلفة.
2. **gemini-3-flash-preview** مو `gemini-2.5` — الثاني 404.
3. **UTF-8 عربي** — كل ملفات الكود مفتوحة بـ `encoding="utf-8"`؛ إذا حدا شاف «ط» «ح» مكسرين → المشكلة ترميز، مو خطأ منطقي.
4. **`os._exit(0)` مقصود** بعد أي تعديل ذاتي ناجح/تراجع — systemd بيرجع البوت بالكود الجديد تلقائياً (Restart=always).
5. **claim_or_check** — أول مين يحكي مع البوت بصير «المالك». الدكتور لازم أول حدا يكتب. لو بدأ شخص تاني → شيل `~/jarvis-ceo.db` (أو افسخ الـ kv key `ceo_chat_id`).
6. **Telegram file upload** — يرسل `.xlsx`: الأزرار بالرسالة الأخيرة؛ رد على رسالة فويس: صوت + نص.
7. **السيرفر 1GB RAM** — أي حل فيه متصفح headless/LLM-agents frameworks/ChromaDB = **سقوط فوراً**.
8. **IPv6** — EC2 ناس بيحتاج `Dualstack` config — إذا خدمة ما ردت، اتأكد من الشبكة.
9. **الرسائل العربية بالأسماء والبروكسيات** — لا تحوّل النصوص أبداً؛ FTS5 بيدعم العربية بما فيها الألف والهمزات.
10. **مطلوب**: أي تعديل على هذا الملف أو الكود → كوميت مستقل على نفس البرانش.

---

## 8. الصورة الكاملة — ما نعمل شغلة ثانية قبل هدول

الدكتور ناطر: نظام «جارفس» يشتغل على تلفونه عبر تلغرام بأقرب وقت، من دون ما يدفع فلساً إضافي، ومن دون ما يتعلم شي، ومن دون ما يلمس بوته القديم، ومن دون أي بيانات تتسرّب. **أي مقترح بيتطلب منو تعلم/دفع/إيقاف البوت القديم — مرفوض.**

أي ما يعرفه المعالج الجديد يحتاج مساعدة تقنية — يرجع لكامل الجلسة السابقة (هذا الملف ملخصها بالكامل).

**آخر تحديث:** 2026-11-13 — بانتظار قرارين من الدكتور: (1) كهربا/كمبيوتر أو آيفون مع Systems Manager (الأقرب)، (2) الموافقة على رفع الكود بكوميت واحد جديد.
