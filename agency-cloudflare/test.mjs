/**
 * اختبارات JARVIS Cloudflare Worker — بدون شبكة حقيقية (شبكة وهمية مدمجة)
 * التشغيل: node test.mjs
 */
import worker from "./worker.js";
import assert from "node:assert/strict";

const state = { sent: [], fetches: [], kv: new Map(), geminiQueue: [], tavilyCalls: 0, callmebot: 0, auditHits: 0 };

function reset() {
  state.sent = []; state.fetches = []; state.kv = new Map();
  state.geminiQueue = []; state.tavilyCalls = 0; state.callmebot = 0; state.auditHits = 0;
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

await t("9) مهمة خلفية تعمل وتُرسل التقرير ورنّة CallMeBot", async () => {
  const env = makeEnv(); const ctx = makeCtx();
  state.geminiQueue.push(
    { text: 'TOOL_CALL: {"tool":"start_background_task","args":{"goal":"جهز عرض لـ NAM Consultant"}}' },
    { text: "بدأت المهمة بالخلفية" },
    { text: "تقرير التنفيذ: تم تجهيز العرض" }
  );
  await runWebhook(env, ctx, tgUpdate("جهز عرض للشركة 2 واطرشلي"));
  const all = sentTexts().join("\n");
  assert.ok(all.includes("بدأت المهمة"), "الرد الفوري ما وصل");
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

console.log(`\n${passed}/10 اختبارات ناجحة`);
process.exit(process.exitCode || 0);
