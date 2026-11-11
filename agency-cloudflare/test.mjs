/**
 * اختبارات JARVIS Cloudflare Worker — بدون شبكة حقيقية (شبكة وهمية مدمجة)
 * التشغيل: node test.mjs
 */
import worker from "./worker.js";
import assert from "node:assert/strict";

const state = { sent: [], fetches: [], kv: new Map(), geminiQueue: [], tavilyCalls: 0, callmebot: 0, auditHits: 0, appsScript: 0, arenaCalls: 0, arenaHealthFails: 0, arenaDown: false, geminiCalls: 0 };

function reset() {
  state.sent = []; state.fetches = []; state.kv = new Map();
  state.geminiQueue = []; state.tavilyCalls = 0; state.callmebot = 0; state.auditHits = 0; state.appsScript = 0; state.arenaCalls = 0; state.arenaHealthFails = 0; state.arenaDown = false; state.geminiCalls = 0;
}

const mockKV = () => ({
  async get(k) { return state.kv.has(k) ? state.kv.get(k) : null; },
  async put(k, v) { state.kv.set(k, v); },
});

global.fetch = async (input, init = {}) => {
  const url = typeof input === "string" ? input : input.url;
  const method = (init.method || "GET").toUpperCase();
  state.fetches.push({ url, method });
  const j = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: { "content-type": "application/json" } });

  if (url.startsWith("https://api.telegram.org/bottest-token/")) {
    state.sent.push({ method: url.split("/").pop(), body: init.body ? JSON.parse(init.body) : null });
    if (url.includes("getFile")) return j({ ok: true, result: { file_path: "voice/test.ogg" } });
    return j({ ok: true, result: {} });
  }
  if (url.startsWith("https://generativelanguage.googleapis.com/")) {
    state.geminiCalls++;
    const next = state.geminiQueue.shift() || { text: "الجواب النهائي الافتراضي" };
    return j({ candidates: [{ content: { parts: [{ text: next.text }] } }] });
  }
  if (url.startsWith("https://api.tavily.com/")) {
    state.tavilyCalls++;
    return j({ results: [{ title: "نتيجة بحث ١", url: "https://example.com/r1", content: "محتوى تجريبي للنتيجة" }] });
  }
  if (url.startsWith("https://html.duckduckgo.com/")) {
    return new Response('<a class="result__a" href="https://ddg.example/r2">نتيجة DDG</a>', { status: 200 });
  }
  if (url === "https://demo-site.test" || url.startsWith("https://demo-site.test/")) {
    state.auditHits++;
    return new Response('<html><head><title>موقع تجريبي</title><meta name="viewport" content="width=device-width"></head><body><a href="#">x</a><a href="#">y</a><a href="https://wa.me/00971521234567">wa</a><form></form></body></html>');
  }
  if (url.startsWith("https://api.callmebot.com/")) { state.callmebot++; return new Response("OK", { status: 200 }); }
  if (url.startsWith("https://api.telegram.org/file/")) return new Response(new Uint8Array([1, 2, 3]), { status: 200 });
  if (url.startsWith("https://script.google.com/")) { state.appsScript++; return j({ ok: true }); }
  /* جسر LMArena الوهمي */
  if (url.startsWith("https://arena.test/")) {
    state.arenaCalls++;
    if (url.endsWith("/v1/models")) return j({ object: "list", data: [{ id: "auto" }, { id: "stealth-model" }] });
    if (url.includes("/arena/selftest")) return j({ service: "jarvis-arena-bridge", checked: "deep", engines: [
      { name: "LMArenaBridge", ready: true, ok: false, error: "غير مهيّأ" },
      { name: "gpt4free:Arena", ready: true, ok: true, ms: 1200, sample: "تم" },
      { name: "OpenAI-compatible", ready: false, ok: false, error: "غير مهيّأ" },
    ] });
    if (url.endsWith("/health")) {
      if (state.arenaHealthFails > 0) { state.arenaHealthFails--; return j({ error: "starting" }, 503); }
      return j({ status: "ok", service: "jarvis-arena-bridge", has_gpt4free: true });
    }
    if (state.arenaDown) return j({ error: "cold" }, 503);
    return j({ choices: [{ index: 0, message: { role: "assistant", content: "رد من Arena" }, finish_reason: "stop" }] });
  }
  throw new Error("unmocked URL: " + url);
};

