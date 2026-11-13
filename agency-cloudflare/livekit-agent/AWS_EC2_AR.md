# ☁️ جارفس اللايف على AWS — 24/7 بدون جهازك الشخصي (برصيدك المجاني $100)

> مكتوب: 2026-11-13 · ينطبق على الفرع `arena/c299d7e2-test`.
> **أنا (الـ Agent) لا أستطيع ولا يجب أن أدخل على حساب AWS تبعك.** هاي خطوات تقوم فيها إنت — كلها مجانية ضمن الخطة.

---

## 1) يعني شو "$100 رصيد" و"182 يوم"؟ (شرح مبسط جداً)

| الشاشة | معناها |
|---|---|
| Current plan: **Free** | خطتك نسخة مجانية — **ما رح تنسحب أي مصاري من أي بطاقة**. إذا خلصت الأيام أو الرصيد، الخدمات بتتوقف (نادر)، **ما بيتحول تلقائياً لمدفوع** إلا إذا إنت ضغطت Upgrade بنفسك. |
| Credits remaining: **$100.00** | فلوس "افتراضية" تعطيك إياها AWS تجرب فيها خدماتها. مو كاش، مو قابل للسحب — يتصرف بس بدل فواتير AWS. |
| Days remaining: **182 يوم (13 مايو 2027)** | بعدها الحساب بيتحول للوضع العادي أو تتوقف الخدمات (حسب قوانين الخطة وقتها). المهم: **كل هاي القيمة لازم تستغلها قبل 2027-05-13**. |
| Amount due: **$0.00** | لأنك على Free Plan — لا يوجد أي مبلغ مطلوب إطلاقاً. |
| **Upgrade** | زر يدفعك لخطة مدفوعة — **ما تضغط عليه** إلا قرار واعٍ بإنك بدك تدفع فعلياً. |

### ماذا تستهلك الرصيد؟ (burn rate حقيقي)
| المورد | الاستهلاك الشهري التقريبي | 6 أشهر |
|---|---|---|
| EC2 `t4g.micro` (ARM، 1GB RAM) — تشغيل الـ Agent 24/7 | ~$6.1 | ~$37 |
| IP عام للـ EC2 ($0.005/ساعة — رسوم AWS العامة منذ 2024) | ~$3.6 | ~$22 |
| قرص EBS 8–16GB gp3 | ~$0.8–1.6 | ~$5–10 |
| **المجموع المتوقع** | **~$10–12/شهر** | **~$60–70** ✅ يظل تحت $100 بهامش أمان |

> ملاحظة صادقة: ما بعرف بالضبط إذا كانت ساعات `t3/t4g.micro` المجانية (750/شهر) مشمولة بخطتك — إذا كانت مشمولة، التكلفة ≈ $0 + بس IP العام. الرصيد يكفي الحالتين. للمراقبة: **Billing → Credits** مرة كل ربع سنة، وتفقد العداد قبل 2027-05-13.

---

> 💡 التالي لحالتك: خطة «كل شي ببلاش وبمحلي» كاملة + أصوات عربية على AWS (Polly) وعلى السيرفر (Nabra-82M) + لماذا Coarena يبقى العقل — بملف **`LOCAL_VOICE_AWS_AR.md`**.

## 2) شو نكسب؟ (الفائدة الحقيقية لهذا المشروع)

اليوم الـ Agent بيشتغل على جهازك الشخصي — يعني جارفس "لايف" بس لما اللابتوبك فاتح والـ Agent شغال. بنقله على AWS EC2:

1. **✅ جارفس يرد عليك 24/7 — حتى لو كان جهازك طافي أو أنت مسافر.** المكالمة بتروح لخادم دايم، مش لجهازك.
2. **✅ أولوية معالجة ثابتة:** الـ Agent ما بيتأذى من تحديث ويندوز/ماك ولا نوم اللابتوب.
3. **✅ نفس كود المستودع تماماً** — لا تعديل، لا fork؛ نفس `agent.py` والتعليمات الشامية والصوت السوري.
4. **✅ مرونة المستقبل بالرصيد:** بعد الـ Agent بتقدر تجرب أشياء مدفوعة خفيفة بنفس الرصيد (مثلاً cloning/نسخ احتياطي S3) بدون ما تدفع شي من جيبك.

