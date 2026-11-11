#!/usr/bin/env python3
"""
نشر جسر LMArena على Hugging Face Space — محرّك واحد يستخدمه:
  • GitHub Actions (‏.github/workflows/deploy-hf-space.yml) — بلا تيرمنال
  • أو من Termux/أي تيرمنال:  python hf_deploy.py --repo <user>/<space>

المتغيرات (أو الأعلام):
  HF_TOKEN        توكن HF بصلاحية write (إلزامي)
  SPACE_NAME      اسم الـ Space (افتراضي jarvis-arena-bridge) — يُنشأ تحت صاحب التوكن
  SPACE_REPO      بديل كامل: user/space (يتقدّم على SPACE_NAME)
  WITH_BROWSER    true/false — تضمين chromium (يرفع فرص نجاح gpt4free)
  BRIDGE_API_KEY  إن وُجد يُضبط كسر على الـ Space تلقائياً
  GITHUB_STEP_SUMMARY  إن وُجد يُكتب ملخص التشغيل (يستخدمه Actions)
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

try:
    from huggingface_hub import HfApi
except ImportError:
    sys.exit("نقص اعتماد: pip install huggingface_hub")

HERE = pathlib.Path(__file__).resolve().parent          # arena-bridge/deploy
ROOT = HERE.parent                                      # arena-bridge
HF_DIR = HERE / "huggingface"


def _flag(value: str | None, default: bool = True) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def deploy(repo_id: str | None, browser: bool, api_key: str) -> str:
    token = os.environ.get("HF_TOKEN", "").strip() or os.environ.get("HUGGINGFACE_TOKEN", "").strip()
    if not token:
        sys.exit("❌ ناقص HF_TOKEN — من huggingface.co/settings/tokens (صلاحية Write)")

    api = HfApi(token=token)

    if not repo_id:
        user = api.whoami().get("name") or ""
        if not user:
            sys.exit("❌ ما قدرت أعرف اسم المستخدم من التوكن")
        space = os.environ.get("SPACE_NAME", "jarvis-arena-bridge").strip() or "jarvis-arena-bridge"
        repo_id = f"{user}/{space}"

    print(f"▶ الـ Space: {repo_id}")
    api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True, private=False)
    print("▶ تم إنشاء/التأكد من الـ Space")

    dockerfile = (HF_DIR / ("Dockerfile" if browser else "Dockerfile.slim")).read_bytes()
    print(f"▶ Dockerfile: {'chromium' if browser else 'slim'}")

    files = {
        "README.md": (HF_DIR / "README.md").read_bytes(),
        "Dockerfile": dockerfile,
        "bridge.py": (ROOT / "bridge.py").read_bytes(),
        "requirements.txt": (ROOT / "requirements.txt").read_bytes(),
    }
    for name, data in files.items():
        api.upload_file(
            path_or_fileobj=data,
            path_in_repo=name,
            repo_id=repo_id,
            repo_type="space",
            commit_message=f"deploy: {name}",
        )
        print(f"✅ رُفع {name} ({len(data)} بايت)")

    if api_key:
        for key, value in (
            ("BRIDGE_API_KEY", api_key),
            ("DEFAULT_MODEL", os.environ.get("DEFAULT_MODEL", "auto")),
            ("G4F_FALLBACK", os.environ.get("G4F_FALLBACK", "true")),
        ):
            api.add_space_secret(repo_id=repo_id, key=key, value=value)
        print("🔑 حُفظت أسرار الـ Space (BRIDGE_API_KEY / DEFAULT_MODEL / G4F_FALLBACK)")
    else:
        print("⚠️ ما في BRIDGE_API_KEY — أضفه من Settings → Variables and secrets، وإلا الجسر مفتوح للجميع")

    url = f"https://{repo_id.replace('/', '-').lower()}.hf.space"
    lines = [
        "",
        f"🌉 رابط الجسر: {url}",
        f"   الفحص: {url}/health",
        "   الخطوة الجاية بتيليجرام:",
        f"     /arena url {url}",
        "     /arena key <نفس BRIDGE_API_KEY>",
        "     /arena test",
        "",
        "   ملاحظة: أول بناء على HF ياخد ٣–٧ دقائق — إذا /health لسا ما فتح، استنى وأعد.",
    ]
    print("\n".join(lines))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("## ✅ تم نشر جسر Arena\n\n")
            f.write(f"- **Space:** `{repo_id}`\n")
            f.write(f"- **الرابط:** {url}\n")
            f.write(f"- **فحص الصحة:** {url}/health\n")
            f.write(f"- **المفتاح:** {'مضبوط ✅' if api_key else 'ناقص ❌ (أضف BRIDGE_API_KEY)'}\n")
            f.write(f"- **المتصفح (chromium):** {'مضمّن' if browser else 'غير مضمّن'}\n\n")
            f.write("### اربطه من تيليجرام\n```\n")
            f.write(f"/arena url {url}\n/arena key <BRIDGE_API_KEY>\n/arena test\n```\n")
    return url


def main() -> None:
    ap = argparse.ArgumentParser(description="نشر جسر LMArena إلى Hugging Face Space")
    ap.add_argument("--repo", default=os.environ.get("SPACE_REPO", ""), help="user/space (افتراضي: من التوكن + SPACE_NAME)")
    ap.add_argument("--browser", dest="browser", action="store_true", help="ضمّن chromium (الافتراضي: نعم)")
    ap.add_argument("--slim", dest="browser", action="store_false", help="بدون chromium (بناء أسرع)")
    ap.set_defaults(browser=_flag(os.environ.get("WITH_BROWSER"), True))
    ap.add_argument("--key", default=os.environ.get("BRIDGE_API_KEY", ""), help="مفتاح الحماية BRIDGE_API_KEY")
    args = ap.parse_args()

    deploy(args.repo.strip() or None, bool(args.browser), args.key.strip())


if __name__ == "__main__":
    main()
