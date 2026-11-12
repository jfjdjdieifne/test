import CALL_PAGE from "./callpage.mjs";
import puppeteer from "@cloudflare/puppeteer";
import remotePuppeteer from "puppeteer-core";
/**
 * J.A.R.V.I.S — Telegram Agent on Cloudflare Workers
 * ----------------------------------------------------
 * ٠ سيرفر ٠ بدون بطاقة ٠ يعمل 24/7 على Workers Free
 * - Webhook (ولا حاجة لـ polling ولا لبطاقة)
 * - LLM failover: Gemini → Mistral → Groq → NVIDIA → OpenRouter free
 * - ذاكرة دائمة في Cloudflare KV (مجاني)
 * - 12 عميل دبي مدمجين + تحديث حالتهم في KV
 * - بحث ويب حي (Tavily أو DuckDuckGo)
 * - فحص مواقع (أزرار # الميتة، روابط واتساب الخاطئة…)
 * - مهام خلفية + رنّة تيليجرام عبر CallMeBot
 *
 * الأسرار كلها تُضبط عبر `wrangler secret put` — لا تضع أي مفتاح هنا.
 */

const LEADS = [
  { i: 1, pri: "هوت", company: "EsthetiCare Clinic Dubai", website: "https://www.estheticaredubai.ae/en/", wa: "971559128418", phone: "+971 4 214 0700", deal: "8,000–35,000+ AED", sector: "عيادة تجميل وزراعة شعر", issues: "أزرار الحجز تروح لعلامات # ميتة؛ رابط wa.me يحتوي +؛ ماكو حاسبة أسعار تفاعلية", offer: "صفحة تحويل بمثبّت + حاسبة تفاعلية لزراعة الشعر والأسعار", price: "$250–$450" },
  { i: 2, pri: "هوت", company: "NAM Consultant", website: "https://www.namconsultant.com/", wa: "971524315575", phone: "+971 52 431 5575", deal: "15,000–45,000+ AED", sector: "تأسيس شركات + إقامة ذهبية", issues: "روابط واتساب بصيغة 0097152… (00 يكسر الروابط)؛ ماكو حاسبة Mainland vs Freezone؛ لا توجد نسخة عربية", offer: "قمع واتساب + حاسبة تفاعلية لتكاليف التأسيس والإقامة الذهبية (EN/AR)", price: "$250–$500" },
  { i: 3, pri: "هوت", company: "Favorite Home Contracting LLC", website: "https://favoritehome.ae/", wa: "971503922777", phone: "+971 55 533 9596", deal: "150,000–800,000+ AED", sector: "تجديد الفلل والديكور", issues: "عداد يعرض «0 سنوات» ويناقض «من 2009»؛ قائمة تنقّل ملخبطة +30 رابط؛ لا توجد حاسبة ميزانية", offer: "Hero ثقة معاد + حاسبة ميزانية ومدة ترميم تفاعلية", price: "$350–$700" },
  { i: 4, pri: "هوت", company: "VIP Luxury Car Rental Dubai", website: "https://vipluxurycarrental.com/", wa: "971501564849", phone: "+971 50 156 4849", deal: "3,000–25,000+ AED", sector: "تأجير سوبركار وسيدان فاخرة", issues: "KPI يعرض «0★» و«0+ سيارة»؛ خطأ إملائي DriveBeyond؛ بلا حاسبة عرض سعر متعدد الأيام", offer: "إصلاح Hero KPI + حاسبة عرض سعر وإيداع متعددة الأيام", price: "$200–$450" },
  { i: 5, pri: "هوت", company: "USBC Interiors", website: "https://www.usbcinteriors.com/villa-fitout/", wa: "971502536606", phone: "+971 4 552 5858", deal: "150,000–1,000,000+ AED", sector: "ديكور داخلي وفلل", issues: "تكرار مراحل 1-4 بشكل مكرر؛ خطأ «Portolio»؛ رابط واتساب فارغ بلا تأهيل للميزانية", offer: "صفحة هبوط نظيفة + نموذج تأهيل BOQ تفاعلي للفلل", price: "$350–$650" },
  { i: 6, pri: "دافئ", company: "La Perla Dental Clinic", website: "https://laperladental.com/", wa: "971564662598", phone: "+971 4 432 1732", deal: "4,000–30,000+ AED", sector: "أسنان تجميلية وزراعة", issues: "كتلة ساعات العمل تتكرر 3 مرات؛ زر «Mob/Whatsapp» رابط اتصال tel: بدل wa.me", offer: "صفحة عيادة ثابتة + حاسبة فينير وزراعة تفاعلية", price: "$200–$400" },
  { i: 7, pri: "دافئ", company: "Bay Avenue Dental Centre", website: "https://www.bayavenuedentalcentre.com/", wa: "971551465512", phone: "+971 4 277 0247", deal: "3,500–25,000+ AED", sector: "أسنان تجميلية وعائلية", issues: "تكرار 4 بطاقات خدمات مرتين؛ رابط wa.link غير موسوم؛ بلا حاسبة ابتسامة", offer: "صفحة تحويل نظيفة + حاسبة ابتسامة وتقسيط تفاعلية", price: "$200–$400" },
  { i: 8, pri: "دافئ", company: "Yacht Rental UAE", website: "https://yachtrentaluae.ae/", wa: "971585513070", phone: "+971 58 551 3070", deal: "3,000–160,000+ AED", sector: "تأجير يخوت", issues: "رابط واتساب فيه + ومسافات غير مشفرة؛ typo؛ بلا حاسبة charter للضيوف/الساعات/الضيافة", offer: "حاسبة Charter يخت تفاعلية (ضيوف+ساعات+كاترينغ) ترسل واتساب", price: "$250–$450" },
  { i: 9, pri: "دافئ", company: "Sasha Aesthetic Clinic", website: "https://sashaaestheticclinic.ae/", wa: "971586907865", phone: "+971 4 458 2226", deal: "1,000–15,000+ AED", sector: "تجميل وليزر وأسنان", issues: "صورة د. ماجد فارغة (Placeholder)؛ بلا بناء عروض BOGO تفاعلية؛ إنجليزي فقط", offer: "حاسبة باقات BOGO تفاعلية + صفحة هبوط عربية", price: "$200–$350" },
  { i: 10, pri: "دافئ", company: "Best Renovation Dubai", website: "https://www.bestrenovation.ae/", wa: "971566123317", phone: "+971 56 612 3317", deal: "50,000–500,000+ AED", sector: "ترميم فلل ومطابخ", issues: "سطر wp-author مطبوع بالصفحة؛ امتدادات .webp.webp؛ بلا حاسبة غرفة بغرفة", offer: "حاسبة BOQ ترميم تفاعلية + صفحة تحويل عربية", price: "$250–$500" },
  { i: 11, pri: "دافئ", company: "RSY Yachts", website: "https://rsyyachts.com/", wa: "971555786772", phone: "+971 55 578 6772", deal: "2,500–50,000+ AED", sector: "يخوت وفعاليات", issues: "عداد تنازلي ثابت لا يتحرك؛ بلا بناء باقة فعالية (حجم+ساعات+جت سكي+كاترينغ)", offer: "باني باقات فعالية تفاعلي + صفحة ثنائية اللغة EN/AR", price: "$250–$450" },
  { i: 12, pri: "دافئ", company: "One Perfect Stay", website: "https://oneperfectstay.com/", wa: "971565663842", phone: "+971 52 566 4648", deal: "15,000–80,000+ AED/سنة", sector: "إدارة وحدات فندقية Airbnb", issues: "صفحة المالك ترسل لزمن توقع عام بدل حاسبة عائد فوري على الصفحة", offer: "حاسبة عائد تأجير قصير/طويل تفاعلية + قمع مالك عربي", price: "$300–$600" },
];

const TOOL_DOC = `الأدوات التالية واجهة Jarvis المحلية وليست حداً لقدرات Arena أو التطبيقات المربوطة بحسابها. لا تدّعِ أن Arena عاجزة عن شيء لمجرد أنه غير موجود بالقائمة:
- search_web(query): بحث ويب حي
- open_url(url): افتح أي رابط واقرأ نص الصفحة (مناسب للتحقق من صفحة، سعر، خبر، شروط…)
- arena_chat(prompt, model?): اسأل نماذج LMArena مباشرة (رأي تاني أو نموذج محدد)
- audit_website(url): فحص سريع لموقع (أزرار # الميتة، واتساب خاطئ، لغة/عنوان/نماذج)
- list_leads(status?): قائمة الـ 12 عميل (فلتر اختياري: جديد/راسلته/مهتم/عرض/مقفل)
- get_lead(index): تفاصيل عميل 1-12
- update_lead(index, status, note): تحديث حالة عميل (تُحفظ دائماً)
- start_background_task(goal): اطلب إذن المالك لفتح مهمة بالخلفية (توصله بطاقة ✅/❌ بتيليجرام — ما تنص المهمة أبداً بدون ضغطته). لو وافق، تنفذ على مراحل كل دقيقة وتوصل تقريراً ورنّة عند الانتهاء
- remember(fact, tags?): حفظ حقيقة دائمة عن المالك/عمله في الذاكرة طويلة المدى (حرفياً بلا تلخيص — صفر توكنات)
- recall_memory(query): استرجاع الحقائق المحفوظة المطابقة
- forget_memory(query): حذف حقيقة مطابقة
- send_email(to, subject, body): تجهيز إيميل من Gmail مالتك — يُرسل بعد موافقتك بضغطة واحدة
- call_me_now(message): رنّة تيليجرام فورية للمالك عبر CallMeBot

لتنفيذ أداة اكتب سحراً بأداة واحدة فقط بهذا الشكل بالضبط ولا شيء غيره:
TOOL_CALL: {"tool":"اسم_الأداة","args":{...}}
بعد وصول TOOL_RESULT أكمل منطقياً. وعند الاكتمال اكتب الجواب النهائي بالكامل بلا أي TOOL_CALL.`;

const BASE_PROMPT = `أنت "جارفس"، ذكاء اصطناعي عربي خاص بصاحب العمل (المالك الوحيد). أسلوبك: واثق، مهني، موجز، وباللهجة الشامية السورية دائماً (مثال: "شلونك يا ريس؟ شو بدك اليوم؟"، "تمام، خليني اشيك لك"، "موشكلة، هسع بتدبرلك ياه"). ممنوع الفصحى الجامدة — رد طبيعي كسوري حقيقي.
- لا تخترع معلومات؛ إن احتجت بيانات استخدم الأداة.
- إجابات قصيرة ومنظّمة بنقاط عند الحاجة (السطرز الموازي بالفصحى بس داخل الكود).
- إذا كانت الرسالة صوتية: ردك جملتين أو ثلاث قصيرة فقط (عشان تتحول لصوت بسرعة)، وكلام طبيعي بدون نقاط أو رموز تنسيق — كإنك صديق ذكي يحكي وياه.
- جميع الأرقام بالإنجليزية (واتساب، أسعار، روابط).
${TOOL_DOC}`;

const WORKER_PROMPT = `أنت "جارفس" تنفذ مهمة خلفية مستقلة نيابة عن المالك، بدون سؤاله.
اتبع الأدوات خطوة خطوة حتى الإنجاز، ثم اكتب تقريراً عربياً موجزاً وحاداً.
تحدث باللهجة الشامية السورية وبالإيجاز. إذا احتجت قرار المالك فقط استخدم call_me_now(message) موجزاً.
${TOOL_DOC}`;

const MAX_HISTORY = 14;
const MAX_TOOL_STEPS = 6;

function arenaConnectPage(origin, token) {
  const endpoint = `${origin}/arena-session-import`;
  const js = `javascript:(async()=>{try{const s={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);s[k]=localStorage.getItem(k)}const r=await fetch(${JSON.stringify(endpoint)},{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({token:${JSON.stringify(token)},storage:s,cookie:document.cookie||''})});const d=await r.json();alert(d.ok?'✅ تم نقل جلسة Arena إلى Jarvis. ارجع لتيليجرام واكتب /arena test للتأكد من صلاحيتها':'❌ '+(d.error||r.status))}catch(e){alert('❌ '+e.message)}})()`;
  const escaped = js.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return `<!doctype html><html lang="ar" dir="rtl"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ربط Arena مع Jarvis</title><style>body{font-family:system-ui;background:#07111f;color:#eef;padding:24px;line-height:1.7;max-width:650px;margin:auto}.box{background:#11223b;padding:18px;border-radius:16px;margin:14px 0}button{font-size:18px;padding:14px;width:100%;border:0;border-radius:12px;background:#39d98a;color:#06140d;font-weight:700}code{word-break:break-all;color:#9ff}b{color:#6ef}</style><h1>🔐 ربط جلسة Arena</h1><p>لا تُنقل كلمة مرور Google. يُنقل رمز جلسة Arena فقط، والرابط صالح عشر دقائق ولمرة واحدة.</p><div class="box"><b>1.</b> اضغط الزر لنسخ كود الربط.<br><button onclick="navigator.clipboard.writeText(document.getElementById('code').textContent).then(()=>alert('تم النسخ ✅'))">انسخ كود الربط</button><code id="code" style="display:none">${escaped}</code></div><div class="box"><b>2.</b> في Safari اعمل Bookmark لأي صفحة، ثم Edit وبدّل عنوانه بالكود المنسوخ. سمّه «ربط جارفس».</div><div class="box"><b>3.</b> افتح <a style="color:#6ef" href="https://arena.ai">arena.ai</a> وأنت مسجّل دخول، ثم افتح Bookmark «ربط جارفس».</div><div class="box"><b>4.</b> بعد ظهور ✅ ارجع لتيليجرام واكتب <code>/arena test</code>.</div></html>`;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/ask" || url.pathname === "/voice-ask" || url.pathname === "/call-end") {
      if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS_HEADERS });
      if (request.method !== "POST") return jsonResponse({ error: "POST only" }, 405, CORS_HEADERS);
      if (url.pathname === "/voice-ask") return handleVoiceAsk(request, env, ctx);
      if (url.pathname === "/call-end") return handleCallEnd(request, env, ctx);
      return handleAsk(request, env, ctx);
    }
    if (url.pathname === "/arena-session-import") {
      if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: { ...CORS_HEADERS, "access-control-allow-headers": "content-type" } });
      if (request.method !== "POST") return jsonResponse({ error: "POST only" }, 405, CORS_HEADERS);
      let body; try { body = await request.json(); } catch { return jsonResponse({ error: "bad json" }, 400, CORS_HEADERS); }
      const expected = await kvGet(env, "arena_connect_token", null);
      const expires = Number(await kvGet(env, "arena_connect_expires", 0)) || 0;
      if (!expected || body?.token !== expected || expires < Date.now()) return jsonResponse({ error: "expired or invalid link" }, 401, CORS_HEADERS);
      const storage = body?.storage && typeof body.storage === "object" ? body.storage : {};
      const safeStorage = {};
      // Arena غيّرت أسماء مفاتيح الجلسة أكثر من مرة؛ المصدر محصور بـarena.ai عبر الـbookmarklet.
      for (const [k, v] of Object.entries(storage)) if (typeof k === "string" && k.length < 200 && typeof v === "string" && v.length < 30000) safeStorage[k] = v;
      const cookie = typeof body?.cookie === "string" ? body.cookie.slice(0, 20000) : "";
      if (!Object.keys(safeStorage).length && !cookie) return jsonResponse({ error: "Arena browser storage is empty; reload Arena and try again" }, 422, CORS_HEADERS);
      await kvPut(env, "arena_imported_storage", safeStorage);
      await kvPut(env, "arena_runtime_storage", safeStorage);
      await kvPut(env, "arena_imported_cookie", cookie);
      await kvPut(env, "arena_imported_at", Date.now());
      await kvPut(env, "arena_connect_token", null);
      await kvPut(env, "arena_connect_expires", 0);
      await kvPut(env, "arena_skip_until", 0);
      await kvPut(env, "arena_session_alerted_at", 0);
      await kvPut(env, "arena_direct_session_v3", null);
      return jsonResponse({ ok: true, imported: Object.keys(safeStorage).length }, 200, CORS_HEADERS);
    }
    if (url.pathname === "/arena-connect") {
      const token = url.searchParams.get("token") || "";
      const expected = await kvGet(env, "arena_connect_token", null);
      const expires = Number(await kvGet(env, "arena_connect_expires", 0)) || 0;
      if (!token || token !== expected || expires < Date.now()) return new Response("رابط الربط منتهي. اطلب /arena connect من جديد.", { status: 401, headers: { "content-type": "text/plain;charset=utf-8" } });
      return new Response(arenaConnectPage(url.origin, token), { headers: { "content-type": "text/html;charset=utf-8", "cache-control": "no-store" } });
    }
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok", service: "jarvis-cf", ts: Date.now() }), { status: 200, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
    }
    if (url.pathname === "/browserless-health") {
      if (!env.CALL_SECRET || url.searchParams.get("key") !== env.CALL_SECRET) return jsonResponse({ error: "unauthorized" }, 401);
      const token = String(await kvGet(env, "browserless_token_v1", env.BROWSERLESS_TOKEN || "") || "").trim();
      if (!token) return jsonResponse({ ok: false, reason: "not_configured" }, 200);
      let b; try {
        b = await connectBrowserlessNative(`wss://production-ams.browserless.io?token=${encodeURIComponent(token)}&timeout=30000`);
        const p = await b.newPage(); await p.goto("https://example.com", { waitUntil: "domcontentloaded", timeout: 15000 });
        await kvPut(env, "browserless_last_error_v1", null);
        const pending = await kvGet(env, "arena_pending_direct_v1", []); for (const item of pending) item.availableAt = Date.now(); await kvPut(env, "arena_pending_direct_v1", pending);
        return jsonResponse({ ok: true }, 200);
      } catch (e) {
        const message = String(e?.message || e); await kvPut(env, "browserless_last_error_v1", { at: Date.now(), error: message.slice(0, 300) });
        return jsonResponse({ ok: false, reason: message.slice(0, 300) }, 200);
      } finally { if (b) try { await b.close(); } catch {} }
    }
    if (url.pathname === "/arena-status") {
      if (!env.CALL_SECRET || url.searchParams.get("key") !== env.CALL_SECRET) return jsonResponse({ error: "unauthorized" }, 401);
      const lastError = await kvGet(env, "arena_browser_last_error", null);
      const lastOk = await kvGet(env, "arena_browser_last_ok", null);
      const importedAt = Number(await kvGet(env, "arena_imported_at", 0)) || 0;
      const skipUntil = Number(await kvGet(env, "arena_skip_until", 0)) || 0;
      let browserLimits = null; try { browserLimits = env.BROWSER ? await puppeteer.limits(env.BROWSER) : null; } catch {}
      return jsonResponse({ lastError, lastOk, browserlessConfigured: !!String(await kvGet(env, "browserless_token_v1", env.BROWSERLESS_TOKEN || "") || ""), browserlessLastError: await kvGet(env, "browserless_last_error_v1", null), browserLimits, pendingDirect: (await kvGet(env, "arena_pending_direct_v1", [])).length, streamShape: await kvGet(env, "arena_stream_shape", null), diagnostic: await kvGet(env, "arena_browser_last_diagnostic", null), importedAgeMinutes: importedAt ? Math.round((Date.now() - importedAt) / 60000) : null, cooldownSeconds: Math.max(0, Math.round((skipUntil - Date.now()) / 1000)), hasDirectSession: !!(await kvGet(env, "arena_direct_session_v3", null)) }, 200);
    }
    if (url.pathname === "/" ) {
      return new Response("JARVIS CF is alive — see /health", { status: 200 });
    }
    if (url.pathname === "/tts") {
      if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS_HEADERS });
      if (request.method !== "GET" && request.method !== "POST") return jsonResponse({ error: "GET/POST only" }, 405, CORS_HEADERS);
      return handleTts(request, env);
    }
    if (url.pathname === "/call") {
      return new Response(CALL_PAGE, { status: 200, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" } });
    }
    if (url.pathname === "/webhook" && request.method === "POST") {
      const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (!env.WEBHOOK_SECRET || secret !== env.WEBHOOK_SECRET) {
        return new Response("forbidden", { status: 403 });
      }
      let update;
      try { update = await request.json(); } catch { return new Response("bad json", { status: 400 }); }
      // نحتاج العنوان لبناء رابط /arena connect بدون متغير يدوي.
      ctx.waitUntil(kvPut(env, "public_worker_url", url.origin));
      ctx.waitUntil(kvPut(env, "last_user_activity_at", Date.now()));
      ctx.waitUntil(handleUpdate(update, env, ctx).catch((e) => console.log("handler error:", e && e.message ? e.message : e)));
      return new Response("ok", { status: 200 });
    }
    return new Response("not found", { status: 404 });
  },
  // يعمل كل دقيقة — موجز صباحي الساعة 06:00 UTC مرة يومياً + طابور المهام دائماً
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      try {
        const now = new Date(event?.scheduledTime || Date.now());
        if (now.getUTCHours() === 6 && now.getUTCMinutes() === 0) await morningBrief(env);
        // Keep-alive لجسر LMArena: يمنع Hosting المجاني (Render/HF) من تنويم الخدمة
        const kaBase = (await arenaCfg(env)).base;
        if (arenaKeepAliveOn(env, kaBase) && kaBase && now.getUTCMinutes() % 10 === 0) {
          const alive = await arenaWake(env, 1, 0);
          if (!alive) console.log("arena keepalive: لا استجابة من الجسر");
        }
        // لا تفتح Browser لمجرد keep-alive: حصة Cloudflare المجانية محدودة،
        // والتجديد يتم عند أول استخدام حقيقي مع حفظ refresh token المحدث.
      } catch (e) { console.log("brief error:", e && e.message ? e.message : e); }
      try { await processDirectRetries(env); } catch (e) { console.log("direct retry error:", e?.message || e); }
      try {
        const lastUser = Number(await kvGet(env, "last_user_activity_at", 0)) || 0;
        // أعطِ رسائل المستخدم أولوية على المهام الخلفية حتى لا تتنافس على Browser.
        if (Date.now() - lastUser > 2 * 60000) await processTaskQueue(env, STEPS_PER_TICK);
      } catch (e) { console.log("queue error:", e && e.message ? e.message : e); }
      try { await proactiveTaskReview(env); } catch (e) { console.log("proactive review error:", e && e.message ? e.message : e); }
    })());
  },
};

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "POST, OPTIONS",
  "access-control-allow-headers": "content-type, x-jarvis-key",
};

