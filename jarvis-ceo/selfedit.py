#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محرك التعديل الذاتي لجارفس — فابل يطوّر نفسه وكوده من تيليجرام.
الضمانات:
  1) المسموح التعديل فقط على ملفات مجلد jarvis-ceo (الأمنية، ما بيمس النظام ولا ~/jarvis.env).
  2) بعد كل تعديل: py_compile ثم تشغيل مجموعة الاختبارات الكاملة — إذا فشل شي، رجّع النسخة فوراً.
  3) نسخة احتياطية قبل كل تعديل + أمر /revert يرجع لآخر نسخة.
  4) تعديل تلقائي بدون إذن مسبق — بس بداخل هالسياج، وهو قرار الدكتور الصريح.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_ROOT = os.path.join(AGENT_DIR, ".backups")
MAX_BACKUPS = 12

EDITABLE = {"agent.py", "brain.py", "db.py", "tools.py", "selfedit.py", "test_agent.py", "README_AR.md"}
NEW_FILE_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}\.py$")


def read_all_source(limit_per_file=14000, limit_total=60000):
    out, total = [], 0
    for path in sorted(glob.glob(os.path.join(AGENT_DIR, "*.py")) + glob.glob(os.path.join(AGENT_DIR, "*.md"))):
        base = os.path.basename(path)
        if base.startswith(("setup-", ".")) or base == "requirements.txt":
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
        except Exception:
            continue
        chunk = src[:limit_per_file]
        out.append(f"===== {base} =====\n{chunk}")
        total += len(chunk)
        if total > limit_total:
            out.append("===== (باقي الملفات مقصوصة للحد الأقصى) =====")
            break
    return "\n\n".join(out)


def list_backups():
    if not os.path.isdir(BACKUP_ROOT):
        return []
    return sorted(os.listdir(BACKUP_ROOT), reverse=True)


def read_backup(ts, name):
    p = os.path.join(BACKUP_ROOT, ts, name)
    return open(p, encoding="utf-8").read() if os.path.isfile(p) else None


def _backup_snapshot():
    ts = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUP_ROOT, ts)
    os.makedirs(dest, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(AGENT_DIR, "*.py")) + glob.glob(os.path.join(AGENT_DIR, "*.md"))):
        shutil.copy2(path, dest)
    backups = list_backups()
    for old in backups[MAX_BACKUPS:]:
        shutil.rmtree(os.path.join(BACKUP_ROOT, old), ignore_errors=True)
    return ts


def _restore(ts):
    src = os.path.join(BACKUP_ROOT, ts)
    if not os.path.isdir(src):
        return False, f"ما لقيت نسخة {ts}"
    for name in os.listdir(src):
        shutil.copy2(os.path.join(src, name), os.path.join(AGENT_DIR, name))
    return True, f"رجّعت النسخة {ts}"


def revert_last():
    backups = list_backups()
    if not backups:
        return False, "ما في نسخ احتياطية بعد"
    return _restore(backups[0])


def _run_tests():
    env = dict(os.environ)
    env["CEO_DB"] = f"/tmp/ceo-test-{int(time.time())}.db"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "test_agent", "-v"],
            cwd=AGENT_DIR, env=env, capture_output=True, text=True, timeout=90,
        )
    except subprocess.TimeoutExpired:
        return False, "الاختبارات أخذت وقت أكثر من اللازم"
    tail = "\n".join((proc.stderr or proc.stdout).splitlines()[-18:])
    ok = proc.returncode == 0
    return ok, tail


def _compile_all():
    for path in glob.glob(os.path.join(AGENT_DIR, "*.py")):
        try:
            import py_compile
            py_compile.compile(path, doraise=True)
        except Exception as e:  # noqa: BLE001
            return False, f"خطأ صياغة في {os.path.basename(path)}: {e}"
    return True, ""


