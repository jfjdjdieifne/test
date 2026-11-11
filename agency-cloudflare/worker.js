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

const TOOL_DOC = `الأدوات المتاحة:
- search_web(query): بحث ويب حي
- audit_website(url): فحص سريع لموقع (أزرار # الميتة، واتساب خاطئ، لغة/عنوان/نماذج)
- list_leads(status?): قائمة الـ 12 عميل (فلتر اختياري: جديد/راسلته/مهتم/عرض/مقفل)
- get_lead(index): تفاصيل عميل 1-12
- update_lead(index, status, note): تحديث حالة عميل (تُحفظ دائماً)
- start_background_task(goal): إطلاق مهمة بحث/تجهيز بالخلفية — تُرسل التقرير وتتصل بالمالك عند الانتهاء
- call_me_now(message): رنّة تيليجرام فورية للمالك عبر CallMeBot

لتنفيذ أداة اكتب سحراً بأداة واحدة فقط بهذا الشكل بالضبط ولا شيء غيره:
TOOL_CALL: {"tool":"اسم_الأداة","args":{...}}
بعد وصول TOOL_RESULT أكمل منطقياً. وعند الاكتمال اكتب الجواب النهائي بالكامل بلا أي TOOL_CALL.`;

const BASE_PROMPT = `أنت "جارفس"، ذكاء اصطناعي عربي خاص بصاحب العمل (المالك الوحيد). أسلوبك: واثق، مهني، موجز، خليجي/فصحى راقية.
- لا تخترع معلومات؛ إن احتجت بيانات استخدم الأداة.
- ردود قصيرة منظمة بنقاط عند الحاجة.
- جميع الأرقام بالإنجليزية (واتساب، أسعار، روابط).
${TOOL_DOC}`;

const WORKER_PROMPT = `أنت "جارفس" تنفذ مهمة خلفية مستقلة نيابة عن المالك، بدون سؤاله.
اتبع الأدوات خطوة خطوة حتى الإنجاز، ثم اكتب تقريراً عربياً موجزاً وحاداً.
إذا احتجت قرار المالك فقط استخدم call_me_now(message) موجزاً.
${TOOL_DOC}`;

const MAX_HISTORY = 14;
const MAX_TOOL_STEPS = 6;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return jsonResponse({ status: "ok", service: "jarvis-cf", ts: Date.now() });
    }
    if (url.pathname === "/" ) {
      return new Response("JARVIS CF is alive — see /health", { status: 200 });
    }
    if (url.pathname === "/webhook" && request.method === "POST") {
      const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (!env.WEBHOOK_SECRET || secret !== env.WEBHOOK_SECRET) {
        return new Response("forbidden", { status: 403 });
      }
      let update;
      try { update = await request.json(); } catch { return new Response("bad json", { status: 400 }); }
      ctx.waitUntil(handleUpdate(update, env, ctx).catch((e) => console.log("handler error:", e && e.message ? e.message : e)));
      return new Response("ok", { status: 200 });
    }
    return new Response("not found", { status: 404 });
  },
};

function jsonResponse(obj, status) {
  return new Response(JSON.stringify(obj), { status: status || 200, headers: { "content-type": "application/json; charset=utf-8" } });
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
const getHistory = (env) => kvGet(env, "history", []);
const saveHistory = (env, convo) => kvPut(env, "history", convo.slice(-MAX_HISTORY));

/* ------------------------------ LLM failover --------------------------- */

async function callGemini(convo, system, env) {
  if (!env.GEMINI_API_KEY) return null;
  try {
    const model = (env.GEMINI_MODEL || "gemini-2.5-flash").trim();
    const contents = convo.map((m) => ({ role: m.role === "assistant" ? "model" : "user", parts: [{ text: String(m.content) }] }));
    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ system_instruction: { parts: [{ text: system }] }, contents }),
      signal: AbortSignal.timeout(45000),
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
      body: JSON.stringify({ model, messages: [{ role: "system", content: system }, ...convo.map((m) => ({ role: m.role, content: String(m.content) }))], temperature: 0.4 }),
      signal: AbortSignal.timeout(45000),
    });
    if (!res.ok) { console.log("llm HTTP", res.status, base); return null; }
    const data = await res.json();
    const text = data?.choices?.[0]?.message?.content?.trim();
    return text || null;
  } catch (e) { console.log("llm error:", e && e.message ? e.message : e); return null; }
}