function jsonResponse(obj, status, extraHeaders) {
  return new Response(JSON.stringify(obj), { status: status || 200, headers: { "content-type": "application/json; charset=utf-8", ...(extraHeaders || {}) } });
}

/* ------------------------------ Telegram ------------------------------ */

async function tgApi(env, method, payload) {
  try {
    const res = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    let data = null;
    try { data = await res.json(); } catch {}
    return { ok: res.ok && data && data.ok !== false, data };
  } catch (e) {
    console.log("tgApi error:", e && e.message ? e.message : e);
    return { ok: false, data: null };
  }
}

async function sendMessage(env, chatId, text) {
  const MAX = 3800;
  let remaining = String(text == null ? "" : text);
  if (!remaining.trim()) remaining = "…";
  while (remaining.length > MAX) {
    let cut = remaining.lastIndexOf("\n", MAX);
    if (cut < 800) cut = remaining.lastIndexOf(" ", MAX);
    if (cut < 800) cut = MAX;
    await tgApi(env, "sendMessage", { chat_id: chatId, text: remaining.slice(0, cut) });
    remaining = remaining.slice(cut).trimStart();
  }
  await tgApi(env, "sendMessage", { chat_id: chatId, text: remaining });
}

/* ------------------------------ KV helpers ----------------------------- */

async function kvGet(env, key, fallback) {
  try {
    if (!env.JARVIS_KV) return fallback;
    const raw = await env.JARVIS_KV.get(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch { return fallback; }
}
async function kvPut(env, key, value) {
  try { if (env.JARVIS_KV) await env.JARVIS_KV.put(key, JSON.stringify(value)); } catch (e) { console.log("kvPut error:", e && e.message ? e.message : e); }
}
const getHistory = (env) => kvGet(env, "history", []); // legacy fallback
const saveHistory = (env, convo) => kvPut(env, "history", convo.slice(-MAX_HISTORY));

/* ---------------- مدير المشاريع/الشاتات فوق Arena ----------------
   Arena قد ينسى الجلسة؛ جارفس لا يعتمد على session المزود. كل مشروع له سياقه في KV،
   ويُعاد حقنه لأي محرك (Arena أو fallback)، لذلك نقدر نرجع لشغل من مبارح أو أسبوع. */
const THREADS_KEY = "context_threads_v1";
const ACTIVE_THREAD_KEY = "active_context_thread_v1";
const AGENTS_KEY = "arena_agent_registry_v1";

/* Registry مفتوح: الاسم/الدستور/skills يحددها المالك، ولا نفترض حدود قدرات Arena. */
async function getAgentRegistry(env) { return (await kvGet(env, AGENTS_KEY, [])) || []; }
async function saveAgentRegistry(env, rows) { await kvPut(env, AGENTS_KEY, rows.slice(0, 100)); }
async function findMentionedAgent(env, text) {
  const rows = await getAgentRegistry(env); const hay = String(text || "").toLowerCase();
  return rows.find((a) => hay.includes(String(a.name || "").toLowerCase())) || null;
}
function arenaRouteIntent(text) {
  const s = String(text || "").trim();
  const forcedDirect = /^(سؤال|اسأل|اشرح|فسر|شو يعني|ما هو|ما هي)\b/i.test(s);
  const forcedAgent = /^(مهمة|نفّذ|نفذ|ابني|اصنع|صمم|صمّم|ابحث|حقق|حقّق)\b/i.test(s);
  const complex = /(pdf|ملف|تقرير|دراسة|خطة كاملة|مشروع|github|git hub|drive|درايف|gmail|ايميل|إيميل|notion|نوشن|vercel|supabase|sheets|slides|docs|ارفع|نزّل|حلّل|حلل|قارن|افحص|صمّم|صمم|ابني|ابحث|راسل|نفّذ|نفذ)/i.test(s);
  if (forcedDirect) return { mode: "direct", reason: "explicit-question" };
  if (forcedAgent || complex) return { mode: "agent", reason: forcedAgent ? "explicit-task" : "complex-action" };
  return { mode: "direct", reason: "conversation" };
}
function threadWords(s) {
  return [...new Set(String(s || "").toLowerCase().replace(/[^\p{L}\p{N}_-]+/gu, " ").split(/\s+/)
    .filter((w) => w.length > 2 && !/^(هذا|هاي|هاد|على|الى|إلى|فيها|عليه|في|من|شو|بدي|كمل|تمام|the|and|for|with)$/.test(w)))];
}
function threadLabel(text) {
  return String(text || "محادثة جديدة").replace(/\s+/g, " ").trim().slice(0, 64) || "محادثة جديدة";
}
async function getThreads(env) { return (await kvGet(env, THREADS_KEY, [])) || []; }
async function putThreads(env, rows) { await kvPut(env, THREADS_KEY, rows.slice(0, 40)); }
function threadScore(t, text) {
  const q = new Set(threadWords(text));
  const hay = new Set(threadWords([t.title, t.summary, ...(t.keywords || []), ...((t.messages || []).slice(-4).map((m) => m.content))].join(" ")));
  let n = 0; for (const w of q) if (hay.has(w)) n++;
  const ageDays = (Date.now() - (t.updated || 0)) / 86400000;
  return n * 10 - Math.min(ageDays, 30) * 0.12;
}
async function resolveThread(env, text, forceId) {
  const rows = await getThreads(env);
  const active = forceId || await kvGet(env, ACTIVE_THREAD_KEY, "");
  if (forceId) {
    const exact = rows.find((t) => t.id === forceId || t.id.endsWith(forceId));
    if (exact) return { rows, thread: exact, reason: "manual" };
  }
  const explicitNew = /^(موضوع|مشروع|شات|محادثة)\s+(جديد|جديدة)|خلينا نبدأ|ابدأ من الصفر/i.test(String(text).trim());
  const continuation = /^(كمل|كمّل|تابع|تمام|طيب|اي|نعم|لا|اعملها|نفذ|نفّذ|وبعدين|شو صار)/i.test(String(text).trim());
  let picked = null, reason = "new";
  if (!explicitNew && rows.length) {
    const ranked = rows.map((t) => ({ t, s: threadScore(t, text) })).sort((a, b) => b.s - a.s);
    const activeThread = rows.find((t) => t.id === active);
    if (ranked[0] && ranked[0].s >= 9.5) { picked = ranked[0].t; reason = "matched"; }
    else if (continuation && activeThread) { picked = activeThread; reason = "continuation"; }
    else if (activeThread && Date.now() - (activeThread.updated || 0) < 45 * 60000) { picked = activeThread; reason = "recent"; }
  }
  if (!picked) {
    picked = { id: "ctx_" + Date.now().toString(36), title: threadLabel(text), summary: "", keywords: threadWords(text).slice(0, 16), messages: [], created: Date.now(), updated: Date.now(), status: "active" };
    rows.unshift(picked);
  }
  await kvPut(env, ACTIVE_THREAD_KEY, picked.id);
  return { rows, thread: picked, reason };
}
async function saveThreadTurn(env, resolved, convo) {
  const t = resolved.thread;
  t.messages = convo.slice(-MAX_HISTORY).map((m) => ({ role: m.role, content: String(m.content || "").slice(0, 3500) }));
  const userTexts = t.messages.filter((m) => m.role === "user").map((m) => m.content);
  t.keywords = threadWords([t.title, ...userTexts].join(" ")).slice(0, 24);
  t.summary = userTexts.slice(-4).join(" | ").slice(0, 900);
  t.updated = Date.now();
  const i = resolved.rows.findIndex((x) => x.id === t.id);
  if (i >= 0) resolved.rows[i] = t; else resolved.rows.unshift(t);
  await putThreads(env, resolved.rows.sort((a, b) => (b.updated || 0) - (a.updated || 0)));
}

/* ---------------- الذاكرة طويلة المدى — بلا استنزاف توكنات -------------- */
// الحفظ خما (بدون LLM): صفر توكنات للتخزين. الاسترجاع محلي بتطابق كلمات: صفر توكنات.
// عند كل رسالة يُحقن فقط المقتطفات المطابقة (أقل من ~400 توكن) — وليس كامل التاريخ.

const MEM_KEY = "mem:all";
const STOPWORDS = new Set(["في","من","على","إلى","عن","مع","هذا","هذه","ذلك","كان","يكون","ما","لا","لم","لن","أن","إن","أو","ثم","كل","بعض","عند","بعد","قبل","حتى","جدا","جداً","يعني","بس","هو","هي","هم","the","a","an","of","to","in","on","for","is","are","and","or","with","at","by"]);

async function getMemories(env) { return kvGet(env, MEM_KEY, []); }
async function saveMemories(env, arr) { await kvPut(env, MEM_KEY, arr.slice(-500)); }

function tokenize(text) {
  return String(text || "").toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/).filter((w) => w.length >= 3 && !STOPWORDS.has(w));
}
function scoreFact(fact, terms) {
  const hay = (fact.text + " " + (fact.tags || []).join(" ")).toLowerCase();
  let sc = 0;
  for (const t of terms) if (hay.includes(t)) sc += t.length > 4 ? 2 : 1;
  if (fact.pinned) sc += 5;
  return sc;
}
async function relevantMemories(env, userText) {
  const all = await getMemories(env);
  if (!all.length) return "";
  const asksAboutSelf = /(شو|ماذا|ايش|إيش|شنو).*تعرف.*(عني|عنّي)|مين أنا|ذاكرتك.*عني|كل.*معلومات.*عني/i.test(String(userText || ""));
  if (asksAboutSelf) return "كل الذاكرة الثابتة المسجلة عن المالك (اعرضها بصدق ونظّمها، ولا تضف شيئاً غير موجود):\n" + all.slice(-40).map((m) => "- " + m.text).join("\n") + "\n";
  const terms = tokenize(userText).slice(0, 40);
  const pinned = all.filter((m) => m.pinned).slice(0, 4);
  const scored = all.map((m) => [scoreFact(m, terms), m])
    .filter(([sc]) => sc > 0).sort((a, b) => b[0] - a[0]).slice(0, 8).map(([, m]) => m);
  const merged = [];
  for (const m of [...pinned, ...scored]) if (!merged.find((x) => x.id === m.id)) merged.push(m);
  if (!merged.length) return "";
  return "سياق ثابت عن المالك وعمله (لا تسأل عنه مرة ثانية أبداً):\n" + merged.map((m) => "- " + m.text).join("\n") + "\n";
}
async function addMemories(env, lines, pinPrefix) {
  const all = await getMemories(env);
  const out = [];
  for (const raw of lines) {
    let text = String(raw || "").trim();
    if (!text) continue;
    const pinned = pinPrefix && text.startsWith("!");
    if (pinned) text = text.slice(1).trim();
    if (!text) continue;
    all.push({ id: "m_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 6), text: text.slice(0, 400), pinned, tags: tokenize(text).slice(0, 8), created: Date.now() });
    out.push((pinned ? "📌 " : "") + text);
  }
  await saveMemories(env, all);
  return out;
}
async function recallMemories(env, query) {
  const all = await getMemories(env);
  if (!all.length) return "(الذاكرة فارغة حتى الآن)";
  if (/^(المالك|عني|عنّي|كل شي|كل شيء|كل المعلومات|everything|owner)$/i.test(String(query || "").trim())) return all.slice(-40).map((m) => "- (" + m.id.slice(-4) + ") " + (m.pinned ? "📌 " : "") + m.text).join("\n");
  const terms = tokenize(query).slice(0, 30);
  const scored = all.map((m) => [scoreFact(m, terms), m]).filter(([sc]) => sc > 0).sort((a, b) => b[0] - a[0]).slice(0, 8);
  if (!scored.length) return all.slice(-8).reverse().map((m) => "- (" + m.id.slice(-4) + ") " + m.text).join("\n");
  return scored.map(([, m]) => "- (" + m.id.slice(-4) + ") " + (m.pinned ? "📌 " : "") + m.text).join("\n");
}
async function forgetMemories(env, query) {
  const all = await getMemories(env);
  const q = String(query || "").trim().toLowerCase();
  if (!q) return "اكتب ماذا تريد أن أنسى.";
  const idx = all.findIndex((m) => m.id.endsWith(q) || m.id === q);
  let removed = null;
  if (idx !== -1) { removed = all.splice(idx, 1)[0]; }
  else {
    const n = Number(q);
    if (Number.isInteger(n) && n >= 1 && n <= all.length) { removed = all.splice(n - 1, 1)[0]; }
    else {
      const terms = tokenize(q);
      let best = -1, bestScore = 0;
      all.forEach((m, i) => { const sc = scoreFact(m, terms); if (sc > bestScore) { bestScore = sc; best = i; } });
      if (bestScore > 0) removed = all.splice(best, 1)[0];
    }
  }
  if (!removed) return "ما لقيت حقيقة مطابقة.";
  await saveMemories(env, all);
  return "انسيت: " + removed.text;
}

/* ------------------------------ LLM failover --------------------------- */

async function callGemini(convo, system, env) {
  if (!env.GEMINI_API_KEY) return null;
  try {
    const model = (env.GEMINI_MODEL || "gemini-2.5-flash").trim();
    const contents = convo.map((m) => ({ role: m.role === "assistant" ? "model" : "user", parts: [{ text: String(m.content) }] }));
    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ system_instruction: { parts: [{ text: system }] }, contents, generationConfig: { maxOutputTokens: 400, temperature: 0.4 } }),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) { console.log("gemini HTTP", res.status); return null; }
    const data = await res.json();
    const parts = data?.candidates?.[0]?.content?.parts || [];
    const text = parts.map((p) => p.text || "").join("").trim();
    return text || null;
  } catch (e) { console.log("gemini error:", e && e.message ? e.message : e); return null; }
}

async function callOpenAICompatible(base, key, model, convo, system) {
  if (!key) return null;
  try {
    const res = await fetch(`${base}/chat/completions`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${key}` },
      body: JSON.stringify({ model, messages: [{ role: "system", content: system }, ...convo.map((m) => ({ role: m.role, content: String(m.content) }))], temperature: 0.4, max_tokens: 400 }),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) { console.log("llm HTTP", res.status, base); return null; }
    const data = await res.json();
    const text = data?.choices?.[0]?.message?.content?.trim();
    return text || null;
  } catch (e) { console.log("llm error:", e && e.message ? e.message : e); return null; }
}

async function callOpenRouterWithFallback(convo, system, env) {
  if (!env.OPENROUTER_API_KEY) return null;
  const wanted = [env.OPENROUTER_MODEL, "moonshotai/kimi-k2:free", "meta-llama/llama-3.3-70b-instruct:free", "google/gemini-2.0-flash-exp:free", "deepseek/deepseek-chat-v3-0324:free", "openrouter/free"]
    .map((m) => String(m || "").trim())
    .filter(Boolean);
  const seen = new Set();
  for (const model of wanted) {
    if (seen.has(model)) continue;
    seen.add(model);
    const out = await callOpenAICompatible("https://openrouter.ai/api/v1", env.OPENROUTER_API_KEY, model, convo, system);
    if (out) return out;
  }
  return null;
}

async function callWorkersAI(convo, system, env) {
  if (!env.AI) return null;
  try {
    const res = await env.AI.run("@cf/meta/llama-3.3-70b-instruct-fp8-fast", {
      messages: [{ role: "system", content: system }, ...convo.map((m) => ({ role: m.role, content: String(m.content) }))],
      max_tokens: 400,
      temperature: 0.4,
    });
    const text = String(res?.response || res?.result || "").trim();
    if (text) return text;
  } catch (e) { console.log("workers-ai error:", e && e.message ? e.message : e); }
  return null;
}

async function callPollinations(convo, system, env) {
  try {
    const res = await fetch("https://text.pollinations.ai/openai", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ model: "mistral", messages: [{ role: "system", content: system }, ...convo.map((m) => ({ role: m.role, content: String(m.content) }))], max_tokens: 400, temperature: 0.4 }),
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) return null;
    const d = await res.json().catch(() => ({}));
    const text = d?.choices?.[0]?.message?.content?.trim();
    return text || null;
  } catch (e) { console.log("pollinations error:", e && e.message ? e.message : e); return null; }
}

/* ------------------------- LMArena bridge (اختياري) -------------------- */
/*
 * الجسور الأصلية (CloudWaddie/LMArenaBridge · Blacklisted-Binary/LMArenaProxy ·
 * lianues/lmarenabridge · xtekky/gpt4free) كلها Python + متصفح حقيقي، فما تشتغل
 * داخل Cloudflare Worker. الحل: خدمة `arena-bridge/` بمستودعنا تكشف API متوافق
 * مع OpenAI، وجارفس بيناديها هنا كمزود إضافي.
 *
 * المتغيرات:
 *   ARENA_BRIDGE_URL    — مطلوب للتفعيل، مثال: https://arena.example.com (بدون /v1)
 *   ARENA_BRIDGE_KEY    — اختياري (يُرسل كـ Bearer)
 *   ARENA_BRIDGE_MODEL  — النموذج الافتراضي، افتراضياً "auto"
 *   ARENA_BRIDGE_FIRST  — "true" يخلي Arena أول مزود قبل Gemini
 *   ARENA_BRIDGE_TIMEOUT_MS — افتراضياً 45000 (المتصفح بطيء)
 */
function arenaBridgeConfig(env) {
  const e = env || {};
  const base = String(e.ARENA_BRIDGE_URL || "").trim().replace(/\/+$/, "");
  const key = String(e.ARENA_BRIDGE_KEY || "").trim();
  return { base, key, enabled: !!base, url: base ? base + "/v1/chat/completions" : "" };
}

/**
 * إعدادات الجسر الفعلية: قيم KV (من أوامر تيليجرام) تتقدّم على متغيرات البيئة.
 * يعني تقدر تضبط كل شي من تيليجرام بدون wrangler ولا لوحة Cloudflare.
 */
async function arenaCfg(env) {
  const envCfg = arenaBridgeConfig(env);
  const kvUrl = await kvGet(env, "arena_url", null);
  const kvKey = await kvGet(env, "arena_key", null);
  const base = String(kvUrl || envCfg.base || "").trim().replace(/\/+$/, "");
  const key = String(kvKey || envCfg.key || "").trim();
  return { base, key, browser: !!(env && env.BROWSER), enabled: !!base || !!(env && env.BROWSER), url: base ? base + "/v1/chat/completions" : "" };
}

function parseArenaDataStream(raw) {
  const chunks = [];
  const add = (value) => { if (typeof value === "string" && value !== "hasArenaError") chunks.push(value); };
  for (let line of String(raw || "").split(/\r?\n/)) {
    line = line.trim(); if (!line) continue;
    try {
      // Arena استعمل a0 سابقاً، وVercel AI Data Stream يستعمل 0 حالياً.
      if (/^(?:a0|0):/.test(line)) { add(JSON.parse(line.slice(line.indexOf(":") + 1))); continue; }
      // بعض إصدارات Direct ترسل SSE حديثاً.
      if (line.startsWith("data:")) {
        const payload = line.slice(5).trim(); if (!payload || payload === "[DONE]") continue;
        const v = JSON.parse(payload);
        if (v?.type === "text-delta") add(v.delta ?? v.textDelta ?? v.text);
        else if (typeof v?.delta === "string") add(v.delta);
        else if (typeof v?.content === "string" && /assistant|text/i.test(String(v.type || v.role || "text"))) add(v.content);
      }
    } catch {}
  }
  return chunks.join("").trim();
}

function arenaStreamShape(raw) {
  const counts = {};
  for (const line of String(raw || "").split(/\r?\n/)) {
    const m = line.trim().match(/^([a-zA-Z0-9_-]{1,20})(?=:)/); const k = m?.[1] || (line.trim().startsWith("data:") ? "data" : "other");
    counts[k] = (counts[k] || 0) + 1;
  }
  return counts;
}

function arenaSessionFromStorage(storage) {
  const seen = new Set();
  function walk(v) {
    if (!v || typeof v !== "object" || seen.has(v)) return null; seen.add(v);
    if (typeof v.access_token === "string" && typeof v.refresh_token === "string") return v;
    for (const x of Object.values(v)) { const found = walk(x); if (found) return found; }
    return null;
  }
  for (const raw of Object.values(storage || {})) {
    if (typeof raw !== "string") continue;
    try { const found = walk(JSON.parse(raw)); if (found) return found; } catch {}
  }
  return null;
}

async function connectBrowserlessNative(endpoint) {
  // puppeteer-core يحاول استعمال حزمة ws الخاصة بـNode، وهي غير متاحة داخل Workers.
  // هذا Transport يربطه مباشرةً بـWebSocket الأصلي في Cloudflare Workers.
  const socket = new WebSocket(endpoint);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("Browserless WebSocket open timeout")), 15000);
    socket.addEventListener("open", () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener("error", () => { clearTimeout(timer); reject(new Error("Browserless WebSocket handshake failed")); }, { once: true });
  });
  const transport = {
    onmessage: null, onclose: null,
    send(message) { socket.send(message); },
    close() { try { socket.close(); } catch {} },
  };
  socket.addEventListener("message", (event) => transport.onmessage?.(typeof event.data === "string" ? event.data : new TextDecoder().decode(event.data)));
  socket.addEventListener("close", () => transport.onclose?.());
  return await remotePuppeteer.connect({ transport });
}

async function acquireArenaBrowser(env) {
  // Browserless المجاني: 1000 وحدة/شهر، بلا بطاقة، ويدعم Puppeteer وCAPTCHA.
  // هو المسار الأول؛ Cloudflare (10 دقائق/يوم) يبقى احتياطياً تلقائياً.
  const browserlessToken = String(await kvGet(env, "browserless_token_v1", env.BROWSERLESS_TOKEN || "") || "").trim();
  if (browserlessToken) {
    try {
      const endpoint = `wss://production-ams.browserless.io?token=${encodeURIComponent(browserlessToken)}&timeout=60000`;
      return { browser: await connectBrowserlessNative(endpoint), provider: "browserless" };
    } catch (e) {
      const message = String(e?.message || e);
      console.log("browserless connect error:", message);
      await kvPut(env, "browserless_last_error_v1", { at: Date.now(), error: message.slice(0, 300) });
    }
  }
  // احتياط Cloudflare الرسمي: 600 ثانية Browser يومياً.
  try {
    const limits = await puppeteer.limits(env.BROWSER);
    if (Number(limits?.usedBrowserTimeSeconds || 0) >= 598) throw new Error(browserlessToken ? "ALL_BROWSER_FREE_TIERS_EXHAUSTED" : "DAILY_BROWSER_LIMIT");
  } catch (e) { if (/DAILY_BROWSER_LIMIT|ALL_BROWSER/.test(String(e?.message || e))) throw e; }
  return { browser: await puppeteer.launch(env.BROWSER, { keep_alive: 60000 }), provider: "cloudflare" };
}

