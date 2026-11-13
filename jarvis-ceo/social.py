#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
السوشيال ميديا تبع الدكتور — نشر X (تويتر) وFacebook Page وInstagram عبر APIs الرسمية.
كل منصة تشتغل بس إذا دكتور حط مفاتيحها بـ ~/jarvis-ceo.env — وكل نشر بيروح بموافقته أولاً.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.request
import urllib.error
import urllib.parse

# ---------- X (تويتر) — OAuth 1.0a ----------

X_API_KEY = os.environ.get("X_API_KEY", "").strip()
X_API_SECRET = os.environ.get("X_API_SECRET", "").strip()
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "").strip()
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "").strip()

def x_configured():
    return all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET])


def _pct(s):
    return urllib.parse.quote(str(s), safe="~-._")


def _oauth_header(method, url, params):
    oauth = {
        "oauth_consumer_key": X_API_KEY,
        "oauth_nonce": hashlib.sha256(os.urandom(32)).hexdigest()[:32],
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": X_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }
    all_params = dict(params)
    all_params.update(oauth)
    param_str = "&".join(f"{_pct(k)}={_pct(v)}" for k, v in sorted(all_params.items()))
    base = "&".join([method.upper(), _pct(url), _pct(param_str)])
    signing_key = f"{_pct(X_API_SECRET)}&{_pct(X_ACCESS_SECRET)}"
    sig = hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).hexdigest()
    oauth["oauth_signature"] = sig
    return "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))


def x_post(text):
    if not x_configured():
        raise RuntimeError("X لسا مو موصول — الدكتور يحط X_API_KEY/X_API_SECRET/X_ACCESS_TOKEN/X_ACCESS_SECRET")
    url = "https://api.twitter.com/2/tweets"
    body = json.dumps({"text": text[:28000]}).encode()
    auth = _oauth_header("POST", url, {})
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": auth,
        "Content-Type": "application/json",
        "User-Agent": "jarvis-ceo",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        return {"ok": True, "id": (data.get("data") or {}).get("id")}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"X HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}") from None


# ---------- Meta (Facebook Page + Instagram Business) ----------

META_PAGE_ID = os.environ.get("META_PAGE_ID", "").strip()
META_PAGE_TOKEN = os.environ.get("META_PAGE_TOKEN", "").strip()
META_IG_USER_ID = os.environ.get("META_IG_USER_ID", "").strip()

def fb_configured():
    return bool(META_PAGE_ID and META_PAGE_TOKEN)

def ig_configured():
    return bool(META_IG_USER_ID and META_PAGE_TOKEN)


def _graph(path, params, method="POST"):
    url = f"https://graph.facebook.com/v19.0/{path}"
    params = dict(params)
    params["access_token"] = META_PAGE_TOKEN
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(url + "?" + data.decode(), method="GET")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=40)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Meta HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}") from None


def fb_post(text, link=None):
    if not fb_configured():
        raise RuntimeError("فيسبوك لسا مو موصول — الدكتور يحط META_PAGE_ID و META_PAGE_TOKEN")
    params = {"message": text[:6000]}
    if link:
        params["link"] = link
    res = _graph(f"{META_PAGE_ID}/feed", params)
    return {"ok": True, "id": res.get("id")}


def ig_post(caption, image_url):
    """IG بدها صورة دايماً — تنشر عبر رابط صورة عام (CDN/GitHub/...)."""
    if not ig_configured():
        raise RuntimeError("انستغرام لسا مو موصول — الدكتور يحط META_IG_USER_ID و META_PAGE_TOKEN")
    if not image_url:
        raise RuntimeError("انستغرام ما بتقبل نص بلا صورة — اعطني رابط صورة")
    media = _graph(f"{META_IG_USER_ID}/media", {"image_url": image_url, "caption": caption[:2200]})
    cid = media.get("id")
    if not cid:
        raise RuntimeError(f"فشل تجهيز الوسيط: {media}")
    time.sleep(4)  # انستغرام بدها لحظات تجهز الصورة
    res = _graph(f"{META_IG_USER_ID}/media_publish", {"creation_id": cid})
    return {"ok": True, "id": res.get("id")}


def status():
    return {
        "x": x_configured(),
        "facebook": fb_configured(),
        "instagram": ig_configured(),
    }
