#!/bin/bash
# رعد — أمر التنصيب الواحد: cd ~/jarvis-ceo && git pull origin arena/e3e2c397-test && bash raad_install.sh
set -e
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"
echo "⚡ رعد — تنصيب"

PY=""
if [ -x "$REPO/.venv/bin/python" ]; then PY="$REPO/.venv/bin/python"; else PY="$(command -v python3)"; fi
echo "بايثون: $PY"

if [ -f "$REPO/requirements.txt" ]; then
  "$PY" -m pip install -q -r "$REPO/requirements.txt" || echo "(تنبيه: pip ما نجح ببعض الحزم — أكمل إذا الموجود يكفي)"
fi

# إزالة أي كرون سابق لرعد ثم إضافة الجدول
{ crontab -l 2>/dev/null | grep -v 'raad_night.py\|raad.py report\|raad.py resolve';
  echo "10 */6 * * * $PY $REPO/raad.py resolve >> $REPO/raad.log 2>&1";
  echo "30 1 * * * $PY $REPO/raad_night.py >> $REPO/raad.log 2>&1";
  echo "5 6 * * * $PY $REPO/raad.py report >> $REPO/raad.log 2>&1";
} | crontab -
echo "الكرون اتركب: فحص كل 6 ساعات + مراجعة ليلية 01:30 UTC + تقرير صباحي 06:05 UTC"

"$PY" "$REPO/raad.py" setup
echo ""
echo "خلص ✅ — رعد ورقي بس. للمراجعة: tail -50 $REPO/raad.log | إلغاء كامل: crontab -l | grep -v raad | crontab -"