async function releaseArenaBrowser(browser) {
  if (!browser) return;
  try { await browser.close(); } catch {}
}

async function arenaReconnectLink(env) {
  const base = String(await kvGet(env, "public_worker_url", "")).replace(/\/+$/, "");
  if (!base) return "";
  const token = crypto.randomUUID().replace(/-/g, "") + crypto.randomUUID().replace(/-/g, "");
  await kvPut(env, "arena_connect_token", token);
  await kvPut(env, "arena_connect_expires", Date.now() + 10 * 60 * 1000);
  return `${base}/arena-connect?token=${token}`;
}

async function refreshArenaSession(env) {
  if (!env?.BROWSER || !(await arenaIsOn(env))) return false;
  let browser;
  try {
    const storage = await kvGet(env, "arena_runtime_storage", await kvGet(env, "arena_imported_storage", {}));
    if (!storage || !Object.keys(storage).length) return false;
    browser = (await acquireArenaBrowser(env)).browser;
    const page = await browser.newPage();
    const cookies = await kvGet(env, "arena_browser_cookies", []);
    if (Array.isArray(cookies) && cookies.length) try { await page.setCookie(...cookies); } catch {}
    await page.goto("https://arena.ai/text/direct", { waitUntil: "domcontentloaded", timeout: 10000 });
    await page.evaluate((items) => { for (const [k, v] of Object.entries(items || {})) localStorage.setItem(k, v); }, storage);
    await page.reload({ waitUntil: "domcontentloaded", timeout: 10000 });
    await new Promise((r) => setTimeout(r, 3500));
    const fresh = await page.evaluate(() => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; });
    if (fresh && Object.keys(fresh).length) await kvPut(env, "arena_runtime_storage", fresh);
    await kvPut(env, "arena_browser_cookies", await page.cookies());
    const session = arenaSessionFromStorage(fresh || {});
    const healthy = !!session && (!session.expires_at || Number(session.expires_at) * 1000 > Date.now() + 2 * 60000);
    if (healthy) { await kvPut(env, "arena_session_alerted_at", 0); return true; }
    const last = Number(await kvGet(env, "arena_session_alerted_at", 0)) || 0;
    if (Date.now() - last > 6 * 60 * 60000) {
      await kvPut(env, "arena_session_alerted_at", Date.now());
      const owner = await getOwnerChatId(env); const link = await arenaReconnectLink(env);
      if (owner) await sendMessage(env, owner, `🔐 جلسة Arena بحاجة لتجديد. حضرتلك رابط آمن صالح 10 دقائق:\n${link || "اكتب /arena connect"}\n\nما تخزّن كلمات مرور، وما في داعي تبعتلي أي توكن.`);
    }
    return false;
  } catch (e) { console.log("arena session refresh error:", e?.message || e); return false; }
  finally { await releaseArenaBrowser(browser); }
}

/** Arena بلا سيرفر: Chromium مُدار من Cloudflare Browser Rendering.
 * نستخدم واجهة Arena الحقيقية، لذلك الصفحة نفسها تنشئ reCAPTCHA والجلسة؛ ثم نحفظ
 * cookies في KV ليستمر تسجيل الدخول بين تشغيل وآخر. */
async function callArenaBrowser(convo, system, env) {
  if (!env || !env.BROWSER) return null;
  if (!(await arenaIsOn(env)) || await arenaInCooldown(env)) return null;
  let browser;
  try {
    browser = (await acquireArenaBrowser(env)).browser;
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });
    const saved = await kvGet(env, "arena_browser_cookies", []);
    if (Array.isArray(saved) && saved.length) { try { await page.setCookie(...saved); } catch {} }
    // Telegram webhook returns immediately and ctx.waitUntil has a ~30s ceiling؛ لازم ننهي
    // نجاحاً أو فشلاً ضمنه حتى ما تختفي نتيجة /arena test بصمت.
    // افتح Direct Chat صراحةً. لا نستخدم الصفحة الرئيسية لأنها تبدأ Battle Mode.
    await page.goto("https://arena.ai/text/direct", { waitUntil: "domcontentloaded", timeout: 8000 });
    const imported = await kvGet(env, "arena_runtime_storage", await kvGet(env, "arena_imported_storage", {}));
    const importedCookie = String(await kvGet(env, "arena_imported_cookie", "") || "");
    if ((imported && typeof imported === "object" && Object.keys(imported).length) || importedCookie) {
      if (imported && typeof imported === "object") await page.evaluate((items) => { for (const [k, v] of Object.entries(items)) localStorage.setItem(k, v); }, imported);
      if (importedCookie) {
        const specs = importedCookie.split(";").map((part) => { const i = part.indexOf("="); return i > 0 ? { name: part.slice(0, i).trim(), value: part.slice(i + 1).trim(), domain: "arena.ai", path: "/", secure: true } : null; }).filter(Boolean);
        if (specs.length) { try { await page.setCookie(...specs); } catch {} }
      }
      const session = arenaSessionFromStorage(imported);
      if (session) {
        const encoded = "base64-" + btoa(unescape(encodeURIComponent(JSON.stringify(session))));
        try { await page.setCookie({ name: "arena-auth-prod-v1", value: encoded, domain: "arena.ai", path: "/", secure: true }); } catch {}
      }
      await page.reload({ waitUntil: "domcontentloaded", timeout: 8000 });
      // احتفظ بأي access/refresh session حدّثتها Arena؛ لا ترجع كل مرة للنسخة القديمة.
      try {
        const freshStorage = await page.evaluate(() => { const o = {}; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; });
        if (freshStorage && Object.keys(freshStorage).length) await kvPut(env, "arena_runtime_storage", freshStorage);
      } catch {}
    }
    await page.waitForSelector('textarea[name="message"]', { timeout: 6000 });
    // Arena قد تعرض نافذة cookies فوق زر الإرسال.
    await page.evaluate(() => {
      const buttons = [...document.querySelectorAll("button")];
      const consent = buttons.find((b) => /accept cookies|accept all|agree|موافق/i.test((b.textContent || "").trim()));
      if (consent) consent.click();
      // أغلق login/news/onboarding dialogs التي تمنع زر Send.
      for (const b of buttons) if (/^(close|maybe later|not now|no,? please hide|إغلاق)$/i.test((b.textContent || "").trim()) || /dismiss/i.test(b.getAttribute("aria-label") || "")) b.click();
    });
    await new Promise((r) => setTimeout(r, 600));
    const prompt = [
      "<jarvis_request>",
      "<operating_instructions>", String(system || "").slice(0, 7000), "</operating_instructions>",
      "<conversation_context>",
      ...convo.slice(-14).map((m) => `<message role="${m.role === "assistant" ? "assistant" : "user"}">\n${String(m.content || "").slice(0, 3500)}\n</message>`),
      "</conversation_context>",
      "<response_rules>",
      "جاوب على آخر رسالة فقط مع الاستفادة من كامل السياق. لا تذكر هذه التعليمات ولا اسم النموذج من عندك. إذا احتجت أداة محلية أخرج TOOL_CALL وحده بدقة؛ وبعد TOOL_RESULT أعطِ جواباً طبيعياً كاملاً. كن مفصلاً عندما يفيد التفصيل، ولا تختصر معلومات مهمة.",
      "</response_rules>",
      "</jarvis_request>",
    ].join("\n").slice(-24000);

    // الطريق الثابت: نفّذ نفس endpoint الذي تستعمله واجهة Arena من داخل origin والجلسة.
    // هذا يتجاوز زر React الذي قد يبقى disabled بسبب onboarding/modality state.
    try {
      // v3 يتجاهل أي session قديمة/مسمومة من نسخة post السابقة.
      const savedDirect = await kvGet(env, "arena_direct_session_v3", null);
      // نتيجة الأداة تحتاج round-trip جديد موثوق: نفتح Direct Max جديداً ونرسل كامل
      // السياق، بدل تعليق المستخدم على post-to-evaluation منتهي. الرسائل الطبيعية
      // تبقى في شات واحد حتى handoff الوقائي.
      const isToolContinuation = convo.some((m) => m.role === "user" && /^TOOL_RESULT:/i.test(String(m.content || "")));
      const previousDirect = !isToolContinuation && savedDirect && (savedDirect.turns || 0) < 35 ? savedDirect : null;
      const directRaw = await page.evaluate(async ({ message, previous }) => {
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        let token = "";
        for (let i = 0; i < 20; i++) { if (window.grecaptcha?.enterprise) break; await sleep(200); }
        if (window.grecaptcha?.enterprise) {
          token = await new Promise((resolve) => window.grecaptcha.enterprise.ready(async () => {
            try { resolve(await window.grecaptcha.enterprise.execute("6LeTGMcsAAAAALuIlkVwIxaAuZA8VledA6d3Nnb0", { action: "chat_submit" })); } catch { resolve(""); }
          }));
        }
        const id = () => {
          const b = crypto.getRandomValues(new Uint8Array(16));
          let ts = BigInt(Date.now());
          for (let i = 5; i >= 0; i--) { b[i] = Number(ts & 255n); ts >>= 8n; }
          b[6] = (b[6] & 0x0f) | 0x70; b[8] = (b[8] & 0x3f) | 0x80;
          const h = [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
          return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
        };
        // Arena ينشر قائمة النماذج داخل HTML. Max هو أول/أسرع اختيار في Direct Chat؛
        // نقرأ الـid ديناميكياً بدل تثبيت اسم قد تغيّره Arena.
        let modelAId = "";
        try {
          const html = await (await fetch("/text/direct")).text();
          const marker = html.indexOf("initialModels");
          if (marker >= 0) {
            const start = html.indexOf("[", marker); let depth = 0, quoted = false, esc = false, end = -1;
            for (let i = start; i >= 0 && i < html.length; i++) { const c = html[i]; if (quoted) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === '"') quoted = false; } else if (c === '"') quoted = true; else if (c === "[") depth++; else if (c === "]" && --depth === 0) { end = i + 1; break; } }
            if (end > start) { const models = JSON.parse(html.slice(start, end).replace(/\\"/g, '"')); const max = models.find((m) => /^max$/i.test(m.publicName || m.name || "")) || models[0]; modelAId = max?.id || ""; }
          }
        } catch {}
        if (!modelAId) throw new Error("Arena Direct Max model id was not found");
        const evaluationId = previous?.id || id();
        const data = { id: evaluationId, mode: "direct-battle", userMessageId: id(), modelAMessageId: id(), modelAId, userMessage: { content: message, experimental_attachments: [], metadata: {} }, modality: "chat", recaptchaV3Token: token || "" };
        const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), 15000);
        try {
          const endpoint = previous?.id ? `/nextjs-api/stream/post-to-evaluation/${previous.id}` : "/nextjs-api/stream/create-evaluation";
          const res = await fetch(endpoint, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(data), signal: ctl.signal });
          const text = await res.text();
          return { status: res.status, text, evaluationId, modelAId };
        } finally { clearTimeout(timer); }
      }, { message: prompt, previous: previousDirect });
      const directText = directRaw && directRaw.status < 400 ? parseArenaDataStream(directRaw.text) : "";
      if (directText) {
        try { await kvPut(env, "arena_browser_cookies", await page.cookies()); } catch {}
        await kvPut(env, "arena_direct_session_v3", { id: directRaw.evaluationId, modelId: directRaw.modelAId, turns: (previousDirect?.turns || 0) + 1, updated: Date.now() });
        await arenaMarkUp(env); await kvPut(env, "arena_browser_last_ok", { at: Date.now(), chars: directText.length, transport: "direct-max" });
        return directText;
      }
      const streamShape = arenaStreamShape(directRaw?.text || "");
      console.log("arena direct diagnostic:", JSON.stringify({ status: directRaw?.status || 0, has_body: !!directRaw?.text, streamShape }));
      await kvPut(env, "arena_stream_shape", { at: Date.now(), status: directRaw?.status || 0, streamShape });
      // إذا Arena قبلت الطلب وأنشأت الشات، ممنوع إعادة إرساله عبر UI وخلق نسخة ثانية.
      if (directRaw?.status > 0 && directRaw.status < 400 && directRaw.text) {
        await kvPut(env, "arena_browser_last_error", { at: Date.now(), error: "Arena stream format not recognized" });
        return null;
      }
      // قد تنتهي جلسة Direct أو يرفض Arena إضافة turn جديد. لا نرمي جواب المستخدم:
      // افتح handoff جديد فوراً مع كامل السياق المرسل وحاول مرة واحدة تلقائياً.
      if (previousDirect) {
        await kvPut(env, "arena_direct_session_v3", null);
        await releaseArenaBrowser(browser); browser = null;
        return await callArenaBrowser(convo, system, env);
      }
    } catch (e) {
      console.log("arena direct error:", e && e.message ? e.message : e);
      const stale = await kvGet(env, "arena_direct_session_v3", null);
      if (stale) { await kvPut(env, "arena_direct_session_v3", null); await releaseArenaBrowser(browser); browser = null; return await callArenaBrowser(convo, system, env); }
    }

    let responseStarted = false;
    const responsePromise = new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Arena stream timeout (12s)")), 12000);
      page.on("response", async (response) => {
        // Arena غيّرت اسم endpoint أكثر من مرة (evaluation/direct chat). التقط أي
        // stream تابع لـnextjs-api؛ الصفحة نفسها هي origin الموثوق، ثم حلّل الداتا.
        if (!/\/nextjs-api\/stream\//.test(response.url())) return;
        responseStarted = true;
        try { const body = await response.text(); clearTimeout(timer); resolve({ body, status: response.status(), path: new URL(response.url()).pathname }); }
        catch (e) { clearTimeout(timer); reject(e); }
      });
    });
    const box = await page.$('textarea[name="message"]');
    await box.click();
    // React controlled textarea: Puppeteer.type يغيّر DOM أحياناً دون state، فيبقى Send disabled.
    await page.evaluate((text) => {
      const ta = document.querySelector('textarea[name="message"]');
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
      if (!ta || !setter) return;
      setter.call(ta, text);
      ta.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
      ta.dispatchEvent(new Event("change", { bubbles: true }));
    }, prompt);
    try { await page.waitForFunction(() => { const b = document.querySelector('button[aria-label="Send message"]'); return b && !b.disabled; }, { timeout: 3500 }); } catch {}
    const clicked = await page.evaluate(() => {
      const ta = document.querySelector('textarea[name="message"]');
      const form = ta && ta.closest("form");
      // ممنوع اختيار أي submit عام: نافذة التسجيل فيها Continue with Google من نفس النوع.
      const exact = document.querySelector('button[aria-label="Send message"], button[aria-label*="send" i]');
      const candidates = form ? [...form.querySelectorAll("button")] : [];
      const submit = exact || candidates.find((b) => !b.disabled && /send|إرسال/i.test(`${b.getAttribute("aria-label") || ""} ${b.textContent || ""}`));
      if (!submit) return false;
      submit.click(); return true;
    });
    if (!clicked) await page.keyboard.press("Enter");
    // أحياناً Arena تفتح Login modal عند أول إرسال للزائر. أغلقها وأعد الإرسال مرة.
    await new Promise((r) => setTimeout(r, 900));
    if (!responseStarted) {
      const dismissed = await page.evaluate(() => {
        const action = [...document.querySelectorAll("button")].find((b) => /^(agree|close|maybe later|not now|موافق|إغلاق)$/i.test((b.textContent || "").trim()));
        if (action) { action.click(); return true; }
        return false;
      });
      if (dismissed) await new Promise((r) => setTimeout(r, 700));
      let retryBox = await page.$('textarea[name="message"]');
      if (retryBox) {
        const current = await page.evaluate(() => document.querySelector('textarea[name="message"]')?.value || "");
        if (!current.trim()) {
          await retryBox.click();
          await page.evaluate((text) => { const ta = document.querySelector('textarea[name="message"]'); const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set; if (ta && set) { set.call(ta, text); ta.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text })); } }, prompt);
        }
        const sent = await page.evaluate(() => {
          const send = document.querySelector('button[aria-label="Send message"], button[aria-label*="send" i]');
          if (send && !send.disabled) { send.click(); return true; }
          return false;
        });
        if (!sent) await page.keyboard.press("Enter");
      }
    }
    let captured;
    try { captured = await responsePromise; }
    catch (e) {
      const diag = await page.evaluate(() => {
        const send = document.querySelector('button[aria-label="Send message"]');
        return {
          path: location.pathname,
          authenticated: !![...document.querySelectorAll("button")].find((b) => /@/.test((b.textContent || "").trim())),
          textarea: !!document.querySelector('textarea[name="message"]'),
          valueLength: (document.querySelector('textarea[name="message"]') || {}).value?.length || 0,
          sendPresent: !!send,
          sendDisabled: !!send?.disabled,
          dialogCount: document.querySelectorAll('[role="dialog"]').length,
        };
      });
      console.log("arena browser diagnostic:", JSON.stringify(diag));
      await kvPut(env, "arena_browser_last_diagnostic", { at: Date.now(), ...diag });
      if (!diag.authenticated && diag.dialogCount > 0 && diag.valueLength > 0) {
        await kvPut(env, "arena_skip_until", 0);
        return "🔐 جلسة Arena انتهت وفتحت نافذة تسجيل الدخول بدل إرسال الرسالة. اكتب /arena connect بتيليجرام، افتح الرابط من Safari وسوّي خطوات الربط مرة واحدة، وبعدها ابعت سؤالك مباشرة.";
      }
      throw e;
    }
    const raw = captured?.body || "";
    const shape = arenaStreamShape(raw);
    await kvPut(env, "arena_stream_shape", { at: Date.now(), status: captured?.status || 0, path: captured?.path || "", streamShape: shape });
    const text = parseArenaDataStream(raw);
    try { await kvPut(env, "arena_browser_cookies", await page.cookies()); } catch {}
    if (!text) throw new Error("Arena browser returned an empty stream");
    await arenaMarkUp(env);
    await kvPut(env, "arena_browser_last_ok", { at: Date.now(), chars: text.length });
    return text;
  } catch (e) {
    const message = String(e && e.message ? e.message : e);
    console.log("arena browser error:", message);
    await kvPut(env, "arena_browser_last_error", { at: Date.now(), error: message.slice(0, 300) });
    await arenaMarkDown(env, 60000);
    if (/DAILY_BROWSER_LIMIT|ALL_BROWSER_FREE_TIERS_EXHAUSTED|Browser time limit exceeded/i.test(message)) return "__ARENA_RETRY_DAILY__";
    if (/429|rate limit|Unable to create new browser/i.test(message)) return "__ARENA_RETRY_429__";
    return null;
  } finally { await releaseArenaBrowser(browser); }
}

function arenaBridgeHeaders(cfg) {
  // ngrok-skip-browser-warning: يمنع صفحة التحذير تبع ngrok المجاني من اعتراض الردود
  const headers = { "content-type": "application/json", "ngrok-skip-browser-warning": "1" };
  if (cfg.key) headers.authorization = "Bearer " + cfg.key;
  return headers;
}

async function arenaIsOn(env) {
  const cfg = await arenaCfg(env);
  if (!cfg.enabled) return false;
  const flag = await kvGet(env, "arena_enabled", true);
  return flag !== false;
}

async function arenaCurrentModel(env) {
  const runtime = await kvGet(env, "arena_model", null);
  const m = String(runtime || (env && env.ARENA_BRIDGE_MODEL) || "auto").trim();
  return m || "auto";
}

const arenaFlagOn = (v) => /^(1|true|yes|on)$/i.test(String(v || ""));

