/**
 * J.A.R.V.I.S 24/7 Serverless Cloudflare Worker + Static Assets Gateway ($0/month)
 * =================================================================================
 * Runs on Cloudflare Workers Free Plan:
 *   - 100,000 requests/day, 0 cold-sleep, no credit card required
 *   - Serves agency/ static HTML apps (jarvis.html, index.html, demos/) for free
 *   - Receives Telegram Bot Webhook (/telegram-webhook) for 24/7 text + voice chat
 *   - Multi-LLM failover: Gemini -> Mistral (~1B/mo free) -> Groq -> NVIDIA NIM -> OpenRouter
 *   - Voice transcription: Groq Whisper (whisper-large-v3-turbo) -> Gemini 2.5 Flash audio
 *   - Voice reply (optional): Groq Orpheus Arabic Saudi / English TTS (safe fallback to text)
 *   - Cron Trigger (* * * * *): Executes queued background tasks & due reminders every minute
 *   - Persistent memory/tasks via private GitHub Gist (GITHUB_GIST_ID + GITHUB_TOKEN)
 */

const BASE_TOOLS_DOC = `Available tools (to call one, reply ONLY with raw valid JSON: {"tool":"<name>","args":{...}}):
1. web_search: {"query":"...","max_results":5} -> searches live internet (Tavily / DuckDuckGo).
2. audit_website: {"url":"https://..."} -> inspects a live site for broken # CTAs, broken wa.me links, emails, tel links, 0+ counters, Arabic support.
3. list_leads: {"limit":12,"status_filter":""} -> reads Dubai high-ticket prospects CSV.
4. update_lead: {"business_name":"...","status":"sent|interested|won|new","note":"..."} -> saves CRM status (requires Gist configured).
5. save_memory: {"key":"...","value":"..."} -> stores long-term memory in Gist.
6. get_memories: {} -> reads stored memories.
7. schedule_reminder: {"minutes_from_now":60,"message":"...","call_me":true} -> schedules reminder & optional Telegram CallMeBot ring.
8. call_me_now: {"message":"..."} -> immediately rings user on Telegram via CallMeBot (short English ASCII <=240 chars).
9. list_tasks: {} -> lists recent background tasks.`;

const SYSTEM_PROMPT = `You are J.A.R.V.I.S, a 24/7 autonomous AI assistant working at $0 cost.
Reply primarily in clear, crisp Arabic (or English if the user writes in English).
${BASE_TOOLS_DOC}
10. start_background_task: {"goal":"...","call_when_done":true} -> queues a multi-step background mission processed by the 1-minute scheduler and rings user when finished (requires Gist; if unavailable, run tools directly right now).

Once you have the facts needed, answer directly in clean plain text without JSON.`;

const WORKER_PROMPT = `You are J.A.R.V.I.S Background Worker executing a queued autonomous mission step by step.
${BASE_TOOLS_DOC}
Use tools to gather facts and audit sites, then write a concise final Arabic report. If user approval is required, explain clearly and invoke call_me_now.`;

// ---------------------------------------------------------------------------
// Security & Encoding Helpers
// ---------------------------------------------------------------------------
async function deriveWebhookSecret(env) {
  if (env.WEBHOOK_SECRET && env.WEBHOOK_SECRET.trim()) {
    return env.WEBHOOK_SECRET.trim().replace(/[^A-Za-z0-9_-]/g, "_").slice(0, 64);
  }
  const seed = `${env.TELEGRAM_BOT_TOKEN || ""}:${env.ALLOWED_TELEGRAM_ID || ""}:jarvis_cf_v1`;
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(seed));
  const hex = [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `jv_${hex.slice(0, 40)}`;
}

function constantTimeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function bytesToBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