### ما لا نكسب (صادق)
- **لا نحصل عقل أقوى مجاناً.** Coarena يضل مصدر العقل (مجاني منهم)؛ AWS هنا **مخزن تشغيل** بس. ما تحول شي على Bedrock — بيحرق الرصيد بلا فائدة لأن Coarena مجاني بنفس الجودة.
- **لا نحصل مكالمات هاتف PSTN مجانية.** AWS ما بيعطي أرقام واردة مجانية توصل للبوت — ما تغيرت هذه الحقيقة.
- **لا نحصل "AWS مجاني للأبد".** هذه 6 أشهر ثم الرصيد بينتهي. الحل الدائم المجاني بعد الرصيد: جهازك (وضعه الحالي) أو Oracle Always Free (يتطلب بطاقة للتحقق فقط).

---

## 3) جدول الخطوات — افتح EC2، شغّل الـ Agent (45 دقيقة أول مرة)

> كل الخطوات في **كونسول AWS** بالمتصفح — لا بنك ولا بطاقة ولا ترقية خطة.

### الخطوة 1 — أنشئ مفتاح دخول (مرة واحدة)
1. اكتب بخانة البحث فوق "EC2" → افتح **EC2**.
2. من اليسار: **Network & Security → Key Pairs** → **Create key pair**.
3. الاسم: `jarvis-key` · النوع: **RSA** · الصيغة: **.pem** → **Create** — رح ينزل ملف `jarvis-key.pem` (احفظه، هذا مفتاحك، لا تحطه GitHub).

### الخطوة 2 — جهّز السيرفر (Instance)
1. **Instances → Launch instances**.
2. **Name**: `jarvis-live`
3. **Application and OS Images**: اختر **Amazon Linux 2023** — وتأكد مكتوب عليها **Free tier eligible**.
4. **Instance type**: اختر **t4g.micro** (الأرخص — ARM 1 vCPU / 1GB) — وإذا خايف من ذاكرة: **t4g.small** (2GB) بضعف السعر (~$12/شهر — ما زال تحت الرصيد).
5. **Key pair**: اختر `jarvis-key`.
6. **Network settings**: الافتراضي ممتاز، بس غيّر **Allow SSH traffic from** → **My IP** (ما تفتح 22 للعالم).
7. **Configure storage**: 8–16 GB gp3 (ضمن الـ 30GB المجانية).
8. اضغط **Launch instance**.

### الخطوة 3 — ادخل على السيرفر
1. انتظر 1–2 دقيقة حتى تصبح الحالة **Running** + **Status check: 2/2 checks passed**.
2. ضع علامة ✓ على `jarvis-live` → **Connect** → تبويب **SSH client**.
3. انتسخ الأمر باللون الرمادي — شكله:
   `ssh -i "jarvis-key.pem" ec2-user@ec2-xx-xxx-xx-xxx.us-east-2.compute.amazonaws.com`
4. على جهازك (Mac/Linux ترمينال؛ ويندوز PowerShell):
   ```bash
   chmod 400 jarvis-key.pem     # Mac/Linux فقط
   ssh -i "jarvis-key.pem" ec2-user@<العنوان-اللي-نسخه>
   ```

