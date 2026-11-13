#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
عيون جارفس على مشروعه وملفاتنا — يفهمهم قبل ما يجاوب «هل نقدر نعمل X؟».
قراءة فقط بصرامة + ملخص مؤقت بالذاكرة (kv) حتى ما يرجع يقرأ كل مرة.
"""
import os
import subprocess
import time

PROJECT_DIR = os.environ.get("PROJECT_DIR", os.path.expanduser("~/jarvis-ceo"))
MAX_FILES = 140
MAX_FILE_READ = 30000
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".backups", "dist", "build"}
TEXT_EXT = {".py", ".js", ".ts", ".json", ".md", ".txt", ".yml", ".yaml", ".toml",
            ".ini", ".sh", ".html", ".css", ".jsx", ".tsx", ".service"}


def tree(root=None, max_depth=3):
    root = root or PROJECT_DIR
    lines = []
    if not os.path.isdir(root):
        return f"(مجلد المشروع مش موجود: {root})"
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        if depth > max_depth:
            dirnames[:] = []
            continue
        indent = "  " * depth
        if rel != ".":
            lines.append(f"{indent}{os.path.basename(dirpath)}/")
        for name in sorted(filenames)[:40]:
            if len(lines) >= MAX_FILES:
                lines.append("…(الباقي مقصوص)")
                return "\n".join(lines)
            lines.append(f"{indent}  {name}")
    return "\n".join(lines)


def read_file(path, root=None):
    root = os.path.realpath(root or PROJECT_DIR)
    dest = os.path.realpath(os.path.join(root, path))
    if not dest.startswith(root + os.sep):
        return None, "المسار خارج مجلد المشروع — مرفوض"
    if not os.path.isfile(dest):
        return None, "الملف مش موجود"
    ext = os.path.splitext(dest)[1].lower()
    if ext not in TEXT_EXT:
        return None, f"نوع الملف {ext} — بقرا النصوص بس"
    try:
        with open(dest, encoding="utf-8", errors="ignore") as fh:
            return fh.read(MAX_FILE_READ), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)


def search(query, root=None, max_hits=12):
    root = root or PROJECT_DIR
    if not os.path.isdir(root):
        return []
    q = (query or "").strip().lower()
    if not q:
        return []
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if len(hits) >= max_hits:
                return hits
            if os.path.splitext(name)[1].lower() not in TEXT_EXT:
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if len(hits) >= max_hits:
                            break
                        if q in line.lower():
                            rel = os.path.relpath(path, root)
                            hits.append(f"{rel}:{i}: {line.strip()[:140]}")
            except Exception:
                continue
    return hits


def summary(root=None, refresh=False):
    """ملخص قابل للحقن بالسياق — مخزن بالذاكرة (kv) لمدة 10 دقايق."""
    import db
    root = root or PROJECT_DIR
    cached = db.kv_get("project_summary")
    cached_ts = float(db.kv_get("project_summary_ts", "0") or 0)
    if cached and not refresh and time.time() - cached_ts < 600:
        return cached
    parts = [f"[مجلد المشروع: {root}]", "الشجرة:", tree(root)]
    readme, _err = read_file("README.md", root)
    if readme:
        parts.append("[README]\n" + readme[:1800])
    try:
        log = subprocess.run(["git", "log", "--oneline", "-6"], cwd=root,
                             capture_output=True, text=True, timeout=10)
        if log.stdout.strip():
            parts.append("[آخر الكوميتات]\n" + log.stdout.strip())
    except Exception:
        pass
    summary_text = "\n".join(parts)[:3500]
    db.kv_set("project_summary", summary_text)
    db.kv_set("project_summary_ts", str(time.time()))
    return summary_text
