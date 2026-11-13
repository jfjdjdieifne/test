#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جارفس CEO — المدير التنفيذي على تيليجرام.
متل ما بياخد منك نص أو فويس، منفهم معناه، بيوزع المهام على وكلائه (فابل + شخصية)،
وبيقدر يعدّل نفسه ويصلح حاله.
التشغيل: ~/jarvis-ceo/run.sh (يحمّل ~/jarvis-ceo.env)
"""
import json
import os
import re
import sys
import threading
import time
import urllib.request
import urllib.error
import uuid

import db
import brain
import tools
import selfedit
import github
import gmail
import social

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

if not BOT_TOKEN:
    print("TELEGRAM_BOT_TOKEN غير موجود — حطه بـ ~/jarvis-ceo.env"); sys.exit(1)

db.ensure_agents()

UPLOAD_DIR = os.environ.get("CEO_UPLOAD_DIR", os.path.expanduser("~/jarvis-ceo-files"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
excel_sessions = {}  # chat_id -> مسار ملف إكسل مرفوع (آخر ملف ينتظر تعليمات)


# ============ طبقة التيليجرام (long-polling خفيف بلا مكتبات) ============

def tg(method, params=None, timeout=60, files=None):
    if files:
        boundary = f"----jarvis{uuid.uuid4().hex}"
        body = b""
        for name, (filename, content, ctype) in files.items():
            body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n'.encode() + content + b"\r\n"
        if params:
            for k, v in params.items():
                body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{API}/{method}", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
    else:
        data = json.dumps(params or {}).encode("utf-8")
        req = urllib.request.Request(
            f"{API}/{method}", data=data,
            headers={"Content-Type": "application/json"},
        )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        payload = json.loads(resp.read().decode("utf-8"))
        return payload.get("result")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "ignore")[:300]
        print(f"[tg:{method}] HTTP {e.code}: {err}")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[tg:{method}] {e}")
        return None


def send_text(chat_id, text, reply_markup=None):
    text = text or "…"
    chunks = [text[i:i + 3800] for i in range(0, len(text), 3800)] or ["…"]
    for n, chunk in enumerate(chunks):
        params = {"chat_id": chat_id, "text": chunk}
        if reply_markup and n == len(chunks) - 1:  # الأزرار بآخر قطعة
            params["reply_markup"] = reply_markup
        tg("sendMessage", params)

def send_voice(chat_id, path):
    with open(path, "rb") as f:
        tg("sendVoice", {"chat_id": chat_id}, files={"voice": ("voice.mp3", f.read(), "audio/mpeg")})

def send_document(chat_id, path, caption=""):
    with open(path, "rb") as f:
        tg("sendDocument", {"chat_id": chat_id, "caption": caption},
           files={"document": (os.path.basename(path), f.read(),
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

def download_file(file_id, suffix=".bin"):
    info = tg("getFile", {"file_id": file_id})
    if not info:
        return None
    path = os.path.join(UPLOAD_DIR, f"{int(time.time())}-{uuid.uuid4().hex[:6]}{suffix}")
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{info['file_path']}"
    try:
        urllib.request.urlretrieve(url, path)
        return path
    except Exception as e:  # noqa: BLE001
        print(f"download: {e}")
        return None


def approval_keyboard(draft_id):
    return {"inline_keyboard": [[
        {"text": "✅ موافق — نفذ", "callback_data": f"ok:{draft_id}"},
        {"text": "❌ كنسل", "callback_data": f"no:{draft_id}"},
    ]]}


# ============ المسودات (موافقة بضغطة قبل أي إرسال) ============

def save_draft(kind, payload):
    draft_id = uuid.uuid4().hex[:10]
    payload = dict(payload)
    payload["kind"] = kind
    db.kv_set(f"draft:{draft_id}", json.dumps(payload, ensure_ascii=False))
    return draft_id

def load_draft(draft_id):
    raw = db.kv_get(f"draft:{draft_id}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def delete_draft(draft_id):
    db.kv_set(f"draft:{draft_id}", "")

def auto_send():
    return db.kv_get("auto_send", "0") == "1"


# ============ من هو الدكتور (قفل المحادثة لرقم واحد) ============

def ceo_chat_id():
    forced = os.environ.get("CEO_CHAT_ID")
    if forced:
        return int(forced)
    v = db.kv_get("ceo_chat_id")
    return int(v) if v else None


def claim_or_check(chat_id):
    forced = os.environ.get("CEO_CHAT_ID")
    if forced:
        return int(chat_id) == int(forced)
    known = ceo_chat_id()
    if known is None:
        db.kv_set("ceo_chat_id", chat_id)
        return True
    return int(chat_id) == known


# ============ تجميع حقائق حقيقية قبل الرد (الأيدي) ============

URL_RE = re.compile(r"(https?://[^\s،,]+|www\.[^\s،,]+)")

def gather_facts(text):
    facts = []
    urls = URL_RE.findall(text or "")
    for u in urls[:3]:
        r = tools.check_site(u)
        if r["ok"]:
            facts.append(f"فحص الموقع {r['url']}: شغال — HTTP {r['status']} — {r['ms']}ms — العنوان: «{r['title']}»")
        else:
            facts.append(f"فحص الموقع {r['url']}: عطلان — {r['error']} ({r['ms']}ms)")
    t = text or ""
    if re.search(r"(ذهب|أونصة|أونصه|الذهب|gold)", t):
        try:
            facts.append(f"سعر أونصة الذهب الآن: {tools.gold_usd():.2f} دولار (PAX Gold)")
        except Exception:
            facts.append("تعذر جلب سعر الذهب حالياً")
    if re.search(r"(بيتكوين|بتكوين|bitcoin|btc)", t, re.I):
        try:
            facts.append(f"سعر بيتكوين الآن: {tools.crypto_usd('bitcoin'):.2f} دولار")
        except Exception:
            facts.append("تعذر جلب سعر بيتكوين حالياً")
    if re.search(r"(ايثريوم|إيثيريوم|ethereum|eth)", t, re.I):
        try:
            facts.append(f"سعر إيثيريوم الآن: {tools.crypto_usd('ethereum'):.2f} دولار")
        except Exception:
            facts.append("تعذر جلب سعر إيثيريوم حالياً")
    if re.search(r"(طقس|الجو|weather)", t):
        try:
            facts.append(f"الطقس: {tools.weather('Damascus')}")
        except Exception:
            facts.append("تعذر جلب الطقس حالياً")
    if re.search(r"(ابحث|دوّر|دور على|بحث عن)", t) and tools.TAVILY_API_KEY:
        res = tools.web_search(t)
        if res:
            facts.append("نتائج بحث:\n" + res)
    return "\n".join(facts)


# ============ العقل والوكلاء ============

AGENT_ALIASES = {"سعيد": "سعيد", "محمود": "محمود", "احمد": "أحمد", "أحمد": "أحمد", "متداول": "متداول"}

def agent_history(chat_id, agent, limit=10):
    return db.history(chat_id, agent=agent, limit=limit)


def think(chat_id, user_text, is_voice=False):
    facts = gather_facts(user_text)
    convo = db.history(chat_id, limit=12)
    convo.append({"role": "user", "content": user_text})
    if facts:
        convo[-1]["content"] += f"\n\n[معلومات حقيقية من الأدوات — استخدمها ولا تخترع أرقام]\n{facts}"

    raw = brain.chat([{"role": "system", "content": brain.system_prompt()}] + convo, temperature=0.6)
    plan = brain.extract_json(raw)
    if not plan:  # رجّع فابل نص حر — جرّبه جوب مباشرة
        return raw.strip()

    action = plan.get("action", "reply")
    if action == "delegate":
        name = AGENT_ALIASES.get(str(plan.get("agent", "")).strip(), str(plan.get("agent", "")).strip())
        task = str(plan.get("task", "")).strip() or user_text
        persona = db.agent_persona(name)
        if not persona:
            reply = f"ما عندي وكيل اسمه {name} — وكلائي: {'، '.join(a['name'] for a in db.list_agents())}"
            db.add_message(chat_id, "assistant", reply)
            return reply
        agent_msgs = [{"role": "system", "content": persona + "\nرد باللهجة الشامية، بإيجاز، واعتمد على المعلومات الحقيقية إن وُجدت."}]
        if facts:
            agent_msgs.append({"role": "user", "content": f"[معلومات حقيقية من الأدوات]\n{facts}"})
        agent_msgs += agent_history(chat_id, name, limit=8)
        agent_msgs.append({"role": "user", "content": task})
        try:
            result = brain.chat(agent_msgs, temperature=0.6, max_tokens=900)
        except brain.BrainError as e:
            result = f"(ما قدرت أحكيه هلأ: {e})"
        result = result.strip()
        db.add_message(chat_id, "agent", result, agent=name)
        db.add_task(name, task, result, status="done")
        return f"👤 {name}: {result}"

    if action == "edit_code":
        task = str(plan.get("task", "")).strip() or user_text
        return handle_self_edit(chat_id, task)

    if action == "draft_email":
        to_addr = str(plan.get("to", "")).strip()
        subject = str(plan.get("subject", "")).strip() or "بدون موضوع"
        body = str(plan.get("body", "")).strip() or str(plan.get("reply", "")).strip()
        if not to_addr:
            return "لمن بدك ابعت الإيميل؟ اكتب «ابعت كذا لكذا» مع العنوان."
        return queue_or_send(chat_id, "email", {"to": to_addr, "subject": subject, "body": body},
                             f"✉️ مسودة إيميل → {to_addr}\nالموضوع: {subject}\n\n{body}")

    if action == "post_social":
        platform = str(plan.get("platform", "")).strip().lower()
        text = str(plan.get("text", "")).strip()
        image_url = str(plan.get("image_url", "") or "").strip()
        if platform not in ("x", "facebook", "instagram"):
            return "أي منصة بدك أنشر؟ (x / facebook / instagram)"
        if not text:
            return "شو بدك أنشر بالضبط؟"
        if platform == "instagram" and not image_url:
            return "انستغرام بدها صورة مع المنشور — عطيني رابط صورة."
        preview = f"📣 نشر على {platform}:\n\n{text}" + (f"\n\nالصورة: {image_url}" if image_url else "")
        return queue_or_send(chat_id, "social", {"platform": platform, "text": text, "image_url": image_url}, preview)

    if action == "github_edit":
        repo = str(plan.get("repo", "")).strip()
        path = str(plan.get("path", "")).strip()
        instruction = str(plan.get("task", "")).strip() or user_text
        return handle_github_edit(chat_id, repo, path, instruction)

    reply = str(plan.get("reply", "")).strip() or raw.strip()
    db.add_message(chat_id, "assistant", reply)
    return reply


def queue_or_send(chat_id, kind, payload, preview_text):
    """لو الموافقة مطفية (auto_send) ينفذ فوراً — غير هيك مسودة + زر."""
    if auto_send():
        ok, msg = execute_draft(kind, payload)
        return ("✅ " if ok else "❌ ") + msg
    draft_id = save_draft(kind, payload)
    send_text(chat_id, preview_text + "\n\nتوافق؟", reply_markup=approval_keyboard(draft_id))
    return ""  # المسودة انبعثت مع الأزرار


def execute_draft(kind, payload):
    try:
        if kind == "email":
            gmail.send(payload["to"], payload["subject"], payload["body"])
            return True, f"انبعت الإيميل لـ {payload['to']} ✉️"
        if kind == "social":
            p = payload["platform"]
            if p == "x":
                social.x_post(payload["text"])
            elif p == "facebook":
                social.fb_post(payload["text"])
            elif p == "instagram":
                social.ig_post(payload["text"], payload.get("image_url", ""))
            return True, f"اننشر على {p} 📣"
        return False, f"نوع مسودة ما بعرفه: {kind}"
    except Exception as e:  # noqa: BLE001
        return False, f"فشل التنفيذ: {e}"


def handle_self_edit(chat_id, instruction):
    send_text(chat_id, "تمام، فهمت — بدي عدّل حالي بناءً على طلبك… لحظة.")
    ok, msg = selfedit.apply_instruction(instruction, brain.chat)
    if ok:
        final = msg + "\n\nبرجع لحالي — لما يرجع البوت بحكي لك."
        send_text(chat_id, final)
        os._exit(0)  # systemd بيرجع يشغلنا بالكود الجديد
    return msg


OP_QUERY = "أهم ترند عالمي أو فرصة عمل بمجال التقنية والأسواق اليوم"


def opportunity_of_the_day():
    """فقرة «فرصة اليوم» للتقرير الصباحي — Tavily + فابل (استدعاء واحد باليوم فقط)."""
    if not tools.TAVILY_API_KEY:
        return None
    news = tools.web_search(OP_QUERY, max_results=4)
    if not news:
        return None
    try:
        out = brain.chat([
            {"role": "system", "content":
             "أنت الشريك الذكي للدكتور. عطيك ترندات اليوم — دورك: فرصة واحدة عملية يقدر يبلشها اليوم بنفس أدواته "
             "(بوت تيليجرام مع فابل 5.2، نشر على السوشيال، GitHub). الشكل: «💡 فرصة اليوم: عنوان» ثم 3 جمل قصيرة: شو هي، ليش هلأ، أول خطوة. "
             "باللهجة الشامية، بلا فذلكة."},
            {"role": "user", "content": f"ترندات اليوم:\n{news}"},
        ], temperature=0.7, max_tokens=350)
        return out.strip()
    except brain.BrainError:
        return None


def handle_debate(chat_id, question):
    send_text(chat_id, "⚖️ بدست المحكمة: متفائل × متشائم → القاضي…")
    optimist = brain.chat([
        {"role": "system", "content": "أنت محامي الفرصة: دورك الوحيد تلتقط الأسباب الإيجابية والربح والتوقيت — بواقعية بلا تهويل. 4 أسطر كحد أقصى، باللهجة الشامية."},
        {"role": "user", "content": question}], temperature=0.6, max_tokens=350)
    pessimist = brain.chat([
        {"role": "system", "content": "أنت محامي الخطر: دورك الوحيد تلتقط المخاطر والعيوب والخسارة والتوقيت الغلط — بواقعية بلا تشاؤم مرضي. 4 أسطر كحد أقصى، باللهجة الشامية."},
        {"role": "user", "content": question}], temperature=0.6, max_tokens=350)
    judge = brain.chat([
        {"role": "system", "content": "أنت القاضي الحكيم: اسمع موقف المتفائل والمتشائم وارمِ حكمك النهائي: القرار الصح + شرط واحد للحماية. 5 أسطر، باللهجة الشامية."},
        {"role": "user", "content": f"القرار المطروح: {question}\n\nالمتفائل:\n{optimist}\n\nالمتشائم:\n{pessimist}"}],
        temperature=0.5, max_tokens=450)
    db.add_message(chat_id, "assistant", judge, agent="القاضي")
    return f"🟢 المتفائل:\n{optimist}\n\n🔴 المتشائم:\n{pessimist}\n\n⚖️ القاضي:\n{judge}"


def handle_github_edit(chat_id, repo, path, instruction):
    if not github.configured():
        return "GitHub لسا مو موصول — الدكتور يحط GITHUB_TOKEN بـ ~/jarvis-ceo.env وبرجع بجرب."
    if not repo or not path:
        return "احكيلي أي ريبو وأي ملف (مثال: «عدّل ملف src/app.py بالريبو myrepo: غيّر اللوجو»)"
    send_text(chat_id, f"📎 بوصل على {repo} — بقرا الملف…")
    try:
        f = github.get_file(repo, path)
    except Exception as e:  # noqa: BLE001
        return f"ما قدرت اقرا الملف: {e}"
    convo = [{"role": "system", "content": (
        "أنت محرر كود عند الدكتور. أمامك محتوى ملف وطلب تعديل.\n"
        "رجّع JSON فقط: {\"content\":\"...محتوى الملف كاملاً بعد التعديل...\",\"message\":\"رسالة كوميت قصيرة\"}\n"
        "حافظ على كل إشي، التعديل المطلوب بس."
    )}, {"role": "user", "content": f"الملف {f['path']} في {f['repo']}:\n```\n{f['content'][:20000]}\n```\n\nطلب الدكتور: {instruction}"}]
    try:
        raw = brain.chat(convo, temperature=0.2, max_tokens=6000)
    except brain.BrainError as e:
        return f"العقل مشغول هلأ: {e}"
    parsed = brain.extract_json(raw)
    new_content = (parsed or {}).get("content") if isinstance(parsed, dict) else None
    message = (parsed or {}).get("message", "jarvis edit") if isinstance(parsed, dict) else "jarvis edit"
    if not new_content or len(new_content) < 5:
        return "فابل ما رجع محتوى صالح — ما عدّلت شي بالريبو."
    try:
        res = github.put_file(repo, path, new_content, message or "jarvis edit",
                              create_branch_from="main" if _default_branch_exists(repo) else None)
        if res.get("branch") and res["branch"] != "main":
            try:
                pr = github.create_pull_request(repo, res["branch"], "main",
                                                title=message[:120], body=f"طلب الدكتور: {instruction}")
                return f"✅ فتحت Pull Request بالريبو {f['repo']}:\n{pr.get('url')}\n(ما بلمس main بلا موافقتك)"
            except Exception as e:  # noqa: BLE001
                return f"✅ كوميت عالبرانش {res['branch']} — بس ما قدرت افتح PR: {e}"
        return f"✅ عدّلت الملف بالريبو {f['repo']} — كوميت {res.get('commit')}\n{res.get('url')}"
    except Exception as e:  # noqa: BLE001
        return f"فشل الدفع على GitHub: {e}"


def _default_branch_exists(repo):
    try:
        github.get_file(repo, "README.md", ref="main")
        return True
    except Exception:
        return False


# ============ أوامر مباشرة (بلا عقل — أسرع وأضمن) ============

def integrations_status():
    gh = github.whoami() if github.configured() else {"ok": False, "error": "GITHUB_TOKEN مش حاطه"}
    lines = [
        "🔌 وصلات الدكتور:",
        f"• GitHub: {'✅ ' + gh.get('login', '') if gh.get('ok') else '❌ ' + str(gh.get('error', ''))[:60]}",
        f"• جيميل: {'✅ ' + os.environ.get('GMAIL_ADDRESS', '') if gmail.configured() else '❌ مش موصول (needs App Password)'}",
        f"• X (تويتر): {'✅' if social.x_configured() else '❌ مش موصول'}",
        f"• فيسبوك (صفحة): {'✅' if social.fb_configured() else '❌ مش موصول'}",
        f"• انستغرام: {'✅' if social.ig_configured() else '❌ مش موصول (يحتاج حساب Business + صفحة)'}",
        f"• وضع الموافقة: {'⚡ بدون سؤال (auto_send)' if auto_send() else '🙋 كل إرسال بضغطة منك'}",
    ]
    return "\n".join(lines)


# ============ ملفات Excel ============

def handle_excel_upload(chat_id, path, caption):
    instruction = (caption or "").strip()
    if not instruction:
        excel_sessions[chat_id] = path
        send_text(chat_id, "وصلني ملف الإكسل 📎 شو بدك تعمل فيه؟ (مثال: «عبيلي كل صف بملاحظته من التسجيلات» أو «وريني الأعمدة»)")
        return
    process_excel(chat_id, path, instruction)


def process_excel(chat_id, path, instruction):
    send_text(chat_id, "استلمت — بقرأ الملف هلأ…")
    try:
        report = tools.excel_report(path)
    except Exception as e:  # noqa: BLE001
        send_text(chat_id, f"ما قدرت أفتح الملف: {e}")
        return

    convo = [{"role": "system", "content": (
        "أنت خبير Excel بتشتغل عبر openpyxl. أمامك ملخص ملف واطلب الدكتور.\n"
        "إذا الطلب مجرد سؤال عن المحتوى — جاوب نص بدون تنفيذ كود وابدأ جوابك بـ \"جواب:\".\n"
        "غير هيك، رجّع JSON فقط بالشكل: {\"code\":\"كود بايثون ينفذ على المتغير wb/ws\"}\n"
        "ملاحظات للكود: استخدم فقط المتغيرين wb (كامل الملف) و ws (الشيت الحالي) و openpyxl؛ "
        "ممنوع import أو open أو os أو أي شيء خارج الملف؛ "
        "استعمل log(...) لتسجيل ما فعلته. لا تغيّر أي خلية إلا المطلوب. "
        "النظام يحفظ الملف تلقائياً بعد نجاح الكود."
    )}, {"role": "user", "content": f"ملخص الملف:\n{report}\n\nطلب الدكتور: {instruction}"}]
    try:
        raw = brain.chat(convo, temperature=0.2, max_tokens=1800)
    except brain.BrainError as e:
        send_text(chat_id, f"العقل مشغول هلأ: {e}")
        return

    if raw.strip().startswith("جواب:"):
        send_text(chat_id, raw.strip()[5:].strip())
        return

    parsed = brain.extract_json(raw)
    code = (parsed or {}).get("code") if isinstance(parsed, dict) else None
    if not code:
        send_text(chat_id, raw.strip()[:3500])
        return
    ok, out = tools.apply_excel_code(path, code)
    if ok:
        send_document(chat_id, path, caption=f"✅ خلصت. {out[:900]}")
    else:
        send_text(chat_id, out)


# ============ أوامر Excel في المحادثة ============

def handle_message(msg):
    chat_id = msg["chat"]["id"]
    if not claim_or_check(chat_id):
        tg("sendMessage", {"chat_id": chat_id, "text": "عذراً، هاد البوت خاص بشخص واحد 🙏"})
        return

    if "document" in msg:
        doc = msg["document"]
        name = doc.get("file_name", "file")
        if name.lower().endswith((".xlsx", ".xlsm")):
            path = download_file(doc["file_id"], os.path.splitext(name)[1])
            if path:
                handle_excel_upload(chat_id, path, msg.get("caption", ""))
            return
        send_text(chat_id, "بعتلي Excel (.xlsx) هلأ — باقي الملفات بمرحلة الجاية.")
        return

    is_voice = "voice" in msg
    if is_voice:
        path = download_file(msg["voice"]["file_id"], ".oga")
        if not path:
            send_text(chat_id, "ما قدرتيش حمّل هالصوت — جرّب تاني")
            return
        try:
            text = tools.gemini_transcribe(path, "audio/ogg")
        except Exception as e:  # noqa: BLE001
            send_text(chat_id, f"ما فهمت الصوت ({e}) — جرّب تحكيلي بالكتابة")
            return
        if not text:
            send_text(chat_id, "ما سمعت شي بالرسالة 🎤 — احكِ تاني؟")
            return
        send_text(chat_id, f"فهمتك: «{text}»")
    else:
        text = (msg.get("text") or "").strip()

    if not text:
        return

    low = text.lower().strip()
    if low in ("/start", "start", "اهلا", "مرحبا", "هاي", "هلا"):
        send_text(chat_id, "أهلاً دكتور 👋 " + HELP.split("\n", 1)[1])
        return
    if low in ("/help", "مساعدة", "اوامر", "أوامر", "شو بتعرف تعمل"):
        send_text(chat_id, HELP)
        return
    if low in ("/agents", "وكلائي", "كلاء", "الوكلاء", "مين وكلائك"):
        lines = ["وكلائي الحاليين (كلهم فابل 5.2 + شخصية):"]
        for a in db.list_agents():
            lines.append(f"• {a['name']} — {a['persona'].splitlines()[0][:110]}")
        lines.append("\nبدك وكيل جديد؟ احكيلي: «أضف وكيل اسمه كذا مهمته كذا»")
        send_text(chat_id, "\n".join(lines))
        return
    if low in ("/stats", "حالة", "احصائيات", "إحصائيات", "انت وينك"):
        st = db.stats()
        send_text(chat_id, f"الحالة: {st['messages']} رسالة — {st['open_tasks']} مهام مفتوحة — {st['done_tasks']} مخلصة\nالإنفاق اليوم: {st['tokens_today']} توكن (السقف {os.environ.get('DAILY_TOKEN_CAP','200000')})")
        return
    if low in ("/integrations", "شو موصول", "الموصول", "الوصلات", "متصلات"):
        send_text(chat_id, integrations_status())
        return
    if low.startswith(("احفظ ", "/note ")):
        note = text.split(None, 1)[1].strip() if len(text.split(None, 1)) > 1 else ""
        if not note:
            send_text(chat_id, "اكتب شو بدك أحفظ — مثال: «احفظ: عقد العيادة بـ150 دولار»")
            return
        db.notes_add(note, f"chat:{chat_id}")
        send_text(chat_id, f"حفظتها بالذاكرة العميقة 🧠 ({db.notes_count()} ملاحظة) — اسألني «تذكر …» وقت ما بدك")
        return
    if low.startswith(("تذكر ", "/recall ")):
        query = text.split(None, 1)[1].strip() if len(text.split(None, 1)) > 1 else ""
        hits = db.notes_search(query, 4)
        if not hits:
            send_text(chat_id, "ما لقيت شي بالذاكرة بهالموضوع.")
        else:
            lines = ["🧠 من ذاكرتي:"] + [f"• {h['text'][:300]}" for h in hits]
            send_text(chat_id, "\n".join(lines))
        return
    if low.startswith(("ناقش قرار", "ناظرني", "/debate ", "ناقشني")):
        q = re.split(r"[:：]", text, maxsplit=1)
        question = q[1].strip() if len(q) > 1 else text.split(None, 1)[-1].strip()
        if len(question) < 6:
            send_text(chat_id, "اكتب القرار المطروح — مثال: «ناقش قرار: استثمر بـ 2000$ بوت تداول الذكاء؟»")
            return
        try:
            send_text(chat_id, handle_debate(chat_id, question))
        except brain.BrainError as e:
            send_text(chat_id, f"العقل مشغول هلأ: {e}")
        return
    if low in ("/inbox", "ايميلاتي", "إيميلي", "وريني الايميل", "وريني الإيميل", "الرسايل"):
        if not gmail.configured():
            send_text(chat_id, "جيميل لسا مو موصول — الدكتور يحط GMAIL_ADDRESS و GMAIL_APP_PASSWORD بـ ~/jarvis-ceo.env")
            return
        try:
            n = gmail.unread_count()
            items = gmail.latest_unread(3) if n else []
            lines = [f"📬 عندك {n} رسالة غير مقروءة"]
            for it in items:
                lines.append(f"\nمن: {it['from']}\nالموضوع: {it['subject']}\n{it['preview'][:200]}…")
            send_text(chat_id, "\n".join(lines))
        except Exception as e:  # noqa: BLE001
            send_text(chat_id, f"ما قدرت أوصل للصندوق: {e}")
        return
    if low in ("/repos", "ربيوزاتي", "ريپوزاتي", "مستودعاتي", "غيتوب"):
        if not github.configured():
            send_text(chat_id, "GitHub لسا مو موصول — الدكتور يحط GITHUB_TOKEN بـ ~/jarvis-ceo.env")
            return
        try:
            repos = github.list_repos(10)
            lines = ["📦 آخر الريبوز:"]
            for r in repos:
                lock = "🔒" if r["private"] else "🌐"
                lines.append(f"• {lock} {r['name']} — {r['updated']} {r['desc']}")
            send_text(chat_id, "\n".join(lines))
        except Exception as e:  # noqa: BLE001
            send_text(chat_id, f"GitHub ما رد: {e}")
        return
    if low in ("/tasks", "مهام", "المهام"):
        open_t = db.open_tasks(10)
        if not open_t:
            send_text(chat_id, "ما في مهام مفتوحة هلأ ✅")
        else:
            send_text(chat_id, "المفتوح:\n" + "\n".join(f"#{t['id']} ({t['agent']}): {t['prompt'][:120]}" for t in open_t))
        return
    if low in ("/revert", "تراجع", "رجع", "رجّع", "ارجع زي ما كنت"):
        ok, out = selfedit.revert_last()
        send_text(chat_id, ("✅ " if ok else "") + out)
        if ok:
            os._exit(0)
        return
    if low in ("/auto", "ارسل بدون موافقة", "بدون موافقة"):
        db.kv_set("auto_send", "1")
        send_text(chat_id, "تمام — من هلأ أي إرسال/نشر بنفذ على طول بدون سؤال. (رجّع الموافقة: «اسألني قبل الإرسال»)")
        return
    if low in ("/ask", "اسألني قبل الارسال", "اسألني قبل الإرسال", "رجع الموافقة"):
        db.kv_set("auto_send", "0")
        send_text(chat_id, "رجعت لوضع الموافقة — كل إرسال/نشر بضغطة منك 🙋")
        return
    if low.startswith(("راقب ", "/watch ")):
        url = text.split(None, 1)[1].strip() if len(text.split(None, 1)) > 1 else ""
        if not url:
            send_text(chat_id, "اكتب هيك: راقب example.com")
            return
        r = tools.check_site(url)
        if not r["ok"]:
            send_text(chat_id, f"الرابط ما فتح معي ({r['error']}) — تأكد منه")
            return
        urls = watch_list()
        if url not in urls:
            urls.append(url)
            watch_save(urls)
        send_text(chat_id, f"تمام، سعيد صار يراقب {url} — كل 30 دقيقة بيخبرك إذا طاح 👁")
        return
    if low in ("مواقع", "/watchlist", "قائمة المراقبة"):
        urls = watch_list()
        send_text(chat_id, ("المواقع تحت عين سعيد:\n" + "\n".join(f"- {u}" for u in urls)) if urls else "القائمة فاضية — ضيف: راقب <رابط>")
        return
    if low.startswith(("الغِ مراقبة ", "الغ مراقبة ", "/unwatch ")):
        parts = text.split()
        url = parts[-1].strip() if parts else ""
        urls = [u for u in watch_list() if u != url and url not in u]
        watch_save(urls)
        send_text(chat_id, "تمام، شلتها من القائمة ✅")
        return
    if low in ("/forget", "خصوصي", "انسى", "امسح المحادثة", "امسحلي الذاكرة"):
        db.forget_all(chat_id)
        send_text(chat_id, "تم المسح — ذاكرتي نظيفة من هالمحادثة 🧹")
        return
    m = re.match(r"^(?:اضف|أضف|ضيف)\s+وكيل(?:\s+اسمه)?\s+([^\s،,]+)\s+(?:مهمته|شغله|مختص)\s+(.+)$", text)
    if m:
        name, desc = m.group(1), m.group(2).strip()
        persona = f"أنت {name}، وكيل في طاقم جارفس. مهمتك: {desc}. احكِ باللهجة الشامية كشخص حقيقي، بجمل قصيرة ومباشرة. لا تتصرف عالم خارجي بدون إذن الدكتور."
        db.add_agent(name, persona)
        send_text(chat_id, f"تم ✅ صار عندك وكيل جديد اسمه {name} — مهمته: {desc}\nجرب: «{name} ...»")
        return
    pending = excel_sessions.pop(chat_id, None)
    if pending and os.path.isfile(pending):
        process_excel(chat_id, pending, text)
        return

    db.add_message(chat_id, "user", text)
    try:
        reply = think(chat_id, text, is_voice=is_voice)
    except brain.BrainError as e:
        reply = f"العقل مشغول هلأ — {e}"
    except Exception as e:  # noqa: BLE001
        reply = f"صار خطأ ما متوقع: {e}"
        print(f"think: {e}")

    if reply:
        send_text(chat_id, reply)
    if is_voice and reply:
        try:
            tts_path = os.path.join(UPLOAD_DIR, f"reply-{int(time.time())}.mp3")
            tools.speak_to_file(reply[:1200], tts_path)
            send_voice(chat_id, tts_path)
        except Exception as e:  # noqa: BLE001
            print(f"tts: {e}")


def handle_callback(cbq):
    cb_id = cbq.get("id")
    data = (cbq.get("data") or "").strip()
    chat_id = ((cbq.get("message") or {}).get("chat") or {}).get("id")
    tg("answerCallbackQuery", {"callback_query_id": cb_id})
    if not chat_id or ":" not in data:
        return
    action, draft_id = data.split(":", 1)
    draft = load_draft(draft_id)
    if not draft:
        send_text(chat_id, "هاي المسودة خلصت أو ما عادت موجودة — اطلبها تاني.")
        return
    if action == "no":
        delete_draft(draft_id)
        send_text(chat_id, "تمام، ألغيت ✅ ما انبعث شي.")
        return
    ok, msg = execute_draft(draft["kind"], draft)
    delete_draft(draft_id)
    send_text(chat_id, ("✅ " if ok else "❌ ") + msg)


# ============ أوامر Excel في المحادثة ============

HELP = (
    "أنا جارفس — مديرك التنفيذي 🤖\n"
    "احكيلي أي شي بأي لهجة، نص أو فويس، وبفهم :)\n\n"
    "أوامر سريعة:\n"
    "وكلائي — شوف وكلائي وما بيعملوا\n"
    "شو موصول — حالة كل الوصلات (GitHub/جيميل/السوشيال)\n"
    "ربيوزاتي — آخر ريبوز GitHub تبعك\n"
    "ايميلاتي — إيميلاتك غير المقروءة\n"
    "احفظ: <أي شي> — بتحفظها بالذاكرة العميقة 🧠 | تذكر <كلمة> — بحث فوري\n"
    "ناقش قرار: <السؤال> — المتفائل × المتشائم × القاضي ⚖️\n"
    "فرصة اليوم — بتقرير الصباح (إذا Tavily مربوط)\n"
    "حالة — إحصائيات سريعة + الإنفاق اليوم\n"
    "مهام — المهام المفتوحة\n"
    "تراجع — الغاء آخر تعديل عملته على حالي\n"
    "راقب <رابط> — ضيف موقع لقائمة سعيد\n"
    "ملف Excel — ابعتلي الملف وهلكيت تعليماتك (أو حط التعليمات بالكابتشن)\n"
    "اسألني قبل الإرسال — رجّع وضع الموافقة | ارسل بدون موافقة — ينفذ فوراً\n"
    "خصوصي — انسى كل المحادثة\n"
    "أي تعديل على نفسك — احكي طبيعي («غيّر/أضف/صلح/احذف…») وبطبقه بحالي\n"
    "نشر/إرسال — بصيغلك وبيعطيك زر ✅ قبل ما ينفذ\n"
    "مساعدة — هالرسالة"
)


# ============ مراقبة المواقع + التقرير الصباحي ============

def watch_list():
    try:
        return json.loads(db.kv_get("watch_urls", "[]"))
    except Exception:
        return []

def watch_save(urls):
    db.kv_set("watch_urls", json.dumps(urls, ensure_ascii=False))

def watch_check_all(chat_id):
    urls = watch_list()
    down = []
    for u in urls:
        r = tools.check_site(u)
        if not r["ok"]:
            down.append(f"🔴 {u} — {r['error']}")
    if down:
        send_text(chat_id, "👤 سعيد: في مواقع طايحه:\n" + "\n".join(down))

def morning_report(chat_id):
    facts = gather_facts("ذهب بيتكوين طقس")
    st = db.stats()
    open_t = db.open_tasks(5)
    opportunity = opportunity_of_the_day()
    lines = ["☀️ صباح الخير دكتور — معك جارفس:", "", facts]
    if opportunity:
        lines += ["", opportunity]
    if open_t:
        lines += ["", "📋 مهام مفتوحة:"] + [f"- ({t['agent']}) {t['prompt'][:90]}" for t in open_t]
    if gmail.configured():
        try:
            n = gmail.unread_count()
            lines += ["", f"📬 جيميل: {n} رسالة غير مقروءة"]
        except Exception:
            pass
    lines += ["", f"الأمس: {st['messages']} رسالة بالمحادثة — {st['done_tasks']} مهمة مخلصة — {st['open_tasks']} مفتوحة",
              f"الإنفاق اليوم: {st['tokens_today']} توكن"]
    send_text(chat_id, "\n".join(x for x in lines if x))

def background_loop():
    last_watch = 0.0
    while True:
        try:
            cid = ceo_chat_id()
            now = time.time()
            lt = time.localtime()
            if cid and watch_list() and now - last_watch > 1800:
                last_watch = now
                watch_check_all(cid)
            if cid and lt.tm_hour == 6 and lt.tm_min == 0:
                key = time.strftime("morning:%Y-%m-%d", lt)
                if not db.kv_get(key):
                    db.kv_set(key, "done")
                    morning_report(cid)
        except Exception as e:  # noqa: BLE001
            print(f"bg: {e}")
        time.sleep(30)


# ============ الحلقة الرئيسية ============

def main():
    threading.Thread(target=background_loop, daemon=True).start()
    me = tg("getMe")
    if not me:
        print("التوكن غلط أو ما في اتصال — راجع TELEGRAM_BOT_TOKEN"); sys.exit(1)
    print(f"جارفس CEO شغال كـ @{me.get('username')} — استنيه بالتيليجرام")
    update_id = int(db.kv_get("tg_offset", "0"))
    while True:
        updates = tg("getUpdates", {"offset": update_id, "timeout": 50,
                                    "allowed_updates": ["message", "callback_query"]}, timeout=65)
        if not updates:
            time.sleep(1)
            continue
        for upd in updates:
            update_id = max(update_id, upd.get("update_id", 0) + 1)
            db.kv_set("tg_offset", update_id)
            if upd.get("callback_query"):
                try:
                    handle_callback(upd["callback_query"])
                except Exception as e:  # noqa: BLE001
                    print(f"cbq: {e}")
                continue
            msg = upd.get("message")
            if not msg:
                continue
            try:
                handle_message(msg)
            except Exception as e:  # noqa: BLE001
                print(f"msg: {e}")
                try:
                    send_text(msg["chat"]["id"], f"صار خلل عندي: {type(e).__name__} — راجعني بعد لحظة")
                except Exception:
                    pass


if __name__ == "__main__":
    main()
