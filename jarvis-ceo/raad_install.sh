#!/bin/bash
# رعد — أمر التنصيب: cd ~/jarvis-ceo && bash raad_install.sh
# القاعدة الذهبية: صفر اعتماد على النت. كل الحلقات الشبكية معطلة افتراضيياً.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"

exec 9>"$REPO/.raad_install.lock"
flock -n 9 || { echo "تنصيب شغال أصلاً — بسكر"; exit 0; }

echo "⚡ رعد — تنصيب (REPO=$REPO)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3.11 || command -v python3)"
echo "بايثون: $PY ($("$PY" -V 2>&1))"

# الاعتماديات تصير تتنصب تلقائيًا كل تحديث (مهلة قاسية 180ث — إذا ما خلص طبيعي)
if [ "${RAAD_PIP:-1}" = "1" ]; then
  timeout 180 "$PY" -m pip install -q --timeout 8 --retries 0 -r "$REPO/requirements.txt" \
    && echo "تنصيب الاعتماديات: OK" || echo "(الاعتماديات ما خلصت — طبيعي؛ رعد + البوت بيشتغلوا بدونها)"
else
  echo "(pip معطّل يدوياً بـ RAAD_PIP=0 — طبيعي البوت بيشتغل بدون الاعتماديات الجديدة)"
fi

echo "--- المصدر: $("$PY" -m pip config list 2>/dev/null | tr '\n' ' | ')" | head -c 200; echo

# الحلقات الأساسية أولاً: كرون إن وجد، وإلا systemd timers من ملفات الريبو
if command -v crontab >/dev/null 2>&1; then
  { crontab -l 2>/dev/null | grep -v 'raad_night.py\|raad.py report\|raad.py resolve\|auto_update.sh';
    echo "10 */6 * * * $PY $REPO/raad.py resolve >> $REPO/raad.log 2>&1";
    echo "30 1 * * * $PY $REPO/raad_night.py >> $REPO/raad.log 2>&1";
    echo "5 6 * * * $PY $REPO/raad.py report >> $REPO/raad.log 2>&1";
    echo "*/10 * * * * bash $REPO/auto_update.sh >> $REPO/auto_update.log 2>&1";
  } | timeout 15 crontab -
  echo "الكرون اتركب ✅"
else
  echo "ما في كرون — باركّب systemd timers (بلا حزم)"
  if sudo -n true 2>/dev/null; then
    timeout 15 sudo cp "$REPO"/raad_systemd/*.service "$REPO"/raad_systemd/*.timer /etc/systemd/system/
    timeout 15 sudo systemctl daemon-reload
    timeout 20 sudo systemctl enable --now raad-night.timer raad-report.timer raad-resolve.timer raad-update.timer
    systemctl list-timers 'raad-*' --no-pager 2>/dev/null | head -8
    echo "systemd timers اتركبت ✅"
  else
    echo "✗ لا كرون ولا sudo — يلزم: sudo bash $REPO/raad_install.sh من الكونسول"
  fi
fi

MARKER="$HOME/.jarvis_raad_setup_done"
if [ -f "$MARKER" ]; then
  echo "(التهيئة الأولى خلصت — ما بيكرر «رعد تفعّل» كل تحديث)"
else
  if timeout 90 "$PY" "$REPO/raad.py" setup; then touch "$MARKER"; else echo "(raad.py setup فشل/تأخر — تخطيناه، الكرون مركّب والباقي شغال)"; fi
fi
echo "RAAD-INSTALLED-OK"
exit 0