function escapeHtml(s) {
  return String(s || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---------------------------------------------------------------------------
// Persistent Cloud State (GitHub Gist — $0, unlimited)
// ---------------------------------------------------------------------------
function defaultState() {
  return { memories: {}, reminders: [], history: [], lead_notes: {}, tasks: [] };
}

async function loadState(env) {
  if (!env.GITHUB_GIST_ID || !env.GITHUB_TOKEN) {
    return { state: defaultState(), persistent: false };
  }
  try {
    const res = await fetch(`https://api.github.com/gists/${env.GITHUB_GIST_ID.trim()}`, {
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN.trim()}`,
        Accept: "application/vnd.github+json",
        "User-Agent": "Jarvis-CF-Worker/1.0",
      },
    });
    if (!res.ok) return { state: defaultState(), persistent: false };
    const data = await res.json();
    const raw = data?.files?.["jarvis_state.json"]?.content;
    if (!raw) return { state: defaultState(), persistent: true };
    const parsed = JSON.parse(raw);
    return { state: { ...defaultState(), ...parsed }, persistent: true };
  } catch {
    return { state: defaultState(), persistent: false };
  }
}

async function saveState(env, state) {
  if (!env.GITHUB_GIST_ID || !env.GITHUB_TOKEN) return false;
  try {
    const res = await fetch(`https://api.github.com/gists/${env.GITHUB_GIST_ID.trim()}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN.trim()}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Jarvis-CF-Worker/1.0",
      },
      body: JSON.stringify({
        files: { "jarvis_state.json": { content: JSON.stringify(state, null, 2) } },
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// CSV, Website Auditor & Search Parsers (CPU-safe < 3ms)
// ---------------------------------------------------------------------------
export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  const clean = String(text || "").replace(/^\uFEFF/, "");
  for (let i = 0; i < clean.length; i++) {
    const ch = clean[i];
    if (inQuotes) {
      if (ch === '"' && clean[i + 1] === '"') {
        field += '"';
        i++;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field);
      if (row.some((c) => c.trim() !== "")) rows.push(row);
      row = [];
      field = "";
    } else if (ch !== "\r") {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    if (row.some((c) => c.trim() !== "")) rows.push(row);
  }
  if (rows.length < 2) return [];
  const headers = rows[0].map((h) => h.trim());
  return rows.slice(1).map((r) => {
    const obj = {};
    headers.forEach((h, idx) => {
      obj[h] = (r[idx] || "").trim();
    });
    return obj;
  });
}

export function auditHtml(url, rawHtml) {
  const htmlSlice = String(rawHtml || "").slice(0, 140000);
  const titleMatch = htmlSlice.match(/<title[^>]*>([\s\S]{0,200}?)<\/title>/i);
  const title = titleMatch ? titleMatch[1].replace(/\s+/g, " ").trim() : "";

  const h1s = [];
  const h1Re = /<h1[^>]*>([\s\S]{0,200}?)<\/h1>/gi;
  let m;
  while ((m = h1Re.exec(htmlSlice)) && h1s.length < 5) {
    const txt = m[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    if (txt) h1s.push(txt);
  }

  const deadHashCtas = [];
  const waLinks = [];
  const brokenWaLinks = [];
  const telLinks = [];
  const linkRe = /<a\b[^>]*href\s*=\s*["']([^"']{1,300})["'][^>]*>([\s\S]{0,160}?)<\/a>/gi;
  let linksChecked = 0;
  while ((m = linkRe.exec(htmlSlice)) && linksChecked < 250) {
    linksChecked++;
    const href = m[1].trim();
    const label = m[2].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim().slice(0, 60);
    const low = href.toLowerCase();
    if ((href === "#" || href === "/#" || href === "/en/#" || low.endsWith("/#")) && label && deadHashCtas.length < 8) {
      deadHashCtas.push({ text: label, href });
    }
    if (low.includes("wa.me/") || low.includes("whatsapp.com/send")) {
      if (waLinks.length < 6) waLinks.push(href);
      if ((low.includes("wa.me/00") || low.includes("wa.me/+") || low.includes("%20") || href.includes(" ")) && brokenWaLinks.length < 6) {
        brokenWaLinks.push(href);
      }
    }
    if (low.startsWith("tel:") && telLinks.length < 6) {
      telLinks.push(href);
    }
  }

  const emails = [...new Set((htmlSlice.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,12}/g) || []).slice(0, 12))].slice(0, 6);
  const bodyText = htmlSlice
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const zeroCounters = (bodyText.match(/(?:0\+|Years[^0-9]{0,15}0\b|Rating[^0-9]{0,10}0\b)/gi) || []).slice(0, 6);
  const hasArabic = /[\u0600-\u06FF]/.test(bodyText);

  return {
    url,
    title,
    h1: h1s,
    has_arabic_content: hasArabic,
    dead_hash_ctas: deadHashCtas,
    whatsapp_links: waLinks,
    broken_whatsapp_links: brokenWaLinks,
    tel_links: telLinks,
    emails_found: emails,
    suspicious_zero_counters: zeroCounters,
    snippet: bodyText.slice(0, 650),
  };
}

export function parseDuckDuckGoHtml(rawHtml, maxResults = 5) {
  const slice = String(rawHtml || "").slice(0, 160000);
  const results = [];
  const aRe = /<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]{0,200}?)<\/a>/gi;
  const sRe = /class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]{0,400}?)<\/(?:a|div)>/gi;
  const titles = [];
  let m;
  while ((m = aRe.exec(slice)) && titles.length < maxResults) {
    let href = m[1].replace(/&amp;/g, "&");
    if (href.includes("uddg=")) {
      try {
        const u = new URL(href.startsWith("http") ? href : `https://duckduckgo.com${href}`);
        const target = u.searchParams.get("uddg");
        if (target) href = target;
      } catch {}
    }
    const title = m[2].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
    titles.push({ title, url: href, snippet: "" });
  }
  let idx = 0;
  while ((m = sRe.exec(slice)) && idx < titles.length) {
    titles[idx].snippet = m[1].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim().slice(0, 280);
    idx++;
  }
  return titles;
}

// ---------------------------------------------------------------------------
// Autonomous Tools
// ---------------------------------------------------------------------------
async function toolListLeads(env, state, limit = 12, statusFilter = "") {
  if (!env.ASSETS) return { error: "Static assets binding unavailable" };
  const res = await env.ASSETS.fetch("https://assets.local/dubai_high_ticket_leads.csv");
  if (!res.ok) return { error: `CSV load status ${res.status}` };
  const rows = parseCsv(await res.text());
  const notes = state.lead_notes || {};
  const filtered = rows
    .map((r) => {
      const name = r.Company || r["Business Name"] || r.name || "";
      const st = notes[name]?.status || "new";
      return { ...r, local_status: st };
    })
    .filter((r) => !statusFilter || r.local_status === statusFilter);
  return { total: filtered.length, leads: filtered.slice(0, Math.max(1, Math.min(limit, 25))) };
}

async function toolAuditWebsite(url) {
  let parsed;
  try {
    parsed = new URL(String(url || "").trim());
  } catch {
    return { error: "Invalid URL. Must start with http:// or https://" };
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    return { error: "Invalid scheme." };
  }
  const host = parsed.hostname.toLowerCase();
  if (
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "0.0.0.0" ||
    host === "::1" ||
    host.startsWith("10.") ||
    host.startsWith("192.168.") ||
    host.startsWith("169.254.")
  ) {
    return { error: "Refused local/private host." };
  }
  try {
    const res = await fetch(parsed.toString(), {
      headers: { "User-Agent": "Mozilla/5.0 (compatible; JarvisAuditor/2.0)" },
      redirect: "follow",
    });
    const html = await res.text();
    return { http_status: res.status, ...auditHtml(res.url, html) };
  } catch (e) {
    return { error: `Fetch failed: ${e.message}` };
  }
}

async function toolWebSearch(env, query, maxResults = 5) {
  const q = String(query || "").trim();
  if (!q) return { error: "Empty query" };
  if (env.TAVILY_API_KEY) {
    try {
      const res = await fetch("https://api.tavily.com/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: env.TAVILY_API_KEY.trim(), query: q, max_results: maxResults }),
      });
      if (res.ok) {
        const data = await res.json();
        return {
          source: "tavily",
          results: (data.results || []).map((r) => ({
            title: r.title,
            url: r.url,
            snippet: String(r.content || "").slice(0, 320),
          })),
        };
      }
    } catch {}
  }
  try {
    const res = await fetch("https://html.duckduckgo.com/html/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
      },
      body: new URLSearchParams({ q }),
    });
    if (res.ok) {
      return { source: "duckduckgo", results: parseDuckDuckGoHtml(await res.text(), maxResults) };
    }
    return { error: `Search HTTP ${res.status}` };
  } catch (e) {
    return { error: `Search failed: ${e.message}` };
  }
}