const makeEnv = (overrides = {}) => ({
  TELEGRAM_BOT_TOKEN: "test-token",
  ALLOWED_TELEGRAM_ID: "42",
  GEMINI_API_KEY: "gem",
  TAVILY_API_KEY: "tav",
  OPENROUTER_API_KEY: "or",
  CALLMEBOT_TELEGRAM_USER: "actian_data",
  WEBHOOK_SECRET: "sec",
  JARVIS_KV: mockKV(),
  ...overrides,
});

function makeCtx() {
  const ps = [];
  return {
    promises: ps,
    waitUntil(p) { ps.push(Promise.resolve(p)); },
    async drain() {
      // انتظر كل ما تم تسجيله — ومن يسجل المزيد أثناء الانتظار يُنتظر أيضاً
      for (let round = 0; round < 10; round++) {
        const n = ps.length;
        await Promise.all(ps.slice());
        if (ps.length === n) break;
      }
    },
  };
}

const tgUpdate = (text, userId = 42, chatId = 1000) => ({ message: { chat: { id: chatId }, from: { id: userId }, text } });

async function runWebhook(env, ctx, update, secret = "sec") {
  const res = await worker.fetch(
    new Request("http://x/webhook", {
      method: "POST",
      headers: { "x-telegram-bot-api-secret-token": secret, "content-type": "application/json" },
      body: JSON.stringify(update),
    }),
    env,
    ctx
  );
  await ctx.drain();
  return res;
}

const sentTexts = () => state.sent.filter((s) => s.method === "sendMessage").map((s) => s.body.text);

let passed = 0;
async function t(name, fn) {
  reset();
  try {
    await fn();
    passed++;
    console.log("PASS —", name);
  } catch (e) {
    console.error("FAIL —", name, "\n   ", e && e.message ? e.message : e);
    process.exitCode = 1;
  }
}

/* --------------------------------- tests -------------------------------- */

await t("1) /health يرجع JSON سليم", async () => {
  const res = await worker.fetch(new Request("http://x/health"), makeEnv(), makeCtx());
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.status, "ok");
});

await t("2) الويبهوك يرفض بدون السر الصحيح (403)", async () => {
  const res = await worker.fetch(new Request("http://x/webhook", { method: "POST", body: "{}" }), makeEnv(), makeCtx());
  assert.equal(res.status, 403);
});

await t("3) شخص غير مالك يتلقى رفض خاص", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("مرحبا", 999));
  assert.ok(sentTexts().some((x) => x.includes("خاص بالمالك")));
});

await t("4) /start يرجع قائمة المساعدة", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/start"));
  assert.ok(sentTexts().join("\n").includes("جارفس"));
});

await t("5) سؤال عادي → رد LLM المباشر", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push({ text: "عندك ١٢ عميل في القائمة" });
  await runWebhook(env, ctx, tgUpdate("شنو عندي؟"));
  assert.ok(sentTexts().join("\n").includes("١٢ عميل"));
});

await t("6) أداة search_web تُستدعى وتُرجع النتائج للنموذج", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"search_web","args":{"query":"شركات ديكور الرياض"}}' },
    { text: "وجدت نتيجة واعدة" }
  );
  await runWebhook(env, ctx, tgUpdate("ابحث عن شركات ديكور بالرياض"));
  assert.equal(state.tavilyCalls, 1);
  assert.ok(sentTexts().join("\n").includes("وجدت نتيجة واعدة"));
});

await t("7) update_lead يحفظ في KV و/leads تعرض الحالة", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"update_lead","args":{"index":2,"status":"راسلته","note":"مهتم"}}' },
    { text: "تم تحديث NAM Consultant" }
  );
  await runWebhook(env, ctx, tgUpdate("حدّث الشركة 2 اني راسلته"));
  const overlay = JSON.parse(state.kv.get("leads_overlay"));
  assert.equal(overlay["2"].status, "راسلته");
  // الآن افحص /leads بنفس الـ KV
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/leads"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("NAM Consultant"));
  assert.ok(all.includes("راسلته"));
});