def apply_instruction(instruction, brain_chat, log_fn=print):
    """
    instruction: وصف التعديل المطلوب (نص).
    brain_chat: دالة chat(messages, temperature, max_tokens) من brain.
    يرجع (ok, رسالة نهائية للدكتور).
    """
    src_bundle = read_all_source()
    messages = [
        {
            "role": "system",
            "content": (
                "أنت كبير مهندسي جارفس. مهمتك: تطبيق تعديل طلب الدكتور على الكود.\n"
                "قواعد صارمة:\n"
                "1) أرجع JSON فقط بالشكل: {\"plan\":\"خطة سطرين\",\"files\":[{\"path\":\"agent.py\",\"content\":\"...الكامل للملف...\"}]}\n"
                "2) content = الملف كاملاً بعد التعديل (مو diff).\n"
                "3) المسموح تعديله: agent.py, brain.py, db.py, tools.py, selfedit.py, test_agent.py, README_AR.md "
                "+ أي ملف جديد باسم حروف إنجليزية صغيرة وأرقام و underscore فقط وينتهي بـ .py.\n"
                "4) ممنوع المساس بـ ~/jarvis-ceo.env أو أي ملف خارج مجلد jarvis-ceo.\n"
                "5) حافظ على البنية العامة والأسماء والميزات كلها — التعديل المطلوب فقط.\n"
                "6) إذا الطلب غامض أو خطير (حذف كل شي مثلاً) — أرجع {\"plan\":\"رفض\",\"files\":[],\"reason\":\"...\"}."
            ),
        },
        {
            "role": "user",
            "content": f"طلب الدكتور:\n{instruction}\n\nالكود الحالي:\n{src_bundle}",
        },
    ]
    try:
        raw = brain_chat(messages, temperature=0.3, max_tokens=7000)
    except Exception as e:  # noqa: BLE001
        return False, f"العقل ما رد: {e}"

    import brain
    payload = brain.extract_json(raw)
    if not payload:
        return False, "فابل رجع جواب ما هو JSON — ما عدّلت شي"
    if payload.get("reason") and not payload.get("files"):
        return False, f"رفض التعديل: {payload.get('reason')}"
    files = payload.get("files") or []
    if not files:
        return False, "ما رجع ملفات — ما عدّلت شي"

    agent_real = os.path.realpath(AGENT_DIR)
    for f in files:
        path_name = str(f.get("path") or "").strip()
        if path_name not in EDITABLE and not NEW_FILE_RE.match(path_name):
            return False, f"اسم ملف غير مسموح: {path_name}"
        if not isinstance(f.get("content"), str) or len(f["content"]) < 20:
            return False, f"محتوى غير صالح للملف {path_name}"
        dest_real = os.path.realpath(os.path.join(AGENT_DIR, path_name))
        if not dest_real.startswith(agent_real + os.sep):
            return False, f"مسار ملف خرج خارج مجلد jarvis-ceo — مرفوض: {path_name}"
        if os.path.basename(dest_real) == "jarvis-ceo.env":
            return False, "محاولة كتابة في ملف الأسرار — مرفوضة"
        if re.search(r"(sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|[0-9]{8,10}:[A-Za-z0-9_-]{35})", f["content"]):
            return False, "المحتوى يبان فيه مفتاح/توكن حقيقي — مرفوض (الأسرار بتضل خارج الكود)"

    snapshot = _backup_snapshot()
    log_fn(f"backup: {snapshot}")
    restored = False
    try:
        for f in files:
            dest = os.path.join(AGENT_DIR, f["path"])
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(f["content"])

        ok, why = _compile_all()
        if not ok:
            raise RuntimeError(why)
        ok_tests, tail = _run_tests()
        if not ok_tests:
            raise RuntimeError(f"الاختبارات فشلت:\n{tail}")
        _git_commit(snapshot, instruction)
        return True, f"✅ طبّقت التعديل ({len(files)} ملف) والاختبارات كلها نجحت. نسخة احتياطية: {snapshot}"
    except Exception as e:  # noqa: BLE001
        _restore(snapshot)
        restored = True
        return False, f"❌ التعديل فشل — رجّعت النسخة الاحتياطية تلقائياً.\n{e}"


def _git_commit(snapshot, instruction):
    try:
        subprocess.run(["git", "add", "-A"], cwd=AGENT_DIR, capture_output=True, timeout=15)
        msg = f"self-edit ({snapshot}): {instruction[:80]}"
        subprocess.run(["git", "commit", "-m", msg, "--no-verify"], cwd=AGENT_DIR, capture_output=True, timeout=15)
    except Exception:
        pass  # git مجرد تتبع — التعديل ما بيوقف عليه