async function arenaBridgeAttempt(cfg, model, convo, system, env) {
  const timeout = Number(env.ARENA_BRIDGE_TIMEOUT_MS || 45000);
  const res = await fetch(cfg.url, {
    method: "POST",
    headers: arenaBridgeHeaders(cfg),
    body: JSON.stringify({
      model,
      messages: [{ role: "system", content: system }, ...convo.map((m) => ({ role: m.role, content: String(m.content) }))],
      temperature: 0.4,
      max_tokens: 400,
      stream: false,
    }),
    signal: AbortSignal.timeout(Number.isFinite(timeout) && timeout > 0 ? timeout : 45000),
  });
  if (!res.ok) throw new Error("HTTP " + res.status);
  const data = await res.json();
  const text = data?.choices?.[0]?.message?.content?.trim();
  if (!text) throw new Error("رد فارغ");
  return text;
}

/**
 * هل Arena هو المحرك الأساسي لجارفس؟
 * الترتيب: KV (من أمر /arena primary) ← ثم ARENA_BRIDGE_FIRST ← ثم الافتراضي: نعم.
 * يعني بمجرد ضبط ARENA_BRIDGE_URL، Arena يصير الأساس وباقي المزودين احتياط.
 */
async function arenaIsPrimary(env) {
  if (!(await arenaCfg(env)).enabled) return false;
  const kv = await kvGet(env, "arena_primary", null);
  if (kv === true || kv === false) return kv;
  const raw = env.ARENA_BRIDGE_FIRST;
  if (raw == null || String(raw).trim() === "") return true;
  return !/^(0|false|no|off)$/i.test(String(raw).trim());
}

/**
 * Keep-alive: افتراضياً يشتغل تلقائياً إذا العنوان من منصة مجانية بتنوّم
 * (hf.space / onrender.com / fly.dev)، ويمكن فرضه أو إطفاؤه بالمتغير.
 */
function arenaKeepAliveOn(env, base) {
  const raw = env.ARENA_BRIDGE_KEEPALIVE;
  if (raw != null && String(raw).trim() !== "") return arenaFlagOn(raw);
  const url = String(base || (env && env.ARENA_BRIDGE_URL) || "");
  return /hf\.space|onrender\.com|fly\.dev|koyeb\.app/i.test(url);
}

/** قاطع الدائرة: بعد فشل متكرر نتجاهل الجسر مدة قصيرة حتى لا يتأخر كل رد. */
async function arenaInCooldown(env) {
  const until = Number(await kvGet(env, "arena_skip_until", 0)) || 0;
  return until > Date.now();
}

async function arenaMarkDown(env, msOverride) {
  const ms = Math.max(15000, Number(msOverride || env.ARENA_BRIDGE_COOLDOWN_MS || 300000));
  await kvPut(env, "arena_skip_until", Date.now() + ms);
}

async function arenaMarkUp(env) {
  await kvPut(env, "arena_skip_until", 0);
}

async function callArenaBridge(convo, system, env, modelOverride) {
  const cfg = await arenaCfg(env);
  if (!cfg.enabled) return null;
  if (!cfg.base && cfg.browser) return await callArenaBrowser(convo, system, env);
  try {
    if (!(await arenaIsOn(env))) return null;
    if (await arenaInCooldown(env)) return null;
    const model = String(modelOverride || (await arenaCurrentModel(env)) || "auto").trim() || "auto";
    try {
      const text = await arenaBridgeAttempt(cfg, model, convo, system, env);
      await arenaMarkUp(env);
      return text;
    } catch (e) {
      console.log("arena bridge attempt failed:", e && e.message ? e.message : e);
      // الاستضافات المجانية (Render/HF/…) بتنوّم عند الخمول — نصحّيها ونعيد مرة وحدة
      if (arenaFlagOn(env.ARENA_BRIDGE_WAKE == null ? "true" : env.ARENA_BRIDGE_WAKE)) {
        const woke = await arenaWake(env, 3, Number(env.ARENA_BRIDGE_WAKE_GAP_MS || 5000));
        if (woke) {
          try {
            const text = await arenaBridgeAttempt(cfg, model, convo, system, env);
            await arenaMarkUp(env);
            return text;
          } catch (e2) {
            console.log("arena bridge retry failed:", e2 && e2.message ? e2.message : e2);
          }
        }
      }
      // فشل نهائي — افتح القاطع مؤقتاً وكمّل على الاحتياط.
      // الخدمة ميتة؟ كولداون كامل. الخدمة حية بس الرد فشل (كوكيز/حصة)؟ كولداون قصير.
      const h = await arenaBridgeHealth(env);
      await arenaMarkDown(env, h.ok ? 60000 : undefined);
      return null;
    }
  } catch (e) { console.log("arena bridge error:", e && e.message ? e.message : e); return null; }
}

/**
 * يصحّي خدمة الجسر (تنفع للاستضافات المجانية اللي بتنام عند الخمول).
 * يرجّع true إذا صار /health سليم.
 */
async function arenaWake(env, attempts = 5, gapMs = 5000) {
  const cfg = await arenaCfg(env);
  if (!cfg.enabled) return false;
  const tries = Math.max(1, Math.min(10, Number(attempts) || 5));
  const gap = Math.max(0, Math.min(30000, Number(gapMs) || 0));
  for (let i = 0; i < tries; i++) {
    const h = await arenaBridgeHealth(env);
    if (h.ok) return true;
    if (i < tries - 1 && gap > 0) await new Promise((r) => setTimeout(r, gap));
  }
  return false;
}

