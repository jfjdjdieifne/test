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
  { crontab -l 2>/dev/null | grep -v 'raad_night.py\|raad.py report\|raad.py resolve\|auto_update.sh';
    echo "10 */6 * * * $PY $REPO/raad.py resolve >> $REPO/raad.log 2>&1";
    echo "30 1 * * * $PY $REPO/raad_night.py >> $REPO/raad.log 2>&1";
    echo "5 6 * * * $PY $REPO/raad.py report >> $REPO/raad.log 2>&1";
    echo "*/10 * * * * bash $REPO/auto_update.sh >> $REPO/auto_update.log 2>&1";
  } | crontab -
  echo "الكرون اتركب: فحص الدفتر + مراجعة ليلية + تقرير صباحي + تحديث تلقائي كل 10 دقايق"
  # marker لأول نشرة (حتى التحديث التلقائي ما يعيد نفس النشر)
  SHA=$(curl -s -m 15 -H "Authorization: Bearer $(grep -E '^GITHUB_TOKEN=' ~/jarvis-ceo.env | head -1 | cut -d= -f2- | tr -d '"')" -H "Accept: application/vnd.github+json" -H "User-Agent: raad-install" "https://api.github.com/repos/jfjdjdieifne/test/branches/arena/e3e2c397-test" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('commit') or {}).get('sha') or '')" 2>/dev/null || true)
  [ -n "$SHA" ] && echo "$SHA" > "$REPO/.deployed_sha" && echo "marker: $SHA"
else
  echo "✗ ما في crontab — بركّب systemd timers بدل الكرون (ما بيحتاج أي حزمة)"
  if sudo -n true 2>/dev/null; then
    sudo cp "$REPO"/raad_systemd/*.service "$REPO"/raad_systemd/*.timer /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now raad-night.timer raad-report.timer raad-resolve.timer raad-update.timer
    systemctl list-timers 'raad-*' --no-pager || true
    echo "systemd timers اتركبت ✅ (بدل الكرون)"
  else
    echo "✗ لا كرون ولا صلاحية sudo لكتابة /etc/systemd/system — اعطِ ec2-user sudo أو نفّذها بلكونسول مع sudo"
  fi
fi

"$PY" "$REPO/raad.py" setup || echo "(raad.py setup فشل — شوف المخرجات فوق)"
echo "RAAD-INSTALLED-OK"