async function triggerCallMeBot(env, text) {
  const user = (env.CALLMEBOT_TELEGRAM_USER || "").trim();
  if (!user) return { ok: false, error: "CALLMEBOT_TELEGRAM_USER is not set in Cloudflare Secrets." };
  const clean = String(text || "Jarvis needs your attention on Telegram").replace(/\s+/g, " ").trim().slice(0, 240);
  const url = `https://api.callmebot.com/start.php?user=${encodeURIComponent(user)}&text=${encodeURIComponent(clean)}&lang=en-US-Standard-B&rpt=2&cc=yes`;
  try {
    const res = await fetch(url);
    return { ok: res.ok, status: res.status, body: (await res.text()).slice(0, 160) };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

async function dispatchTool(name, args, ctxObj) {
  const { env, stateObj, allowBg } = ctxObj;
  const st = stateObj.state;

  if (name === "list_leads") return toolListLeads(env, st, Number(args.limit || 12), String(args.status_filter || ""));
  if (name === "audit_website") return toolAuditWebsite(args.url);
  if (name === "web_search") return toolWebSearch(env, args.query, Number(args.max_results || 5));
  if (name === "call_me_now") return triggerCallMeBot(env, args.message);

  if (name === "update_lead") {
    st.lead_notes[String(args.business_name || "")] = {
      status: String(args.status || "sent"),
      note: String(args.note || ""),
      updated_at: new Date().toISOString(),
    };
    const saved = await saveState(env, st);
    return { ok: true, persisted: saved, business_name: args.business_name };
  }
  if (name === "save_memory") {
    st.memories[String(args.key || "").trim()] = { value: String(args.value || "").trim(), saved_at: new Date().toISOString() };
    const saved = await saveState(env, st);
    return { ok: true, persisted: saved, key: args.key };
  }
  if (name === "get_memories") return st.memories || {};
  if (name === "list_tasks") return { tasks: (st.tasks || []).slice(-10) };

  if (name === "schedule_reminder") {
    const mins = Math.max(0.5, Number(args.minutes_from_now || 60));
    const dueTs = Date.now() + mins * 60000;
    st.reminders.push({
      id: `rem_${Date.now()}`,
      due_ts: dueTs,
      message: String(args.message || "").trim(),
      call_me: Boolean(args.call_me),
      done: false,
    });
    const saved = await saveState(env, st);
    return { ok: true, persisted: saved, due_iso: new Date(dueTs).toISOString(), note: saved ? "Scheduled" : "Add GITHUB_GIST_ID & GITHUB_TOKEN for persistent reminders" };
  }

  if (name === "start_background_task") {
    if (!allowBg) return { error: "Already inside background execution" };
    if (!stateObj.persistent) {
      return {
        error: "Cloud Gist storage (GITHUB_GIST_ID + GITHUB_TOKEN) not configured yet — execute the research tools directly now instead of queuing!",
      };
    }
    const taskId = `task_${Math.floor(Date.now() / 1000) % 100000}`;
    st.tasks.push({
      id: taskId,
      goal: String(args.goal || "").trim(),
      status: "queued",
      call_when_done: args.call_when_done !== false,
      created_at: new Date().toISOString(),
    });
    st.tasks = st.tasks.slice(-20);
    await saveState(env, st);
    return { ok: true, task_id: taskId, status: "queued_for_1min_cron" };
  }

  return { error: `Unknown tool: ${name}` };
}

// ---------------------------------------------------------------------------
// 5-Provider Free LLM Router
// ---------------------------------------------------------------------------
async function callGemini(env, messages, systemPrompt, model) {
  if (!env.GEMINI_API_KEY) return null;
  const convo = messages.map((m) => `${m.role.toUpperCase()}: ${m.content}`).join("\n\n");
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(env.GEMINI_API_KEY.trim())}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: systemPrompt }] },
      contents: [{ role: "user", parts: [{ text: convo }] }],
      generationConfig: { temperature: 0.4 },
    }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data?.candidates?.[0]?.content?.parts?.[0]?.text || null;
}