async function arenaBridgeHealth(env) {
  const cfg = await arenaCfg(env);
  if (!cfg.enabled) return { ok: false, reason: "لا يوجد جسر ولا Browser Rendering" };
  if (!cfg.base && cfg.browser) {
    const ok = await kvGet(env, "arena_browser_last_ok", null);
    const err = await kvGet(env, "arena_browser_last_error", null);
    return { ok: true, data: { engine: "cloudflare-browser-rendering", ready: true, last_ok: ok, last_error: err } };
  }
  try {
    const res = await fetch(cfg.base + "/health", {
      method: "GET",
      headers: arenaBridgeHeaders(cfg),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return { ok: false, reason: "HTTP " + res.status };
    const data = await res.json().catch(() => ({}));
    return { ok: true, data };
  } catch (e) { return { ok: false, reason: e && e.message ? e.message : String(e) }; }
}

async function arenaBridgeModels(env) {
  const cfg = await arenaCfg(env);
  if (!cfg.enabled) return [];
  try {
    const res = await fetch(cfg.base + "/v1/models", {
      method: "GET",
      headers: arenaBridgeHeaders(cfg),
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) return [];
    const data = await res.json().catch(() => ({}));
    return (Array.isArray(data?.data) ? data.data : []).map((m) => String(m && m.id ? m.id : m)).filter(Boolean);
  } catch (e) { console.log("arena models error:", e && e.message ? e.message : e); return []; }
}

/**
 * تشخيص عميق: يسأل الجسر عن حالة محركاته (LMArenaBridge / gpt4free / compat).
 * يرجّع null لو الجسر ما يدعم /arena/selftest (نسخة قديمة) حتى نرجع لفحص /health.
 */
async function arenaSelftest(env, deep) {
  const cfg = await arenaCfg(env);
  if (!cfg.enabled) return null;
  if (!cfg.base && cfg.browser) {
    const answer = deep ? await callArenaBrowser([{ role: "user", content: "رد بكلمة OK فقط" }], "اختبار اتصال قصير", env) : null;
    return { ok: deep ? !!answer : true, engines: [{ name: "cloudflare-browser-rendering", ready: true, ok: deep ? !!answer : true, ms: 0, sample: answer ? answer.slice(0, 80) : "Chromium binding ready", error: answer || !deep ? "" : "Arena لم يرجع جواباً" }] };
  }
  try {
    const url = cfg.base + "/arena/selftest" + (deep ? "?deep=1" : "");
    const res = await fetch(url, {
      method: "GET",
      headers: arenaBridgeHeaders(cfg),
      signal: AbortSignal.timeout(deep ? 150000 : 20000),
    });
    if (!res.ok) return null;
    const data = await res.json().catch(() => null);
    if (!data || !Array.isArray(data.engines)) return null;
    return data;
  } catch (e) { console.log("arena selftest error:", e && e.message ? e.message : e); return null; }
}

async function llmComplete(convo, system, env) {
  // Arena هو الأساس افتراضياً (بمجرد ضبط ARENA_BRIDGE_URL). باقي المزودين احتياط،
  // فإذا الجسر نايم/فشل، رد جارفس ما يتوقف — بس ما بيوصل من Arena.
  if (await arenaIsPrimary(env)) {
    const arena = await callArenaBridge(convo, system, env);
    if (arena) return arena;
    // وضع Arena-only يمنع تبديل العقل بصمت. خدمات الصوت/التفريغ أدوات مستقلة وليست عقل الرد.
    if (/^(1|true|yes|on)$/i.test(String(env.ARENA_ONLY || ""))) return null;
  }
  return (
    (await callGemini(convo, system, env)) ||
    (await callOpenAICompatible("https://api.mistral.ai/v1", env.MISTRAL_API_KEY, (env.MISTRAL_MODEL || "mistral-large-latest").trim(), convo, system)) ||
    (await callOpenAICompatible("https://api.groq.com/openai/v1", env.GROQ_API_KEY, (env.GROQ_MODEL || "llama-3.3-70b-versatile").trim(), convo, system)) ||
    (await callOpenAICompatible("https://integrate.api.nvidia.com/v1", env.NVIDIA_API_KEY, (env.NVIDIA_MODEL || "meta/llama-3.3-70b-instruct").trim(), convo, system)) ||
    (await callOpenRouterWithFallback(convo, system, env)) ||
    (await callArenaBridge(convo, system, env)) ||
    (await callWorkersAI(convo, system, env)) ||
    (await callPollinations(convo, system, env)) ||
    null
  );
}

/* -------------------------------- Tools ------------------------------- */

async function searchWeb(query, env) {
  const q = String(query || "").slice(0, 200);
  if (!q) return "query فارغ";
  try {
    if (env.TAVILY_API_KEY) {
      const res = await fetch("https://api.tavily.com/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ api_key: env.TAVILY_API_KEY, query: q, max_results: 5 }),
        signal: AbortSignal.timeout(15000),
      });
      if (res.ok) {
        const d = await res.json();
        const items = (d.results || []).slice(0, 5);
        if (items.length) return items.map((r, idx) => `${idx + 1}. ${r.title}\n${r.url}\n${String(r.content || "").slice(0, 280)}`).join("\n\n");
      }
    }
  } catch (e) { console.log("tavily error:", e && e.message ? e.message : e); }
  try {
    const res = await fetch(`https://html.duckduckgo.com/html/?q=${encodeURIComponent(q)}`, { headers: { "user-agent": "Mozilla/5.0 (JARVIS-CF)" }, signal: AbortSignal.timeout(15000) });
    const html = await res.text();
    const out = [];
    const re = /<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g;
    let m;
    while ((m = re.exec(html)) && out.length < 5) {
      const title = decodeEntities(m[2].replace(/<[^>]+>/g, "").trim());
      let href = decodeEntities(m[1]);
      if (href.includes("uddg=")) { try { href = decodeURIComponent(new URL(href, "https://duckduckgo.com").searchParams.get("uddg") || href); } catch {} }
      out.push(`${out.length + 1}. ${title}\n${href}`);
    }
    return out.length ? out.join("\n\n") : "لا توجد نتائج.";
  } catch (e) {
    return "تعذر البحث: " + (e && e.message ? e.message : e);
  }
}

function decodeEntities(s) {
  return String(s).replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&#39;/g, "'");
}

function countMatches(html, re) { const m = html.match(re); return m ? m.length : 0; }

async function auditWebsite(rawUrl) {
  let url = String(rawUrl || "").trim();
  if (!url) return "url فارغ";
  if (!/^https?:\/\//i.test(url)) url = "https://" + url;
  let res;
  try {
    res = await fetch(url, { headers: { "user-agent": "Mozilla/5.0 (JARVIS-CF audit)" }, redirect: "follow", signal: AbortSignal.timeout(15000) });
  } catch (e) {
    return `تعذر فتح ${url}: ${e && e.message ? e.message : e}`;
  }
  const html = (await res.text()).slice(0, 400000);
  const title = (html.match(/<title[^>]*>([^<]*)<\/title>/i) || [])[1]?.trim() || "";
  const deadHash = countMatches(html, /href\s*=\s*["']#["']/gi);
  const waLinks = html.match(/https?:\/\/wa\.me\/[^"'\s<>]+/gi) || [];
  const badWa = waLinks.filter((l) => /wa\.me\/(\+|00)/.test(l) || /wa\.me\/[^"'\s<>]*[+%\s]/.test(l));
  const telLinks = countMatches(html, /href\s*=\s*["']tel:/gi);
  const forms = countMatches(html, /<form[\s>]/gi);
  const hasViewport = /<meta[^>]+name=["']viewport["']/i.test(html);
  const rtl = /dir\s*=\s*["']rtl["']/i.test(html);
  const langAr = /lang\s*=\s*["']ar["']/i.test(html);
  const bytes = html.length;
  const lines = [
    `تدقيق سريع لـ ${url}`,
    `الحالة: HTTP ${res.status}`,
    title ? `العنوان: ${title.slice(0, 120)}` : `العنوان: مفقود!`,
    `روابط href="#" المعطلة: ${deadHash}`,
    `روابط واتساب wa.me: ${waLinks.length}${badWa.length ? ` — منها ${badWa.length} خاطئة الصيغة` : " (الكل سليم الصيغة)"}`,
    `روابط tel: ${telLinks} | نماذج <form>: ${forms}`,
    `meta viewport: ${hasViewport ? "موجود" : "مفقود"} | دعم RTL/العربية: ${rtl || langAr ? "نعم" : "لا"}`,
    `حجم الصفحة التقريبي: ${Math.round(bytes / 1024)} KB`,
  ];
  if (badWa.length) lines.push("أمثلة خاطئة: " + badWa.slice(0, 3).join(" | "));
  return lines.join("\n");
}

async function leadsOverlay(env) { return kvGet(env, "leads_overlay", {}); }

async function mergedLeads(env) {
  const overlay = await leadsOverlay(env);
  return LEADS.map((l) => ({ ...l, status: overlay[l.i]?.status || "جديد", note: overlay[l.i]?.note || "" }));
}

async function listLeads(env, statusFilter) {
  const merged = await mergedLeads(env);
  const f = String(statusFilter || "").trim();
  const rows = f ? merged.filter((l) => (l.status || "").includes(f)) : merged;
  if (!rows.length) return "ماكو عملاء بهذه الحالة.";
  return rows.map((l) => `#${l.i} [${l.pri}] ${l.company}\n   الحالة: ${l.status || "جديد"}${l.note ? ` | ملاحظة: ${l.note}` : ""}\n   القطاع: ${l.sector}`).join("\n");
}

function getLeadText(merged, index) {
  const idx = Number(index);
  const l = merged.find((x) => x.i === idx);
  if (!l) return `رقم غير صالح — اختر 1 إلى ${LEADS.length}`;
  return [
    `#${l.i} [${l.pri}] ${l.company}`,
    `القطاع: ${l.sector}`,
    `الصفقة: ${l.deal}`,
    `الموقع: ${l.website}`,
    `واتساب: ${l.wa} | الهاتف: ${l.phone}`,
    `العيوب المرصودة: ${l.issues}`,
    `العرض المقترح: ${l.offer}`,
    `السعر المقترح: ${l.price}`,
    `الحالة: ${l.status || "جديد"}${l.note ? ` | ملاحظة: ${l.note}` : ""}`,
  ].join("\n");
}

async function updateLead(env, index, status, note) {
  const idx = Number(index);
  if (!LEADS.find((x) => x.i === idx)) return `رقم غير صالح — اختر 1 إلى ${LEADS.length}`;
  const overlay = await leadsOverlay(env);
  overlay[idx] = { status: String(status || "محدّثة").slice(0, 60), note: String(note || "").slice(0, 300), updated: Date.now() };
  await kvPut(env, "leads_overlay", overlay);
  const l = LEADS.find((x) => x.i === idx);
  return `تم تحديث «${l.company}» — الحالة: ${overlay[idx].status}${overlay[idx].note ? ` | ملاحظة: ${overlay[idx].note}` : ""}`;
}

async function callMeNow(env, message) {
  const user = (env.CALLMEBOT_TELEGRAM_USER || "").trim();
  if (!user) return "CallMeBot غير مفعّل — أضف CALLMEBOT_TELEGRAM_USER (اسم مستخدمك بالتيليجرام بدون @ أو رقمك بالصيغة الدولية).";
  const url = `https://api.callmebot.com/start.php?user=${encodeURIComponent(user)}&text=${encodeURIComponent(String(message || "جارفس يحتاج قرارك").slice(0, 250))}`;
  let res, body = "";
  try {
    res = await fetch(url, { signal: AbortSignal.timeout(15000) });
    body = (await res.text().catch(() => "")).trim().slice(0, 300);
  } catch (e) {
    return "تعذر الوصول إلى CallMeBot: " + (e && e.message ? e.message : e) + "\nجرّب مرة ثانية بعد دقيقة.";
  }
  console.log("callmebot HTTP", res.status, body);
  const looksFailed = !res.ok || /error|invalid|not\s*authorized|unauthorized|start|denied|fail/i.test(body);
  if (looksFailed) {
    return [
      `❌ CallMeBot ما طلع لك رنّة (HTTP ${res.status}${body ? " — " + body.slice(0, 140) : ""}).`,
      "",
      "السبب المعتاد: ما ضغطت Start عند @CallMeBot_txtbot أو المعرف غلط:",
      "1) افتح تيليجرام ← @CallMeBot_txtbot ← اضغط Start (رسالة واحدة)",
      "2) تأكد أن CALLMEBOT_TELEGRAM_USER = اسم مستخدمك بالضبط (بدون @) أو رقمك بمفتاح الدولة مثل +9639…",
      "3) جرّب: /call اختبار",
    ].join("\n");
  }
  return "📞 رنّة طلعت لك عبر CallMeBot — افتح تيليجرام.\n(ملاحظة: CallMeBot خدمة خارجية غير مضمونة؛ إذا ما وصلت، الضغط على Start عند @CallMeBot_txtbot هو الحل 90% من المرات.)";
}

function parseToolCall(out) {
  if (!out) return null;
  const at = out.indexOf("TOOL_CALL:");
  if (at === -1) return null;
  const rest = out.slice(at + "TOOL_CALL:".length);
  const start = rest.indexOf("{");
  const end = rest.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) return null;
  try {
    const parsed = JSON.parse(rest.slice(start, end + 1));
    if (parsed && parsed.tool) return { tool: String(parsed.tool), args: parsed.args || {} };
  } catch {}
  return null;
}

/** يفتح أي رابط ويستخرج نصاً مقروءاً — يخدم "أي مهمة تحتاج إنترنت". */
async function openUrl(url) {
  const raw = String(url || "").trim();
  if (!/^https?:\/\//i.test(raw)) return "لازم رابط كامل يبدأ بـ http:// أو https://";
  try {
    const res = await fetch(raw, {
      headers: { "user-agent": "Mozilla/5.0 (compatible; JarvisBot/1.0)", accept: "text/html,text/plain,*/*" },
      signal: AbortSignal.timeout(20000),
      redirect: "follow",
    });
    if (!res.ok) return `تعذر فتح الرابط (HTTP ${res.status})`;
    const ct = String(res.headers.get("content-type") || "");
    const body = await res.text();
    if (!/html/i.test(ct)) return body.slice(0, 3500) || "الصفحة فاضية";
    const text = body
      .replace(/<script[\s\S]*?<\/script>/gi, " ")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<noscript[\s\S]*?<\/noscript>/gi, " ")
      .replace(/<[^>]+>/g, " ")
      .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
      .replace(/\s+/g, " ")
      .trim();
    const title = (body.match(/<title[^>]*>([\s\S]*?)<\/title>/i) || [])[1];
    const head = title ? `العنوان: ${title.replace(/<[^>]+>/g, "").trim()}\n\n` : "";
    return (head + text).slice(0, 3500) || "ما لقيت نص بالصفحة (غالباً JS أو محتوى محمي)";
  } catch (e) {
    return "خطأ بفتح الرابط: " + (e && e.message ? e.message : e);
  }
}

/** سؤال مباشر لنماذج Arena — يتجاوز سلسلة الـ failover. */
async function arenaAskDirect(prompt, model, env) {
  const p = String(prompt || "").trim();
  if (!p) return "prompt فارغ";
  if (!(await arenaCfg(env)).enabled) return "جسر Arena مو مضبوط (ARENA_BRIDGE_URL).";
  const out = await callArenaBridge(
    [{ role: "user", content: p }],
    "أنت جارفس — رد بالعربي الشامي، موجز ومفيد.",
    env,
    model || undefined
  );
  return out || "جسر Arena ما رد — جرّب /arena test";
}

async function runTool(call, env, ctx) {
  try {
    const a = call.args || {};
    switch (call.tool) {
      case "search_web": return await searchWeb(a.query, env);
      case "open_url": return await openUrl(a.url);
      case "arena_chat": return await arenaAskDirect(a.prompt, a.model, env);
      case "audit_website": return await auditWebsite(a.url);
      case "list_leads": return await listLeads(env, a.status);
      case "get_lead": { const m = await mergedLeads(env); return getLeadText(m, a.index); }
      case "update_lead": return await updateLead(env, a.index, a.status, a.note);
      case "start_background_task": return await startBackgroundTask(a.goal, env, ctx);
      case "call_me_now": return await callMeNow(env, a.message);
      case "remember": { const r = await addMemories(env, [String(a.fact || "")], true); return r.length ? "حُفظت: " + r[0] : "ما حفظت شيئاً."; }
      case "recall_memory": return await recallMemories(env, a.query);
      case "forget_memory": return await forgetMemories(env, a.query);
      case "send_email": return await sendEmailCard(env, a.to, a.subject, a.body);
      default: return "أداة غير معروفة: " + call.tool;
    }
  } catch (e) {
    return "خطأ في الأداة: " + (e && e.message ? e.message : e);
  }
}

const STEPS_PER_TICK = 3;   // أقصى خطوات بالدقيقة الواحدة
const MAX_TASK_STEPS = 60;  // سقف صلب لمهمة واحدة (~ ساعات)

async function getOwnerChatId(env) {
  const kv = await kvGet(env, "owner_chat_id", null);
  if (kv) return kv;
  return env.OWNER_CHAT_ID ? Number(env.OWNER_CHAT_ID) : null;
}

async function queueApprovedTask(env, goal, ctx, meta) {
  const g = String(goal || "").trim().slice(0, 6000);
  const tasks = await kvGet(env, "tasks", []);
  const id = "task_" + Date.now();
  const threadId = await kvGet(env, ACTIVE_THREAD_KEY, "");
  const m = meta || {};
  tasks.unshift({ id, goal: g, threadId, route: m.route || "agent", agentId: m.agentId || null, agentName: m.agentName || null, status: "queued", phase: "queued", progress: 0, trace: [], stepCount: 0, created: Date.now(), updated: Date.now(), lockedAt: 0, consecutiveFailures: 0 });
  await kvPut(env, "tasks", tasks.slice(0, 30));
  if (ctx && typeof ctx.waitUntil === "function") ctx.waitUntil(processTaskQueue(env, STEPS_PER_TICK));
  return id;
}

async function startBackgroundTask(goal, env, ctx) {
  const g = String(goal || "").trim().slice(0, 500);
  if (!g) return "هدف المهمة فارغ";
  const owner = await getOwnerChatId(env);
  if (!owner) return "ما أعرف محادثتك — أرسل /start أولاً.";
  const id = "ap_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const approvals = await kvGet(env, "approvals", []);
  approvals.unshift({ id, type: "task", payload: { goal: g }, created: Date.now() });
  await kvPut(env, "approvals", approvals.slice(0, 30));
  const kb = { inline_keyboard: [[
    { text: "✅ ابدأ المهمة", callback_data: "approve:" + id },
    { text: "❌ لا تبدأ", callback_data: "cancel:" + id },
  ]] };
  await tgApi(env, "sendMessage", { chat_id: owner, text: `🧠 جارفس يبغي يبدأ مهمة بالخلفية:\n\n«${g}»\n\nموافق تبدأ؟`, reply_markup: kb });
  return "بانتظار موافقة المالك على بدء المهمة — ما رح تبدأ بدون ضغطته ✅ على البطاقة.";
}

function buildTaskPrompt(task) {
  const trace = (task.trace || []).map((t) => `الخطوة ${t.step} — ${t.tool}(${JSON.stringify(t.args).slice(0, 150)}) \nالنتيجة: ${String(t.result).slice(0, 900)}`).join("\n\n").slice(-6000);
  return `الهدف: ${task.goal}\n\nما أُنجز حتى الآن (${task.stepCount || 0} خطوة):\n${trace || "(لا شيء بعد — هذه أول خطوة)"}\n\nنفّذ الخطوة التالية الآن. لو اكتملت المهمة كلها اكتب التقرير النهائي كاملاً (بدون أي TOOL_CALL).`;
}

async function finishTask(task, tasks, env, status, note) {
  task.status = status;
  task.result = String(note || "").slice(0, 3000);
  task.finished = Date.now();
  task.lockedAt = 0;
  const idx = tasks.findIndex((t) => t.id === task.id);
  if (idx !== -1) tasks[idx] = { ...task };
  await kvPut(env, "tasks", tasks);
  const owner = await getOwnerChatId(env);
  if (owner) {
    const icon = status === "done" ? "✅" : "⚠️";
    await sendMessage(env, owner, `${icon} المهمة ${task.id} ${status === "done" ? "اكتملت" : "توقفت"} (${task.stepCount || 0} خطوة):\n\n${task.result}`);
  }
  await callMeNow(env, `جارفس: مهمتك ${status === "done" ? "خلصت" : "توقفت"} — افتح التيليجرام`);
}

async function proactiveTaskReview(env) {
  const tasks = await kvGet(env, "tasks", []);
  const now = Date.now(); let changed = false;
  const owner = await getOwnerChatId(env);
  for (const task of tasks) {
    if (!["queued", "running"].includes(task.status)) continue;
    const quiet = now - (task.updated || task.created || now);
    // لا نزعج المستخدم كل دقيقة: تنبيه استباقي واحد إذا علقت المهمة فعلاً.
    if (quiet > 12 * 60000 && (!task.proactiveAlertAt || now - task.proactiveAlertAt > 60 * 60000)) {
      task.proactiveAlertAt = now; changed = true;
      if (owner) await sendMessage(env, owner, `⚠️ انتبهت إن المهمة معلّقة وما عم تتقدم:\n${String(task.goal).slice(0, 180)}\n\nآخر مرحلة: ${task.phase || task.status}\nرح ضل راقبها وأعيد المحاولة تلقائياً. إذا بدك غيّر الأولوية خبرني.`);
    }
  }
  if (changed) await kvPut(env, "tasks", tasks);
}

async function processTaskQueue(env, maxSteps) {
  let tasks = await kvGet(env, "tasks", []);
  const now = Date.now();
  const task = tasks.find((t) => (t.status === "queued" || t.status === "running"));
  if (!task) return;
  // قفل بسيط حتى ما تشتغل خطوتين بنفس اللحظة بين الكرون المباشر واللحظة
  if (task.lockedAt && now - task.lockedAt < 45 * 1000) return;
  task.lockedAt = now;
  task.status = "running";
  task.updated = now;
  // خزّن القفل قبل التنفيذ
  const li = tasks.findIndex((t) => t.id === task.id);
  if (li !== -1) tasks[li] = { ...task };
  await kvPut(env, "tasks", tasks);

  const budget = Math.max(0, Math.min(maxSteps || STEPS_PER_TICK, MAX_TASK_STEPS - (task.stepCount || 0)));
  if (budget === 0) { await finishTask(task, tasks, env, "done", (task.trace && task.trace.length ? String(task.trace[task.trace.length - 1].result) : "") + "\n\n(بلغت الحد الأقصى للخطوات — ها هي أفضل النتائج المتاحة)"); return; }

  for (let i = 0; i < budget; i++) {
    const convo = [{ role: "user", content: buildTaskPrompt(task) }];
    const out = await llmComplete(convo, WORKER_PROMPT, env);
    if (out === "__ARENA_RETRY_429__" || out === "__ARENA_RETRY_DAILY__") {
      task.lockedAt = 0; task.phase = "waiting_for_browser"; task.updated = Date.now();
      const idxR = tasks.findIndex((t) => t.id === task.id); if (idxR !== -1) tasks[idxR] = { ...task };
      await kvPut(env, "tasks", tasks); return;
    }
    task.stepCount = (task.stepCount || 0) + 1;
    if (!out) {
      task.consecutiveFailures = (task.consecutiveFailures || 0) + 1;
      const idxF = tasks.findIndex((t) => t.id === task.id);
      if (idxF !== -1) tasks[idxF] = { ...task };
      await kvPut(env, "tasks", tasks);
      if (task.consecutiveFailures >= 3) {
        await finishTask(task, tasks, env, "failed", "الذكاء رجع فارغ ٣ مرات متتالية — أوقفت المهمة عشان ما تحرق الحصة ببلا لزوم. شيك على المفاتيح ثم اطلبها من جديد.");
      }
      return;
    }
    task.consecutiveFailures = 0;
    const call = parseToolCall(out);
    if (!call) { await finishTask(task, tasks, env, "done", out); return; }
    const result = await runTool(call, env, null);
    task.trace = (task.trace || []).concat([{ step: task.stepCount, tool: call.tool, args: call.args, result: String(result).slice(0, 1200), at: Date.now() }]).slice(-40);
    task.phase = call.tool || "working";
    task.progress = Math.min(95, Math.max(task.progress || 0, 10 + task.stepCount * 7));
    task.updated = Date.now();
    if (!task.lastProgressAt || Date.now() - task.lastProgressAt > 2 * 60000) {
      task.lastProgressAt = Date.now();
      const owner = await getOwnerChatId(env);
      if (owner) await sendMessage(env, owner, `⏳ ${task.agentName ? task.agentName + " · " : ""}${String(task.goal).slice(0, 100)}\nالتقدم: ${task.progress}% · المرحلة: ${task.phase}\nآخر نتيجة: ${String(result).slice(0, 350)}`);
    }
    const idx2 = tasks.findIndex((t) => t.id === task.id);
    if (idx2 !== -1) tasks[idx2] = { ...task };
    await kvPut(env, "tasks", tasks);
  }
  // لم تنته بعد — تُكمل في الكرون القادم
}

async function agentLoop(userText, env, chatId, opts) {
  const o = opts || {};
  const memBlock = o.mode === "worker" ? "" : await relevantMemories(env, userText);
  const resolved = o.mode === "worker" ? null : await resolveThread(env, userText, o.threadId);
  const threadBlock = resolved ? `\n\nسياق مساحة العمل الحالية:\n- الاسم: ${resolved.thread.title}\n- المعرف: ${resolved.thread.id}\n- سبب اختيارها: ${resolved.reason}\n- الملخص السابق: ${resolved.thread.summary || "أول رسالة"}\nالتزم بهذه المهمة فقط ولا تخلطها بمشروع آخر.` : "";
  const system = o.mode === "worker" ? WORKER_PROMPT : (BASE_PROMPT + (memBlock ? "\n\n" + memBlock : "") + threadBlock);
  const hist = o.mode === "worker" ? [] : (resolved.thread.messages || []);
  const convo = [...hist, { role: "user", content: String(userText) }];
  for (let step = 0; step < MAX_TOOL_STEPS; step++) {
    const out = await llmComplete(convo, system, env);
    if (!out) return "صار انقطاع مؤقت بين جارفس وArena قبل ما يكتمل الرد. حفظت رسالتك وسياقها؛ جرّب ابعتها مرة ثانية بعد لحظات. ما في داعي لأي مفتاح جديد.";
    if (out === "__ARENA_RETRY_429__" || out === "__ARENA_RETRY_DAILY__") return out;
    const call = parseToolCall(out);
    if (!call) {
      if (o.mode !== "worker") await saveThreadTurn(env, resolved, [...convo, { role: "assistant", content: out }]);
      return out;
    }
    const result = await runTool(call, env, o.ctx || null);
    convo.push({ role: "assistant", content: out });
    convo.push({ role: "user", content: "TOOL_RESULT: " + String(result).slice(0, 3500) });
  }
  const finalOut = await llmComplete([...convo, { role: "user", content: "أعطني الجواب النهائي الآن فقط بدون أدوات." }], system, env);
  const answer = finalOut || "اكتملت الخطوات — راجع النتائج أعلاه.";
  if (o.mode !== "worker") await saveThreadTurn(env, resolved, [...convo, { role: "assistant", content: answer }]);
  return answer;
}

/* ------------------------- Voice input (optional) ------------------------ */

function arrayBufferToBase64(buf) {
  const bytes = new Uint8Array(buf);
  let bin = "";
  const CHUNK = 0x8000;
  for (let i = 0; i < bytes.length; i += CHUNK) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  return btoa(bin);
}


/* ------------------- النطق: تحويل رد جارفس إلى صوت عربي ------------------- */
/* غير رسمي عبر Google Translate TTS — مجاني، والصوت عربي عام (مو شامي مئة بالمئة).
   عند أي فشل: الرد النصي يصل دائماً — الصوت ميزة إضافية ولا يكسر شيء. */
function splitForTts(text, max) {
  const words = String(text || "").split(/\s+/);
  const chunks = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).trim().length > (max || 170)) { if (cur.trim()) chunks.push(cur.trim()); cur = w; }
    else cur += " " + w;
  }
  if (cur.trim()) chunks.push(cur.trim());
  return chunks;
}
const EDGE_TTS_TOKEN = "6A5AA1D4EAFF4E9FB37E23D68491D6F4";
const EDGE_TTS_GEC_VERSION = "1-143.0.3650.75";
const EDGE_TTS_DEFAULT_VOICE = "ar-SY-LaithNeural"; // شامي — صوت رجل (جارفس). بديل: ar-SY-AmanyNeural (أنثى)

async function edgeSecMsGec() {
  const filetime = Math.floor((Date.now() / 1000 + 11644473600) * 1e7);
  const rounded = filetime - (filetime % 3000000000);
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(String(rounded) + EDGE_TTS_TOKEN));
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("").toUpperCase();
}
function edgeEscapeXml(s) {
  return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}
function uuidNoDashes() { return crypto.randomUUID().replace(/-/g, ""); }

/* نطق شامي طبيعي عبر Edge TTS — مجاني بالكامل، بلا مفتاح وبلا بطاقة (نفس صوت "Read Aloud") */
async function edgeTtsMp3(text, voice, msTimeout) {
  const voiceName = voice || EDGE_TTS_DEFAULT_VOICE;
  const clean = String(text || "").trim().slice(0, 450);
  if (!clean) return null;
  let sec;
  try { sec = await edgeSecMsGec(); } catch (e) { console.log("edge tts gec error:", e && e.message ? e.message : e); return null; }
  const url = "wss://speech.platform.bing.com/edge/v1?TrustedClientToken=" + EDGE_TTS_TOKEN + "&Sec-MS-GEC=" + sec + "&Sec-MS-GEC-Version=" + EDGE_TTS_GEC_VERSION;
  return new Promise((resolve) => {
    let done = false;
    const chunks = [];
    let total = 0;
    let ws = null;
    const timer = setTimeout(() => finish(null), msTimeout || 25000);
    const finish = (out) => {
      if (done) return; done = true; clearTimeout(timer);
      try { if (ws) ws.close(); } catch {}
      resolve(out);
    };
    try { ws = new WebSocket(url); } catch (e) { console.log("edge tts ws ctor error:", e && e.message ? e.message : e); return finish(null); }
    try { ws.binaryType = "arraybuffer"; } catch {}
    ws.addEventListener("open", () => {
      try {
        const cfg = { context: { synthesis: { audio: { metadataoptions: { sentenceBoundaryEnabled: "false", wordBoundaryEnabled: "false" }, outputFormat: "audio-24khz-48kbitrate-mono-mp3" } } } };
        ws.send("X-Timestamp:" + new Date().toISOString() + "\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n" + JSON.stringify(cfg));
        const ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ar-SY'><voice name='" + voiceName + "'><prosody rate='+0%'>" + edgeEscapeXml(clean) + "</prosody></voice></speak>";
        ws.send("X-RequestId:" + uuidNoDashes() + "\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:" + new Date().toISOString() + "\r\nPath:ssml\r\n\r\n" + ssml);
      } catch (e) { console.log("edge tts send error:", e && e.message ? e.message : e); finish(null); }
    });
    ws.addEventListener("message", (event) => {
      try {
        const data = event.data;
        if (typeof data === "string") {
          if (data.includes("Path:turn.end")) {
            if (!total) return finish(null);
            const all = new Uint8Array(total); let off = 0;
            for (const c of chunks) { all.set(c, off); off += c.length; }
            return finish(all);
          }
          return;
        }
        const buf = data instanceof ArrayBuffer ? new Uint8Array(data) : new Uint8Array(awaitableBuffer(data));
        if (buf.length < 2) return;
        const headerLen = (buf[0] << 8) | buf[1];
        if (buf.length < 2 + headerLen) return;
        const header = new TextDecoder().decode(buf.subarray(2, 2 + headerLen));
        if (header.includes("Path:audio")) {
          const audio = buf.subarray(2 + headerLen);
          chunks.push(audio); total += audio.length;
        }
      } catch (e) { console.log("edge tts frame error:", e && e.message ? e.message : e); }
    });
    ws.addEventListener("error", (e) => { console.log("edge tts ws error:", (e && (e.message || e.type)) || "unknown"); finish(null); });
    ws.addEventListener("close", () => {
      if (done) return;
      if (total > 2000) { const all = new Uint8Array(total); let off = 0; for (const c of chunks) { all.set(c, off); off += c.length; } return finish(all); }
      finish(null);
    });
  });
}
function awaitableBuffer(data) { return data && data.buffer ? data.buffer : new ArrayBuffer(0); }

async function googleTtsMp3(chunk) {
  try {
    const q = encodeURIComponent(chunk);
    const url = "https://translate.googleapis.com/translate_tts?ie=UTF-8&client=tw-in-chrome&tl=ar&q=" + q;
    const res = await fetch(url, {
      headers: {
        "user-agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "referer": "https://translate.google.com/",
      },
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) return null;
    return new Uint8Array(await res.arrayBuffer());
  } catch (e) { console.log("google tts error:", e && e.message ? e.message : e); return null; }
}
async function ttsArabicMp3(chunk, env) {
  const voice = env && env.EDGE_TTS_VOICE ? String(env.EDGE_TTS_VOICE) : EDGE_TTS_DEFAULT_VOICE;
  const edge = await edgeTtsMp3(chunk, voice, 25000);
  if (edge && edge.length > 500) return edge;
  console.log("edge tts: فشل أو رد ناقص — رجوع إلى Google TTS");
  return googleTtsMp3(chunk);
}
async function tgSendVoice(env, chatId, mp3Bytes, name) {
  try {
    const form = new FormData();
    form.append("chat_id", String(chatId));
    form.append("voice", new Blob([mp3Bytes], { type: "audio/mpeg" }), name || "jarvis.mp3");
    const res = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendVoice`, { method: "POST", body: form });
    const d = await res.json().catch(() => ({}));
    if (res.ok && d && d.ok !== false) return true;
    console.log("sendVoice رفض — أجرب sendAudio:", res.status, JSON.stringify(d).slice(0, 200));
    const form2 = new FormData();
    form2.append("chat_id", String(chatId));
    form2.append("audio", new Blob([mp3Bytes], { type: "audio/mpeg" }), name || "jarvis.mp3");
    const res2 = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendAudio`, { method: "POST", body: form2 });
    const d2 = await res2.json().catch(() => ({}));
    return res2.ok && d2 && d2.ok !== false;
  } catch (e) { console.log("sendVoice error:", e && e.message ? e.message : e); return false; }
}
async function sendVoiceReply(env, chatId, text) {
  try {
    const clean = String(text || "").replace(/[*_`~]/g, "").replace(/https?:\/\/\S+/g, "الرابط").trim();
    const chunks = splitForTts(clean, 170).slice(0, 3);
    for (let i = 0; i < chunks.length; i++) {
      const mp3 = await ttsArabicMp3(chunks[i], env);
      if (mp3) await tgSendVoice(env, chatId, mp3, "jarvis_" + i + ".mp3");
    }
  } catch (e) { console.log("voice reply error:", e && e.message ? e.message : e); }
}

async function transcribeGroqAudio(env, buf) {
  if (!env.GROQ_API_KEY) return null;
  try {
    const fd = new FormData();
    fd.append("model", "whisper-large-v3-turbo");
    fd.append("file", new Blob([buf], { type: "audio/ogg" }), "voice.ogg");
    const res = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", { method: "POST", headers: { authorization: `Bearer ${env.GROQ_API_KEY}` }, body: fd, signal: AbortSignal.timeout(45000) });
    if (res.ok) { const d = await res.json(); if (d.text) return String(d.text).trim() || null; }
    else { console.log("groq whisper HTTP", res.status, (await res.text().catch(() => "")).slice(0, 300)); }
  } catch (e) { console.log("groq whisper error:", e && e.message ? e.message : e); }
  return null;
}

async function transcribeWorkersAIAudio(env, buf) {
  if (!env.AI) return null;
  try {
    const bytes = Array.from(new Uint8Array(buf));
    const out = await env.AI.run("@cf/openai/whisper-large-v3-turbo", { audio: bytes });
    const t = out && (out.text || (out.result && out.result.text) || (typeof out === "string" ? out : ""));
    if (t && String(t).trim()) return String(t).trim();
    console.log("workers ai whisper: رد بدون نص");
  } catch (e) { console.log("workers ai whisper error:", e && e.message ? e.message : e); }
  return null;
}

async function transcribeGeminiAudio(env, mimeType, buf) {
  if (!env.GEMINI_API_KEY) return null;
  try {
    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${env.GEMINI_API_KEY}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ contents: [{ role: "user", parts: [{ text: "فرّغ هذه الرسالة الصوتية حرفياً بلغتها الأصلية (عربي أو إنجليزي). اكتب التفريغ فقط بدون أي تعليق." }, { inlineData: { mimeType: mimeType || "audio/ogg", data: arrayBufferToBase64(buf) } }] }] }),
      signal: AbortSignal.timeout(45000),
    });
    if (res.ok) { const d = await res.json(); const t = d?.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("").trim(); if (t) return t; }
    else { console.log("gemini stt HTTP", res.status, (await res.text().catch(() => "")).slice(0, 300)); }
  } catch (e) { console.log("gemini stt error:", e && e.message ? e.message : e); }
  return null;
}

/* السلسلة كاملة: Groq (كوتا سخية) ← Workers AI (حصة يومية تتجدد كل يوم) ← Gemini (كوتا محدودة) */
async function transcribeAudioBuffer(env, mimeType, buf) {
  return (
    (await transcribeGroqAudio(env, buf)) ||
    (await transcribeWorkersAIAudio(env, buf)) ||
    (await transcribeGeminiAudio(env, mimeType || "audio/ogg", buf))
  );
}

async function transcribeVoice(env, fileId) {
  const f = await tgApi(env, "getFile", { file_id: fileId });
  const filePath = f?.data?.result?.file_path;
  if (!filePath) return null;
  let bin;
  try {
    const res = await fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_BOT_TOKEN}/${filePath}`, { signal: AbortSignal.timeout(30000) });
    bin = await res.arrayBuffer();
  } catch { return null; }
  return await transcribeAudioBuffer(env, "audio/ogg", bin);
}

/* ===== قراءة الملفات والصور (مجاني بالكامل) ===== */
const TEXT_DOC_EXT = new Set(["txt","md","markdown","csv","tsv","json","xml","html","htm","log","yaml","yml","ini","conf","env","sql","py","js","ts","css","sh"]);

function xmlDecode(s) {
  return String(s || "")
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n) || 0))
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16) || 0))
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
}

async function inflateRawBytes(bytes) {
  const ds = new DecompressionStream("deflate-raw");
  const stream = new Blob([bytes]).stream().pipeThrough(ds);
  const buf = await new Response(stream).arrayBuffer();
  return new Uint8Array(buf);
}

/* قارئ ZIP مصغّر للملفات Office (xlsx/docx) — بدون أي مكتبات */
async function readZipMap(buf) {
  const bytes = new Uint8Array(buf);
  let eocd = -1;
  const scanFrom = Math.max(0, bytes.length - 70000);
  for (let i = bytes.length - 22; i >= scanFrom; i--) {
    if (bytes[i] === 0x50 && bytes[i + 1] === 0x4b && bytes[i + 2] === 0x05 && bytes[i + 3] === 0x06) { eocd = i; break; }
  }
  if (eocd < 0) return null;
  const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const count = dv.getUint16(eocd + 10, true);
  let p = dv.getUint32(eocd + 16, true);
  const dec = new TextDecoder();
  const map = new Map();
  for (let i = 0; i < count && p + 46 <= bytes.length; i++) {
    if (!(bytes[p] === 0x50 && bytes[p + 1] === 0x4b && bytes[p + 2] === 0x01 && bytes[p + 3] === 0x02)) break;
    const method = dv.getUint16(p + 10, true);
    const compSize = dv.getUint32(p + 20, true);
    const nameLen = dv.getUint16(p + 28, true);
    const extraLen = dv.getUint16(p + 30, true);
    const commentLen = dv.getUint16(p + 32, true);
    const localOffset = dv.getUint32(p + 42, true);
    const name = dec.decode(bytes.subarray(p + 46, p + 46 + nameLen));
    if (compSize <= 5 * 1024 * 1024 && localOffset + 30 <= bytes.length && bytes[localOffset] === 0x50 && bytes[localOffset + 1] === 0x4b) {
      const lNameLen = dv.getUint16(localOffset + 26, true);
      const lExtraLen = dv.getUint16(localOffset + 28, true);
      const dataStart = localOffset + 30 + lNameLen + lExtraLen;
      const comp = bytes.slice(dataStart, dataStart + compSize);
      let content = null;
      if (method === 0) content = comp;
      else if (method === 8) { try { content = await inflateRawBytes(comp); } catch { content = null; } }
      if (content) map.set(name, content);
    }
    p += 46 + nameLen + extraLen + commentLen;
  }
  return map;
}

async function extractXlsxText(buf) {
  const entries = await readZipMap(buf); if (!entries) return null;
  const dec = new TextDecoder();
  const sharedXml = entries.get("xl/sharedStrings.xml");
  const shared = sharedXml ? [...dec.decode(sharedXml).matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((m) => xmlDecode(m[1])) : [];
  const sheetNames = {};
  const wb = entries.get("xl/workbook.xml");
  if (wb) { for (const m of dec.decode(wb).matchAll(/<sheet[^>]*name="([^"]*)"[^>]*sheetId="(\d+)"/g)) sheetNames[Number(m[2])] = xmlDecode(m[1]); }
  const sheetFiles = [...entries.keys()].filter((n) => /^xl\/worksheets\/sheet\d+\.xml$/.test(n)).sort((a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0])).slice(0, 4);
  const out = [];
  for (const sf of sheetFiles) {
    const idx = Number((sf.match(/(\d+)\.xml$/) || [])[1] || "1");
    out.push("=== ورقة: " + (sheetNames[idx] || ("sheet" + idx)) + " ===");
    const xml = dec.decode(entries.get(sf));
    let rows = 0;
    for (const rm of xml.matchAll(/<row[^>]*>([\s\S]*?)<\/row>/g)) {
      if (++rows > 150) { out.push("… (اقتطع عند 150 صفاً)"); break; }
      const cells = [];
      for (const cm of rm[1].matchAll(/<c([^>]*)>([\s\S]*?)<\/c>|<c([^>]*)\/>/g)) {
        const attrs = cm[1] || cm[3] || "";
        const inner = cm[2] || "";
        const t = (attrs.match(/t="([^"]+)"/) || [])[1];
        const vm = inner.match(/<v>([\s\S]*?)<\/v>/);
        const isM = inner.match(/<t[^>]*>([\s\S]*?)<\/t>/);
        let v = "";
        if (t === "s" && vm) v = shared[Number(vm[1])] || "";
        else if (isM) v = xmlDecode(isM[1]);
        else if (vm) v = xmlDecode(vm[1]);
        const ref = (attrs.match(/r="([A-Z]+)\d+"/) || [])[1] || "";
        cells.push((ref ? ref + ":" : "") + String(v).trim().slice(0, 60));
      }
      if (cells.length) out.push(cells.join(" | ").slice(0, 500));
    }
  }
  const text = out.join("\n").trim();
  return text ? text.slice(0, 12000) : null;
}

async function extractDocxText(buf) {
  const entries = await readZipMap(buf); if (!entries) return null;
  const doc = entries.get("word/document.xml"); if (!doc) return null;
  let xml = new TextDecoder().decode(doc);
  xml = xml.replace(/<\/w:p>/g, "\n");
  const text = xmlDecode(xml.replace(/<[^>]+>/g, "")).replace(/\n{3,}/g, "\n\n").trim();
  return text ? text.slice(0, 12000) : null;
}

async function downloadTelegramFile(env, fileId, timeoutMs) {
  const f = await tgApi(env, "getFile", { file_id: fileId });
  const filePath = f?.data?.result?.file_path;
  if (!filePath) return null;
  const res = await fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_BOT_TOKEN}/${filePath}`, { signal: AbortSignal.timeout(timeoutMs || 45000) });
  if (!res.ok) return null;
  return await res.arrayBuffer();
}

/* يرجّع { text, kind } أو { error } أو null (نوع غير مدعوم) */
async function extractDocumentText(env, fileId, filename, mime) {
  const buf = await downloadTelegramFile(env, fileId, 60000);
  if (!buf) return { error: "ما قدرت أحمّل الملف من تيليجرام (أكبر من 20MB أو مشكلة اتصال)." };
  if (buf.byteLength > 10 * 1024 * 1024) return { error: "الملف أكبر من 10 ميغابايت — قسّمه أو ابعته أصغر." };
  const ext = (String(filename || "").split(".").pop() || "").toLowerCase();
  const mimeL = String(mime || "").toLowerCase();
  if (TEXT_DOC_EXT.has(ext) || mimeL.startsWith("text/") || mimeL.includes("json") || mimeL.includes("csv") || mimeL.includes("xml")) {
    return { text: new TextDecoder().decode(buf).slice(0, 12000), kind: "text" };
  }
  if (ext === "xlsx" || ext === "xlsm" || mimeL.includes("spreadsheetml")) {
    const t = await extractXlsxText(buf);
    return t ? { text: t, kind: "xlsx" } : { error: "ما قدرت أقرأ ملف Excel (فاضي أو محمي بكلمة سر؟)." };
  }
  if (ext === "docx" || mimeL.includes("wordprocessingml")) {
    const t = await extractDocxText(buf);
    return t ? { text: t, kind: "docx" } : { error: "ما قدرت أقرأ ملف Word (فاضي أو محمي بكلمة سر؟)." };
  }
  if (ext === "pdf") return { error: "PDF لسا ما مدعوم — ابعته كصور (سكيرينشوت لكل صفحة) أو حوّله Word/نص وأنا بقراه فوراً." };
  return null;
}

/* رؤية مجانية: Workers AI (حصة يومية تتجدد) ثم Gemini كاحتياط */
async function visionDescribe(env, fileId, question, mimeType) {
  const buf = await downloadTelegramFile(env, fileId, 45000);
  if (!buf) return null;
  const prompt = question || "صف هذه الصورة باختصار مفيد باللهجة الشامية: شو فيها بالضبط، واقرأ أي نص مكتوب فيها حرفياً (OCR).";
  if (env.AI) {
    try {
      const out = await env.AI.run("@cf/meta/llama-3.2-11b-vision-instruct", { image: Array.from(new Uint8Array(buf)), prompt, max_tokens: 800 });
      const t = out && (out.response || out.description || out.text || (typeof out === "string" ? out : ""));
      if (t && String(t).trim()) return String(t).trim();
      console.log("workers ai vision: رد بدون وصف");
    } catch (e) { console.log("workers ai vision error:", e && e.message ? e.message : e); }
  }
  if (env.GEMINI_API_KEY) {
    try {
      const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${env.GEMINI_API_KEY}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ contents: [{ role: "user", parts: [{ text: prompt }, { inlineData: { mimeType: mimeType || "image/jpeg", data: arrayBufferToBase64(buf) } }] }] }),
        signal: AbortSignal.timeout(45000),
      });
      if (res.ok) { const d = await res.json(); const t = d?.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("").trim(); if (t) return t; }
      else { console.log("gemini vision HTTP", res.status, (await res.text().catch(() => "")).slice(0, 200)); }
    } catch (e) { console.log("gemini vision error:", e && e.message ? e.message : e); }
  }
  return null;
}

/* --------------------------- Command handling --------------------------- */

const WELCOME = [
  "🇦🇪 أهلاً بك في جارفس — مساعدك الخاص الفعال على مدار الساعة.",
  "",
  "أقدر أسوي لك:",
  "• بحث ويب حي وملخصات (اطلب أي موضوع)",
  "• تدقيق أي موقع (أزرار # ميتة، واتساب خاطئ، عناصر أساسية)",
  "• إدارة عملاؤك الـ12 بدبي: /leads ثم /lead 2 أو قل لي «حدّث الشركة 2 راسلته»",
  "• تشغيل مهام بالخلفية تطرشلك تقرير + رنّة: «دور على 5 شركات ديكور بالرياض وفحص مواقعهم واطرشلي»",
  "• محادثات عربية صوتية/نصية (الرسائل الصوتية أسمعها وأفهمها)",
  "• بقرا الصور (وصف + OCR) وملفاتك: txt/csv/xlsx/docx — وبعدّل جداولك وارجعيلك CSV",
  "",
  "الأوامر:",
  "/start — هذه القائمة",
  "/leads [حالة] — قائمة العملاء (جديد/راسلته/مهتم/عرض/مقفل)",
  "/lead <رقم> — تفاصيل عميل 1–12",
  "/audit <موقع> — تدقيق سريع لموقع",
  "/tasks — آخر المهام الخلفية مع عدد الخطوات",
  "/chats — كل مساحات العمل القديمة والجديدة",
  "/chat new <اسم> — افتح مشروعاً منفصلاً | /chat <رقم> — ارجع لشات قديم",
  "/progress — تقدم وسياق مساحة العمل الحالية",
  "/cancel task_ID — إلغاء مهمة جارية",
  "/learn <نص> — احفظ حقائق (كل سطر = حقيقة، ابدأ بـ ! للتثبيت الدائم)",
  "/memories — كل اللي كنت تعلمته",
  "/forget <الرقم أو المعرف> — امسح حقيقة",
  "/export — حمّل نسخة كاملة من ذاكرتي (JSON)",
  "/report — ملخص الحالة",
  "/arena — جسر LMArena: حالة/تشغيل/إيقاف/نماذج/تشخيص",
  "/browserless — ربط 1000 وحدة Browser مجانية/شهر كمسار أساسي (Cloudflare احتياط)",
  "/arena primary — Arena أساس كل الردود ↔ رجوع للترتيب العادي",
  "/arena test — تشخيص المحركات (يقولك مين شغال فعلياً)",
  "/arena_ask <سؤال> — سؤال مباشر عبر Arena (بدون أي مزود آخر)",
  "/call <نص> — رنّة تيليجرام فورية عبر CallMeBot",
  "/health — فحص أني شغال",
  "/files — شو الملفات والصور بقدر أقراها وأعدلها",
  "/reset — مسح ذاكرة المحادثة",
].join("\n");

async function handleCommand(text, env, chatId) {
  const m = text.match(/^(\S+)(?:\s+([\s\S]*))?$/);
  const cmd = ((m && m[1]) || "").toLowerCase();
  const arg = ((m && m[2]) || "").trim();
  switch (cmd) {
    case "/start": case "/help": case "/مساعدة":
      await sendMessage(env, chatId, WELCOME); return true;
    case "/leads":
      await sendMessage(env, chatId, await listLeads(env, arg)); return true;
    case "/lead": {
      const m = await mergedLeads(env);
      await sendMessage(env, chatId, getLeadText(m, arg.split(/\s+/)[0])); return true;
    }
    case "/audit": {
      if (!arg) { await sendMessage(env, chatId, "اكتب الموقع بعد الأمر: /audit namconsultant.com"); return true; }
      await sendMessage(env, chatId, await auditWebsite(arg)); return true;
    }
    case "/tasks": {
      const tasks = await kvGet(env, "tasks", []);
      if (!tasks.length) { await sendMessage(env, chatId, "ماكو مهام خلفية لحد الآن."); return true; }
      const icon = (st) => st === "done" ? "✅" : st === "cancelled" ? "⛔" : st === "failed" ? "⚠️" : "⏳";
      await sendMessage(env, chatId, tasks.slice(0, 10).map((t) => `${icon(t.status)} ${t.id} \n   ${t.goal.slice(0, 90)} \n   الحالة: ${t.status} | ${(t.stepCount) || 0} خطوة`).join("\n")); return true;
    }
    case "/cancel": {
      const id = arg.trim();
      if (!id) { await sendMessage(env, chatId, "اكتب معرف المهمة: /cancel task_...."); return true; }
      const tasks = await kvGet(env, "tasks", []);
      const t = tasks.find((x) => x.id === id);
      if (!t) { await sendMessage(env, chatId, "ما لقيت هالمهمة — شوف /tasks"); return true; }
      t.status = "cancelled"; t.lockedAt = 0; t.updated = Date.now();
      await kvPut(env, "tasks", tasks);
      await sendMessage(env, chatId, `⛔ أُلغيت المهمة ${id}`); return true;
    }
    case "/chats": case "/contexts": case "/شاتات": {
      const rows = await getThreads(env);
      const active = await kvGet(env, ACTIVE_THREAD_KEY, "");
      if (!rows.length) { await sendMessage(env, chatId, "ما في مساحات عمل بعد. ابعت أول طلب وأنا بفتحها تلقائياً."); return true; }
      const tasks = await kvGet(env, "tasks", []);
      const lines = rows.slice(0, 15).map((t, i) => {
        const linked = tasks.filter((x) => x.threadId === t.id && ["queued", "running"].includes(x.status)).length;
        const age = Math.max(0, Math.floor((Date.now() - (t.updated || Date.now())) / 3600000));
        return `${t.id === active ? "🟢" : "⚪"} ${i + 1}. ${t.title}\n   ${t.id} · آخر نشاط ${age < 24 ? age + " ساعة" : Math.floor(age / 24) + " يوم"}${linked ? ` · ${linked} مهمة شغالة` : ""}`;
      });
      await sendMessage(env, chatId, `🗂 مساحات العمل:\n\n${lines.join("\n")}\n\n/chat <رقم أو ctx_...> للرجوع · /chat new <اسم> للجديد · /progress للتقدم`); return true;
    }
    case "/chat": case "/context": {
      const rows = await getThreads(env);
      if (/^(new|جديد|جديدة)(\s|$)/i.test(arg)) {
        const title = threadLabel(arg.replace(/^(new|جديد|جديدة)\s*/i, "") || "محادثة جديدة");
        const t = { id: "ctx_" + Date.now().toString(36), title, summary: "", keywords: threadWords(title), messages: [], created: Date.now(), updated: Date.now(), status: "active" };
        rows.unshift(t); await putThreads(env, rows); await kvPut(env, ACTIVE_THREAD_KEY, t.id);
        await sendMessage(env, chatId, `✅ فتحت مساحة جديدة: «${title}»\n${t.id}`); return true;
      }
      const n = Number(arg); const t = Number.isInteger(n) && n > 0 ? rows[n - 1] : rows.find((x) => x.id === arg || x.id.endsWith(arg));
      if (!t) { await sendMessage(env, chatId, "ما لقيتها. استخدم /chats وشوف الرقم أو المعرف."); return true; }
      await kvPut(env, ACTIVE_THREAD_KEY, t.id);
      await sendMessage(env, chatId, `🟢 رجعت لمساحة «${t.title}»\nآخر سياق: ${t.summary || "فارغة"}\nهلق أي «كمل» رح ينفهم ضمنها.`); return true;
    }
    case "/progress": case "/تقدم": {
      const rows = await getThreads(env); const active = await kvGet(env, ACTIVE_THREAD_KEY, "");
      const t = rows.find((x) => x.id === active); if (!t) { await sendMessage(env, chatId, "ما في شات نشط بعد."); return true; }
      const tasks = (await kvGet(env, "tasks", [])).filter((x) => x.threadId === t.id || (!x.threadId && String(x.goal || "").toLowerCase().includes(String(t.title).toLowerCase())));
      const lines = tasks.slice(0, 8).map((x) => `${x.status === "done" ? "✅" : x.status === "running" ? "⏳" : "▫️"} ${x.goal.slice(0, 100)} — خطوة ${x.stepCount || 0}`);
      await sendMessage(env, chatId, `📍 ${t.title}\nالمعرف: ${t.id}\nآخر سياق: ${t.summary || "—"}\n\nالمهام:\n${lines.join("\n") || "لا توجد مهمة خلفية مرتبطة بعد."}`); return true;
    }
    case "/agents": case "/ايجنتات": {
      const rows = await getAgentRegistry(env);
      if (!rows.length) { await sendMessage(env, chatId, "ما في Agents مسمّيين بعد. أضف واحد:\n/agent add أحمد | التداول | ضع الدستور والـskills أو رابط ملف GitHub هون"); return true; }
      await sendMessage(env, chatId, "🧩 فريق Jarvis:\n\n" + rows.map((a, i) => `${i + 1}. ${a.name} — ${a.scope || "بدون نطاق ثابت"}\n   ${String(a.instructions || "").slice(0, 180)}`).join("\n\n")); return true;
    }
    case "/agent": {
      if (/^add\s+/i.test(arg)) {
        const parts = arg.replace(/^add\s+/i, "").split("|").map((x) => x.trim());
        if (parts.length < 3 || !parts[0]) { await sendMessage(env, chatId, "الصيغة:\n/agent add أحمد | التداول | دستور أحمد والـskills أو رابطها"); return true; }
        const rows = await getAgentRegistry(env); const name = parts[0].slice(0, 40);
        const item = { id: "agt_" + Date.now().toString(36), name, scope: parts[1].slice(0, 120), instructions: parts.slice(2).join(" | ").slice(0, 6000), created: Date.now(), updated: Date.now() };
        const old = rows.findIndex((x) => String(x.name).toLowerCase() === name.toLowerCase());
        if (old >= 0) rows[old] = { ...rows[old], ...item, id: rows[old].id }; else rows.push(item);
        await saveAgentRegistry(env, rows); await sendMessage(env, chatId, `✅ حفظت ${name}. لما تذكر اسمه، Jarvis يربط الطلب بدستوره وسياقه.`); return true;
      }
      if (/^(delete|حذف)\s+/i.test(arg)) {
        const name = arg.replace(/^(delete|حذف)\s+/i, "").trim().toLowerCase(); let rows = await getAgentRegistry(env); const before = rows.length;
        rows = rows.filter((x) => String(x.name).toLowerCase() !== name); await saveAgentRegistry(env, rows);
        await sendMessage(env, chatId, before === rows.length ? "ما لقيت هالاسم." : "🗑️ حذفت Agent من السجل."); return true;
      }
      await sendMessage(env, chatId, "الأوامر:\n/agents\n/agent add الاسم | النطاق | الدستور والـskills\n/agent delete الاسم"); return true;
    }
    case "/route": {
      const r = arenaRouteIntent(arg); const a = await findMentionedAgent(env, arg);
      await sendMessage(env, chatId, `🧭 المسار: ${r.mode === "agent" ? "Agent Mode" : "Direct Chat"}\nالسبب: ${r.reason}${a ? `\nAgent: ${a.name} (${a.scope})` : ""}`); return true;
    }
    case "/report": {
      const merged = await mergedLeads(env);
      const counts = {};
      for (const l of merged) counts[l.status || "جديد"] = (counts[l.status || "جديد"] || 0) + 1;
      const lines = ["📊 ملخص عملاؤك في دبي (12):"];
      for (const [k, v] of Object.entries(counts)) lines.push(`• ${k}: ${v}`);
      lines.push("", "للتفاصيل: /leads و /lead <رقم>");
      await sendMessage(env, chatId, lines.join("\n")); return true;
    }
    case "/call":
      await sendMessage(env, chatId, await callMeNow(env, arg || "جارفس يحتاج قرارك")); return true;
    case "/learn": {
      if (!arg) { await sendMessage(env, chatId, "اكتب اللي تريدني أتذكره — كل سطر = حقيقة، وابدأ بـ ! للتثبيت:\n/learn ! أنا صاحب وكالة تسويق بدبي\nميزانيتي 15K بالشهر"); return true; }
      const lines = arg.split("\n").map((l) => l.trim()).filter(Boolean);
      const saved = await addMemories(env, lines, true);
      await sendMessage(env, chatId, `🧠 حفظت ${saved.length} حقيقة:\n${saved.map((x) => "• " + x).join("\n")}`.slice(0, 3500)); return true;
    }
    case "/memories": {
      const all = await getMemories(env);
      if (!all.length) { await sendMessage(env, chatId, "الذاكرة فاضية — علّمني: /learn <نص>"); return true; }
      const lines = all.map((m, i) => `${i + 1}. ${m.pinned ? "📌 " : ""}${m.text} (${m.id.slice(-4)})`);
      await sendMessage(env, chatId, `🧠 ذاكرتي (${all.length}/500):\n${lines.join("\n")}`.slice(0, 3700) + "\n\nللحذف: /forget <الرقم أو المعرف>"); return true;
    }
    case "/forget": {
      if (!arg) { await sendMessage(env, chatId, "اكتب الرقم أو المعرف: /forget 3"); return true; }
      await sendMessage(env, chatId, await forgetMemories(env, arg)); return true;
    }
    case "/voice": {
      if (!arg) {
        const cur = await kvGet(env, "voice_replies", false);
        await sendMessage(env, chatId, cur === true ? "🔊 الردود الصوتية شغالة (اكتب /voice off للإيقاف)." : "🔇 الردود الصوتية موقفة — نصوص فقط (اكتب /voice on لتفعيلها).");
        return true;
      }
      const turnOn = /^(on|تشغيل|true|نعم|1)$/i.test(arg);
      await kvPut(env, "voice_replies", turnOn);
      await sendMessage(env, chatId, turnOn ? "🔊 صوتي شغال — رح أطلع لك ريكوردات مع النص." : "🔇 من الآن نصوص فقط، بدون ريكوردات.");
      return true;
    }
    case "/tasks": {
      const tasks = (await kvGet(env, "tasks", [])) || [];
      if (!tasks.length) { await sendMessage(env, chatId, "📦 الطابور فاضي — ولا مهمة عندي هلق."); return true; }
      const lines = tasks.slice(0, 12).map((t, i) => `${i + 1}. [${t.status || "?"}] «${String(t.goal).slice(0, 80)}» — خطوة ${t.stepCount || 0} (${t.id.slice(-4)})`);
      await sendMessage(env, chatId, `📦 مهامي (${tasks.length}):\n${lines.join("\n")}\n\nلإلغائها كلها: /clear_tasks`); return true;
    }
    case "/clear_tasks": {
      const before = ((await kvGet(env, "tasks", [])) || []).length;
      await kvPut(env, "tasks", []);
      await sendMessage(env, chatId, `🧹 مسحنا ${before} مهمة من الطابور — الطابور فاضي. (الذاكرة والإيميل ما تأثروا)`); return true;
    }
    case "/export": {
      const all = await getMemories(env);
      const json = JSON.stringify(all, null, 2);
      const ok = await tgSendDocument(env, chatId, "jarvis_memory.json", json, "application/json");
      if (ok) await sendMessage(env, chatId, "📤 هذي نسختك الكاملة من ذاكرتي (JSON). احتفظ فيها بأمان.");
      else await sendMessage(env, chatId, json.length > 3500 ? json.slice(0, 3500) + "\n…(طويلة — انقطعت)" : json);
      return true;
    }
    case "/files":
      await sendMessage(env, chatId, [
        "📂 شو بقدر أقرا وأفهم:",
        "🖼 صور (photo أو image/ملف): وصف + قراءة أي نص مكتوب — اكتب سؤالك كـ caption",
        "📄 نصوص: txt · md · csv · tsv · json · xml · html · لوجات · كود",
        "📊 Excel: xlsx · xlsm (لحد 4 ورقات، 150 صف لكل ورقة — اسألني أي شي عنها)",
        "📝 Word: docx",
        "🚫 PDF لسا لا — ابعته كصور (سكرينشوت لكل صفحة) أو Word وأنا بقراه",
        "",
        "✏️ تعديل وارجاع ملف: اكتب مع الملف «ترجملي هالجدول» أو «نظف الفاضي واحذف التكرار وارجعلي ملف» → بترجعلك CSV معدّل يفتح بأي برنامج.",
        "",
        "⚠️ ما فيني أوصل ملفات على تلفونك مباشرة — بس كل ملف تطرشيلي بقراه وبتعامل معه وبرجعيلك الناتج.",
      ].join("\n")); return true;
    case "/reset": {
      const rows = await getThreads(env); const active = await kvGet(env, ACTIVE_THREAD_KEY, "");
      const t = rows.find((x) => x.id === active);
      if (t) { t.messages = []; t.summary = ""; t.updated = Date.now(); await putThreads(env, rows); }
      await kvPut(env, "history", []);
      await sendMessage(env, chatId, t ? `تم مسح رسائل «${t.title}» فقط. باقي الشاتات والمهام محفوظة.` : "تم مسح ذاكرة المحادثة."); return true;
    }
    case "/browserless": {
      const sub = arg.trim();
      if (/^(test|فحص)$/i.test(sub)) {
        const token = String(await kvGet(env, "browserless_token_v1", env.BROWSERLESS_TOKEN || "") || "").trim();
        if (!token) { await sendMessage(env, chatId, "اربط التوكن أولاً: /browserless TOKEN"); return true; }
        let b; try {
          b = await connectBrowserlessNative(`wss://production-ams.browserless.io?token=${encodeURIComponent(token)}&timeout=30000`);
          const p = await b.newPage(); await p.goto("https://example.com", { waitUntil: "domcontentloaded", timeout: 15000 });
          await kvPut(env, "browserless_last_error_v1", null);
          await sendMessage(env, chatId, "✅ Browserless اتصل فعلياً وفتح صفحة اختبار. صار جاهز لـArena.");
        } catch (e) {
          const message = String(e?.message || e); await kvPut(env, "browserless_last_error_v1", { at: Date.now(), error: message.slice(0, 300) });
          await sendMessage(env, chatId, `❌ Browserless مربوط بالتخزين لكن الاتصال فشل: ${message.slice(0, 500)}`);
        } finally { if (b) try { await b.close(); } catch {} }
        return true;
      }
      if (/^(off|delete|حذف|وقف)$/i.test(sub)) { await kvPut(env, "browserless_token_v1", null); await sendMessage(env, chatId, "تم حذف Browserless. رجعنا لـCloudflare فقط."); return true; }
      if (!sub) {
        const configured = !!String(await kvGet(env, "browserless_token_v1", env.BROWSERLESS_TOKEN || "") || "");
        await sendMessage(env, chatId, configured
          ? "🟢 Browserless المجاني مربوط كمتصفح أساسي، وCloudflare احتياط. للحذف: /browserless off"
          : "🟡 لتوسيع الحصة مجاناً: افتح https://www.browserless.io وسجّل بلا بطاقة، انسخ API Token، وبعت هون بتيليجرام الخاص: /browserless TOKEN\nJarvis يخزنه في KV ولا يطبعه بالتشخيص.");
        return true;
      }
      if (sub.length < 20 || /\s/.test(sub)) { await sendMessage(env, chatId, "التوكن شكله غير صالح. انسخه وحده بعد /browserless"); return true; }
      await kvPut(env, "browserless_token_v1", sub.slice(0, 500));
      await kvPut(env, "arena_skip_until", 0);
      const pending = await kvGet(env, "arena_pending_direct_v1", []); for (const item of pending) item.availableAt = Date.now(); await kvPut(env, "arena_pending_direct_v1", pending);
      await sendMessage(env, chatId, "✅ تم ربط Browserless كمسار أول: 1000 وحدة مجانية بالشهر، متصفحين متزامنين، وCloudflare صار احتياط تلقائي. ما رح أعرض التوكن بأي سجل.");
      return true;
    }
    case "/arena": {
      const cfg = await arenaCfg(env);
      const on = await arenaIsOn(env);
      const cur = await arenaCurrentModel(env);
      const sub = arg.trim();
      const low = sub.toLowerCase();
      const kvUrl = await kvGet(env, "arena_url", null);
      const kvKey = await kvGet(env, "arena_key", null);

      if (/^(connect|login|ربط|دخول)$/i.test(low)) {
        const base = String(await kvGet(env, "public_worker_url", "")).replace(/\/+$/, "");
        if (!base) { await sendMessage(env, chatId, "أرسل /health أولاً ثم أعد /arena connect حتى أعرف رابط Worker."); return true; }
        const link = await arenaReconnectLink(env);
        await sendMessage(env, chatId, [
          "🔐 رابط نقل جلسة Arena من Safari (صالح 10 دقائق ولمرة واحدة):",
          link,
          "",
          "افتحه في Safari واتبع 4 خطوات. لا يطلب كلمة مرور Google ولا يرسلها لجارفس.",
        ].join("\n"));
        return true;
      }

      /* ----- الإعداد الكامل من تيليجرام (بدون wrangler ولا لوحة) ----- */
      if (/^setup|شرح|اعداد|إعداد/.test(low)) {
        await sendMessage(env, chatId, [
          "🧭 خلّي Arena يشتغل بجارفس — ٣ خطوات من الآيفون:",
          "",
          "1️⃣ جهّز الجسر (سيرفر بايثون): أسهل طريق بلا بطاقة = Render أو Hugging Face.",
          "   الدليل خطوة-خطوة بالعربي: arena-bridge/README_IPHONE_AR.md",
          "   بيطلعلك رابط مثل: https://jarvis-arena.onrender.com",
          "",
          "2️⃣ ابعتلي هون:",
          "   /arena url https://jarvis-arena.onrender.com",
          "   /arena key المفتاح-اللي-اخترته",
          "",
          "3️⃣ افحص: /arena test — إذا أخضر، صار Arena أساس كل ردودي.",
          "",
          "بعدها: /arena primary يقلب الأساسي/الاحتياطي · /arena off يوقفه فوراً.",
        ].join("\n"));
        return true;
      }
      if (/^url\b/i.test(sub)) {
        const link = sub.replace(/^url\s+/i, "").trim().replace(/\/+$/, "");
        if (!/^https?:\/\//i.test(link)) { await sendMessage(env, chatId, "لازم رابط كامل: /arena url https://xxx.onrender.com"); return true; }
        await kvPut(env, "arena_url", link);
        await sendMessage(env, chatId, `✅ حفظت عنوان الجسر:\n${link}\n\nهلق ابعت المفتاح: /arena key <المفتاح> ثم /arena test`);
        return true;
      }
      if (/^key\b/i.test(sub)) {
        const k = sub.replace(/^key\s+/i, "").trim();
        if (!k) { await sendMessage(env, chatId, "اكتب المفتاح بعد الأمر: /arena key xxxx"); return true; }
        await kvPut(env, "arena_key", k);
        await sendMessage(env, chatId, "🔑 حفظت المفتاح. جاهز للفحص: /arena test");
        return true;
      }
      if (/^(reset|مسح|حذف)$/i.test(low)) {
        await kvPut(env, "arena_url", null);
        await kvPut(env, "arena_key", null);
        await kvPut(env, "arena_skip_until", 0);
        await sendMessage(env, chatId, "🧹 مسحت عنوان الجسر ومفتاحه من الذاكرة (المتغيرات بالـ Worker ما تأثرت).");
        return true;
      }

      if (!cfg.enabled) {
        await sendMessage(env, chatId, [
          "🌉 جسر LMArena مو مضبوط بعد.",
          "",
          "شغّل الخدمة من مجلد arena-bridge بمستودعنا (Python + gpt4free/Arena):",
          "  cd arena-bridge && pip install -r requirements.txt && python bridge.py",
          "",
          "بعدها ضيف لجارفس:",
          "  ARENA_BRIDGE_URL=https://عنوان-الجسر (بدون /v1)",
          "  ARENA_BRIDGE_KEY=نفس BRIDGE_API_KEY (اختياري لكن مستحسن)",
          "  ARENA_BRIDGE_MODEL=auto",
          "",
          "الأسهل: ابعتلي الرابط من هون مباشرة (بدون wrangler ولا لوحة):",
          "  /arena url https://عنوان-الجسر",
          "  /arena key المفتاح",
          "أو بـ wrangler: npx wrangler secret put ARENA_BRIDGE_URL",
          "",
          "استضافة مجانية ٢٤/٧ من الموبايل فقط؟ شوف arena-bridge/README_DEPLOY_FREE_AR.md",
        ].join("\n"));
        return true;
      }
      if (/^(off|ايقاف|إيقاف|وقف|0)$/i.test(low)) {
        await kvPut(env, "arena_enabled", false);
        await sendMessage(env, chatId, "⏸️ الجسر موقوف — رح أرجع لباقي المزودين. للتفعيل: /arena on");
        return true;
      }
      if (/^(on|تشغيل|1)$/i.test(low)) {
        await kvPut(env, "arena_enabled", true);
        const h = await arenaBridgeHealth(env);
        await sendMessage(env, chatId, h.ok ? "▶️ جسر LMArena شغال — رح أدخلو بسلسلة الردود." : "▶️ فعّلت الجسر بس ما وصلت له: " + h.reason);
        return true;
      }
      if (/^(primary|أساسي|اساسي|اساس)$/i.test(low)) {
        const curPrimary = await arenaIsPrimary(env);
        await kvPut(env, "arena_primary", !curPrimary);
        await sendMessage(env, chatId, !curPrimary
          ? "⭐ صار Arena هو المحرك الأساسي — كل رد ومهمة بتمرق عليه أولاً، وباقي المزودين احتياط."
          : "↩️ رجّعت الترتيب العادي — Gemini أولاً وArena احتياط. (نفس الشي بـ /arena primary مرة تانية)");
        return true;
      }
      if (/^(wake|ايقاظ|إيقاظ|صحّي|صحى)$/i.test(low)) {
        const gap = Number(env.ARENA_BRIDGE_WAKE_GAP_MS || 5000);
        const ok = await arenaWake(env, 6, gap);
        await sendMessage(env, chatId, ok
          ? "🟢 الجسر صحّي وشغال — جاهز يستقبل الأسئلة."
          : "🔴 ما وصلت للجسر بعد 6 محاولات — تأكد إن الخدمة مشغّلة على المنصة، أو جرّب /arena test.");
        return true;
      }
      if (/^(test|فحص|ping)$/i.test(low)) {
        await sendMessage(env, chatId, "🔎 عمّال أفحص المحركات فعلياً (ياخد وقت — المتصفح بطيء)…");
        const deepRes = await arenaSelftest(env, true);
        if (deepRes) {
          const icon = (e) => e.ok ? "🟢" : e.ready ? "🔴" : "⚪️";
          const lines = deepRes.engines.map((e) => {
            const extra = e.ok ? `${e.ms || 0}ms` : (e.error || "غير مهيّأ");
            return `${icon(e)} ${e.name}: ${extra}${e.ok && e.sample ? `\n   «${String(e.sample).slice(0, 60)}»` : ""}`;
          });
          const anyOk = deepRes.engines.some((e) => e.ok);
          await sendMessage(env, chatId, [
            anyOk ? "✅ في محرك شغال — Arena جاهز" : "⚠️ ولا محرك رد الآن",
            "", ...lines,
            "",
            anyOk ? "جرّب: /arena_ask اكتب لي خبر اليوم" : "إذا كلهن أحمر: تأكد من الكوكيز/الجلسة أو شغّل LMArenaBridge وحدد LMArenaBridge_URL",
          ].join("\n"));
          return true;
        }
        const h = await arenaBridgeHealth(env);
        await sendMessage(env, chatId, h.ok
          ? "🟢 الجسر سليم:\n" + JSON.stringify(h.data).slice(0, 1200)
          : "🔴 ما وصلت للجسر: " + h.reason);
        return true;
      }
      if (/^(models|موديلات|نماذج)$/i.test(low) || !sub) {
        let models = [];
        if (on) models = await arenaBridgeModels(env);
        const lines = [
          cfg.browser && !cfg.base ? "🌐 Arena عبر Cloudflare Browser Rendering" : "🌉 جسر LMArena (gpt4free + LMArenaBridge)",
          "الحالة: " + (on ? "🟢 شغال" : "⏸️ موقوف") + " | النموذج: " + cur,
          cfg.browser && !cfg.base ? "التشغيل: Chromium داخل Cloudflare (بلا سيرفر خارجي)" : "العنوان: " + cfg.base + (kvUrl ? "  (محفوظ من تيليجرام)" : ""),
          "الأولوية: " + (/^(1|true|yes|on)$/i.test(String(env.ARENA_BRIDGE_FIRST || "")) ? "قبل كل المزودين" : "بعد المزودين مع مفتاح"),
          "المحرك: " + (await arenaIsPrimary(env) ? "⭐ أساسي (قبل كل المزودين)" : "احتياطي بعد المزودين"),
          "Keep-alive: " + (arenaKeepAliveOn(env, cfg.base) ? "مفعّل (كل 10 دقائق)" : "موقوف"),
          "قاطع الدائرة: " + (await arenaInCooldown(env) ? "مفتوح — الجسر فشل حديثاً، رح أنتظر شوية قبل ما أجرّبه" : "مغلق (طبيعي)"),
        ];
        if (models.length) lines.push("", "النماذج المتاحة (" + models.length + "):", ...models.slice(0, 25).map((m) => "• " + m));
        else lines.push("", "ما قدرت أجيب قائمة النماذج — جرّب /arena test");
        lines.push("", "الأوامر: /arena on · off · primary · wake · models · test · /arena <اسم-نموذج> · /arena_ask <سؤال>");
        await sendMessage(env, chatId, lines.join("\n").slice(0, 3800));
        return true;
      }
      await kvPut(env, "arena_model", sub);
      await sendMessage(env, chatId, `✅ النموذج صار: ${sub}\nجرّب: /arena_ask اكتب لي قصيدة قصيرة عن دبي`);
      return true;
    }
    case "/arena_ask": {
      if (!arg) { await sendMessage(env, chatId, "اكتب سؤالك: /arena_ask <نص>"); return true; }
      const cfg = await arenaCfg(env);
      if (!cfg.enabled) { await sendMessage(env, chatId, "الجسر مو مضبوط — شوف /arena للتعليمات."); return true; }
      const model = await arenaCurrentModel(env);
      const answer = await callArenaBridge([{ role: "user", content: arg }], "أنت جارفس — مساعد عربي مختصر ومفيد. جوابك بالعربي.", env, model);
      await sendMessage(env, chatId, answer ? `🌉 (${model})\n\n${answer}` : "⚠️ الجسر ما رد — شوف /arena test وتأكد إن الخدمة شغالة.");
      return true;
    }
    case "/health":
      await sendMessage(env, chatId, "🟢 جارفس Cloudflare شغال تمام."); return true;
    default:
      return false;
  }
}

async function queueDirectRetry(env, chatId, text, daily) {
  const rows = await kvGet(env, "arena_pending_direct_v1", []);
  const duplicate = rows.find((r) => r.chatId === chatId && r.text === text && Date.now() - r.created < 10 * 60000);
  if (duplicate) return duplicate.id;
  const nextUtc = Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate() + 1, 0, 2);
  const item = { id: "retry_" + Date.now().toString(36), chatId, text: String(text).slice(0, 6000), created: Date.now(), availableAt: daily ? nextUtc : Date.now() + 65000, attempts: 0 };
  rows.push(item); await kvPut(env, "arena_pending_direct_v1", rows.slice(-20)); return item.id;
}

