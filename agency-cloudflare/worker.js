import CALL_PAGE from "./callpage.mjs";
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
- start_background_task(goal): إدراج مهمة بحث/تجهيز في الطابور — تنفذ تلقائياً على مراحل كل دقيقة حتى لو استمرت ساعات، وتطرش تقريراً وتتصل بالمالك عند الانتهاء
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
- إذا كانت الرسالة صوتية: ردك جملتين أو ثلاث قصيرة فقط (عشان تتحول لصوت بسرعة).
- جميع الأرقام بالإنجليزية (واتساب، أسعار، روابط).
${TOOL_DOC}`;

const WORKER_PROMPT = `أنت "جارفس" تنفذ مهمة خلفية مستقلة نيابة عن المالك، بدون سؤاله.
اتبع الأدوات خطوة خطوة حتى الإنجاز، ثم اكتب تقريراً عربياً موجزاً وحاداً.
تحدث باللهجة الشامية السورية وبالإيجاز. إذا احتجت قرار المالك فقط استخدم call_me_now(message) موجزاً.
${TOOL_DOC}`;

const MAX_HISTORY = 14;
const MAX_TOOL_STEPS = 6;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/ask") {
      if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS_HEADERS });
      if (request.method !== "POST") return jsonResponse({ error: "POST only" }, 405, CORS_HEADERS);
      return handleAsk(request, env, ctx);
    }
    if (url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok", service: "jarvis-cf", ts: Date.now() }), { status: 200, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
    }
    if (url.pathname === "/" ) {
      return new Response("JARVIS CF is alive — see /health", { status: 200 });
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
      } catch (e) { console.log("brief error:", e && e.message ? e.message : e); }
      try { await processTaskQueue(env, STEPS_PER_TICK); } catch (e) { console.log("queue error:", e && e.message ? e.message : e); }
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
const getHistory = (env) => kvGet(env, "history", []);
const saveHistory = (env, convo) => kvPut(env, "history", convo.slice(-MAX_HISTORY));

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

async function startBackgroundTask(goal, env, ctx) {
  const g = String(goal || "").trim().slice(0, 500);
  if (!g) return "هدف المهمة فارغ";
  const tasks = await kvGet(env, "tasks", []);
  const id = "task_" + Date.now();
  tasks.unshift({ id, goal: g, status: "queued", trace: [], stepCount: 0, created: Date.now(), updated: Date.now(), lockedAt: 0 });
  await kvPut(env, "tasks", tasks.slice(0, 30));
  if (ctx && typeof ctx.waitUntil === "function") ctx.waitUntil(processTaskQueue(env, STEPS_PER_TICK));
  return `أُدرجت المهمة ${id} في الطابور: «${g}»\nتنفذ تلقائياً حتى لو استمرت ساعات — أطرشلك التقرير هنا${env.CALLMEBOT_TELEGRAM_USER ? " وأوصلك رنّة" : ""} عند الانتهاء. تابع بـ /tasks`;
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
    task.stepCount = (task.stepCount || 0) + 1;
    if (!out) { await finishTask(task, tasks, env, "failed", "الذكاء ما رجع رد — تأكد من GEMINI/OPENROUTER."); return; }
    const call = parseToolCall(out);
    if (!call) { await finishTask(task, tasks, env, "done", out); return; }
    const result = await runTool(call, env, null);
    task.trace = (task.trace || []).concat([{ step: task.stepCount, tool: call.tool, args: call.args, result: String(result).slice(0, 1200) }]).slice(-40);
    task.updated = Date.now();
    const idx2 = tasks.findIndex((t) => t.id === task.id);
    if (idx2 !== -1) tasks[idx2] = { ...task };
    await kvPut(env, "tasks", tasks);
  }
  // لم تنته بعد — تُكمل في الكرون القادم
}

async function agentLoop(userText, env, chatId, opts) {
  const o = opts || {};
  const memBlock = o.mode === "worker" ? "" : await relevantMemories(env, userText);
  const system = o.mode === "worker" ? WORKER_PROMPT : (BASE_PROMPT + (memBlock ? "\n\n" + memBlock : ""));
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
async function ttsArabicMp3(chunk) {
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
  try { return new Uint8Array(await res.arrayBuffer()); } catch { return null; }
}
async function tgSendVoice(env, chatId, mp3Bytes, name) {
  try {
    const form = new FormData();
    form.append("chat_id", String(chatId));
    form.append("voice", new Blob([mp3Bytes], { type: "audio/mpeg" }), name || "jarvis.mp3");
    const res = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendVoice`, { method: "POST", body: form });
    const d = await res.json().catch(() => ({}));
    return res.ok && d && d.ok !== false;
  } catch (e) { console.log("sendVoice error:", e && e.message ? e.message : e); return false; }
}
async function sendVoiceReply(env, chatId, text) {
  try {
    const clean = String(text || "").replace(/[*_`~]/g, "").replace(/https?:\/\/\S+/g, "الرابط").trim();
    const chunks = splitForTts(clean, 170).slice(0, 3);
    for (let i = 0; i < chunks.length; i++) {
      const mp3 = await ttsArabicMp3(chunks[i]);
      if (mp3) await tgSendVoice(env, chatId, mp3, "jarvis_" + i + ".mp3");
    }
  } catch (e) { console.log("voice reply error:", e && e.message ? e.message : e); }
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
  "/tasks — آخر المهام الخلفية مع عدد الخطوات",
  "/cancel task_ID — إلغاء مهمة جارية",
  "/learn <نص> — احفظ حقائق (كل سطر = حقيقة، ابدأ بـ ! للتثبيت الدائم)",
  "/memories — كل اللي كنت تعلمته",
  "/forget <الرقم أو المعرف> — امسح حقيقة",
  "/export — حمّل نسخة كاملة من ذاكرتي (JSON)",
  "/report — ملخص الحالة",
  "/call <نص> — رنّة تيليجرام فورية عبر CallMeBot",
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
    case "/export": {
      const all = await getMemories(env);
      const json = JSON.stringify(all, null, 2);
      const ok = await tgSendDocument(env, chatId, "jarvis_memory.json", json, "application/json");
      if (ok) await sendMessage(env, chatId, "📤 هذي نسختك الكاملة من ذاكرتي (JSON). احتفظ فيها بأمان.");
      else await sendMessage(env, chatId, json.length > 3500 ? json.slice(0, 3500) + "\n…(طويلة — انقطعت)" : json);
      return true;
    }
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
  const cq = update.callback_query;
  if (cq) { await handleCallbackQuery(cq, env); return; }
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
    if (!text) { await sendMessage(env, chatId, "ما قدرت أفهم الرسالة الصوتية (Gemini/Groq غير متاحين حالياً) — أرسل نصاً."); return; }
  }
  if (!text) { await sendMessage(env, chatId, "أرسل نصاً أو رسالة صوتية."); return; }
  if (text.startsWith("/") && (await handleCommand(text, env, chatId))) return;
  const answer = await agentLoop(text, env, chatId, { ctx });
  await sendMessage(env, chatId, answer);
  if (isVoice) ctx.waitUntil(sendVoiceReply(env, chatId, answer));
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

async function handleCallbackQuery(cq, env) {
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