async function callOpenAICompat(url, key, model, messages, systemPrompt, extraHeaders = {}) {
  if (!key) return null;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key.trim()}`,
      "Content-Type": "application/json",
      ...extraHeaders,
    },
    body: JSON.stringify({
      model,
      messages: [{ role: "system", content: systemPrompt }, ...messages],
      temperature: 0.4,
    }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data?.choices?.[0]?.message?.content || null;
}

async function askFreeLlm(env, messages, systemPrompt = SYSTEM_PROMPT) {
  const gModel = (env.GEMINI_MODEL || "gemini-2.5-flash").trim();
  const mModel = (env.MISTRAL_MODEL || "mistral-large-latest").trim();
  const attempts = [
    () => callGemini(env, messages, systemPrompt, gModel),
    () => (gModel !== "gemini-2.5-flash" ? callGemini(env, messages, systemPrompt, "gemini-2.5-flash") : null),
    () => callOpenAICompat("https://api.mistral.ai/v1/chat/completions", env.MISTRAL_API_KEY, mModel, messages, systemPrompt),
    () => (mModel !== "mistral-small-latest" ? callOpenAICompat("https://api.mistral.ai/v1/chat/completions", env.MISTRAL_API_KEY, "mistral-small-latest", messages, systemPrompt) : null),
    () => callOpenAICompat("https://api.groq.com/openai/v1/chat/completions", env.GROQ_API_KEY, (env.GROQ_MODEL || "llama-3.3-70b-versatile").trim(), messages, systemPrompt),
    () => callOpenAICompat("https://integrate.api.nvidia.com/v1/chat/completions", env.NVIDIA_API_KEY, (env.NVIDIA_MODEL || "meta/llama-3.3-70b-instruct").trim(), messages, systemPrompt),
    () => callOpenAICompat("https://openrouter.ai/api/v1/chat/completions", env.OPENROUTER_API_KEY, "openrouter/free", messages, systemPrompt, { "X-Title": "Jarvis CF 24/7" }),
  ];
  for (const fn of attempts) {
    try {
      const out = await fn();
      if (out && out.trim()) return out.trim();
    } catch {}
  }
  return "لم ينجح أي مزود ذكاء — تأكد من إضافة أحد المفاتيح المجانية (GEMINI_API_KEY / MISTRAL_API_KEY / GROQ_API_KEY / NVIDIA_API_KEY / OPENROUTER_API_KEY) في Cloudflare Variables & Secrets.";
}

export function extractToolCall(text) {
  let clean = String(text || "").trim();
  if (clean.startsWith("```")) {
    clean = clean.replace(/^```(?:json)?\s*|\s*```$/g, "").trim();
  }
  if (!(clean.startsWith("{") && clean.endsWith("}"))) return null;
  try {
    const obj = JSON.parse(clean);
    if (obj && typeof obj === "object" && typeof obj.tool === "string") return obj;
  } catch {}
  return null;
}

