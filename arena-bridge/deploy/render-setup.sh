#!/usr/bin/env bash
# ============================================================================
# JARVIS Arena Bridge — نشر على Render (خطة مجانية) من الموبايل
# Render المجاني: بلا بطاقة، لكن الخدمة تنام بعد 15 دقيقة خمول و512MB RAM فقط.
# الحل للنوم: ARENA_BRIDGE_KEEPALIVE=true بجارفس (cron كل 10 دقائق تصحّيها).
# 512MB قد ما تكفي متصفح gpt4free — إذا صار OOM انتقل لـ Hugging Face أو Oracle.
# ============================================================================
set -euo pipefail
echo "هذا الملف مرجع/شرح — ما بينفّذ تنصيب تلقائي على Render."
cat <<'GUIDE'
خطوات Render من متصفح الموبايل:
1) ارفع المشروع على GitHub (موجود أصلاً: jfjdjdieifne/test).
2) render.com → New → Web Service → Connect repo.
3) Root Directory: arena-bridge
   Runtime: Docker   (أو Python مع Start Command تحت)
   Start Command: uvicorn bridge:app --host 0.0.0.0 --port $PORT
4) Environment Variables:
   BRIDGE_API_KEY = <مفتاح طويل عشوائي>
   DEFAULT_MODEL  = auto
   G4F_FALLBACK   = true
   (PORT يعطيه Render تلقائياً — لا تثبته)
5) Deploy → خُد الرابط https://<name>.onrender.com
6) بجارفس:
   npx wrangler secret put ARENA_BRIDGE_URL     # https://<name>.onrender.com
   npx wrangler secret put ARENA_BRIDGE_KEY     # نفس BRIDGE_API_KEY
   npx wrangler secret put ARENA_BRIDGE_KEEPALIVE  # true  ← ضروري هنا
7) /arena test من تيليجرام.

بديل أخف (لو صار OOM): حط LMArenaBridge_URL لجسر خفيف، أو ارفع MEMORY.
GUIDE
