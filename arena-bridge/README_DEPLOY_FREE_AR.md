# 📱 تشغيل جسر LMArena ٢٤/٧ ببلاش — من الموبايل فقط

سؤالك صح ومهم: الجسر لازمه جهاز **شغّال دايماً**. تحت أفضل ٤ طرق حقيقية، مرتبة،
وكلها تشتغل من متصفح الموبايل أو Termux — بدون لابتوب.

> **قبل أي شي، حقيقة تخفّف عليك الضغط:** جارفس **ما يحتاج** الجسر دايماً. إذا الجسر
> نايم أو مقفول، جارفس يكمّل تلقائياً على Gemini/Mistral/Groq/OpenRouter. الجسر
> "إضافة" لنماذج Arena، مو شرط للبوت. فحتى لو شغّلته ساعة بالنهار، البوت ما يتأثر.

---

## مقارنة سريعة (اقرأ هذي قبل ما تختار)

| الخيار | ببلاش فعلاً؟ | بطاقة بنك؟ | ٢٤/٧ بدون نوم؟ | من الموبايل؟ | ملاحظة |
|---|---|---|---|---|---|
| **A. Oracle Cloud Always Free** | ✅ للأبد | ⚠️ بطاقة للتحقق فقط (بدون خصم) | ✅ نعم | سهل (متصفح + Cloud Shell) | **الأفضل والأثبت** — 4 vCPU ARM + 24GB RAM |
| **B. Hugging Face Docker Space** | ✅ | ❌ لا | ⚠️ تنام بعد ~48 ساعة خمول → الـ Keep-alive يمنعها | سهل جداً | 16GB RAM مجاناً، بس الـ Space **عام** |
| **C. Termux على نفس الموبايل** | ✅ | ❌ لا | ❌ بس وقت الموبايل شغّال | متوسط | يحتاج نفق ngrok/cloudflared |
| **D. Render Free** | ✅ | ❌ لا | ⚠️ تنام بعد 15 دقيقة → Keep-alive يمنعها | سهل | 512MB RAM — ممكن ما تكفي المتصفح |

**توصيتي:** إذا عندك بطاقة (حتى لو رصيدها صفر) → **الخيار A**. إذا ما بدك بطاقة أبداً →
**الخيار B**. إذا بدك صفر تعقيد وصفر حسابات → **الخيار C** (بس بيوقف لما تقفل النت).

---

## ⭐ خلّي Arena أساس جارفس (مو مجرد إضافة)

بمجرد ما تحط `ARENA_BRIDGE_URL`، جارفس بيعتبر **Arena عقله الأساسي**: كل رد، كل مهمة
بالخلفية، وكل أداة (بحث ويب · فتح رابط · تدقيق موقع · إيميل · جدولة مهمة · تذكير) بتمرق
على Arena أولاً — وباقي المزودين (Gemini/Mistral/Groq/OpenRouter) صاروا احتياط فقط.

**ليش هيك صح؟** الأدوات والبحث ما بتصير داخل Arena — بتصير **بجارفس**: Arena بيقرر
"شو الخطوة" (يكتب `TOOL_CALL`)، وجارفس بينفذها فعلياً (بيفتح الرابط، بيبحث، بيبعت…) ويرجّع
النتيجة لـ Arena لي كمّل. يعني Arena = العقل، جارفس = اليدين. وهاد أحسن من أي "وكيل"
بموقع Arena لأنه بيمر على مفاتيحك وأدواتك وذاكرتك.

### تفعيله (دقيقتين)
```bash
cd agency-cloudflare
npx wrangler secret put ARENA_BRIDGE_URL   # https://<space>.hf.space أو http://<ip>:8000
npx wrangler secret put ARENA_BRIDGE_KEY   # BRIDGE_API_KEY
npx wrangler deploy
```
بعدها من تيليجرام:
- `/arena test` → يقولك أي محرك شغال فعلياً داخل الجسر (مش بس الصفحة شغالة).
- `/arena primary` → يقلب (أساسي ↔ احتياطي) بأي وقت بدون deploy.

### شو بصير لو Arena وقع؟
1. جارفس يصحّي الخدمة (`/health`) ويعيد المحاولة مرة.
2. إذا فشلت، يفتح **قاطع دائرة** ويتجاهل Arena 5 دقائق حتى ما يتأخر كل رد.
3. يكمّل على Gemini/Mistral/Groq/OpenRouter — البوت ما بيوقف ولا ثانية.

### أضمن طريق "أساسي ٢٤/٧" ببلاش
1. **HF Space** (بلا بطاقة): ارفع الجسر بأمر واحد من Termux:
```bash
pkg install -y python && pip install huggingface_hub
export HF_TOKEN=hf_xxxxxxxx        # من huggingface.co/settings/tokens (write)
python arena-bridge/deploy/hf_push.py --repo <حسابك>/jarvis-arena-bridge --browser
```
   `--browser` يحمّل chromium داخل الـ Space (يرفع فرص نجاح gpt4free/Arena كثيراً).
   الـ Keep-alive يشتغل تلقائياً لأن العنوان `hf.space`.