// ---------------------------------------------------------------------------
// Voice STT & TTS ($0)
// ---------------------------------------------------------------------------
async function transcribeTelegramAudio(env, fileId) {
  const token = env.TELEGRAM_BOT_TOKEN.trim();
  const infoRes = await fetch(`https://api.telegram.org/bot${token}/getFile?file_id=${encodeURIComponent(fileId)}`);
  const info = await infoRes.json();
  const filePath = info?.result?.file_path;
  if (!filePath) return null;

  const audioRes = await fetch(`https://api.telegram.org/file/bot${token}/${filePath}`);
  if (!audioRes.ok) return null;
  const audioBuf = new Uint8Array(await audioRes.arrayBuffer());

  if (env.GROQ_API_KEY) {
    try {
      const form = new FormData();
      form.append("file", new Blob([audioBuf], { type: "audio/ogg" }), "voice.ogg");
      form.append("model", "whisper-large-v3-turbo");
      const r = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
        method: "POST",
        headers: { Authorization: `Bearer ${env.GROQ_API_KEY.trim()}` },
        body: form,
      });
      if (r.ok) {
        const d = await r.json();
        if (d.text && d.text.trim()) return d.text.trim();
      }
    } catch {}
  }

  if (env.GEMINI_API_KEY) {
    try {
      const b64 = bytesToBase64(audioBuf);
      const r = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${encodeURIComponent(env.GEMINI_API_KEY.trim())}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{
              role: "user",
              parts: [
                { text: "Transcribe this voice note verbatim in its original language (Arabic or English). Output ONLY the transcription." },
                { inlineData: { mimeType: "audio/ogg", data: b64 } },
              ],
            }],
          }),
        }
      );
      if (r.ok) {
        const d = await r.json();
        return d?.candidates?.[0]?.content?.parts?.[0]?.text?.trim() || null;
      }
    } catch {}
  }
  return null;
}

async function tryGroqTtsAudio(env, text) {
  if (!env.GROQ_API_KEY || String(env.ENABLE_VOICE_REPLIES || "true").toLowerCase() !== "true") return null;
  const clean = String(text || "").replace(/[*_`#<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, 190);
  if (!clean) return null;
  const hasArabic = /[\u0600-\u06FF]/.test(clean);
  const model = hasArabic ? "canopylabs/orpheus-arabic-saudi" : "canopylabs/orpheus-v1-english";
  const voice = hasArabic ? "fahad" : "troy";
  try {
    const res = await fetch("https://api.groq.com/openai/v1/audio/speech", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GROQ_API_KEY.trim()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model, voice, input: clean, response_format: "wav" }),
    });
    if (!res.ok) return null;
    return new Uint8Array(await res.arrayBuffer());
  } catch {
    return null;
  }
}

async function tgSend(env, chatId, text, wantVoice = false) {
  const token = env.TELEGRAM_BOT_TOKEN.trim();
  const full = String(text || "");
  for (let i = 0; i < full.length; i += 3900) {
    await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text: full.slice(i, i + 3900) }),
    });
  }
  if (wantVoice) {
    const wav = await tryGroqTtsAudio(env, full);
    if (wav && wav.length > 200) {
      const form = new FormData();
      form.append("chat_id", String(chatId));
      form.append("title", "JARVIS");
      form.append("audio", new Blob([wav], { type: "audio/wav" }), "jarvis.wav");
      await fetch(`https://api.telegram.org/bot${token}/sendAudio`, { method: "POST", body: form });
    }
  }
}

