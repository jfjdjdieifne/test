# Arena Router + Jarvis Orchestrator

## المبدأ

Arena هو عقل الردود. Jarvis لا يضع سقفاً لقدراته؛ دوره إدارة السياق، اختيار مسار العمل، حفظ الحالة، تسمية الـAgents، وإرجاع Progress ونتائج موثقة إلى Telegram. أدوات STT/TTS السريعة تُعامل كواجهات صوت، لا كعقول بديلة.

## التوجيه

- **Direct Chat**: شرح، نقاش، سؤال، متابعة وفهم سريع.
- **Agent task**: بحث، بناء، تصميم، ملفات، تقارير، PDF، مراسلات، GitHub/Drive/Gmail/Notion/Vercel/Supabase وما شابه.
- `/route <الطلب>` يعرض قرار Router قبل التنفيذ.
- `ARENA_ONLY=true` يمنع تبديل عقل الرد بصمت إلى Gemini أو OpenRouter عند تعطل Arena.

## فريق Agents المفتوح

لا توجد قدرات ثابتة داخل الكود. المالك يعرّف الاسم والنطاق والدستور والـSkills:

```text
/agent add أحمد | التداول | دستور أحمد، قواعد المخاطر، ورابط skills/trading.md
/agent add سعيد | المبيعات | دستور سعيد وقوالب التواصل ومعايير التأهيل
/agents
```

عندما يذكر المستخدم الاسم، تُربط المهمة تلقائياً به وبسياقه. يمكن لاحقاً حفظ ملفات Skills ضخمة في GitHub وإبقاء الـRegistry كمؤشر إليها.

## المهام والتقدم

الطلب المعقد يدخل طابوراً مرتبطاً بمساحة العمل وAgent المسمّى. المهمة تحفظ:

- `threadId`, `agentId`, `route`
- `status`, `phase`, `progress`
- trace لأحدث الخطوات والنتائج
- قفل منع التنفيذ المكرر

Jarvis يرسل Progress دورياً. سؤال طبيعي مثل «شو صار؟» يقرأ سجل التنفيذ الحقيقي ولا يفتح شاتاً جديداً ولا يخمّن.

## الخصوصية

- تشخيص المتصفح لا يسجل البريد أو نص الصفحة أو عناوين الشاتات أو prompts.
- Workflow النشر لا يشغّل `wrangler tail` ولا يرسل Telegram payloads.
- رابط نقل جلسة Arena صالح 10 دقائق ولمرة واحدة.
- كلمة مرور Google لا تمر عبر Jarvis.

## ربط تطبيقات Arena

Dropbox، Gmail، GitHub، Google Docs/Sheets/Slides/Drive، Notion، Linear، Supabase وVercel هي Connectors داخل حساب Arena. Jarvis لا يعيد اختراعها ولا يحدد إمكانياتها؛ Agent Mode يستخدم ما هو مفعّل في جلسة Arena وفق صلاحيات المستخدم.
