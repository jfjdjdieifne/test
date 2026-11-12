#!/usr/bin/env bash
# ============================================================================
# تشغيل جسر LMArena على نفس الموبايل (Android + Termux)
# - مجاني 100%، بلا بطاقة، بلا سيرفر
# - بيشتغل بس وقت الموبايل شغّال ومتصل (ويُفضّل يكون على الشاحن)
#
# التنصيب أول مرة (داخل Termux):
#   pkg update -y && pkg install -y python git curl
#   git clone --depth 1 https://github.com/jfjdjdieifne/test.git ~/jarvis
#   bash ~/jarvis/arena-bridge/deploy/termux-run.sh
# ============================================================================
set -euo pipefail

DIR="${DIR:-$HOME/jarvis/arena-bridge}"
cd "$DIR"

if [ ! -d .venv ]; then
  echo "▶ تجهيز Python venv (أول مرة — يأخذ دقائق)…"
  python -m venv .venv
  ./.venv/bin/pip install -q -U pip
  ./.venv/bin/pip install -q -r requirements.txt
fi

if [ ! -f .env ]; then
  KEY="$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"
  sed "s|^BRIDGE_API_KEY=.*|BRIDGE_API_KEY=$KEY|" .env.example > .env
  echo "✅ مفتاحك: $KEY  (خليه لجارفس)"
fi

echo "▶ تشغيل الجسر على 127.0.0.1:8000…"
nohup ./.venv/bin/python bridge.py > bridge.log 2>&1 &
echo $! > bridge.pid
sleep 3
curl -s -m 5 http://127.0.0.1:8000/health || echo "⚠️ ما في استجابة — شوف bridge.log"

cat <<'TIP'

────────────────────────────────────────────────────────────
صار الجسر شغال داخل الموبايل، بس جارفس (Cloudflare) ما بيوصل لـ localhost
تبع تلفونك. لازم نفق عام (Tunnel) مجاني:

الخيار 1 — cloudflared (بدون حساب، رابط عشوائي يتغير كل تشغيل):
  pkg install -y wget
  wget -O cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
  chmod +x cloudflared
  ./cloudflared tunnel --url http://127.0.0.1:8000
  → بيطبع رابط مثل https://xxxx.trycloudflare.com

الخيار 2 — ngrok (حساب مجاني + دومين ثابت مجاني):
  pkg install -y ngrok   # أو حمّل الـ APK/bin من ngrok.com
  ngrok config add-authtoken <TOKEN>
  ngrok http 8000 --domain=<اسمك>.ngrok-free.app

بعدها بجارفس:
  npx wrangler secret put ARENA_BRIDGE_URL   # الرابط https
  npx wrangler secret put ARENA_BRIDGE_KEY   # من .env
  → من تيليجرام: /arena test

ملاحظات صادقة:
• لما تقفل الشاشة/النت، الجسر يوقف — جارفس بيرجع تلقائياً لباقي المزودين.
• رابط trycloudflare يتغير كل تشغيل؛ ngrok بدومين ثابت أفضل.
• أيقونة Termux: اضغط عليها مطولاً → Keep running (وامنع تحسين البطارية لها).
• الاستهلاك: بياناتك اللي تمرّ عبر الجسر (كل سؤال/جواب) — راقب باقة النت.
────────────────────────────────────────────────────────────
TIP
