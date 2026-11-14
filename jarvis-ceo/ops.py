#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حالة النظام — جارفس يشوف نفسه: حقائق حية من السيرفر بدل «ابعثلي صورة».
- systemctl (الخدمات) + مؤقّتات رعد
- tail آخر الأسطر من سجل رعد/التحديث/البوت
- إحصائيات الإسناد اليومية من قاعدة البيانات
- كل النص بييجي للعقل بعد تنقية الأسرار (ما بينسرب ولا مفتاح للنموذج)
"""
import os
import re
import subprocess

SECRET = re.compile(
    r"(AIza[0-9A-Za-z_\-]{8,}|coa_[0-9A-Za-z]{6,}|sk-[0-9A-Za-z]{8,}|github_pat_[0-9A-Za-z_]{8,}"
    r"|ghp_[0-9A-Za-z]{8,}|gho_[0-9A-Za-z]{8,}|xox[baprs]-[0-9A-Za-z\-]{6,}"
    r"|[0-9]{8,10}:[A-Za-z0-9_\-]{30,}"
    r"|[A-Za-z][A-Za-z0-9_\-]*(token|secret|password|pass|api[_\-]?key)[A-Za-z0-9_\-]*\s*[:=]\s*[^\s,]{8,})",
    re.I,
)


def redact(text):
    return SECRET.sub("…(محجوبة)", text or "")


def _run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        return redact(out.strip())[:1200] or "(فاضي)"
    except Exception as e:  # noqa: BLE001
        return f"(تعذر: {e})"


def snapshot(runner=_run):
    repo = os.path.dirname(os.path.abspath(__file__))
    parts = [
        "— الخدمات:\n" + runner("systemctl is-active jarvis-ceo jarvis-voice 2>&1; "
                                "systemctl list-timers 'raad-*' --no-pager 2>&1 | head -7"),
        "— رعد (آخر نشاط):\n" + runner(f"tail -n 6 '{repo}/raad.log' 2>&1"),
        "— التحديث التلقائي (آخر عملية):\n" + runner(f"tail -n 4 '{repo}/auto_update.log' 2>&1"),
        "— البوت (آخر سطور اللوقات):\n" + runner("journalctl -u jarvis-ceo --since '3 hours ago' -n 12 --no-pager 2>&1 | tail -12"),
    ]
    try:
        import db
        st = db.stats()
        parts.append(f"— الإحصائيات: {st.get('messages', 0)} رسالة · {st.get('open_tasks', 0)} مهام مفتوحة · "
                     f"{st.get('tokens_today', 0)} توكن اليوم")
    except Exception:  # noqa: BLE001
        pass
    return "\n\n".join(parts)


SYSTEM_PROMPT = (
    "أنت جارفس — جاوب سؤال الدكتور عن حالة النظام مباشرة وبإيجاز عربي، بدون فذلكة وبدون حشو.\n"
    "إذا كل شي شغال قول هيدا بإيجاز وإذا في مشكلة حددها من السطور ووضح الحل.\n"
    "إذا قال الدكتور «رعد» فهو يقصد رعد (المتداول الورقي). هذه معلومات حية من السيرفر:\n"
)