async function processDirectRetries(env) {
  const rows = await kvGet(env, "arena_pending_direct_v1", []); if (!rows.length) return;
  const now = Date.now(); const item = rows.find((r) => (r.availableAt || 0) <= now); if (!item) return;
  item.attempts = (item.attempts || 0) + 1;
  const answer = await agentLoop(item.text, env, item.chatId, { route: "direct", retry: true });
  if (["__ARENA_RETRY_429__", "__ARENA_RETRY_DAILY__"].includes(answer) || /صار انقطاع مؤقت/.test(answer)) {
    const d = new Date(); const nextUtc = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + 1, 0, 2);
    item.availableAt = answer === "__ARENA_RETRY_DAILY__" ? nextUtc : now + Math.min(15 * 60000, 60000 * Math.pow(2, Math.min(item.attempts, 4)));
    await kvPut(env, "arena_pending_direct_v1", rows); return;
  }
  await sendMessage(env, item.chatId, `✅ رجعت كملت طلبك تلقائياً:\n\n${answer}`);
  await kvPut(env, "arena_pending_direct_v1", rows.filter((r) => r.id !== item.id));
}

async function handleUpdate(update, env, ctx) {
  const cq = update.callback_query;
  if (cq) { await handleCallbackQuery(cq, env, ctx); return; }
  const msg = update.message || update.edited_message;
  if (!msg || !msg.chat || !msg.from) return;
  const chatId = msg.chat.id;
  const isVoice = !!msg.voice;
  const userId = String(msg.from.id);
  if (!env.ALLOWED_TELEGRAM_ID || userId !== String(env.ALLOWED_TELEGRAM_ID).trim()) {
    await sendMessage(env, chatId, "⛔ هذا جارفس خاص بالمالك فقط.");
    return;
  }
  await kvPut(env, "owner_chat_id", chatId);
  let text = String(msg.text || msg.caption || "").trim();
  if (!text && msg.voice) {
    text = await transcribeVoice(env, msg.voice.file_id);
    if (!text) { await sendMessage(env, chatId, "ما قدرت أفرّغ الريكورد — جرّبت Groq ثم Workers AI ثم Gemini وكلهم مشغولين/خلصوا. اكتب لي مؤقتاً وأنا برجع اسمع بأول تجديد للكوتا."); return; }
  }
  /* صور (فوتو أو صورة كملف) — رؤية مجانية */
  const photoSizes = Array.isArray(msg.photo) ? msg.photo : [];
  const docIsImage = msg.document && /^image\//.test(String(msg.document.mime_type || ""));
  if (photoSizes.length || docIsImage) {
    const caption = String(msg.caption || "").trim();
    const fileId = photoSizes.length ? photoSizes[photoSizes.length - 1].file_id : msg.document.file_id;
    const mime = photoSizes.length ? "image/jpeg" : String(msg.document.mime_type || "image/jpeg");
    const desc = await visionDescribe(env, fileId, caption || null, mime);
    if (!desc) { await sendMessage(env, chatId, "ما قدرت أقرأ الصورة هالمرة — Workers AI و Gemini مشغولين. جرّب مرة ثانية بعد دقيقة."); return; }
    const userText = `[المستخدم بعت صورة — تفريغها الآلي:\n${desc.slice(0, 2500)}]\n\n${caption ? "سؤال المستخدم عنها: " + caption : "علّق على الصورة باختصار وبأسلوبك، واقرأ أي نص فيها حرفياً."}`;
    const answer = await agentLoop(userText, env, chatId, { ctx });
    await sendMessage(env, chatId, answer);
    return;
  }
  /* مستندات: txt/csv/json/md + xlsx/docx — قراءة واستخراج */
  if (msg.document) {
    const d = msg.document;
    const name = String(d.file_name || "file").slice(0, 120);
    const caption = String(msg.caption || "").trim();
    const got = await extractDocumentText(env, d.file_id, name, d.mime_type);
    if (!got) { await sendMessage(env, chatId, `📄 وصلني «${name}» بس ما بعرف أقرأ هالنوع. المدعوم: txt/md/csv/json/xml · xlsx · docx · صور (للـ PDF: ابعته صور أو Word).`); return; }
    if (got.error) { await sendMessage(env, chatId, got.error); return; }
    /* طلب تعديل/إرجاع ملف ← نرجّع CSV معدّل */
    const wantFile = /ارجع(لي)?\s*ملف|صدّر?(لي)?|احفظ(لي)?|عدّل|عدل|ترجم|نظّف|نظف|وحّد|وحد|احذف|أضف\s*عمود|حول.*(csv|excel)/i.test(caption);
    if (wantFile && (got.kind === "xlsx" || got.kind === "text")) {
      const edited = await llmComplete(
        [{ role: "user", content: `الجدول/الملف الأصلي:\n${got.text.slice(0, 6000)}\n\nطلب المستخدم: ${caption}\n\nأرجع المحتوى المعدّل كاملاً بصيغة CSV فقط، بدون أي شرح أو مقدمة أو علامات كود.` }],
        "أنت محرك جداول دقيق. الناتج CSV فقط. حافظ على الأعمدة والبيانات ما لم يطلب المستخدم غير ذلك.",
        env
      );
      if (edited && edited.trim()) {
        const clean = edited.trim().replace(/^```[a-z]*\n?/i, "").replace(/```$/, "").trim();
        const outName = name.replace(/\.(xlsx|xls|xlsm|csv|tsv|txt|md)$/i, "") + "-jarvis.csv";
        const ok = await tgSendDocument(env, chatId, outName, clean, "text/csv");
        await sendMessage(env, chatId, ok ? "📄 هون الملف المعدّل (CSV — يفتح بأي برنامج Excel/Sheets)." : "ما قدرت ابعث الملف — بس هون النص:\n\n" + clean.slice(0, 3000));
        return;
      }
    }
    const userText = `[المستخدم بعت ملف «${name}».\nمحتواه (مستخرج آلياً):\n${got.text.slice(0, 9000)}]\n\n${caption ? "طلب المستخدم: " + caption : "لخّص الملف باختصار شديد وركز على: أهم الأرقام، أهم البنود، وأي شي بدّي أتحرك فيه. جدول صغير إذا فيه بيانات."}`;
    const answer = await agentLoop(userText, env, chatId, { ctx });
    await sendMessage(env, chatId, answer);
    return;
  }
  if (!text) { await sendMessage(env, chatId, "أرسل نصاً، صوتاً، صورة أو ملف (txt/csv/xlsx/docx)."); return; }
  if (text.startsWith("/") && (await handleCommand(text, env, chatId))) return;
  const route = arenaRouteIntent(text);
  const namedAgent = await findMentionedAgent(env, text);
  if (/شو\s*(صار|وصل)|وين\s*(وصلنا|صرت)|اعطيني\s*(تقدم|ابديت)|update|progress/i.test(text)) {
    const tasks = await kvGet(env, "tasks", []); const activeThread = await kvGet(env, ACTIVE_THREAD_KEY, "");
    const pool = tasks.filter((t) => !activeThread || t.threadId === activeThread);
    const t = (namedAgent ? pool.find((x) => x.agentId === namedAgent.id || x.agentName === namedAgent.name) : null) || pool.find((x) => ["queued", "running"].includes(x.status)) || pool[0];
    if (t) { const last = (t.trace || []).slice(-1)[0]; await sendMessage(env, chatId, `📍 ${t.agentName ? t.agentName + " · " : ""}${String(t.goal).slice(0, 140)}\nالحالة: ${t.status} · التقدم: ${t.progress || 0}%\nالمرحلة: ${t.phase || "queued"}\n${last ? "آخر نتيجة: " + String(last.result).slice(0, 700) : "لم تبدأ أول خطوة بعد."}`); return; }
  }
  if (route.mode === "agent") {
    // أنشئ/اختر مساحة المشروع قبل ربط المهمة بها.
    const taskThread = await resolveThread(env, text, null);
    await putThreads(env, taskThread.rows);
    const skill = namedAgent ? `\n\nAgent المكلّف: ${namedAgent.name}\nالنطاق: ${namedAgent.scope}\nالدستور والـSkills:\n${namedAgent.instructions}` : "";
    const id = await queueApprovedTask(env, text + skill, ctx, { route: "agent", agentId: namedAgent?.id, agentName: namedAgent?.name });
    await sendMessage(env, chatId, `🚀 بدأت المهمة ${id.slice(-6)}${namedAgent ? ` مع ${namedAgent.name}` : ""}\nرح أبعت Progress حقيقي أثناء التنفيذ. اسأل «شو صار؟» بأي وقت.`);
    return;
  }
  const answer = await agentLoop(text, env, chatId, { ctx, route: "direct", namedAgent });
  if (answer === "__ARENA_RETRY_429__" || answer === "__ARENA_RETRY_DAILY__") {
    const daily = answer === "__ARENA_RETRY_DAILY__";
    const retryId = await queueDirectRetry(env, chatId, text, daily);
    await sendMessage(env, chatId, daily
      ? `🕛 استُهلكت حصة Cloudflare المجانية الرسمية (10 دقائق Browser باليوم). حفظت طلبك (${retryId.slice(-6)}) ورح أنفذه تلقائياً بعد تجدد الحصة الساعة 00:00 UTC. إعادة الربط ما بتغيّر هالحد.`
      : `⏳ Cloudflare وصل حد إنشاء المتصفح المؤقت، بس ما ضاع طلبك. حفظته (${retryId.slice(-6)}) ورح أعيده تلقائياً — ما تعيد الرسالة ولا تعمل /arena connect.`);
    return;
  }
  await sendMessage(env, chatId, answer);
  if (isVoice) {
    const voiceOn = await kvGet(env, "voice_replies", false);
    if (voiceOn === true) ctx.waitUntil(sendVoiceReply(env, chatId, answer));
  }
}