### الخطوة 4 — ثبّت وحضّر المشروع (على السيرفر)
انسخ هذه الأوامر كتلة واحدة (بعد الدخول بالـ SSH):
```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip git
git clone --branch arena/c299d7e2-test --depth 1 https://github.com/jfjdjdieifne/test.git
cd test/agency-cloudflare/livekit-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### الخطوة 5 — جهّز إعدادات الـ Agent (ملف خدمة نظام — systemd)
```bash
sudo tee /etc/systemd/system/jarvis-live.service > /dev/null <<'EOF'
[Unit]
Description=Jarvis Live Voice Agent (LiveKit)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/test/agency-cloudflare/livekit-agent
Restart=always
RestartSec=5
Environment=LIVEKIT_URL=ضع_wss_مالتك_هون
Environment=LIVEKIT_API_KEY=ضع_المفتاح_هون
Environment=LIVEKIT_API_SECRET=ضع_السر_هون
Environment=COARENA_API_KEY=ضع_coa_هون
Environment=COARENA_API_KEY_2=ضع_مفتاح_Coarena_الثاني_هون_أو_احذف_السطر
Environment=COARENA_API_KEY_3=ضع_مفتاح_Coarena_الثالث_هون_أو_احذف_السطر
Environment=COARENA_MODEL=claude-fable-5-2
Environment=GROQ_API_KEY=ضع_gsk_هون
Environment=JARVIS_TTS=edge
Environment=EDGE_TTS_VOICE=ar-SY-LaithNeural
# لما تختار Polly على AWS: JARVIS_TTS=polly + POLLY_VOICE=Zayd|Hala + AWS_REGION=us-east-2
# Environment=JARVIS_TTS=polly
# Environment=POLLY_VOICE=Zayd
# Environment=AWS_REGION=us-east-2
ExecStart=/home/ec2-user/test/agency-cloudflare/livekit-agent/.venv/bin/python agent.py start

[Install]
WantedBy=multi-user.target
EOF
sudo nano /etc/systemd/system/jarvis-live.service   # املأ القيم بدل ضع_... (Ctrl+O حفظ، Ctrl+X خروج)
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis-live
journalctl -u jarvis-live -f     # شوف السجلات — Ctrl+C لإيقاف العرض (الخدمة تظل شغالة)
```
القيم هي نفسها الموجودة عندك ب `wrangler.toml [vars]` (LIVEKIT_* / COARENA_*) + مفتاح Groq المجاني الجديد من https://console.groq.com (بدون بطاقة):
- `LIVEKIT_URL` = `LIVEKIT_WS_URL` (المشروع 1) أو قيمة المشروع 2 لو حابب
- `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` = نفس الاسم ب `[vars]`
- `COARENA_API_KEY` (+ `_2`/`_3`… لو حبيت مجمع مفاتيح للـ Agent — توزيع round-robin على الـ Worker بين كل المفاتيح ب [vars] أصلاً)
- `GROQ_API_KEY` = مفتاح جديد من console.groq.com — مجاني، بدون بطاقة

**«كل المفاتيح على AWS» — الجرد الكامل:** ملف الخدمة على السيرفر هو المكان الوحيد اللي بتحط فيه: LIVEKIT_URL/KEY/SECRET (مشروع واحد يكفي للـ Agent — الثاني للصفحة `/live` كاحتياط وبتبديل تلقائي)، COARENA_API_KEY (+_2..)، GROQ_API_KEY، JARVIS_TTS/POLLY_* — **Linphone SIP/API-KEY بتظل ب [vars] للتوثيق بس — ما إلها استخدام بالـ Agent**. **مفتاح البوت التيليجرام والكرسي وDB ما بتحطها هون ولا بأي ملف بالمستودع** — bot يضل على Cloudflare منفصلاً. وملف الخدمة على السيرفر بـ root-readable، وبرة git تماماً.

> **لا تكتب القيم بأي ملف بالمستودع، ولا ترسلها بتيليجرام.** ملف الخدمة `/etc/systemd/system/jarvis-live.service` موجود على السيرفر فقط.

### الخطوة 5.5 — صوت AWS Polly (بشري، داخل حسابك — اختياري لكن موصى به)
> **تنبيه أمين:** أمازون ما عندها صوت **سوري** — أصواتها العربية Neural هي **Zayd (ذكر، ar-AE خليجي/فصحى)** و**Hala (أنثى، ar-AE)**. إذا بدك **سوري ذكر حرفي، يضل Edge TTS `ar-SY-LaithNeural` هو الحل** (الافتراضي، وشغّال الآن).

**التبديل لصوت Polly (15 دقيقة):**
1. IAM → Roles → **Create role** → AWS service → EC2 → attach policy **AmazonPollyReadOnlyAccess** → اسم `jarvis-polly` → Create.
2. EC2 → **Instances** → `jarvis-live` → **Actions → Security → Modify IAM role** → اختر `jarvis-polly` → Update. (هيك الـ Agent بياخد صلاحية Polly بدون أي مفتاح AWS بملف.)
3. عدّل السيرفر: `sudo nano /etc/systemd/system/jarvis-live.service` → خلّي `JARVIS_TTS=polly` و أضف `POLLY_VOICE=Zayd` و`AWS_REGION=us-east-2` → `sudo systemctl daemon-reload && sudo systemctl restart jarvis-live`.
4. `journalctl -u jarvis-live -f` ← لازم يطلع `polly-1` كمصدر صوت بدون أخطاء.

**الكلفة:** Neural Polly فيها **1M حرف/شهر مجاني لأول 12 شهر** للحسابات الجديدة — استخدامك الشخصي ≈ 5–50k حرف/شهر → **$0 فعلياً**. وبعدها: سنتات معدودة.

### الخطوة 6 — جرّب
1. من تيليجرام: `/live` → يتأكد إن LiveKit مضبوط.
2. افتح `https://<worker-مالتك>/live` → «اتصل بجارفس لايف» → احكِ.
3. افصل اللابتوب، اسحب التلفون، اتصل — جارفس بيرد حتى لو جهازك طافي. هون صار الفرق الحقيقي.