2. **قبل النوم**: `/arena test` مرة — إذا كل المحركات حمراء، معناها الكوكيز/الجلسة بدها تجديد.
3. **احتياط ذكي**: خلي مفاتيح Gemini/OpenRouter موجودة. إذا Arena تعطّل، البوت يضل شغال ٢٤/٧.

### الحقيقة الصادقة عن "Arena أساسي ٢٤/٧ ببلاش"
- LMArena موقع مجاني بجلسة متصفح، مو API رسمي — ممكن يطلب تسجيل دخول أو يحظر الاستخدام الآلي.
- أحياناً كل المحركات بترجع حمراء (كوكيز منتهية/حماية Cloudflare). الحل: أعد بناء الجلسة أو
  شغّل LMArenaBridge محلياً على الموبايل (Termux) وحدد `LMArenaBridge_URL`.
- عشان هيك صمّمنا الاحتياط التلقائي: **Arena أساس، بس مو نقطة فشل واحدة**.

---

## 🥇 الخيار A — Oracle Cloud Always Free (موصى به)

Oracle تعطي **سيرفر حقيقي ٢٤/٧ مجاناً للأبد** (Always Free): 4 vCPU ARM + 24GB RAM.
البطاقة للتحقق من الهوية فقط، ما ينسحب منها ولا دولار (بس لا تختار أي شي "Paid").

**من متصفح الموبايل:**

1. سجّل: https://signup.oraclecloud.com — اختر **Home Region: Germany/Frankfurt** (الأقرب لك).
2. التحقق بالبطاقة (خصم تجريبي ~1$ يرجع). بعدها: **Skip** أي ترقية لـ Pay-as-you-go.
3. من القائمة: **Compute → Instances → Create instance**
   - Image: **Ubuntu 22.04** (أو 24.04)
   - Shape: **Ampere (ARM)** → `VM.Standard.A1.Flex` → **4 OCPU / 24 GB**
   - ✅ **Assign a public IPv4 address**
   - حمّل/انسخ مفتاح SSH (أو استخدم **Cloud Shell** — أسهل من الموبايل: زر `>_` أعلى الصفحة، يفتحلك Terminal بالمتصفح مباشرة بدون SSH).
4. بـ Cloud Shell أو SSH، الصق:

```bash
git clone --depth 1 https://github.com/jfjdjdieifne/test.git ~/jarvis
bash ~/jarvis/arena-bridge/deploy/oracle-bootstrap.sh
```

   السكربت ينصّب كل شي (Python + venv + systemd) حتى الخدمة ترجع لحالها إذا السيرفر
   انعاد تشغيله، ويطبعلك **BRIDGE_API_KEY** — احتفظ فيه.

5. **افتح المنفذ 8000** — Oracle يسكّره مرتين:
   - اللوحة: **Networking → VCN → Subnet → Security List → Add Ingress Rule**
     `0.0.0.0/0 | TCP | 8000`
   - على السيرفر: `sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT && sudo netfilter-persistent save`
6. اختبر من المتصفح: `http://<IP-العام>:8000/health` → لازم يطلع `{"status":"ok",...}`
7. اربط بجارفس:

```bash
cd agency-cloudflare
npx wrangler secret put ARENA_BRIDGE_URL      # http://<IP>:8000
npx wrangler secret put ARENA_BRIDGE_KEY      # المفتاح المطبوع
npx wrangler secret put ARENA_BRIDGE_KEEPALIVE  # false  (Oracle ما ينام)
npx wrangler deploy
```

8. من تيليجرام: `/arena test` ثم `/arena_ask شو أخبار دبي؟`

**نصايح Oracle:** خُد نسخة احتياطية (Instance → Boot volume backup)، وإذا حسابك جديد
Oracle أحياناً ترفض البطاقة — جرّب بطاقة تانية أو انتقل للخيار B.

---

## 🥈 الخيار B — Hugging Face Space (بلا بطاقة نهائياً)

مجاني، **16GB RAM**، وبدك بس ترفع ٤ ملفات من متصفح الموبايل. الـ Space المجاني
**عام** (الكود ظاهر) — عشان هيك الحماية بـ `BRIDGE_API_KEY` إلزامية.

1. أنشئ حساب: https://huggingface.co/join
2. **New → Space** → الاسم `jarvis-arena-bridge` → SDK: **Docker** → Template: **Blank** → **Public**
3. من صفحة الـ Space: **Files → Add file → Upload files** وارفع:
   - `README.md` (من `arena-bridge/deploy/huggingface/README.md`)
   - `Dockerfile` (من `arena-bridge/deploy/huggingface/Dockerfile`)
   - `bridge.py` (من `arena-bridge/bridge.py`)
   - `requirements.txt` (من `arena-bridge/requirements.txt`)
