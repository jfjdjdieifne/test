#!/bin/bash
# رعد — أمر التنصيب: cd ~/jarvis-ceo && bash raad_install.sh
# stdlib فقط — ما بيرهن حاله بأي pip. بيعطي رسائل واضحة بكل خطوة.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"
echo "⚡ رعد — تنصيب (REPO=$REPO)"

PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3.11 || command -v python3)"
echo "بايثون: $PY ($("$PY" -V 2>&1))"

"$PY" -m pip install -q --upgrade pip 2>/dev/null || echo "(pip -U تعذر — م كبط)"

# الحزم الضرورية للبوت النصي والرعد — livekit اختياري للمكالمات
"$PY" -m pip install -q edge-tts openpyxl \
  && echo "تنصيب edge-tts + openpyxl: OK" \
  || echo "(تنبيه: edge-tts/openpyxl ما ركبوا — البوت بيشتغل بسبلك إلا الصوت/إكسل)"
"$PY" -m pip install -q -r "$REPO/requirements.txt" \
  && echo "تنصيب requirements.txt كامل: OK (فيها livekit — المكالمات جاهزة)" \
  || echo "(livekit ما ركب — طبيعي على بايثون قديم/مرآة داخلية؛ المكالمات بتستنى)"

echo "--- فحص المصدر: $("$PY" -m pip config list 2>/dev/null | tr '\n' ' | ')"

if command -v crontab >/dev/null 2>&1; then
  { crontab -l 2>/dev/null | grep -v 'raad_night.py\|raad.py report\|raad.py resolve';
    echo "10 */6 * * * $PY $REPO/raad.py resolve >> $REPO/raad.log 2>&1";
    echo "30 1 * * * $PY $REPO/raad_night.py >> $REPO/raad.log 2>&1";
    echo "5 6 * * * $PY $REPO/raad.py report >> $REPO/raad.log 2>&1";
  } | crontab -
  echo "الكرون اتركب: فحص كل 6 ساعات + مراجعة 01:30 UTC + تقرير 06:05 UTC"
else
  echo "✗ ما في crontab — الكرون ما تركّب. الحل: sudo dnf install -y cronie && sudo systemctl enable --now crond"
fi

"$PY" "$REPO/raad.py" setup || echo "(raad.py setup فشل — شوف المخرجات فوق)"
echo "RAAD-INSTALLED-OK"