---

## 4) قواعد أمان الرصيد (مهمة جداً)

1. **لا تضغط Upgrade** بأي شاشة ما لم تقرر بإرادتك الدفع الفعلي.
2. **لا تُشغّل** instance أكبر من t4g.small — GPU و p3/g4/p4 ياكلون الرصيد خلال أيام.
3. **لا Elastic IP** (IP ثابت محجوز بدون instance) — $0.005/ساعة بصمت. استعمل الـ IP التلقائي مع Instance.
4. **لا AMIs من Marketplace** (مدفوعة) — Amazon Linux فقط.
5. **لا EBS كبيرة** — 8–16GB تكفي للـ Agent بفارق ضخم.
6. **الأمان**: SSH من **My IP** بس — أي instance مفتوح 22 للعالم بيتضرب scan خلال دقائق.
7. **راقب**: Billing → Credits → مرة بالشهر؛ وتأكد **Days remaining** ما قرب من الصفر بدون خطة (بعدها الخدمات بتتوقف وما بتنسحب مصاري — بس انقطع جارفس اللايف).
8. عند انتهاء الرصيد: انقل نفس الخطوات على Oracle Always Free (دائم مجاني بشروطهما) أو ارجع تشغيله على جهازك.

---

## 5) أسئلة شائعة

**س: هل $100 فلوس حقيقية أقدر أصرفها بأي شي؟**
لا — رصيد AWS تجريبي: يُصرف بس داخل AWS، وما يتحول كاش ولا ينحول خارجها.

**س: هل بيصير علي فاتورة؟**
ما دام انت على Free Plan ولا ضغطت Upgrade — لا. الـ $0.00 Amount due حقيقي.

**س: يعني جارفس بقى لايف 24/7 مدى الحياة؟**
لمدة الرصيد + ما بعده بـ Oracle Always Free (أو جهازك). AWS مجرد جسر مثالي لهالمرحلة لأن كل شي مجاني فيه بحدوده.

**س: بقدر أستعمله لاستضافة بوتات ثانية؟**
تقنياً نعم (أي شيء خفيف: Node/Python/static) — بس ضمن $100 و6 أشهر؛ كل instance إضافية بتنزل من نفس الرصيد.
