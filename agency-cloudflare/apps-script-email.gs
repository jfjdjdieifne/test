/**
 * آلة إرسال إيميل جارفس — تُنشر كـ Web App مربوطة بحساب Gmail مالتك
 * ------------------------------------------------------------------
 * خطوات التركيب (5 دقائق — مجاني 100% من جوجل):
 * 1. افتح https://script.google.com → New project → سمّه "jarvis-email"
 * 2. احذف الكود الفاضي والصق هذا الملف كاملاً
 * 3. غيّر SECRET بالأسفل — اجعلها نفس قيمة APPS_SCRIPT_SECRET اللي راح تحطها بـ wrangler
 * 4. زر Deploy → New deployment → النوع: Web app
 *      - Execute as: Me
 *      - Who has access: Anyone
 *    → Deploy → انسخ رابط /exec الناتج
 * 5. بالطرفال عندك:
 *      npx wrangler secret put APPS_SCRIPT_URL     # رابط /exec
 *      npx wrangler secret put APPS_SCRIPT_SECRET  # نفس SECRET بالأعلى
 *      npx wrangler deploy
 * 6. فعّل الأزرار بالبوت (مرة واحدة):
 *      curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<SUBDOMAIN>.workers.dev/webhook"
 *    (بدون allowed_updates حتى توصل تحديثات callback_query تلقائياً)
 *
 * حصص جوجل المجانية: ~100 إيميل يومياً لحسابات Gmail العادية (1500 لـ Workspace).
 * لماذا الموافقة بضغطة واحدة لكل إيميل؟ لأن الإرسال الآلي الجماعي يقتل حسابك (spam) — وهذا حمايتك قبل فائدتك.
 */

const SECRET = "ضع-نفس-قيمة-APPS_SCRIPT_SECRET-هنا";

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    if (!SECRET || SECRET.indexOf("ضع-نفس") === 0) return jsonOut({ ok: false, error: "عيّن SECRET داخل السكربت أولاً" });
    if (data.secret !== SECRET) return jsonOut({ ok: false, error: "unauthorized" });

    if (data.action === "send_email") {
      const to = String(data.to || "").trim();
      const subject = String(data.subject || "").slice(0, 200);
      const body = String(data.body || "").slice(0, 8000);
      if (!to || !subject) return jsonOut({ ok: false, error: "to/subject مطلوبين" });
      GmailApp.sendEmail(to, subject, body, { name: "JARVIS" });
      return jsonOut({ ok: true });
    }

    // اختياري: قراءة آخر رسائل (غير موصولة بأي أداة بالبوت حالياً — للتوسع لاحقاً)
    if (data.action === "list_emails") {
      const threads = GmailApp.search("newer_than:7d", 0, 5);
      const out = threads.map(function (t) {
        const m = t.getMessages()[0];
        return { subject: t.getFirstMessageSubject(), from: m.getFrom(), date: String(t.getLastMessageDate()) };
      });
      return jsonOut({ ok: true, emails: out });
    }

    return jsonOut({ ok: false, error: "unknown action" });
  } catch (err) {
    return jsonOut({ ok: false, error: String(err) });
  }
}

function jsonOut(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