// ---------------------------------------------------------------------------
// Agent Turn & Cron Background Runner
// ---------------------------------------------------------------------------
async function runAgentTurn(env, chatId, userText, isVoice) {
  const stateObj = await loadState(env);
  const st = stateObj.state;
  const memPrefix = Object.keys(st.memories || {}).length
    ? `[Saved Memories: ${JSON.stringify(st.memories)}]\n`
    : "";
  const msgs = [...(st.history || []).slice(-8), { role: "user", content: memPrefix + userText }];

  let finalReply = "";
  for (let step = 0; step < 4; step++) {
    const reply = await askFreeLlm(env, msgs, SYSTEM_PROMPT);
    const toolCall = extractToolCall(reply);
    if (!toolCall) {
      finalReply = reply;
      break;
    }
    const res = await dispatchTool(toolCall.tool, toolCall.args || {}, { env, stateObj, allowBg: true });
    msgs.push({ role: "assistant", content: reply });
    msgs.push({
      role: "user",
      content: `[TOOL RESULT for ${toolCall.tool}]: ${JSON.stringify(res).slice(0, 5500)}\nNow give a helpful Arabic answer (or invoke the next tool).`,
    });
  }
  if (!finalReply) finalReply = await askFreeLlm(env, msgs, SYSTEM_PROMPT);

  st.history = [...(st.history || []), { role: "user", content: userText }, { role: "assistant", content: finalReply }].slice(-16);
  await saveState(env, st);
  await tgSend(env, chatId, finalReply, isVoice);
}

async function handleTelegramUpdate(update, env) {
  const msg = update?.message;
  if (!msg || !env.TELEGRAM_BOT_TOKEN || !env.ALLOWED_TELEGRAM_ID) return;
  const chatId = msg.chat?.id;
  const fromId = String(msg.from?.id || "");
  if (!chatId || fromId !== env.ALLOWED_TELEGRAM_ID.trim()) return;

  let text = String(msg.text || "").trim();
  let isVoice = false;
  const voiceObj = msg.voice || msg.audio;

  if (voiceObj) {
    isVoice = true;
    const transcript = await transcribeTelegramAudio(env, voiceObj.file_id);
    if (!transcript) {
      await tgSend(env, chatId, "لم أتمكن من تفريغ الرسالة الصوتية — أضف GROQ_API_KEY أو GEMINI_API_KEY في Cloudflare Secrets.");
      return;
    }
    text = transcript;
    await tgSend(env, chatId, `🎙️ سمعتك: «${text}»`);
  }

  if (!text) return;

  if (text === "/start") {
    await tgSend(
      env,
      chatId,
      "أهلاً بك! أنا جارفس (نسخة Cloudflare 24/7 المجانية). أرسل لي نصاً أو رسالة صوتية: أستطيع البحث بالويب، فحص المواقع، قراءة عملاء دبي، العمل بالخلفية (/tasks)، والاتصال بك عبر تيليجرام.",
      false
    );
    return;
  }

  if (text === "/tasks") {
    const { state } = await loadState(env);
    const list = (state.tasks || []).slice(-6);
    const body = list.length
      ? "📋 آخر المهام:\n" + list.map((t) => `• ${t.id} [${t.status}]: ${t.goal.slice(0, 80)}`).join("\n")
      : "لا توجد مهام مسجلة بعد.";
    await tgSend(env, chatId, body);
    return;
  }

  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN.trim()}/sendChatAction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, action: "typing" }),
  });

  await runAgentTurn(env, chatId, text, isVoice);
}

async function runScheduledTick(env) {
  if (!env.TELEGRAM_BOT_TOKEN || !env.ALLOWED_TELEGRAM_ID || !env.GITHUB_GIST_ID || !env.GITHUB_TOKEN) return;
  const stateObj = await loadState(env);
  if (!stateObj.persistent) return;
  const st = stateObj.state;
  const chatId = env.ALLOWED_TELEGRAM_ID.trim();
  let dirty = false;

  // 1. Due Reminders
  const now = Date.now();
  for (const rem of st.reminders || []) {
    if (!rem.done && Number(rem.due_ts || 0) <= now) {
      rem.done = true;
      dirty = true;
      await tgSend(env, chatId, `⏰ تذكير من جارفس:\n${rem.message}`, true);
      if (rem.call_me) await triggerCallMeBot(env, `Jarvis reminder: ${rem.message}`);
    }
  }

  // 2. Process 1 queued/running background task per minute tick
  const task = (st.tasks || []).find((t) => t.status === "queued" || t.status === "running");
  if (task) {
    task.status = "running";
    dirty = true;
    const msgs = task.messages && task.messages.length
      ? task.messages
      : [{ role: "user", content: `[BACKGROUND MISSION ${task.id}]\nMemories: ${JSON.stringify(st.memories || {})}\nGoal: ${task.goal}` }];

    let report = "";
    let finished = false;
    for (let i = 0; i < 3; i++) {
      const reply = await askFreeLlm(env, msgs, WORKER_PROMPT);
      const tc = extractToolCall(reply);
      if (!tc) {
        report = reply;
        finished = true;
        break;
      }
      const res = await dispatchTool(tc.tool, tc.args || {}, { env, stateObj, allowBg: false });
      msgs.push({ role: "assistant", content: reply });
      msgs.push({ role: "user", content: `[TOOL RESULT for ${tc.tool}]: ${JSON.stringify(res).slice(0, 5500)}` });
    }
    if (!finished) {
      task.step_count = (task.step_count || 0) + 1;
      if (task.step_count >= 2) {
        report = await askFreeLlm(env, [...msgs, { role: "user", content: "Summarize all findings cleanly in Arabic now." }], WORKER_PROMPT);
        finished = true;
      } else {
        task.messages = msgs.slice(-8);
      }
    }
    if (finished) {
      task.status = "done";
      task.finished_at = new Date().toISOString();
      delete task.messages;
      await tgSend(env, chatId, `🤖 انتهت مهمة الخلفية (${task.id}):\n${task.goal}\n\n${report}`, true);
      if (task.call_when_done) await triggerCallMeBot(env, `Jarvis finished task ${task.id}. Open Telegram for report.`);
    }
  }

  if (dirty) await saveState(env, st);
}