async function llmComplete(convo, system, env) {
  return (
    (await callGemini(convo, system, env)) ||
    (await callOpenAICompatible("https://api.mistral.ai/v1", env.MISTRAL_API_KEY, (env.MISTRAL_MODEL || "mistral-large-latest").trim(), convo, system)) ||
    (await callOpenAICompatible("https://api.groq.com/openai/v1", env.GROQ_API_KEY, (env.GROQ_MODEL || "llama-3.3-70b-versatile").trim(), convo, system)) ||
    (await callOpenAICompatible("https://integrate.api.nvidia.com/v1", env.NVIDIA_API_KEY, (env.NVIDIA_MODEL || "meta/llama-3.3-70b-instruct").trim(), convo, system)) ||
    (await callOpenAICompatible("https://openrouter.ai/api/v1", env.OPENROUTER_API_KEY, "openrouter/free", convo, system)) ||
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
  if (!user) return "CallMeBot غير مفعّل — أضف CALLMEBOT_TELEGRAM_USER من @CallMeBot_txtbot";
  try {
    const url = `https://api.callmebot.com/start.php?user=${encodeURIComponent(user)}&text=${encodeURIComponent(String(message || "جارفس يحتاج قرارك").slice(0, 250))}`;
    await fetch(url, { signal: AbortSignal.timeout(15000) });
    return "تم إرسال رنّة تيليجرام لك عبر CallMeBot.";
  } catch (e) {
    return "تعذرت الرنّة: " + (e && e.message ? e.message : e);
  }
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

async function runTool(call, env, ctx) {
  try {
    const a = call.args || {};
    switch (call.tool) {
      case "search_web": return await searchWeb(a.query, env);
      case "audit_website": return await auditWebsite(a.url);
      case "list_leads": return await listLeads(env, a.status);
      case "get_lead": { const m = await mergedLeads(env); return getLeadText(m, a.index); }
      case "update_lead": return await updateLead(env, a.index, a.status, a.note);
      case "start_background_task": return await startBackgroundTask(a.goal, env, null, ctx);
      case "call_me_now": return await callMeNow(env, a.message);
      default: return "أداة غير معروفة: " + call.tool;
    }
  } catch (e) {
    return "خطأ في الأداة: " + (e && e.message ? e.message : e);
  }
}

async function startBackgroundTask(goal, env, ctx, ownerCtx) {
  const g = String(goal || "").trim().slice(0, 500);
  if (!g) return "هدف المهمة فارغ";
  const tasks = await kvGet(env, "tasks", []);
  const id = "task_" + Date.now();
  const task = { id, goal: g, status: "running", started: Date.now() };
  tasks.unshift(task);
  await kvPut(env, "tasks", tasks.slice(0, 20));
  const bg = backgroundLoop(task, env, ownerCtx || ctx).catch((e) => console.log("bg error:", e && e.message ? e.message : e));
  if (ctx && typeof ctx.waitUntil === "function") ctx.waitUntil(bg);
  return `أُطلقت مهمة خلفية ${id}: «${g}» — راح أطرشلك التقرير هنا${env.CALLMEBOT_TELEGRAM_USER ? " ورنّ عليك عبر CallMeBot" : ""} عند الانتهاء.`;
}

async function backgroundLoop(task, env, bgCtx) {
  const chatId = (await kvGet(env, "owner_chat_id", null));
  const report = await agentLoop(task.goal, env, null, { mode: "worker", ctx: bgCtx });
  const tasks = await kvGet(env, "tasks", []);
  const idx = tasks.findIndex((t) => t.id === task.id);
  if (idx !== -1) { tasks[idx].status = "done"; tasks[idx].finished = Date.now(); }
  await kvPut(env, "tasks", tasks);
  const target = chatId || (env.OWNER_CHAT_ID ? Number(env.OWNER_CHAT_ID) : null);
  if (target) await sendMessage(env, target, `✅ اكتملت مهمة ${task.id}:\n\n${report}`);
  if (env.CALLMEBOT_TELEGRAM_USER) await callMeNow(env, `جارفس خلص مهمتك: ${task.goal.slice(0, 120)}`);
}

async function agentLoop(userText, env, chatId, opts) {
  const o = opts || {};
  const system = o.mode === "worker" ? WORKER_PROMPT : BASE_PROMPT;
  const hist = o.mode === "worker" ? [] : await getHistory(env);
  const convo = [...hist, { role: "user", content: String(userText) }];
  for (let step = 0; step < MAX_TOOL_STEPS; step++) {
    const out = await llmComplete(convo, system, env);
    if (!out) return "تعذر الوصول لكل مزودي الذكاء الآن — تأكد من GEMINI_API_KEY أو OPENROUTER_API_KEY في الأسرار.";
    const call = parseToolCall(out);
    if (!call) {
      if (o.mode !== "worker") await saveHistory(env, [...convo, { role: "assistant", content: out }]);
      return out;
    }
    const result = await runTool(call, env, o.ctx || null);
    convo.push({ role: "assistant", content: out });
    convo.push({ role: "user", content: "TOOL_RESULT: " + String(result).slice(0, 3500) });
  }
  const finalOut = await llmComplete([...convo, { role: "user", content: "أعطني الجواب النهائي الآن فقط بدون أدوات." }], system, env);
  const answer = finalOut || "اكتملت الخطوات — راجع النتائج أعلاه.";
  if (o.mode !== "worker") await saveHistory(env, [...convo, { role: "assistant", content: answer }]);
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

async function transcribeVoice(env, fileId) {
  const f = await tgApi(env, "getFile", { file_id: fileId });
  const filePath = f?.data?.result?.file_path;
  if (!filePath) return null;
  let bin;
  try {
    const res = await fetch(`https://api.telegram.org/file/bot${env.TELEGRAM_BOT_TOKEN}/${filePath}`, { signal: AbortSignal.timeout(30000) });
    bin = await res.arrayBuffer();
  } catch { return null; }
  if (env.GROQ_API_KEY) {
    try {
      const fd = new FormData();
      fd.append("model", "whisper-large-v3-turbo");
      fd.append("file", new Blob([bin], { type: "audio/ogg" }), "voice.ogg");
      const res = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", { method: "POST", headers: { authorization: `Bearer ${env.GROQ_API_KEY}` }, body: fd, signal: AbortSignal.timeout(45000) });
      if (res.ok) { const d = await res.json(); if (d.text) return String(d.text).trim() || null; }
    } catch (e) { console.log("groq whisper error:", e && e.message ? e.message : e); }
  }
  if (env.GEMINI_API_KEY) {
    try {
      const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${env.GEMINI_API_KEY}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ contents: [{ role: "user", parts: [{ text: "فرّغ هذه الرسالة الصوتية حرفياً بلغتها الأصلية (عربي أو إنجليزي). اكتب التفريغ فقط بدون أي تعليق." }, { inlineData: { mimeType: "audio/ogg", data: arrayBufferToBase64(bin) } }] }] }),
        signal: AbortSignal.timeout(45000),
      });
      if (res.ok) { const d = await res.json(); const t = d?.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("").trim(); if (t) return t; }
    } catch (e) { console.log("gemini stt error:", e && e.message ? e.message : e); }
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
  "",
  "الأوامر:",
  "/start — هذه القائمة",
  "/leads [حالة] — قائمة العملاء (جديد/راسلته/مهتم/عرض/مقفل)",
  "/lead <رقم> — تفاصيل عميل 1–12",
  "/audit <موقع> — تدقيق سريع لموقع",
  "/tasks — آخر المهام الخلفية",
  "/report — ملخص الحالة",
  "/call <نص> — رنّة تيليجرام فورية عبر CallMeBot",
  "/reset — مسح ذاكرة المحادثة",
].join("\n");

