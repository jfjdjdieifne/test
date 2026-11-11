#!/usr/bin/env python3
"""
رفع الجسر إلى Hugging Face Space من الموبايل (Termux) بأمر واحد.
مجاني بالكامل، بدون بطاقة. يحتاج توكن HF بصلاحية "write".

الاستخدام:
    pip install huggingface_hub
    export HF_TOKEN=hf_xxxxxxxx
    python hf_push.py --repo <اسم-حسابك>/jarvis-arena-bridge

بعد الرفع، الـ Space يبني نفسه ويعطيك:
    https://<اسم-حسابك>-jarvis-arena-bridge.hf.space
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi
except ImportError:
    sys.exit("نقص اعتماد: pip install huggingface_hub")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # arena-bridge/

SPACE_README = """---
title: JARVIS Arena Bridge
emoji: 🌉
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# جسر LMArena لجارفس

خدمة FastAPI متوافقة مع OpenAI توجّه الطلبات إلى LMArena (gpt4free/Arena + LMArenaBridge).

**لا تحط أي مفتاح بالكود.** من Settings → Variables and secrets أضف:
`BRIDGE_API_KEY` (إلزامي) · `DEFAULT_MODEL=auto` · `G4F_FALLBACK=true`
"""

DOCKERFILE = """FROM python:3.12-slim

# chromium + مكتبات نظام تسمح لـ gpt4free بمحاكاة متصفح حقيقي (nodriver/playwright)
ENV PYTHONUNBUFFERED=1 PORT=7860 HOST=0.0.0.0 G4F_BROWSER=1
RUN apt-get update && apt-get install -y --no-install-recommends \\
        chromium ca-certificates fonts-liberation ffmpeg \\
        libnss3 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libasound2 \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bridge.py .

EXPOSE 7860
CMD ["uvicorn", "bridge:app", "--host", "0.0.0.0", "--port", "7860"]
"""


def build_files(browser: bool) -> dict[str, Path | bytes]:
    dockerfile = DOCKERFILE if browser else (HERE / "huggingface" / "Dockerfile").read_bytes()
    return {
        "README.md": SPACE_README.encode("utf-8"),
        "Dockerfile": dockerfile,
        "bridge.py": (ROOT / "bridge.py").read_bytes(),
        "requirements.txt": (ROOT / "requirements.txt").read_bytes(),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="ارفع جسر LMArena إلى Hugging Face Space")
    ap.add_argument("--repo", required=True, help="اسم الـ Space مثل: myuser/jarvis-arena-bridge")
    ap.add_argument("--browser", action="store_true", help="ضمّن chromium (يبني أبطأ، يرفع فرص نجاح gpt4free)")
    ap.add_argument("--private", action="store_true", help="Space خاص (يحتاج خطة مدفوعة للموارد المجانية)")
    args = ap.parse_args()

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        sys.exit("لازم توكن: export HF_TOKEN=hf_xxx  (من huggingface.co/settings/tokens بصلاحية write)")

    api = HfApi(token=token)
    print(f"▶ إنشاء/التأكد من الـ Space: {args.repo}")
    try:
        api.create_repo(repo_id=args.repo, repo_type="space", space_sdk="docker", exist_ok=True, private=args.private)
    except Exception as e:
        print(f"  ⚠️ create_repo: {e}")

    files = build_files(args.browser)
    for name, content in files.items():
        print(f"▶ رفع {name} ({len(content)} بايت)")
        if isinstance(content, Path):
            api.upload_file(path_or_fileobj=str(content), path_in_repo=name, repo_id=args.repo, repo_type="space")
        else:
            api.upload_file(path_or_fileobj=content, path_in_repo=name, repo_id=args.repo, repo_type="space")

    host = args.repo.replace("/", "-").lower()
    print("\n✅ تم الرفع. الخطوات الجاية:")
    print(f"1) Settings → Variables and secrets → New secret:  BRIDGE_API_KEY=<مفتاح طويل عشوائي>")
    print(f"2) استنى البناء ثم افتح: https://{host}.hf.space/health")
    print("3) اربط جارفس:")
    print(f"   npx wrangler secret put ARENA_BRIDGE_URL   # https://{host}.hf.space")
    print("   npx wrangler secret put ARENA_BRIDGE_KEY   # نفس BRIDGE_API_KEY")
    print("   # Keep-alive يشتغل تلقائياً لأن العنوان hf.space")
    print("   npx wrangler deploy")
    print("4) من تيليجرام: /arena test")


if __name__ == "__main__":
    main()