// ---------------------------------------------------------------------------
// Setup Page HTML (/setup)
// ---------------------------------------------------------------------------
function renderSetupHtml(env, origin) {
  const checks = [
    ["TELEGRAM_BOT_TOKEN", Boolean(env.TELEGRAM_BOT_TOKEN), "مطلوب — توكن البوت من @BotFather"],
    ["ALLOWED_TELEGRAM_ID", Boolean(env.ALLOWED_TELEGRAM_ID), "مطلوب — رقم حسابك من @userinfobot للحماية"],
    ["GEMINI_API_KEY", Boolean(env.GEMINI_API_KEY), "مجاني بدون بطاقة (aistudio.google.com)"],
    ["MISTRAL_API_KEY", Boolean(env.MISTRAL_API_KEY), "مجاني ~1 مليار توكن/شهر (console.mistral.ai)"],
    ["GROQ_API_KEY", Boolean(env.GROQ_API_KEY), "مجاني بدون بطاقة + تفريغ الصوت Whisper"],
    ["NVIDIA_API_KEY", Boolean(env.NVIDIA_API_KEY), "اختياري مجاني (build.nvidia.com)"],
    ["OPENROUTER_API_KEY", Boolean(env.OPENROUTER_API_KEY), "اختياري مجاني (openrouter.ai)"],
    ["CALLMEBOT_TELEGRAM_USER", Boolean(env.CALLMEBOT_TELEGRAM_USER), "اختياري — @اسمك ليتصل عليك تيليجرام"],
    ["GITHUB_GIST_ID + GITHUB_TOKEN", Boolean(env.GITHUB_GIST_ID && env.GITHUB_TOKEN), "اختياري — لحفظ الذاكرة والمهام المجدولة"],
  ];
  const rows = checks
    .map(
      ([k, ok, desc]) =>
        `<tr><td style="font-family:monospace">${escapeHtml(k)}</td><td>${ok ? '<span style="color:#22c55e;font-weight:700">✓ مضبوط</span>' : '<span style="color:#f59e0b">غير مضاف</span>'}</td><td>${escapeHtml(desc)}</td></tr>`
    )
    .join("");

  return `<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>إعداد J.A.R.V.I.S 24/7 على Cloudflare</title>
<style>
  body{font-family:system-ui,-apple-system,sans-serif;background:#07111e;color:#e6f1ff;margin:0;padding:24px;line-height:1.6}
  .box{max-width:780px;margin:auto;background:#0d1b2e;border:1px solid #1f3554;border-radius:16px;padding:24px}
  h1{margin-top:0;color:#38bdf8;font-size:24px}
  table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px}
  td,th{border-bottom:1px solid #1b2f4a;padding:10px 8px;text-align:right}
  .btn{background:#0ea5e9;color:#04121f;border:0;border-radius:10px;padding:12px 18px;font-weight:800;font-size:15px;cursor:pointer}
  input{padding:11px;border-radius:10px;border:1px solid #2b476e;background:#07111e;color:#fff;width:240px;font-size:15px}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:14px}
  .nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
  .link{color:#38bdf8;text-decoration:none;border:1px solid #1f3554;padding:8px 14px;border-radius:9px;font-size:14px}
  pre{background:#050c16;padding:12px;border-radius:10px;overflow:auto;direction:ltr;text-align:left;font-size:13px}
</style>
</head>
<body>
<div class="box">
  <h1>🤖 إعداد J.A.R.V.I.S 24/7 على Cloudflare ($0)</h1>
  <p>الخادم يعمل الآن 24/7 بدون توقف على: <code>${escapeHtml(origin)}</code></p>
  <table><thead><tr><th>المتغير</th><th>الحالة</th><th>المصدر</th></tr></thead><tbody>${rows}</tbody></table>
  <h3>خطوة الربط النهائية لتيليجرام (ضغطة واحدة):</h3>
  <p>من لوحة Cloudflare لمشروع <code>jarvis-24-7</code> افتح <b>Settings → Variables and Secrets → Add</b> وأضف <code>TELEGRAM_BOT_TOKEN</code> و <code>ALLOWED_TELEGRAM_ID</code> ومفتاح ذكاء واحد على الأقل (<code>GEMINI_API_KEY</code> أو <code>MISTRAL_API_KEY</code> أو <code>GROQ_API_KEY</code>) ثم اضغط Deploy. بعدها أدخل رقم حسابك هنا واضغط الزر:</p>
  <div class="row">
    <input id="tgId" placeholder="رقم Telegram ID (من @userinfobot)" />
    <button class="btn" onclick="bindBot()">🔗 ربط بوت تيليجرام الآن</button>
  </div>
  <pre id="out">بانتظار الضغط...</pre>
  <div class="nav">
    <a class="link" href="/">📊 فتح غرفة عمليات دبي</a>
    <a class="link" href="/jarvis.html">🎙️ فتح جارفس الصوتي بالمتصفح</a>
  </div>
</div>
<script>
async function bindBot(){
  const out = document.getElementById('out');
  const id = document.getElementById('tgId').value.trim();
  out.textContent = 'جاري ربط تيليجرام...';
  try{
    const r = await fetch('/api/set-webhook',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({telegram_id:id})});
    out.textContent = JSON.stringify(await r.json(), null, 2);
  }catch(e){ out.textContent = e.message; }
}
</script>
</body></html>`;
}

