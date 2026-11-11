#!/usr/bin/env bash
# ============================================================================
# JARVIS Arena Bridge — تنصيب على Oracle Cloud Always Free (Ubuntu ARM/x86)
# الاستخدام: انسخ هذي الأوامر والصقها في نافذة الـ SSH (أو Oracle Cloud Shell)
#   bash oracle-bootstrap.sh
#
# Oracle Always Free: 4 vCPU ARM + 24GB RAM مجاناً للأبد (يحتاج بطاقة للتحقق فقط،
# بدون أي خصم). مناسب لتشغيل الجسر ٢٤/٧ بلا نوم.
# ============================================================================
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/jfjdjdieifne/test.git}"
DIR="${DIR:-$HOME/jarvis}"

echo "▶ تحديث النظام وتنصيب المتطلبات…"
sudo apt-get update -y -qq
sudo apt-get install -y -qq git curl python3 python3-venv python3-pip

echo "▶ تحميل المشروع…"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only || true
else
  git clone --depth 1 "$REPO_URL" "$DIR"
fi
cd "$DIR/arena-bridge"

echo "▶ تجهيز البيئة الافتراضية…"
python3 -m venv .venv
./.venv/bin/pip install -q -U pip
./.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  echo "▶ توليد BRIDGE_API_KEY وملف .env…"
  KEY="$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"
  sed "s|^BRIDGE_API_KEY=.*|BRIDGE_API_KEY=$KEY|" .env.example > .env
  echo "   ✅ مفتاحك (انسخه لجارفس): $KEY"
else
  echo "▶ .env موجود مسبقاً — ما لمسته."
fi

echo "▶ تنصيب خدمة systemd (تشغيل تلقائي + إعادة تشغيل عند الطوارئ)…"
sudo tee /etc/systemd/system/jarvis-arena-bridge.service >/dev/null <<EOF
[Unit]
Description=JARVIS Arena Bridge (LMArena -> OpenAI compatible)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DIR/arena-bridge
EnvironmentFile=$DIR/arena-bridge/.env
ExecStart=$DIR/arena-bridge/.venv/bin/python bridge.py
Restart=always
RestartSec=5
StandardOutput=append:$DIR/arena-bridge/bridge.log
StandardError=append:$DIR/arena-bridge/bridge.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now jarvis-arena-bridge
sleep 3
echo "▶ حالة الخدمة:"
sudo systemctl --no-pager --lines=5 status jarvis-arena-bridge || true

echo
echo "▶ فحص محلي:"
curl -s -m 5 http://127.0.0.1:8000/health || echo "   ⚠️ ما في استجابة — شوف: tail -50 $DIR/arena-bridge/bridge.log"

cat <<'TIP'

────────────────────────────────────────────────────────────
الخطوة الأخيرة: المنفذ 8000 لازم يكون مفتوح.
Oracle يبلوك المنافذ افتراضياً مرتين — افتحها كلها:

1) من لوحة Oracle (تقدر من المتصفح بالموبايل):
   Networking → Virtual Cloud Networks → subnet → Security Lists
   → Default Security List → Add Ingress Rule
   Source: 0.0.0.0/0 | Protocol: TCP | Destination Port: 8000

2) على السيرفر (iptables):
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
   sudo netfilter-persistent save

بعدها:  http://<IP-العام>:8000/health
واربط بجارفس:
   npx wrangler secret put ARENA_BRIDGE_URL   # http://<IP>:8000
   npx wrangler secret put ARENA_BRIDGE_KEY   # المفتاح المطبوع فوق
   npx wrangler secret put ARENA_BRIDGE_KEEPALIVE  # false (Oracle ما ينام)
────────────────────────────────────────────────────────────
TIP