/* --------------------- /tts — نطق شامي للـ call page --------------------- */

async function handleTts(request, env) {
  const url = new URL(request.url);
  const key = request.headers.get("x-jarvis-key") || url.searchParams.get("key") || "";
  if (!env.CALL_SECRET) return jsonResponse({ error: "CALL_SECRET غير مفعّل" }, 501, CORS_HEADERS);
  if (!key || key !== env.CALL_SECRET) return jsonResponse({ error: "غير مصرّح — x-jarvis-key خاطئ" }, 401, CORS_HEADERS);
  const text = String(url.searchParams.get("text") || "").trim().slice(0, 700);
  if (!text) return jsonResponse({ error: "text مطلوب" }, 400, CORS_HEADERS);
  const want = String(url.searchParams.get("voice") || env.EDGE_TTS_VOICE || EDGE_TTS_DEFAULT_VOICE);
  const safeVoice = /^ar-[A-Z]{2}-[A-Za-z]+Neural$/.test(want) ? want : EDGE_TTS_DEFAULT_VOICE;
  const audio = (await edgeTtsMp3(text, safeVoice, 25000)) || (await googleTtsMp3(text.slice(0, 180)));
  if (!audio) return jsonResponse({ error: "تعذر توليد الصوت — جرّب كمان شوي" }, 502, CORS_HEADERS);
  return new Response(audio, { status: 200, headers: { ...CORS_HEADERS, "content-type": "audio/mpeg", "cache-control": "no-store" } });
}