await t("8) audit_website يفحص الموقع ويرجع للنموذج", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"audit_website","args":{"url":"https://demo-site.test"}}' },
    { text: "وجدت مشكلتين في الموقع" }
  );
  await runWebhook(env, ctx, tgUpdate("افحص الموقع demo-site.test"));
  assert.equal(state.auditHits, 1);
  assert.ok(sentTexts().join("\n").includes("مشكلتين"));
});

await t("9) مهمة خلفية: بطاقة موافقة ← تبدأ بعد ✅ ويوصل التقرير والرنّة", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"start_background_task","args":{"goal":"جهز عرض لـ NAM Consultant"}}' },
    { text: "طلبت موافقتك بتيليجرام قبل ما أبدأ أي مهمة" },
    { text: "تقرير التنفيذ: تم تجهيز العرض" }
  );
  await runWebhook(env, ctx, tgUpdate("جهز عرض للشركة 2 واطرشلي"));
  await ctx.drain();
  let all = sentTexts().join("\n");
  assert.ok(all.includes("موافق") || all.includes("يبدأ"), "بطاقة الموافقة ما وصلت");
  assert.equal((JSON.parse(state.kv.get("tasks") || "[]")).length, 0, "المهمة بلشت بدون موافقة!");
  const approvals = JSON.parse(state.kv.get("approvals"));
  assert.equal(approvals.length, 1);
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, { callback_query: { id: "cbqtask", data: "approve:" + approvals[0].id, from: { id: 42 }, message: { chat: { id: 1000 }, message_id: 777 } } });
  await ctx2.drain();
  all = sentTexts().join("\n");
  assert.ok(all.includes("تقرير التنفيذ"), "تقرير الخلفية ما وصل");
  assert.equal(state.callmebot, 1, "رنّة CallMeBot ما انطلقت");
  const tasks = JSON.parse(state.kv.get("tasks"));
  assert.equal(tasks[0].status, "done");
});

await t("10) الردود الطويلة تتقسم تلقائياً برسائل متعددة", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push({ text: "x".repeat(9000) });
  await runWebhook(env, ctx, tgUpdate("اكتب تقرير طويل"));
  const msgs = state.sent.filter((s) => s.method === "sendMessage");
  assert.ok(msgs.length >= 2, `متوقع رسالتين على الأقل، وصل ${msgs.length}`);
});


await t("11) مسار /ask يرفض المفتاح الخاطئ (401)", async () => {
  const res = await worker.fetch(new Request("http://x/ask", { method: "POST", headers: { "content-type": "application/json", "x-jarvis-key": "wrong" }, body: JSON.stringify({ text: "مرحبا" }) }), makeEnv({ CALL_SECRET: "s3cr3t" }), makeCtx());
  assert.equal(res.status, 401);
});

await t("12) مسار /ask يجاوب بالمفتاح الصحيح + CORS", async () => {
  const env = makeEnv({ CALL_SECRET: "s3cr3t" }); const ctx = makeCtx();
  state.geminiQueue.push({ text: "أنا جارفس، أسمعك" });
  const res = await worker.fetch(new Request("http://x/ask", { method: "POST", headers: { "content-type": "application/json", "x-jarvis-key": "s3cr3t" }, body: JSON.stringify({ text: "هلا" }) }), env, ctx);
  await ctx.drain();
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("access-control-allow-origin"), "*");
  const body = await res.json();
  assert.ok(body.reply.includes("أسمعك"));
});

await t("13) طلب OPTIONS (Preflight) يرجع 204", async () => {
  const res = await worker.fetch(new Request("http://x/ask", { method: "OPTIONS" }), makeEnv({ CALL_SECRET: "s3cr3t" }), makeCtx());
  assert.equal(res.status, 204);
});


await t("14) /learn يحفظ الحقائق (مع تثبيت !) و/memories تعرضها", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/learn ! أنا مالك وكالة تسويق بدبي\nميزانيتي 15000 بالشهر"));
  const mem = JSON.parse(state.kv.get("mem:all"));
  assert.equal(mem.length, 2);
  assert.equal(mem[0].pinned, true);
  assert.equal(mem[1].pinned, false);
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/memories"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("وكالة تسويق"));
  assert.ok(all.includes("15000"));
});

