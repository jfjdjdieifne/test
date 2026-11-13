# جارفس CEO — مديرك التنفيذي على تيليجرام

بوت تيليجرام شخصي يحكي باللهجة الشامية، يدير فريق وكلاء (كل وكيل = فابل 5.2 + شخصية)،
يشتغل على Excel، يراقب مواقعك، وبيقدر **يعدّل نفسه** من الشات.

## التشغيل على السيرفر (مرة واحدة)

```bash
git clone <هذا الريبو> ~/jarvis-source
mkdir -p ~/jarvis-ceo && cp ~/jarvis-source/jarvis-ceo/* ~/jarvis-ceo/ && cd ~/jarvis-ceo
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
python3 -m unittest test_agent   # لازم تطلع OK
```

## الأسرار (مرة واحدة)

ملف `~/jarvis-ceo.env` بصلاحيات 600 — **ولا ترسله بأي شات**:

```bash
TELEGRAM_BOT_TOKEN=<توكن بوت jarvis v1>
COARENA_BASE_URL=https://coarena.ai/api/v1
COARENA_MODEL=claude-fable-5-2
COARENA_API_KEY=<مفتاح Coarena>
GEMINI_API_KEY=<نفس مفتاح Gemini اللي بالتجارب>
DAILY_TOKEN_CAP=200000
CEO_CHAT_ID=<رقم محادثتك مع البوت>   # اختياري: أول من يحكي مع البوت بينحصر فيه
```

```bash
chmod 600 ~/jarvis-ceo.env
```

## التشغيل الدائم (systemd)

```bash
sed -e "s/REPLACE_USER/$USER/g" -e "s/REPLACE_HOME/$HOME/g" jarvis-ceo.service > /tmp/jarvis-ceo.service
sudo cp /tmp/jarvis-ceo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis-ceo
sudo systemctl status jarvis-ceo
```

## الأوامر بالتيليجرام

| الأمر | شو بيعمل |
|---|---|
| أي نص أو فويس | يفهم ويرد — نص أو صوت |
| `وكلائي` | لستة الوكلاء وشخصياتهم |
| `سعيد` / `محمود` / `أحمد` / `متداول` + طلب | يوزع المهمة على الوكيل المناسب |
| Excel مرفق | «عبيلي كل صف…» / «وريني الأعمدة» |
| `راقب example.com` | سعيد يفحص الموقع كل 30 دقيقة |
| `حالة` / `مهام` / `تراجع` | إحصائيات / مفتوحة / إلغاء آخر تعديل ذاتي |
| «أضف وكيل اسمه X مهمته Y» | وكيل جديد فوراً |
| أي طلب تعديل على نفسه | «غيّر/أضف/احذف/صلح…» — يطبقه ويفحصه ويرجع للنسخة إذا فشل |

## الضمانات

- **سقف إنفاق يومي** `DAILY_TOKEN_CAP` (افتراضي 200k توكن) — فابل ما بينحرق الـ $55 بحلقة مجنونة.
- **التعديل الذاتي**: نسخة احتياطية → تعديل → `py_compile` + كل الاختبارات → إذا فشل أي شي يرجع للنسخة تلقائياً → `تراجع` بأي وقت.
- **ما بيلمس** `~/jarvis-ceo.env` ولا أي شي خارج مجلد jarvis-ceo.
- **قرارات مالية/خارجية**: اقتراحات فقط — التنفيذ بموافقتك الصريحة.
