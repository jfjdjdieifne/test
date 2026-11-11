# غرفة عمليات دبي B2B — وكالة بتكلفة 0$

هذا المجلد يحتوي على منظومة كاملة لاستهداف شركات عالية الدخل في **دبي** بثغرات تقنية حقيقية وموثقة على مواقعهم، مع عينات تحويل جاهزة للإرسال.

## محتويات المجلد

1. **`jarvis.html`** — **مساعدك الصوتي والذكي J.A.R.V.I.S ($0):**
   - واجهة أوامر بالصوت (Web Speech API المجاني في Chrome/Edge) والكتابة، متصلة بمبيعات دبي، مع ربط اختياري مجاني بـ **Google Gemini** أو **Groq** أو **OpenRouter (`openrouter/free`)** و**Webhook** لـ Make.com / n8n.
2. **`jarvis-stack/` + `wrangler.jsonc`** — **حزمة J.A.R.V.I.S الكاملة 24/7 ($0):**
   - `wrangler.jsonc` + `cf_worker.js`: ربط مباشر من GitHub إلى **Cloudflare Workers** بضغطة واحدة (ينشر الموقع + بوت تيليجرام 24/7 بدون توقف + مجدول مهام كل دقيقة، بدون بطاقة بنكية).
   - `BLUEPRINT_AR.md`: الخطوات الموثقة خطوة بخطوة (Cloudflare Workers، Render، Oracle Cloud، والمفاتيح المجانية).
   - `jarvis_telegram_agent.py`: نسخة البايثون الكاملة (Render / Oracle / الجهاز الشخصي).
   - `docker-compose.yml`: تشغيل n8n المجاني بأمر واحد.
2. **`index.html`** — **غرفة العمليات (War Room):**
   - تعرض 12 شركة حقيقية مفحوصة في دبي (تجميل، أسنان، تجديد فلل، تأسيس شركات، يخوت، سيارات فاخرة، بيوت عطلات).
   - توضح الثغرة الفعلية في موقع كل شركة + العرض المقترح + رسائل واتساب وإيميل مخصصة (EN/AR) + متابعة بعد 48 ساعة + متتبع حالة محلي.
3. **`dubai_high_ticket_leads.csv`** — ملف جدول بيانات بالـ 12 شركة وبيانات التواصل والثغرات.
4. **`demos/estheticare-dubai-demo.html`** — عينة حية لعيادة **EsthetiCare Clinic Dubai** (تصلح أزرار `#` المعطلة + حاسبة تكلفة زراعة الشعر والتجميل + تبديل عربي/إنجليزي).
5. **`demos/nam-consultant-calculator.html`** — عينة حية لشركة **NAM Consultant** (تصلح خطأ روابط `wa.me/00971...` + حاسبة تكلفة تأسيس الشركات والإقامة الذهبية).
6. **`demos/favorite-home-renovation-calc.html`** — عينة حية لشركة **Favorite Home Contracting LLC** (تصلح عداد `"0 Years of experience"` + حاسبة ميزانية ومدة تجديد الفلل).

## طريقة التشغيل على اللابتوب خلال ثوانٍ ($0)

1. اضغط **Code -> Download ZIP** من GitHub، وفك الضغط على جهازك.
2. افتح `agency/jarvis.html` (أو `agency/index.html`) بالضغط عليه مرتين في متصفح Chrome/Edge.
3. لنشر أي صفحة كرابط HTTPS مجاني (مهم خصوصاً لتفعيل الميكروفون من أي جهاز أو لإرسال عينة لعميل): اسحب المجلد أو الملف إلى [Netlify Drop](https://app.netlify.com/drop) لتحصل على رابط مباشر خلال 5 ثوانٍ.