await t("15) remember/forget عبر أدوات LLM تعمل وتحفظ بالـ KV", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"remember","args":{"fact":"العميل المفضل هو NAM Consultant"}}' },
    { text: "حُفظت في ذاكرتي" }
  );
  await runWebhook(env, ctx, tgUpdate("تذكر إن العميل المفضل NAM"));
  let mem = JSON.parse(state.kv.get("mem:all"));
  assert.ok(mem.some((m) => m.text.includes("NAM Consultant")));
  const ctx2 = makeCtx();
  state.geminiQueue.push({ text: 'TOOL_CALL: {"tool":"forget_memory","args":{"query":"NAM"}}' }, { text: "تم النسيان" });
  await runWebhook(env, ctx2, tgUpdate("انسى العميل المفضل"));
  mem = JSON.parse(state.kv.get("mem:all"));
  assert.ok(!mem.some((m) => m.text.includes("NAM Consultant")));
});

await t("16) /forget بالرقم يحذف الحقيقة المحددة", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/learn هدفنا الربع الجاري 10 صفقات\nنشتغل بس على واتساب بزنس"));
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/forget 1"));
  const mem = JSON.parse(state.kv.get("mem:all"));
  assert.equal(mem.length, 1);
  assert.ok(mem[0].text.includes("واتساب"));
});

await t("17) send_email يبني بطاقة موافقة بأزرار بدل الإرسال المباشر", async () => {
  const env = makeEnv({ OWNER_CHAT_ID: "1000", APPS_SCRIPT_URL: "https://script.google.com/macros/s/ABC/exec", APPS_SCRIPT_SECRET: "s" });
  const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"send_email","args":{"to":"info@namconsultant.com","subject":"عرض شراكة","body":"أهلاً…"}}' },
    { text: "الإيميل بانتظار موافقتك" }
  );
  await runWebhook(env, ctx, tgUpdate("ابعت إيميل لـ NAM Consultant بعرض الشراكة"));
  assert.equal(state.appsScript, 0, "الإيميل انرسل بدون موافقة! هذا خطأ");
  const appr = JSON.parse(state.kv.get("approvals"));
  assert.equal(appr.length, 1);
  assert.equal(appr[0].payload.to, "info@namconsultant.com");
  const card = state.sent.find((x) => x.method === "sendMessage" && x.body.reply_markup);
  assert.ok(card, "بطاقة الأزرار ما وصلت");
  assert.equal(card.body.reply_markup.inline_keyboard[0][0].callback_data, "approve:" + appr[0].id);
});

await t("18) ضغط زر ✅ يُرسل عبر Apps Script ويحفظ الحالة", async () => {
  const env = makeEnv({ OWNER_CHAT_ID: "1000", APPS_SCRIPT_URL: "https://script.google.com/macros/s/ABC/exec", APPS_SCRIPT_SECRET: "s" });
  const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"send_email","args":{"to":"info@namconsultant.com","subject":"عرض شراكة","body":"أهلاً…"}}' },
    { text: "بانتظار موافقتك" }
  );
  await runWebhook(env, ctx, tgUpdate("ابعت الإيميل"));
  const appr = JSON.parse(state.kv.get("approvals"))[0];
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, { callback_query: { id: "cbq1", data: "approve:" + appr.id, from: { id: 42 }, message: { chat: { id: 1000 }, message_id: 555 } } });
  assert.equal(state.appsScript, 1, "Apps Script ما انادى");
  const edited = state.sent.find((x) => x.method === "editMessageText");
  assert.ok(edited && edited.body.text.includes("أُرسل"));
  assert.equal(JSON.parse(state.kv.get("approvals")).length, 0, "الموافقة ما اختفت من الطابور");
});