4. **Settings → Variables and secrets → New secret**:
   - `BRIDGE_API_KEY` = مفتاح طويل عشوائي
   - (اختياري) `DEFAULT_MODEL=auto` · `G4F_FALLBACK=true`
5. استنى البناء (Logs) — بيصير عندك رابط:
   `https://<اسمك>-jarvis-arena-bridge.hf.space/health`
6. اربط بجارفس:

```bash
npx wrangler secret put ARENA_BRIDGE_URL      # https://<اسمك>-jarvis-arena-bridge.hf.space
npx wrangler secret put ARENA_BRIDGE_KEY      # نفس BRIDGE_API_KEY
npx wrangler secret put ARENA_BRIDGE_KEEPALIVE  # true  ← ضروري (HF تنوّم الخامل)
npx wrangler deploy
```

الـ Keep-alive: جارفس عنده cron كل دقيقة أصلاً، ولمّا `ARENA_BRIDGE_KEEPALIVE=true`
يضرب `/health` كل ١٠ دقائق → الـ Space يضل صاحي بدون أي أداة تانية.

---

## 🥉 الخيار C — Termux على نفس الموبايل + نفق ngrok

صفر حسابات سحابية، صفر بطاقات. بس الجسر بيشتغل **بس وقت الموبايل شغّال ومتصل**
(خليه على الشاحن، وامنع تحسين البطارية عن Termux).

```bash
# 1) من F-Droid نزّل Termux (لا تاخذه من Play Store — نسخة قديمة)
pkg update -y && pkg install -y python git curl
git clone --depth 1 https://github.com/jfjdjdieifne/test.git ~/jarvis
bash ~/jarvis/arena-bridge/deploy/termux-run.sh
```

بعدها افتح نفق (السكربت بيطبعلك الخطوات كاملة):

```bash
# ngrok بدومين ثابت مجاني (الأفضل — الرابط ما يتغير)
ngrok http 8000 --domain=<اسمك>.ngrok-free.app
# أو cloudflared (بدون حساب، رابط يتغير كل تشغيل)
./cloudflared tunnel --url http://127.0.0.1:8000
```

وحدّث جارفس بالرابط: `npx wrangler secret put ARENA_BRIDGE_URL`.
(جارفس يرسل هيدر `ngrok-skip-browser-warning` تلقائياً، فصفحة ngrok ما تعترض الردود.)

---

## الخيار D — Render (لو بدك GitHub فقط)

`arena-bridge/deploy/render-setup.sh` فيه الشرح خطوة بخطوة. المهم: **512MB RAM** فقط،
و`ARENA_BRIDGE_KEEPALIVE=true` إلزامي وإلا تنام بعد 15 دقيقة.

---

## أسئلة بتتكرر

**هل في حل بدون أي جهاز إطلاقاً؟** لا. Cloudflare Workers ما يشغّل Python ولا متصفح —
وهذا سبب وجود الجسر من الأصل. Colab وCodespaces كمان محدودة الساعات (مو ٢٤/٧).

**ليش ما نشغّل gpt4free داخل Cloudflare؟** لأنه يحتاج متصفح حقيقي/curl_cffi وكوكيز
جلسة Arena — Cloudflare Workers بيئة JS بدون متصفح.

**كم يستهلك نت؟** كل سؤال/جواب بيمرق عبر الجسر (نصوص فقط) — عادةً كيلوبايتات للرد.
بس إذا الموبايل هو السيرفر (الخيار C)، خليك على Wi-Fi أو راقب الباقة.

**شو يصير إذا الجسر نايم؟** جارفس يجرّب `/health` (Wake) ثم يرد مرة تانية، وإذا فشل
يكمّل على باقي المزودين ويشتغل عادي — ما بيتعطل البوت.

**كيف أتأكد إنه شغال؟** من تيليجرام: `/arena test` — يفحص الوصول من Cloudflare نفسه
(مو من متصفحك). و`/arena wake` يفيّق الخدمة النايمة.

---

## ملاحظات قانونية/أمان (مهمة)

- استخدام LMArena آلياً قد يخالف شروط استخدامهم وقد يُحظر الحساب — على حسابك الشخصي وعلى مسؤوليتك.
- Hugging Face Spaces المجاني عام: **لا تحط كوكيز Arena داخل الكود** — بالـ Secrets فقط، وإن أمكن لا تحطها إطلاقاً.
- أي VPS مكشوف على الإنترنت: `BRIDGE_API_KEY` إلزامي، ويفضّل HTTPS (Caddy/Cloudflare Tunnel).
- لا تحط أي مفتاح بمستودع Git — كل شي عبر `wrangler secret put`.
