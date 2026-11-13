#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub بتاع الدكتور — تيليجرام → تحكم كامل بالريبوز (قراءة، تعديل، برانش، PR، إنشاء repos).
التوكن: GITHUB_TOKEN (Fine-grained PAT مسوّيه الدكتور بنفسه من حسابه — ما بنعرفه إحنا).
كل شيء ينعمل بـ REST API مباشرة بلا مكتبات.
"""
import base64
import json
import os
import urllib.request
import urllib.error

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
DEFAULT_OWNER = os.environ.get("GITHUB_OWNER", "").strip()  # مثلاً: jfjdjdieifne — إذا فاضي منستنتج من التوكن


def configured():
    return bool(TOKEN)


def _req(method, path, body=None, accept="application/vnd.github+json"):
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN غير موجود — حطه بـ ~/jarvis-ceo.env (بلا تبعثه بالشات)")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "jarvis-ceo",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=40)
        raw = resp.read().decode("utf-8", "ignore")
        return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(f"GitHub HTTP {e.code}: {detail}") from None


def whoami():
    if not configured():
        return {"ok": False, "error": "GITHUB_TOKEN غير موجود"}
    try:
        me = _req("GET", "/user")
        return {"ok": True, "login": me.get("login"), "name": me.get("name")}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def list_repos(limit=15):
    repos = _req("GET", f"/user/repos?sort=updated&per_page={int(limit)}&affiliation=owner,collaborator")
    return [{"name": r["name"], "private": r.get("private"), "url": r.get("html_url"),
             "updated": r.get("updated_at", "")[:10], "desc": (r.get("description") or "")[:80]}
            for r in repos]


def _owner(repo):
    if "/" in repo:
        return repo.split("/", 1)
    owner = DEFAULT_OWNER or whoami().get("login")
    if not owner:
        raise RuntimeError("ما قدرت أستنتج صاحب الريبو — احط GITHUB_OWNER بـ .env")
    return owner, repo


def get_file(repo, path, ref=None):
    owner, name = _owner(repo)
    q = f"?ref={ref}" if ref else ""
    data = _req("GET", f"/repos/{owner}/{name}/contents/{path}{q}")
    if isinstance(data, list):
        raise RuntimeError("المطلوب ملف مش مجلد — اكتب ملف محدد")
    content = base64.b64decode(data.get("content", "")).decode("utf-8", "ignore")
    return {"content": content, "sha": data.get("sha"), "path": path, "repo": f"{owner}/{name}"}


def put_file(repo, path, content, message, branch=None, create_branch_from=None):
    """ينشئ/يحدّث ملف واحد بكوميت (اختياري: ينشئ برانش جديد أولاً)."""
    owner, name = _owner(repo)
    branch = branch or (create_branch_from and f"jarvis/{os.urandom(3).hex()}") or None
    if create_branch_from:
        base = _req("GET", f"/repos/{owner}/{name}/git/ref/heads/{create_branch_from}")
        sha = (base.get("object") or {}).get("sha")
        _req("POST", f"/repos/{owner}/{name}/git/refs",
             {"ref": f"refs/heads/{branch}", "sha": sha})
    q = f"?ref={branch}" if branch else ""
    try:
        existing = _req("GET", f"/repos/{owner}/{name}/contents/{path}{q}")
        sha = existing.get("sha") if isinstance(existing, dict) else None
    except Exception:  # noqa: BLE001 — الملف مش موجود بعد
        sha = None
    body = {
        "message": message[:400],
        "content": base64.b64encode(content.encode("utf-8")).decode(),
    }
    if sha:
        body["sha"] = sha
    if branch:
        body["branch"] = branch
    res = _req("PUT", f"/repos/{owner}/{name}/contents/{path}", body)
    return {
        "ok": True,
        "commit": (res.get("commit") or {}).get("sha", "")[:10],
        "branch": branch or (res.get("content", {}).get("path") and "main/default"),
        "url": (res.get("content") or {}).get("html_url", ""),
    }


def create_repo(name, private=True, description=""):
    body = {"name": name, "private": bool(private), "description": description[:200],
            "auto_init": True}
    res = _req("POST", "/user/repos", body)
    return {"ok": True, "name": res.get("full_name"), "url": res.get("html_url")}


def create_pull_request(repo, head, base, title, body=""):
    owner, name = _owner(repo)
    res = _req("POST", f"/repos/{owner}/{name}/pulls",
               {"title": title[:200], "head": head, "base": base, "body": body[:3000]})
    return {"ok": True, "number": res.get("number"), "url": res.get("html_url")}


def latest_release(repo):
    owner, name = _owner(repo)
    try:
        res = _req("GET", f"/repos/{owner}/{name}/releases/latest")
        return {"ok": True, "tag": res.get("tag_name"), "name": res.get("name"), "url": res.get("html_url")}
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