await t("19) ضغط زر ❌ يلغي بدون إرسال لأي جهة", async () => {
  const env = makeEnv({ OWNER_CHAT_ID: "1000", APPS_SCRIPT_URL: "https://script.google.com/macros/s/ABC/exec", APPS_SCRIPT_SECRET: "s" });
  const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"send_email","args":{"to":"a@b.com","subject":"s","body":"b"}}' },
    { text: "بانتظار موافقتك" }
  );
  await runWebhook(env, ctx, tgUpdate("ابعت إيميل"));
  const appr = JSON.parse(state.kv.get("approvals"))[0];
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, { callback_query: { id: "cbq2", data: "cancel:" + appr.id, from: { id: 42 }, message: { chat: { id: 1000 }, message_id: 556 } } });
  assert.equal(state.appsScript, 0);
  assert.equal(JSON.parse(state.kv.get("approvals")).length, 0);
});
await t("20) /arena بدون ARENA_BRIDGE_URL يعطي تعليمات وبدون أي نداء شبكة", async () => {
  const env = makeEnv();
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("جسر LMArena مو مضبوط"), "ما وصلت رسالة التعليمات");
  assert.ok(all.includes("ARENA_BRIDGE_URL"), "التعليمات ما فيها اسم المتغير");
  assert.equal(state.arenaCalls, 0, "اننادى الجسر وهو مو مضبوط!");
  assert.equal(state.fetches.filter((f) => f.url.includes("arena.test")).length, 0);
});

await t("21) /arena مع جسر مضبوط يعرض الصحة والنماذج", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_KEY: "ak" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("شغال"), "الحالة ما ظهرت");
  assert.ok(all.includes("stealth-model"), "قائمة النماذج ما وصلت");
  assert.ok(state.arenaCalls >= 1, "ما انادى /v1/models");
});

await t("22) /arena_ask يمرّر السؤال للجسر ويحفظ النموذج المختار", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test/" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena stealth-model"));
  assert.ok(sentTexts().join("\n").includes("stealth-model"), "النموذج ما انحفظ");
  assert.equal(state.kv.get("arena_model"), JSON.stringify("stealth-model"), "KV ما تخزّن النموذج");
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/arena_ask شو أخبار دبي؟"));
  const reply = sentTexts().join("\n");
  assert.ok(reply.includes("رد من Arena"), "رد الجسر ما وصل");
  assert.ok(reply.includes("stealth-model"), "اسم النموذج ما ظهر بالرد");
});

await t("23) بدون مفاتيح مزودين — جارفس يستعمل جسر Arena تلقائياً", async () => {
  const env = makeEnv({ GEMINI_API_KEY: "", OPENROUTER_API_KEY: "", ARENA_BRIDGE_URL: "https://arena.test" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("احكي لي عن دبي"));
  assert.ok(state.arenaCalls >= 1, "الجسر ما اننادى");
  assert.ok(sentTexts().join("\n").includes("رد من Arena"), "رد Arena ما وصل للمستخدم");
});

await t("24) /arena off يوقف الجسر بالكامل", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", GEMINI_API_KEY: "" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena off"));
  assert.ok(sentTexts().join("\n").includes("موقوف"), "ما وصل تأكيد الإيقاف");
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/arena_ask سؤال"));
  assert.equal(state.arenaCalls, 0, "الجسر اننادى وهو موقوف!");
  assert.ok(sentTexts().join("\n").includes("ما رد"), "المستخدم ما انطاه تنبيه");
});

await t("25) /arena wake يصحّي خدمة نايمة (503 ثم 200)", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_WAKE_GAP_MS: "1" });
  state.arenaHealthFails = 2;
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena wake"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("صحّي وشغال"), "ما وصل تأكيد الإفاقة: " + all.slice(0, 200));
  assert.ok(state.arenaCalls >= 3, "عدد محاولات /health غير كافٍ");
});

await t("26) طلب فاشل يصحّي الجسر ويعيد المحاولة تلقائياً", async () => {
  const env = makeEnv({ GEMINI_API_KEY: "", OPENROUTER_API_KEY: "", ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_WAKE_GAP_MS: "1" });
  state.arenaDown = true;
  // نجعل أول محاولة تفشل فقط ثم ترجع الخدمة
  const originalFetch = global.fetch;
  let posts = 0;
  global.fetch = async (input, init) => {
    const url = typeof input === "string" ? input : input.url;
    if (url.startsWith("https://arena.test/v1/chat/completions")) {
      posts++;
      state.arenaCalls++;
      if (posts === 1) return new Response(JSON.stringify({ error: "cold" }), { status: 503 });
      return new Response(JSON.stringify({ choices: [{ message: { role: "assistant", content: "رد بعد الإفاقة" } }] }), { status: 200, headers: { "content-type": "application/json" } });
    }
    return originalFetch(input, init);
  };
  try {
    const ctx = makeCtx();
    await runWebhook(env, ctx, tgUpdate("احكي لي عن دبي"));
  } finally {
    global.fetch = originalFetch;
  }
  assert.equal(posts, 2, "ما صار إعادة محاولة بعد الإفاقة");
  assert.ok(sentTexts().join("\n").includes("رد بعد الإفاقة"), "رد ما وصل بعد الإفاقة");
});