/* --------------------- /ask — جسر صفحة المكالمة --------------------- */

async function handleAsk(request, env, ctx) {
  const send = (obj, status) => jsonResponse(obj, status || 200, CORS_HEADERS);
  const provided = request.headers.get("x-jarvis-key") || "";
  if (!env.CALL_SECRET) return send({ error: "CALL_SECRET غير مفعّل على السيرفر — أضفه: npx wrangler secret put CALL_SECRET" }, 501);
  if (!provided || provided !== env.CALL_SECRET) return send({ error: "غير مصرّح — x-jarvis-key خاطئ" }, 401);
  let body;
  try { body = await request.json(); } catch { return send({ error: "JSON غير صالح" }, 400); }
  const text = String(body?.text || "").trim().slice(0, 1500);
  if (!text) return send({ error: "text فارغ" }, 400);
  const reply = await agentLoop(text, env, null, { ctx });
  return send({ reply });
}

function b64ToArrayBuffer(b64) {
  const bin = atob(String(b64 || ""));
  const len = bin.length;
  const buf = new Uint8Array(len);
  for (let i = 0; i < len; i++) buf[i] = bin.charCodeAt(i);
  return buf.buffer;
}

async function handleVoiceAsk(request, env, ctx) {
  const send = (obj, status) => jsonResponse(obj, status || 200, CORS_HEADERS);
  const provided = request.headers.get("x-jarvis-key") || "";
  if (!env.CALL_SECRET) return send({ error: "CALL_SECRET غير مفعّل" }, 501);
  if (!provided || provided !== env.CALL_SECRET) return send({ error: "غير مصرّح — x-jarvis-key خاطئ" }, 401);
  let body;
  try { body = await request.json(); } catch { return send({ error: "JSON غير صالح" }, 400); }
  const audio = body?.audio || {};
  if (!audio?.data) return send({ error: "audio.data مطلوب (base64)" }, 400);
  const buf = b64ToArrayBuffer(audio.data);
  const mime = String(audio.mimeType || "audio/webm").slice(0, 100);
  const text = await transcribeAudioBuffer(env, mime, buf);
  if (!text) return send({ error: "ما قدرت أفرّغ الصوت — Groq وWorkers AI وGemini كلهم مشغولين هلق. حاول مرة ثانية أو اكتب." }, 422);
  const reply = await agentLoop(text, env, null, { ctx });
  return send({ reply, transcript: text });
}

async function handleCallEnd(request, env, ctx) {
  const provided = request.headers.get("x-jarvis-key") || "";
  if (!env.CALL_SECRET) return jsonResponse({ error: "CALL_SECRET غير مفعّل" }, 501, CORS_HEADERS);
  if (!provided || provided !== env.CALL_SECRET) return jsonResponse({ error: "غير مصرّح" }, 401, CORS_HEADERS);
  let body;
  try { body = await request.json(); } catch { return jsonResponse({ error: "JSON غير صالح" }, 400, CORS_HEADERS); }
  const transcript = Array.isArray(body?.transcript) ? body.transcript.slice(-40) : [];
  const durationSec = Math.max(0, Number(body?.durationSec || 0));
  const lines = transcript.map((t) => ((t && t.role === "user") ? "أنا: " : "جارفس: ") + String((t && t.text) || "").slice(0, 300)).join("\n");
  if (!lines.trim()) {
    const ownerEmpty = await kvGet(env, "owner_chat_id", null);
    if (ownerEmpty && transcript.length > 0) await sendMessage(env, ownerEmpty, "📞 المكالمة ما فيها كلام واضح (ما سمعتك) — جرّب مرة ثانية بمكان أردا أو اكتب لي.");
    return jsonResponse({ ok: true, skipped: "empty" }, 200, CORS_HEADERS);
  }
  const summaryIn = lines.slice(0, 6000);
  const summary = await llmComplete(
    [{ role: "user", content: "لخّص هذه المحادثة بإيجاز حاد: أهم النقاط والقرارات وأي مهام/تواريخ/أسماء/أرقام، ثم قائمة تنفيذية قصيرة:\n\n" + summaryIn }],
    "أنت تلخص محادثات عمل باللهجة الشامية. الأهم: نقاط عملية قابلة للتنفيذ بدون حشو.",
    env
  );
  const s = summary || summaryIn.slice(0, 600);
  const now = new Date().toISOString();
  await addMemories(env, ["!ملخص مكالمة (" + now.slice(0, 10) + "): " + String(s).replace(/\n/g, " • ").slice(0, 380)], true);
  const calls = (await kvGet(env, "call_transcripts", [])) || [];
  calls.push({ id: "call_" + Date.now().toString(36), saved: now, durationSec, summary: String(s).slice(0, 2000), transcript: lines.slice(0, 9000) });
  await kvPut(env, "call_transcripts", calls.slice(-10));
  const owner = await kvGet(env, "owner_chat_id", null);
  if (owner) {
    const mins = durationSec >= 60 ? Math.round(durationSec / 60) + " د" : durationSec + " ث";
    await sendMessage(env, owner, "📞 ملخص مكالمتك مع جارفس (" + mins + ")\n\n" + s + "\n\n🧠 محفوظة بذاكرتي كاملة — اسألني «شنو حكينا بالمكالمة؟» بأي وقت.");
  } else {
    console.log("call-end: لا يوجد owner_chat_id — ابدأ البوت بتيليجرام بـ /start أولاً");
  }
  return jsonResponse({ ok: true }, 200, CORS_HEADERS);
}

/* ------------------- الموجز الصباحي (Cron Trigger) ------------------- */

async function morningBrief(env) {
  const owner = await kvGet(env, "owner_chat_id", null);
  const target = owner || (env.OWNER_CHAT_ID ? Number(env.OWNER_CHAT_ID) : null);
  if (!target) { console.log("morningBrief: لا يوجد owner_chat_id بعد — ابدأ البوت أولاً بـ /start"); return; }
  const overlay = await leadsOverlay(env);
  const stateOf = (i) => (overlay[i] && overlay[i].status) || "جديد";
  const hotNew = LEADS.filter((l) => l.pri === "هوت" && stateOf(l.i) === "جديد");
  const counts = {};
  for (const l of LEADS) counts[stateOf(l.i)] = (counts[stateOf(l.i)] || 0) + 1;
  const done = (await kvGet(env, "tasks", [])).filter((t) => t.status === "done").slice(0, 3);

  const lines = ["☀️ صباح الخير — موجز جارفس:", ""];
  lines.push(`🎯 صفقات ساخنة لم تُراسل بعد (${hotNew.length}):`);
  for (const l of hotNew.slice(0, 5)) lines.push(`• #${l.i} ${l.company} — ${l.sector} (${l.price})`);
  if (done.length) {
    lines.push("", "✅ مهام خلّصت:");
    for (const t of done) lines.push(`• ${t.goal.slice(0, 90)}`);
  }
  lines.push("", "📊 الحالة: " + Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(" | "));
  lines.push("", "قل للبوت «راسل الشركة 1» أو اكتب /leads لكل التفاصيل.");
  await sendMessage(env, target, lines.join("\n"));
  if (String(env.CALL_ON_BRIEF).toLowerCase() === "true") {
    await callMeNow(env, "جارفس: موجز صباحك جاهز — افتح التيليجرام");
  }
}

/* ---------- إرسال إيميل Gmail عبر Google Apps Script + موافقة بضغطة ---------- */

async function sendEmailCard(env, to, subject, body) {
  const owner = await getOwnerChatId(env);
  if (!owner) return "ما أعرف محادثتك معي — أرسل /start أولاً.";
  if (!env.APPS_SCRIPT_URL) return "اتصال Gmail غير مفعّل بعد. فعله خلال 5 دقائق: انشر apps-script-email.gs كـ Web App وضع APPS_SCRIPT_URL (وراجع README).";
  const id = "ap_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  const approvals = await kvGet(env, "approvals", []);
  approvals.unshift({ id, type: "email", payload: { to: String(to || "").slice(0, 150), subject: String(subject || "").slice(0, 200), body: String(body || "").slice(0, 4000) }, created: Date.now() });
  await kvPut(env, "approvals", approvals.slice(0, 30));
  const kb = { inline_keyboard: [[
    { text: "✅ أرسل الآن", callback_data: "approve:" + id },
    { text: "❌ الغي", callback_data: "cancel:" + id },
  ]] };
  await tgApi(env, "sendMessage", { chat_id: owner, text: `📧 إيميل معلّق بانتظار موافقتك:\n\nإلى: ${to}\nالموضوع: ${subject}\n\n${body}`, reply_markup: kb });
  return "الإيميل جاهز — بطاقة ✅/❌ وصلتك فوق. بانتظر ضغطتك قبل الإرسال.";
}

async function handleCallbackQuery(cq, env, ctx) {
  const cqId = cq.id;
  const data = String(cq.data || "");
  const fromId = String(cq?.from?.id || "");
  const chatId = cq?.message?.chat?.id;
  const msgId = cq?.message?.message_id;
  if (!env.ALLOWED_TELEGRAM_ID || fromId !== String(env.ALLOWED_TELEGRAM_ID).trim()) {
    await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: "غير مصرّح" });
    return;
  }
  const j = data.indexOf(":");
  const action = j === -1 ? data : data.slice(0, j);
  const id = j === -1 ? "" : data.slice(j + 1);
  const approvals = await kvGet(env, "approvals", []);
  const ap = approvals.find((x) => x.id === id);
  if (!ap) { await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: "هذي البطاقة انتهت صلاحيتها أو نُفذت" }); return; }
  const rest = approvals.filter((x) => x.id !== id);

  if (ap.type === "task") {
    if (action === "approve") {
      await kvPut(env, "approvals", rest);
      const newId = await queueApprovedTask(env, ap.payload.goal, ctx || null);
      await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: "انبدأت ✅" });
      if (chatId) await tgApi(env, "editMessageText", { chat_id: chatId, message_id: msgId, text: `✅ انبدأت المهمة «${String(ap.payload.goal).slice(0, 200)}»\n\nراح أطرشلك التقرير هون لما تخلص (رقمها ${newId.slice(-4)}).` });
      return;
    }
    await kvPut(env, "approvals", rest);
    await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: "تم الإلغاء" });
    if (chatId) await tgApi(env, "editMessageText", { chat_id: chatId, message_id: msgId, text: "❌ ما بلشت المهمة — ولا شي رح يصير بالخلفية." });
    return;
  }

  if (action === "cancel") {
    await kvPut(env, "approvals", rest);
    await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: "أُلغي ✅" });
    if (chatId) await tgApi(env, "editMessageText", { chat_id: chatId, message_id: msgId, text: "❌ أُلغي الإيميل — ما انرسل أي شيء." });
    return;
  }
  if (action === "approve") {
    let ok = false, errText = "";
    try {
      const res = await fetch(env.APPS_SCRIPT_URL, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ secret: env.APPS_SCRIPT_SECRET || "", action: "send_email", to: ap.payload.to, subject: ap.payload.subject, body: ap.payload.body }),
        signal: AbortSignal.timeout(20000),
      });
      const d = await res.json().catch(() => ({}));
      ok = res.ok && d && d.ok === true;
      if (!ok) errText = String(d?.error || ("HTTP " + res.status));
    } catch (e) { errText = e && e.message ? e.message : String(e); }
    await kvPut(env, "approvals", rest);
    await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: ok ? "انرسل ✅" : "فشل الإرسال ⚠️" });
    if (chatId) await tgApi(env, "editMessageText", { chat_id: chatId, message_id: msgId, text: ok ? `✅ أُرسل الإيميل إلى ${ap.payload.to}` : `⚠️ فشل الإرسال: ${errText}` });
    return;
  }
  await tgApi(env, "answerCallbackQuery", { callback_query_id: cqId, text: "أمر غير معروف" });
}

async function tgSendDocument(env, chatId, filename, content, mime) {
  try {
    const fd = new FormData();
    fd.append("chat_id", String(chatId));
    fd.append("document", new Blob([content], { type: mime || "application/json" }), filename);
    const res = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendDocument`, { method: "POST", body: fd, signal: AbortSignal.timeout(30000) });
    const d = await res.json().catch(() => ({}));
    return d.ok === true;
  } catch { return false; }
}
