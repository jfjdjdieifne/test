#!/bin/bash
# جارفس/رعد — تحديث تلقائي من GitHub (فرع arena/e3e2c397-test)
# كل تشغيل = فحص HEAD رخيص O(1)؛ التنزيل والتفرض والرجعة عند الفشل.
# التنفيذ دائم بـ root عبر sudo -n (ec2-user بـ AL2023 = NOPASSWD افتراضياً للأوامر المحدودة)
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"
BRANCH="arena/e3e2c397-test"
STATE="$REPO/.deployed_sha"
BAK="/home/ec2-user/jarvis-ceo.autoupdate.bak"
LOG="$REPO/auto_update.log"
API="https://api.github.com/repos/jfjdjdieifne/test/branches/$BRANCH"

exec 9>"$REPO/.auto_update.lock"
flock -n 9 || exit 0

ENV_FILE="${CEO_ENV_PATH:-$HOME/jarvis-ceo.env}"
grab() { grep -E "^$1=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' '; }
TOKEN=$(grab GITHUB_TOKEN)
TG_TOKEN=$(grab TELEGRAM_BOT_TOKEN)
CHAT_ID=$(grab CEO_CHAT_ID)

notify() {
  [ -z "$TG_TOKEN" ] || [ -z "$CHAT_ID" ] && return 0
  curl -s -m 10 -X POST "https://api.telegram.org/bot$TG_TOKEN/sendMessage" \
    -H 'Content-Type: application/json' \
    -d "{\"chat_id\":\"$CHAT_ID\",\"text\":\"$1\"}" >/dev/null 2>&1 || true
}
[ -z "$TOKEN" ] && { echo "$(date -u +%F_%T) no GITHUB_TOKEN" >> "$LOG"; exit 0; }

REMOTE_SHA=$(curl -s -m 20 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "User-Agent: jarvis-autoupdate" "$API" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('commit') or {}).get('sha') or '')" 2>/dev/null)
[ -z "$REMOTE_SHA" ] && { echo "$(date -u +%F_%T) api-fail" >> "$LOG"; exit 0; }
DEPLOYED=$(cat "$STATE" 2>/dev/null || echo "")
[ "$REMOTE_SHA" = "$DEPLOYED" ] && exit 0

echo "$(date -u +%F_%T) deploying $REMOTE_SHA" >> "$LOG"
rm -rf "$BAK"; mkdir -p "$BAK"
tar --exclude=./.venv --exclude='./*.db' -cf - . | tar -xf - -C "$BAK"

TMP=$(mktemp -d)
DOWN_OK=1
curl -sL -m 180 -H "Authorization: token $TOKEN" -o "$TMP/src.tar.gz" "https://api.github.com/repos/jfjdjdieifne/test/tarball/$BRANCH" || DOWN_OK=0
if [ "$DOWN_OK" = "1" ]; then
  tar -xzf "$TMP/src.tar.gz" -C "$TMP" 2>/dev/null || DOWN_OK=0
fi
SRC=$(find "$TMP" -maxdepth 2 -mindepth 2 -type d -name jarvis-ceo 2>/dev/null | head -1)
if [ "$DOWN_OK" = "1" ] && [ -n "$SRC" ]; then
  cp -r "$SRC/." "$REPO/"
else
  rm -rf "$TMP"
  echo "$(date -u +%F_%T) download-or-layout-fail" >> "$LOG"
  notify "⚠️ تحديث تلقائي فشل بالتنزيل — ما صار شي نهائي، بحاول مرة ثانية بعد ١٠ دقايق"
  exit 0
fi
rm -rf "$TMP"

NEED_PIP=0
cmp -s "$BAK/requirements.txt" "$REPO/requirements.txt" || NEED_PIP=1

sudo -n systemctl restart jarvis-ceo >/dev/null 2>&1
RC=$?
if [ "$RC" != "0" ]; then
  systemctl restart jarvis-ceo >/dev/null 2>&1
  RC=$?
fi
if [ "$RC" != "0" ]; then
  echo "$REMOTE_SHA" > "$STATE"
  notify "🚨 النسخة نزلت بس ما قدت أعمل restart (بتحتاج صلاحية sudo). اشغل: sudo systemctl restart jarvis-ceo"
  echo "$(date -u +%F_%T) restart-permission-fail" >> "$LOG"
  exit 0
fi
sleep 6
OK=0
for i in 1 2 3 4 5; do
  systemctl is-active --quiet jarvis-ceo && { OK=1; break; }
  sleep 4
done
if [ "$OK" = "1" ]; then
  echo "$REMOTE_SHA" > "$STATE"
  MSG="✅ وصلني آخر تحديث تلقائياً (${REMOTE_SHA:0:7})"
  [ "$NEED_PIP" = "1" ] && MSG="$MSG — في حزم جديدة بـ requirements.txt: ابعتلي «تحديث» مرة وحدة"
  notify "$MSG"
  echo "$(date -u +%F_%T) deployed $REMOTE_SHA OK" >> "$LOG"
else
  cp -a "$BAK/." "$REPO/" 2>/dev/null
  sudo -n systemctl restart jarvis-ceo >/dev/null 2>&1 || true
  notify "🚨 التحديث التلقائي فشل بالتشغيل — رجّعت للنسخة القديمة تلقائياً. الحالة مستقرة."
  echo "$(date -u +%F_%T) ROLLBACK" >> "$LOG"
fi