await t("27) Keep-alive عبر cron يضرب /health كل 10 دقائق فقط", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_KEEPALIVE: "true" });
  const ctx = makeCtx();
  const at = (min) => new Date(Date.UTC(2026, 0, 1, 12, min, 0)).getTime();
  await worker.scheduled({ scheduledTime: at(30) }, env, ctx);
  await ctx.drain();
  const hits30 = state.arenaCalls;
  assert.ok(hits30 >= 1, "Keep-alive ما ضرب على الدقيقة 30");
  reset();
  const ctx2 = makeCtx();
  await worker.scheduled({ scheduledTime: at(3) }, makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_KEEPALIVE: "true" }), ctx2);
  await ctx2.drain();
  assert.equal(state.arenaCalls, 0, "ضرب /health بدقيقة مو مضاعفة للعشرة");
});

await t("28) Keep-alive معطّل افتراضياً (بدون المتغير)", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test" });
  const ctx = makeCtx();
  await worker.scheduled({ scheduledTime: new Date(Date.UTC(2026, 0, 1, 12, 30, 0)).getTime() }, env, ctx);
  await ctx.drain();
  assert.equal(state.arenaCalls, 0, "Keep-alive شغال بدون ما نطلبه");
});

await t("29) /arena test يعرض نتيجة تشخيص المحركات", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena test"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("gpt4free:Arena"), "أسماء المحركات ما ظهرت");
  assert.ok(all.includes("1200ms"), "زمن الاستجابة ما ظهر");
  assert.ok(all.includes("في محرك شغال"), "ملخص الحالة ما ظهر");
});

await t("30) Arena أساسي افتراضياً: Gemini ما ينادى إطلاقاً", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", GEMINI_API_KEY: "gem" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("شو أخبار دبي اليوم؟"));
  assert.ok(sentTexts().join("\n").includes("رد من Arena"), "رد Arena ما وصل");
  assert.equal(state.geminiCalls, 0, "Gemini اننادى رغم أن Arena أساسي");
});

await t("31) ARENA_BRIDGE_FIRST=false يرجّع Gemini للأول", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_FIRST: "false" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("شو أخبار دبي اليوم؟"));
  assert.equal(state.geminiCalls, 1, "Gemini ما اننادى رغم إطفاء أولوية Arena");
});

await t("32) /arena primary يقلب الأولوية ويحفظها بالـ KV", async () => {
  const env = makeEnv({ ARENA_BRIDGE_URL: "https://arena.test" });
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena primary"));
  assert.equal(state.kv.get("arena_primary"), JSON.stringify(false), "القيمة ما انحفظت");
  assert.ok(sentTexts().join("\n").includes("الترتيب العادي"), "ما وصل تأكيد التبديل");
});

await t("33) قاطع الدائرة: فشل متكرر يوقف محاولات Arena مؤقتاً", async () => {
  const env = makeEnv({ GEMINI_API_KEY: "gem", ARENA_BRIDGE_URL: "https://arena.test", ARENA_BRIDGE_WAKE: "false" });
  state.arenaDown = true;
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("سؤال أول"));
  assert.ok(Number(state.kv.get("arena_skip_until")) > Date.now(), "القاطع ما انفتح");
  const before = state.arenaCalls;
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("سؤال تاني"));
  assert.equal(state.arenaCalls, before, "جرّب Arena رغم أن القاطع مفتوح");
  assert.ok(sentTexts().join("\n").includes("الجواب النهائي الافتراضي"), "ما رجع للاحتياط");
});

