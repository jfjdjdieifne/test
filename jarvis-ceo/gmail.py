#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
جيميل الدكتور — قراءة الصندوق + مسودة بموافقته → إرسال.
الطريقة: IMAP/SMTP + App Password (بلا OAuth وبلا منصة جوجل).
المتغيرات: GMAIL_ADDRESS, GMAIL_APP_PASSWORD (من myaccount.google.com/apppasswords).
"""
import email
import imaplib
import os
import re
import smtplib
import ssl
from email.header import decode_header
from email.message import EmailMessage
from email import policy

ADDR = os.environ.get("GMAIL_ADDRESS", "").strip()
APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "").strip()


def configured():
    return bool(ADDR and APP_PASSWORD)


def _imap():
    if not configured():
        raise RuntimeError("جيميل لسا مو موصول — الدكتور يحط GMAIL_ADDRESS و GMAIL_APP_PASSWORD بـ ~/jarvis-ceo.env")
    m = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    m.login(ADDR, APP_PASSWORD)
    return m


def _decode(s):
    if not s:
        return ""
    out = []
    for part, enc in decode_header(s):
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", "ignore"))
        else:
            out.append(part)
    return "".join(out)


def unread_count():
    m = _imap()
    try:
        m.select("INBOX", readonly=True)
        typ, data = m.search(None, "UNSEEN")
        return len(data[0].split()) if typ == "OK" and data and data[0] else 0
    finally:
        try:
            m.logout()
        except Exception:
            pass


def latest_unread(limit=5, max_chars=400):
    m = _imap()
    try:
        m.select("INBOX", readonly=True)
        typ, data = m.search(None, "UNSEEN")
        ids = (data[0].split() if typ == "OK" and data and data[0] else [])[-limit:]
        items = []
        for i in reversed(ids):
            typ, msg_data = m.fetch(i, "(BODY.PEEK[])")
            if typ != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1], policy=policy.default)
            frm = _decode(msg.get("From", ""))
            subj = _decode(msg.get("Subject", ""))
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_content()
                            break
                        except Exception:  # noqa: BLE001
                            continue
            else:
                try:
                    body = msg.get_content()
                except Exception:  # noqa: BLE001
                    body = ""
            body = re.sub(r"\s+", " ", str(body)).strip()
            items.append({"from": frm[:120], "subject": subj[:160], "preview": body[:max_chars]})
        return items
    finally:
        try:
            m.logout()
        except Exception:
            pass


def send(to_addr, subject, body_text):
    """إرسال حقيقي — ينفَّذ فقط بعد موافقة الدكتور (الزر ✅)."""
    if not configured():
        raise RuntimeError("جيميل لسا مو موصول")
    msg = EmailMessage()
    msg["From"] = ADDR
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body_text)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=30) as s:
        s.login(ADDR, APP_PASSWORD)
        s.send_message(msg)
    return True
