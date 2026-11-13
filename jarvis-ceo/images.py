#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""توليد صور مجاني بلا مفاتيح (Pollinations) — للنشر والعينات السريعة."""
import urllib.parse


def image_url(prompt, width=1024, height=1024):
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("وصف الصورة فاضي")
    return (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt)
        + f"?width={int(width)}&height={int(height)}&nologo=true"
    )