await t("34) إعداد الجسر بالكامل من تيليجرام (/arena url + key) بدون wrangler", async () => {
  const env = makeEnv(); // لا ARENA_BRIDGE_URL بالبيئة
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena"));
  assert.ok(sentTexts().join("\n").includes("مو مضبوط"), "المفروض يبدأ غير مضبوط");
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/arena url https://arena.test/"));
  assert.equal(state.kv.get("arena_url"), JSON.stringify("https://arena.test"), "الرابط ما انحفظ");
  const ctx3 = makeCtx();
  await runWebhook(env, ctx3, tgUpdate("/arena key ak-123"));
  assert.equal(state.kv.get("arena_key"), JSON.stringify("ak-123"), "المفتاح ما انحفظ");
  const ctx4 = makeCtx();
  await runWebhook(env, ctx4, tgUpdate("/arena_ask شو الأخبار؟"));
  assert.ok(sentTexts().join("\n").includes("رد من Arena"), "الجسر ما اننادى بعد الإعداد");
});

await t("35) /arena setup يشرح الخطوات بالعربي", async () => {
  const env = makeEnv();
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena setup"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("٣ خطوات"), "ما وصل الشرح");
  assert.ok(all.includes("/arena url"), "الشرح ما فيه أمر الرابط");
  assert.ok(all.includes("README_IPHONE_AR.md"), "ما دل على دليل الآيفون");
});

await t("36) /arena reset يمسح الإعداد من KV", async () => {
  const env = makeEnv();
  state.kv.set("arena_url", JSON.stringify("https://arena.test"));
  state.kv.set("arena_key", JSON.stringify("ak"));
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena reset"));
  assert.equal(JSON.parse(state.kv.get("arena_url")), null, "الرابط ما انمسح");
  assert.ok(sentTexts().join("\n").includes("مسحت"), "ما وصل تأكيد المسح");
});

await t("37) /arena يعرض أن العنوان محفوظ من تيليجرام", async () => {
  const env = makeEnv();
  const ctx = makeCtx();
  await runWebhook(env, ctx, tgUpdate("/arena url https://arena.test"));
  const ctx2 = makeCtx();
  await runWebhook(env, ctx2, tgUpdate("/arena"));
  assert.ok(sentTexts().join("\n").includes("محفوظ من تيليجرام"), "المصدر ما ظهر");
});

await t("38) مدير السياق يفتح مساحة ويربط كمل بنفسها", async () => {
  const env = makeEnv();
  state.geminiQueue.push({ text: "بدأت المشروع" }, { text: "كملت بنفس السياق" });
  await runWebhook(env, makeCtx(), tgUpdate("ابني متجر الزهور الجديد"));
  let rows = JSON.parse(state.kv.get("context_threads_v1"));
  assert.equal(rows.length, 1, "ما فتح مساحة");
  const id = rows[0].id;
  await runWebhook(env, makeCtx(), tgUpdate("كمل واضف الدفع"));
  rows = JSON.parse(state.kv.get("context_threads_v1"));
  assert.equal(rows.length, 1, "فتح شات جديد بدل الاستمرار");
  assert.equal(JSON.parse(state.kv.get("active_context_thread_v1")), id);
});

await t("39) موضوع جديد ينفصل ويمكن الرجوع للقديم", async () => {
  const env = makeEnv();
  state.geminiQueue.push({ text: "أ" }, { text: "ب" });
  await runWebhook(env, makeCtx(), tgUpdate("مشروع جديد حملة مطعم دمشق"));
  await runWebhook(env, makeCtx(), tgUpdate("مشروع جديد تطبيق العقارات"));
  let rows = JSON.parse(state.kv.get("context_threads_v1"));
  assert.equal(rows.length, 2, "المشروعين اختلطوا");
  await runWebhook(env, makeCtx(), tgUpdate("/chat 2"));
  assert.equal(JSON.parse(state.kv.get("active_context_thread_v1")), rows[1].id, "ما رجع للشات القديم");
});

await t("40) /chats و/progress يعرضان المساحات والتقدم", async () => {
  const env = makeEnv();
  state.geminiQueue.push({ text: "جاهز" });
  await runWebhook(env, makeCtx(), tgUpdate("جهز خطة إطلاق المنتج"));
  await runWebhook(env, makeCtx(), tgUpdate("/chats"));
  await runWebhook(env, makeCtx(), tgUpdate("/progress"));
  const out = sentTexts().join("\n");
  assert.ok(out.includes("مساحات العمل"));
  assert.ok(out.includes("آخر سياق"));
});

console.log(`\n${passed}/40 اختبارات ناجحة`);
process.exit(process.exitCode || 0);