async function handleCommand(text, env, chatId) {
  const [cmdRaw, ...rest] = text.split(/\s+/);
  const cmd = (cmdRaw || "").toLowerCase();
  const arg = rest.join(" ").trim();
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
      await sendMessage(env, chatId, tasks.slice(0, 8).map((t) => `${t.status === "done" ? "✅" : "⏳"} ${t.id} — ${t.goal.slice(0, 80)}`).join("\n")); return true;
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
    case "/reset":
      await kvPut(env, "history", []);
      await sendMessage(env, chatId, "تم مسح ذاكرة المحادثة."); return true;
    case "/health":
      await sendMessage(env, chatId, "🟢 جارفس Cloudflare شغال تمام."); return true;
    default:
      return false;
  }
}

async function handleUpdate(update, env, ctx) {
  const msg = update.message || update.edited_message;
  if (!msg || !msg.chat || !msg.from) return;
  const chatId = msg.chat.id;
  const userId = String(msg.from.id);
  if (!env.ALLOWED_TELEGRAM_ID || userId !== String(env.ALLOWED_TELEGRAM_ID).trim()) {
    await sendMessage(env, chatId, "⛔ هذا جارفس خاص بالمالك فقط.");
    return;
  }
  await kvPut(env, "owner_chat_id", chatId);
  let text = String(msg.text || msg.caption || "").trim();
  if (!text && msg.voice) {
    text = await transcribeVoice(env, msg.voice.file_id);
    if (!text) { await sendMessage(env, chatId, "ما قدرت أفهم الرسالة الصوتية (Gemini/Groq غير متاحين حالياً) — أرسل نصاً."); return; }
  }
  if (!text) { await sendMessage(env, chatId, "أرسل نصاً أو رسالة صوتية."); return; }
  if (text.startsWith("/") && (await handleCommand(text, env, chatId))) return;
  const answer = await agentLoop(text, env, chatId, { ctx });
  await sendMessage(env, chatId, answer);
}
