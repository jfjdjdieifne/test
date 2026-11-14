#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
وضع الوكيل — حلقة ReAct حقيقية جوّا جارفس (على تيليجرام، مثل Agent Mode).

المرحلة 1 (هالنسخة): صندوق تجارب محلي معزول عن أسرار البوت — مجلد ~/agent_ws،
   بيئة بلا مفاتيح (PATH بس)، مهلة صريحة لكل أمر، أوامر خطرة بتوقف لإذن الدكتور،
   وممنوعات مطلقة على النواة الحية (مجلد البوت، ~/.ssh، ملفات البيئة).
   ملاحظة صراحة: العزل المحلي مش بديل عن بوكس منفصل — هيدا وضع تجارب آمن "بقدر"،
   والعزل الحقيقي بيجي لما نشبّك CEO_SANDBOX_HOST (بوكس AWS تجارب، مرحلة 2).

المرحلة 2 (لا حق): نفس الحلقة بس التنفيذ على بوكس AWS منفصل بـ SSH — البوت نفسه
   ما بيلمس الصندوق إلا عبر ssh، وما فيه ولا مفتاح إنتاج جوز الو صندوق.

كل خطوة = سطر واحد للدكتور بالتيليجرام؛ الملفات اللي بتنعمل بتنبعتلو على الخلاصة.
"""
import json
import os
import re
import subprocess
import time
import urllib.request
import urllib.error

import brain

WS = os.environ.get("CEO_AGENT_WS", os.path.expanduser("~/agent_ws"))
MAX_STEPS = int(os.environ.get("CEO_AGENT_STEPS", "10"))
STEP_TIMEOUT = int(os.environ.get("CEO_AGENT_TIMEOUT", "90"))
MAX_OUT = 5000
MAX_FILES = 8
MAX_FILE_BYTES = 9 * 1024 * 1024
PENDING_TTL = 300  # ثوانٍ — بعدها بيتلغى طلب الإذن لحاله

# أوامر «خطرة لكن ممكنة بإذن» → نعم/لا
DANGER_RE = re.compile(
    r"(rm\s+(-[a-z]*r[a-z]*f|-rf|-fr)\b|sudo\b|systemctl\b|\bservice\b|shutdown|reboot|poweroff"
    r"|mkfs|\bdd\b[^\n]*of=/dev|:\(\)\s*\{|chmod\s+(-R\s+)?777|chown\s+-R"
    r"|curl[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh|wget[^\n|]*\|\s*(sudo\s+)?(ba|z)?sh"
    r"|git\s+push[^\n]*(--force|\+)|fdisk|parted|iptables|nft\b)",
    re.I,
)
# ممنوع مطلق حتى بإذن — النواة الحية (البوت، المفاتيح، القاعدة، الكرون)
PROTECTED_RE = re.compile(
    r"(jarvis-ceo|jarvis_ceo|\.ssh|\.jarvis|jarvis-ceo\.env|jarvis-ceo\.db|authorized_keys"
    r"|/etc/(passwd|shadow|sudoers)|crontab|auto_update\.sh|raad_install|\.deployed_sha)",
    re.I,
)

SYSTEM = (
    "أنت «جارفس‑وكيل» — مهندس تنفيذ مستقل يعمل عبر تيليجرام. مهمتك تحقق هدف الدكتور بخطوات عبر أدوات.\n"
    "أرجع JSON فقط — ممنوع أي كلام خارج الكائن.\n"
    'الشكل: {"thought":"فكرة قصيرة","action":"bash|web_search|read_file|write_file|http_get|done","args":{...}}\n'
    "- bash: {\"cmd\":\"...\"} — Linux. بايثون/pip/نود متوفرين، cwd = ~/agent_ws (مساحتك الخاصة). ممنوع sudo/systemctl/ssh/مسارات خارج مساحتك.\n"
    "- write_file/read_file: مسارات نسبية داخل ~/agent_ws فقط.\n"
    "- web_search: {\"query\":\"...\",\"n\":4} · http_get: {\"url\":\"...\"}\n"
    "- لا تكرر خطوة فاشلة أكثر من مرتين — غيّر النهج أو اختم بصراحة ووضّح شو ناقص.\n"
    "- الحلول العملية: اوامر صغيرة قابلة للتحقق؛ أي ملف نهائي لازم يتعمل بـ write_file عشان ينبعث للدكتور.\n"
    '- done: {"final":"ملخص عربي قصير: شو عملت + شو الملفات + شو الناقص لو إشي"}\n'
    "- بدون حشو ولا فذلكة. هدفك: نتيجة ملموسة بأقصر طريق.\n"
)

_running = {}
_stop = {}


def _ws():
    p = os.path.abspath(WS)
    os.makedirs(p, exist_ok=True)
    return p


def is_running(chat_id):
    return _running.get(chat_id, False)


def request_stop(chat_id):
    _stop[chat_id] = True


def _extract_first_json(s):
    start = -1
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(s[start:i + 1])
                except Exception:
                    return None
    return None


def _safe_path(rel):
    p = os.path.abspath(os.path.normpath(os.path.join(_ws(), rel)))
    if p != _ws() and not p.startswith(_ws() + os.sep):
        raise ValueError("خارج مساحة التجربة")
    return p


def _run_bash(cmd):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": _ws(), "LANG": "C.UTF-8", "TERM": "dumb"}
    try:
        p = subprocess.run(cmd, shell=True, cwd=_ws(), env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=STEP_TIMEOUT)
        out = p.stdout.decode("utf-8", "ignore")
    except subprocess.TimeoutExpired:
        return f"(انتهت مهلة {STEP_TIMEOUT} ثوانٍ — الأمر توقف)"
    out = out.strip()
    if len(out) > MAX_OUT:
        out = out[-MAX_OUT:]
    return out or "(بدون خرج)"


def _http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "jarvis-agent/1"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = r.read(60000).decode("utf-8", "ignore")
    data = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", data, flags=re.I)
    data = re.sub(r"<[^>]+>", " ", data)
    data = re.sub(r"\s+", " ", data).strip()
    return data[:5500] or "(صفحة فاضية)"


def _do_tool(act, args):
    """ينفذ أداة وبرجع نص النتيجة. بترمي ValueError للممنوعات."""
    if act == "bash":
        cmd = str(args.get("cmd") or "").strip()
        if not cmd:
            return "(ما في command — رجّع args.cmd)"
        if PROTECTED_RE.search(cmd):
            raise ValueError("هذا الأمر بيلمس النواة الحية (البوت/المفاتيح/البيانات) — ممنوع حتى بموافقة")
        return _run_bash(cmd)
    if act == "web_search":
        import tools
        q = str(args.get("query") or "").strip()
        if not q:
            return "(ما في query)"
        try:
            n = int(args.get("n") or 4)
        except Exception:
            n = 4
        res = tools.web_search(q, max(1, min(n, 6)))
        return res or "(البحث رجع فاضي)"
    if act == "read_file":
        p = _safe_path(str(args.get("path") or ""))
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read(MAX_OUT) or "(ملف فاضي)"
    if act == "write_file":
        p = _safe_path(str(args.get("path") or ""))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        content = str(args.get("content") or "")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
        return f"انكتب ({len(content)} حرف) → {os.path.relpath(p, _ws())}"
    if act == "http_get":
        return _http_get(str(args.get("url") or ""))
    return f"(أداة مجهولة: {act})"


def _send_new_files(chat_id, start_ts, send_doc):
    try:
        root = _ws()
        new = []
        for dirpath, _, names in os.walk(root):
            for name in names:
                fp = os.path.join(dirpath, name)
                try:
                    st = os.stat(fp)
                except OSError:
                    continue
                if st.st_mtime >= start_ts - 1 and 0 < st.st_size <= MAX_FILE_BYTES:
                    new.append((st.st_mtime, fp))
        new.sort(reverse=True)
        for _, fp in new[:MAX_FILES]:
            send_doc(chat_id, fp, caption=os.path.relpath(fp, root))
        if len(new) > MAX_FILES:
            send_doc(chat_id, new[0][1], caption=f"(و {len(new) - MAX_FILES} ملفات زيادة بالمجلد)")
    except Exception as e:  # noqa: BLE001
        print(f"agent_loop send files: {e}")


def _need_approval(cmd):
    return bool(DANGER_RE.search(cmd))


def _loop(chat_id, goal, messages, start_ts, send, send_doc, db, first_step=1):
    _running[chat_id] = True
    _stop[chat_id] = False
    try:
        for step in range(first_step, MAX_STEPS + 1):
            if _stop.get(chat_id):
                send(chat_id, "🛑 الوكيل وقف عند طلبك — الهدف ما اكتمل.")
                return
            try:
                raw = brain.chat(messages, temperature=0.3, max_tokens=1400)
            except Exception as e:  # noqa: BLE001
                send(chat_id, f"🤖 العقل توقف: {e}\nالحل: مفاتيح كوارينا السليمة («احفظ كل المفاتيح») أو جرّب بعد كم دقيقة.")
                return
            messages.append({"role": "assistant", "content": raw[:3000]})
            act_obj = _extract_first_json(raw)
            if not act_obj:
                messages.append({"role": "user", "content": "JSON فقط بالشكل المطلوب — بدون شرح."})
                continue
            act = str(act_obj.get("action") or "").lower().strip()
            args = act_obj.get("args") if isinstance(act_obj.get("args"), dict) else {}
            thought = str(act_obj.get("thought") or "").strip()
            if act == "done":
                final = str(act_obj.get("final") or "خلصت.").strip()
                send(chat_id, f"✅ خلص الوكيل ({step - first_step + 1} خطوات · {int(time.time() - start_ts)}ث)\n\n{final[:2500]}")
                _send_new_files(chat_id, start_ts, send_doc)
                return
            try:
                if act == "bash":
                    cmd = str(args.get("cmd") or "").strip()
                    if PROTECTED_RE.search(cmd):
                        result = "(مرفوض: بيلمس النواة الحية — البوت/المفاتيح/البيانات)"
                    elif _need_approval(cmd):
                        pending = {"goal": goal, "messages": messages[-14:], "cmd": cmd,
                                   "start_ts": start_ts, "next_step": step + 1, "ts": time.time()}
                        db.kv_set(f"agent_pending:{chat_id}", json.dumps(pending, ensure_ascii=False))
                        send(chat_id, f"⚠️ الخطوة {step}/{MAX_STEPS} خطرة على النظام:\n{cmd[:400]}\n\nردّ «نعم» خلال ٥ دقايق لتنفذ، أو أي إشي تاني لتتجاهلها.")
                        return
                    else:
                        result = _do_tool(act, args)
                else:
                    result = _do_tool(act, args)
            except ValueError as e:
                result = f"(مرفوض: {e})"
            preview = {"bash": str(args.get("cmd") or ""), "web_search": str(args.get("query") or ""),
                       "read_file": str(args.get("path") or ""), "write_file": str(args.get("path") or ""),
                       "http_get": str(args.get("url") or "")}.get(act, act)
            send(chat_id, f"🔧 {step}/{MAX_STEPS} · {act} — {thought[:90] or preview[:90]}")
            messages.append({"role": "user", "content": f"نتيجة {act}:\n{result[:MAX_OUT]}"})
        send(chat_id, f"⏳ وصلت لحد {MAX_STEPS} خطوات بدون إنجاز نهائي — ما بدي حروق توكنك على حلاقة.\nاكتب «وضع الوكيل <الهدف>» من جديد لو بدك أكمل، أو ضيّق الهدف.")
        _send_new_files(chat_id, start_ts, send_doc)
    finally:
        _running[chat_id] = False


def run_agent(chat_id, goal, send, send_doc, db):
    _ws()
    start_ts = time.time()
    send(chat_id, f"🤖 وضع الوكيل انطلق.\nالهدف: {goal}\nحتى {MAX_STEPS} خطوات — و«وقف» بوقفه وقت ما بدك.")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"الهدف: {goal}"}]
    _loop(chat_id, goal, messages, start_ts, send, send_doc, db)


def resume_after_approval(chat_id, send, send_doc, db, approved=True):
    raw = db.kv_get(f"agent_pending:{chat_id}", "")
    db.kv_set(f"agent_pending:{chat_id}", "")
    if not raw:
        send(chat_id, "ما في خطوة بانتظار إذن (انتهت مدتها).")
        return
    try:
        pending = json.loads(raw)
    except Exception:
        send(chat_id, "ما قدرت أقرا الخطوة المعلقة — الغيها وابدأ من جديد.")
        return
    if time.time() - float(pending.get("ts", 0)) > PENDING_TTL:
        send(chat_id, "⏰ فات وقت الإذن (٥ دقايق) — تجاهلت الخطوة. الهدف توقف.")
        return
    if not approved:
        send(chat_id, "تمام — تجاهلت الخطوة. الهدف توقف.")
        return
    cmd = pending.get("cmd", "")
    send(chat_id, f"⚙️ نفذتها بإذنك:\n{cmd[:300]}")
    result = _run_bash(cmd)
    messages = pending.get("messages") or [{"role": "system", "content": SYSTEM}]
    messages.append({"role": "user", "content": f"نتيجة bash (بعد إذن الدكتور):\n{result[:MAX_OUT]}"})
    _loop(chat_id, pending.get("goal", ""), messages, float(pending.get("start_ts") or time.time()),
          send, send_doc, db, first_step=int(pending.get("next_step") or 1))