// ---------------------------------------------------------------------------
// Cloudflare Worker Entrypoint
// ---------------------------------------------------------------------------
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname === "/health" || url.pathname === "/api/health") {
      return Response.json({
        ok: true,
        status: "ok",
        mode: "cloudflare-worker",
        has_bot_token: Boolean(env.TELEGRAM_BOT_TOKEN),
        has_owner_id: Boolean(env.ALLOWED_TELEGRAM_ID),
        has_gist_memory: Boolean(env.GITHUB_GIST_ID && env.GITHUB_TOKEN),
        time: new Date().toISOString(),
      });
    }

    if (url.pathname === "/setup") {
      return new Response(renderSetupHtml(env, url.origin), {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    if (url.pathname === "/api/set-webhook" && request.method === "POST") {
      if (!env.TELEGRAM_BOT_TOKEN || !env.ALLOWED_TELEGRAM_ID) {
        return Response.json({ ok: false, error: "أضف TELEGRAM_BOT_TOKEN و ALLOWED_TELEGRAM_ID في Cloudflare Settings -> Variables and Secrets أولاً." }, { status: 400 });
      }
      let body = {};
      try {
        body = await request.json();
      } catch {}
      if (!constantTimeEqual(String(body.telegram_id || "").trim(), env.ALLOWED_TELEGRAM_ID.trim())) {
        return Response.json({ ok: false, error: "رقم Telegram ID لا يطابق ALLOWED_TELEGRAM_ID المضبوط في الخادم." }, { status: 403 });
      }
      const secret = await deriveWebhookSecret(env);
      const webhookUrl = `${url.origin}/telegram-webhook`;
      const tgRes = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN.trim()}/setWebhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: webhookUrl, secret_token: secret, allowed_updates: ["message"] }),
      });
      const tgJson = await tgRes.json();
      return Response.json({ ok: Boolean(tgJson.ok), webhook_url: webhookUrl, telegram_response: tgJson }, { status: tgJson.ok ? 200 : 502 });
    }

    if (url.pathname === "/telegram-webhook" && request.method === "POST") {
      if (!env.TELEGRAM_BOT_TOKEN || !env.ALLOWED_TELEGRAM_ID) {
        return new Response("Bot not configured", { status: 503 });
      }
      const expectedSecret = await deriveWebhookSecret(env);
      const gotSecret = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (!constantTimeEqual(gotSecret, expectedSecret)) {
        return new Response("Unauthorized", { status: 401 });
      }
      let update = null;
      try {
        update = await request.json();
      } catch {
        return new Response("Bad JSON", { status: 400 });
      }
      ctx.waitUntil(handleTelegramUpdate(update, env));
      return new Response("OK", { status: 200 });
    }

    if (env.ASSETS) {
      return env.ASSETS.fetch(request);
    }
    return new Response("Not Found", { status: 404 });
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(runScheduledTick(env));
  },
};
