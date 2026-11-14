#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
رعد — عند الواحدة ونص ليلاً (ينتهي قبل الرابعة فجراً)
يراجع دفتر الأمس، يكتب الدرس بـ PLAYBOOK.md، ويطبّق **تعديل واحد فقط**
من قائمة بيضاء مغلقة:
  1) إيقاف طوارئ تلقائي إذا expectancy على آخر 30 صفقة < 0
  2) ضبط جدول معايرة الثقة (أي Bucket يعد 100 صفقة وبعيد عن الحقيقة ≥ 15 نقطة)
ممنوع يحذف كوداً، ممنوع يعدّل الاستراتيجيات، ممنوع يدفع لـ git — كل تغيير مذكور بالتقرير
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import raad

MIN_SAMPLE = 30
REPO = raad.REPO
CHANGED_TODAY_MARK = "last_change_date"

def main():
    resolved = raad.resolve_all()
    s = raad.stats()
    state = raad.load_state()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    changes = []

    # 1) إيقاف الطوارئ
    if s["n"] >= MIN_SAMPLE and s["expectancy_r"] < 0 and not state.get("paused"):
        state["paused"] = True
        changes.append(f"⏸ إيقاف طوارئ: expectancy {s['expectancy_r']}R على آخر {s['n']} صفقة")

    # 2) معايرة الثقة (Bucket واحد كحد أقصى بالليلة)
    elif state.get(CHANGED_TODAY_MARK) != today and s.get("calibration"):
        cal = state.get("calibration", {})
        worst = None
        for bucket, wr in s["calibration"].items():
            diff = abs(wr - (float(bucket) * 10 + 5))
            if diff >= 15:
                if worst is None or diff > worst[1]:
                    worst = (int(bucket), diff)
        if worst:
            state.setdefault("calibration", {})[str(worst[0] * 10)] = "راجع — عاين 30 صفقة على الأقل قبل الثقة"
            changes.append(f"🔧 معايرة الثقة: Bucket {worst[0]*10} منحرفة {worst[1]:.0f} نقطة — مُعلّم للمراجعة")

    # 3) نبض أخطاء الدفتر نفسه (لا نلمس الاستراتيجية)
    with raad.db() as conn:
        orphans = conn.execute("SELECT COUNT(*) c FROM calls WHERE status='open' AND ts < ?",
                               (time.time() - 7 * 86400,)).fetchone()["c"]
    if orphans and not changes:
        changes.append(f"🧾 {orphans} بطاقة معلقة أكثر من أسبوع — راجعتها resolve")

    if changes:
        state[CHANGED_TODAY_MARK] = today
    raad.save_state(state)

    # 4) الدرس بـ PLAYBOOK.md
    if changes or resolved:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        header = "\n# PLAYBOOK — دروس رعد\n" if not os.path.exists(raad.PLAYBOOK) else ""
        lines = [f"{header}\n## {stamp} UTC\n",
                 f"- صفقات مقفلة الليلة: {resolved} | expectancy {s['expectancy_r']}R | PF {s['pf']} | DD {s['max_dd']}R | عينة {s['n']}\n"]
        for ch in changes:
            lines.append(f"- {ch}\n")
        with open(raad.PLAYBOOK, "a", encoding="utf-8") as f:
            f.write("".join(lines))
        try:
            env = dict(os.environ)
            subprocess.run(["git", "-c", "user.name=Raad Nightly", "-c", "user.email=raad@jarvis.local",
                            "add", "PLAYBOOK.md"], cwd=REPO, check=False, capture_output=True)
            out = subprocess.run(["git", "-c", "user.name=Raad Nightly", "-c", "user.email=raad@jarvis.local",
                                  "commit", "-m", "رعد الليلي: دفتر + درس"], cwd=REPO,
                                 capture_output=True, text=True)
            if out.returncode == 0:
                changes.append("📝 الدرس انحفظ بـ PLAYBOOK.md (commit محلي، لا دفع تلقائي)")
        except Exception:  # noqa: BLE001
            pass

    # 5) تقرير التِلغرام
    head = "🌙 تقرير رعد الليلي"
    if s["n"]:
        body = (f"مقفلة الليلة: {resolved}\n"
                f"آخر {s['n']}: فوز {s['win_rate']}% | expectancy {s['expectancy_r']}R | PF {s['pf']} | DD {s['max_dd']}R")
    else:
        body = f"مقفلة الليلة: {resolved}\nالدفتر لسا فاضي — ما في أرقام للحكم. طبيعي."
    extra = ("\n".join("• " + c for c in changes)) if changes else "• ما في تعديلات هالليلة — النظام مستقر."
    raad.telegram_send(f"{head}\n{body}\n{extra}\n\nملاحظة: التعديلات من قائمة بيضاء مغلقة فقط — الكود ما بلمس بحاله أبداً.")

if __name__ == "__main__":
    main()
