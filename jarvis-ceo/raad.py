#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
رعد — وكيل التحليل الورقي ⚡ (ورقي 100% — ما بينفذ أي صفقة حقيقية أبداً)
===========================================================================
يشوف سوق كريبتو عبر Binance public API (مجاني، بلا مفتاح)، مرشح ذكي بفلسفة
«الرفض قبل الاقتراح»: ما بتوصلك توصية إلا إذا اجتازت الفلتر — وبالعادة
الرسالة اليومية: «ما في شي يستاهل — الصمت هنة».
كل بطاقة تتنزل بالدفتر (sqlite) وتتقرّر بعدين كتابي استراتيجية بملف نصي
بمجلد raad_strategies/.
الأوامر:
  raad.py setup     تهيئة الدفتر + فحص تيليجرام + فحص Coarena (بثّ تجريبي)
  raad.py once      فحص فوري — يرسل بطاقة لو المرشح اجتاز، وإلا يسجل الصمت
  raad.py resolve   يقرر الصفقات المفتوحة القديمة بالسعر الحالي
  raad.py report    تقرير الصباح (يصير تلقائياً بالكرون 06:05 UTC)
  raad.py resume    تشغيل رعد بعد إيقاف الطوارئ التلقائي
  raad.py backtest  اختبار رجعي على سنين كاملة للمرشح المدمج (أرقام لا وعود)
"""
import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

BINANCE = ["https://data-api.binance.vision/api/v3", "https://api.binance.com/api/v3"]
RAAD_DB = os.environ.get("RAAD_DB", os.path.expanduser("~/jarvis-raad.db"))
STATE_PATH = os.environ.get("RAAD_STATE", os.path.expanduser("~/jarvis-raad-state.json"))
REPO = os.path.dirname(os.path.abspath(__file__))
STRATS_DIR = os.path.join(REPO, "raad_strategies")
PLAYBOOK = os.path.join(REPO, "PLAYBOOK.md")
DISCLAIMER = "\n\n⚠️ ورقي بحت — مو نصيحة مالية ملزمة. القرار والحجم والوقف عليك."

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS calls(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL, symbol TEXT NOT NULL, tf TEXT NOT NULL, side TEXT NOT NULL,
    entry REAL, stop REAL, target REAL, atr REAL, confidence INTEGER,
    regime TEXT, reason TEXT, source TEXT DEFAULT 'filter',
    status TEXT NOT NULL DEFAULT 'open',   -- open | win | loss | flat
    exit_price REAL, r_multiple REAL, pnl_pct REAL, resolved_ts REAL, note TEXT
);
CREATE TABLE IF NOT EXISTS lessons(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, text TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
"""

def _load_env_file():
    """يقرا ~/jarvis-ceo.env سطر سطر (KEY=VALUE فقط) — بدون أي تنفيذ. ما بطغى على env مضبوط مسبقاً."""
    path = os.environ.get("CEO_ENV_PATH") or os.path.expanduser("~/jarvis-ceo.env")
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:  # noqa: BLE001
        pass


_load_env_file()

def _kv_get(path, k):
    try:
        with sqlite3.connect(path) as c:
            r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
            return (r[0] or "").strip() if r else ""
    except Exception:
        return ""

def tg_creds():
    """(token, chat_id) — يقرا من env أولاً، ثم من قاعدة البوت (~/jarvis-ceo.db → kv) كنسخة احتياط."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("CEO_CHAT_ID", "").strip()
    if not chat or not token:
        dbp = os.environ.get("CEO_DB") or os.path.expanduser("~/jarvis-ceo.db")
        chat = chat or _kv_get(dbp, "ceo_chat_id")
        token = token or _kv_get(dbp, "telegram_bot_token")
    return token, chat


def now_ts():
    return time.time()

def db():
    c = sqlite3.connect(RAAD_DB)
    c.row_factory = sqlite3.Row
    c.executescript(DB_SCHEMA)
    return c

def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"paused": False, "calibration": {}, "last_change_date": ""}

def save_state(s):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)

def telegram_send(text):
    bot_token, ceo_chat_id = tg_creds()
    if not bot_token or not ceo_chat_id:
        print("TELEGRAM غير مضبوط — حط TELEGRAM_BOT_TOKEN وCEO_CHAT_ID بـ ~/jarvis-ceo.env")
        print(text)
        return False
    body = json.dumps({"chat_id": ceo_chat_id, "text": text[:4000]}).encode()
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=body, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20):
            return True
    except Exception as e:  # noqa: BLE001
        print(f"telegram fail: {e}")
        return False

# ---------- بيانات السوق (Binance public — مجاني وبدون مفتاح) ----------

def _get(path):
    last = None
    for base in BINANCE:
        try:
            with urllib.request.urlopen(base + path, timeout=15) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError(f"تعذر جلب البيانات من Binance: {last}")

def klines(symbol="BTCUSDT", interval="4h", limit=200):
    raw = _get(f"/klines?symbol={symbol}&interval={interval}&limit={limit}")
    bars = []
    for k in raw:
        bars.append({"ts": k[0] / 1000.0, "o": float(k[1]), "h": float(k[2]),
                     "l": float(k[3]), "c": float(k[4]), "v": float(k[5])})
    return bars

def price_now(symbol="BTCUSDT"):
    d = _get(f"/ticker/price?symbol={symbol}")
    return float(d["price"])

# ---------- مؤشرات حقيقية (stdlib فقط) ----------

def ema(values, period):
    if not values:
        return []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out

def sma(values, period):
    out = []
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= period:
            s -= values[i - period]
        out.append(s / min(i + 1, period))
    return out

def atr(bars, period=14):
    trs = []
    for i, b in enumerate(bars):
        if i == 0:
            trs.append(b["h"] - b["l"])
            continue
        pc = bars[i - 1]["c"]
        trs.append(max(b["h"] - b["l"], abs(b["h"] - pc), abs(b["l"] - pc)))
    out = [trs[0]]
    for t in trs[1:]:
        out.append((out[-1] * (period - 1) + t) / period)
    return out

def pct_rank(values, v):
    if not values:
        return 50.0
    below = sum(1 for x in values if x <= v)
    return 100.0 * below / len(values)

def regime(bars):
    closes = [b["c"] for b in bars]
    e20 = ema(closes, 20)
    a = atr(bars)[-1]
    px = closes[-1]
    atrp = 100.0 * a / px if px else 0
    slope = (100.0 * (e20[-1] - e20[-6]) / e20[-6]) if e20[-6] else 0
    if atrp > 6.0:
        r = "عاصفة تذبذب"
    elif slope > 0.4:
        r = "ترند صاعد"
    elif slope < -0.4:
        r = "ترند هابط"
    else:
        r = "عرضي"
    return r, atrp, e20[-1], ema(closes, 50)[-1]

# ---------- المرشح المدمج (فكرة بداية بسيطة — الحكم للدفتر) ----------

def candidate(symbol="BTCUSDT"):
    bars = klines(symbol, "4h", 180)
    if len(bars) < 80:
        return None
    closes = [b["c"] for b in bars]
    vols = [b["v"] for b in bars]
    e20, e50 = ema(closes, 20), ema(closes, 50)
    a = atr(bars)[-1]
    reg, atrp, _, _ = regime(bars)
    if reg == "عاصفة تذبذب":
        return None
    cross_idx = None
    for i in range(-6, 0):
        j = len(bars) + i
        if j < 1:
            continue
        prev, cur = j - 1, j
        if e20[prev] <= e50[prev] and e20[cur] > e50[cur]:
            cross_idx = ("long", i)
            break
        if e20[prev] >= e50[prev] and e20[cur] < e50[cur]:
            cross_idx = ("short", i)
            break
    if not cross_idx:
        return None
    side, _i = cross_idx
    vol_pct = pct_rank(vols[-60:], vols[-1])
    if vol_pct < 60:
        return None
    if side == "long" and reg == "ترند هابط":
        return None
    if side == "short" and reg == "ترند صاعد":
        return None
    px = closes[-1]
    if side == "long":
        stop, target = px - 1.5 * a, px + 2.5 * a
    else:
        stop, target = px + 1.5 * a, px - 2.5 * a
    conf = 60 + (10 if vol_pct >= 80 else 0) + (5 if (side == "long") == (reg == "ترند صاعد") else 0)
    conf = min(conf, 80)
    return {"symbol": symbol, "tf": "4h", "side": side, "entry": px, "stop": stop,
            "target": target, "atr": a, "confidence": conf, "regime": reg,
            "reason": f"تقاطع EMA20/50 {'صعودي' if side == 'long' else 'هبوطي'} + حجم أعلى من {vol_pct:.0f}% من آخر ٦٠ شمعة"}

def llm_opinion(c):
    """استدعاء واحد على الأكثر لكل بطاقة — Coarena (claude-fable-5-2 افتراضياً)."""
    try:
        import brain
        msgs = [
            {"role": "system", "content": "أنت رعد، محلل أسواق — تكتب بالشامية بجمل قصيرة. مهمتك: تشريح الفكرة (قوة/ضعف/مخاطر كامنة)، مو توليد إشارات جديدة. لا تعطي ضمانات ربح."},
            {"role": "user", "content": (
                f"المرشح: {c['symbol']} {c['tf']} — {'شراء' if c['side'] == 'long' else 'بيع'} ورقي.\n"
                f"السعر {c['entry']:.2f} | الوقف {c['stop']:.2f} | الهدف {c['target']:.2f} | ATR {c['atr']:.2f}\n"
                f"النظام: {c['regime']} | السبب: {c['reason']} | الثقة المبدئية {c['confidence']}/100\n"
                "اكتب ٥ أسطر كحد أقصى: أقوى سبب للدخول + أخطر خطر + كيف تُبطل الفكرة. بدون مقدمات."
            )},
        ]
        out = brain.chat(msgs, temperature=0.4, max_tokens=350)
        return (out or "").strip() or "(ما قدر العقل يكتب — القرار بالدفتر)"
    except Exception as e:  # noqa: BLE001
        return f"(رأي العقل تعذر: {e})"

def log_call(c, source="filter"):
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO calls(ts,symbol,tf,side,entry,stop,target,atr,confidence,regime,reason,source)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (now_ts(), c["symbol"], c["tf"], c["side"], c["entry"], c["stop"], c["target"],
             c["atr"], c["confidence"], c["regime"], c["reason"], source))
        return cur.lastrowid

def resolve_all():
    """يقرر كل صفقة مفتوحة أقدم من ٦ ساعات — يرجع عدد المحلولة."""
    resolved = 0
    with db() as conn:
        rows = conn.execute("SELECT * FROM calls WHERE status='open'").fetchall()
    for r in rows:
        if now_ts() - r["ts"] > 36 * 3600:
            forced = True
        else:
            forced = False
        if not forced and now_ts() - r["ts"] < 6 * 3600:
            continue
        try:
            bars = klines(r["symbol"], "1h", 500)
        except Exception as e:  # noqa: BLE001
            print(f"resolve fetch fail: {e}")
            continue
        outcome = None
        exit_p = None
        for b in bars:
            if b["ts"] <= r["ts"]:
                continue
            if r["side"] == "long":
                if b["l"] <= r["stop"]:
                    outcome, exit_p = "loss", r["stop"]; break
                if b["h"] >= r["target"]:
                    outcome, exit_p = "win", r["target"]; break
            else:
                if b["h"] >= r["stop"]:
                    outcome, exit_p = "loss", r["stop"]; break
                if b["l"] <= r["target"]:
                    outcome, exit_p = "win", r["target"]; break
        if outcome is None:
            if not forced:
                continue
            exit_p = price_now(r["symbol"])
            outcome = "win" if ((exit_p - r["entry"]) * (1 if r["side"] == "long" else -1)) > 0 else "loss"
        risk = abs(r["entry"] - r["stop"]) or 1e-9
        direction = 1 if r["side"] == "long" else -1
        r_mult = ((exit_p - r["entry"]) * direction) / risk
        pnl = 100.0 * ((exit_p - r["entry"]) * direction) / r["entry"]
        with db() as conn:
            conn.execute(
                "UPDATE calls SET status=?, exit_price=?, r_multiple=?, pnl_pct=?, resolved_ts=? WHERE id=?",
                (outcome, exit_p, r_mult, pnl, now_ts(), r["id"]))
        resolved += 1
    return resolved

def stats():
    with db() as conn:
        rows = conn.execute("SELECT * FROM calls WHERE status IN ('win','loss') ORDER BY resolved_ts DESC LIMIT 100").fetchall()
    n = len(rows)
    if n == 0:
        return {"n": 0, "win_rate": 0, "expectancy_r": 0, "pf": 0, "max_dd": 0}
    wins = [r for r in rows if r["status"] == "win"]
    losses = [r for r in rows if r["status"] == "loss"]
    wr = 100.0 * len(wins) / n
    exp_r = sum(r["r_multiple"] or 0 for r in rows) / n
    gain = sum(r["r_multiple"] for r in wins)
    pain = -sum(r["r_multiple"] for r in losses)
    pf = (gain / pain) if pain > 0 else (999.0 if gain > 0 else 0.0)
    eq, peak, dd = 0.0, 0.0, 0.0
    for r in reversed(rows):
        eq += r["r_multiple"] or 0
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    cal = {}
    for r in rows:
        bucket = min(9, max(0, int((r["confidence"] or 50) // 10)))
        cal.setdefault(bucket, []).append(1 if r["status"] == "win" else 0)
    cal_map = {int(k): round(100 * sum(v) / len(v), 1) for k, v in cal.items()}
    return {"n": n, "win_rate": round(wr, 1), "expectancy_r": round(exp_r, 3), "pf": round(pf, 2), "max_dd": round(dd, 2), "calibration": cal_map}

def setup():
    db().close()
    ok = telegram_send("⚡ رعد تفعّل ورقيًا — جاهز يشوف السوق ويرجع يقرر كل توصية بالدفتر. صفقات حقيقية: مستحيل بدون ✅ صريح منك.")
    try:
        import brain
        brain.chat([{"role": "user", "content": "قل «رعد جاهز» بكلمتين فقط."}], max_tokens=20)
        coarena = "وصلك صح ✅"
    except Exception as e:  # noqa: BLE001
        coarena = f"ما وصل ⚠️ ({e}) — البطاقات رح تنزل بس بدون رأي العقل لحد ما يصلح المفتاح"
    telegram_send(f"فحص Coarena: {coarena}")
    print("setup done. telegram:", ok)

def once():
    state = load_state()
    if state.get("paused"):
        telegram_send("⏸ رعد متوقف بالطوارئ (دفتر الخسارة ما يقبل مزايدة). لترجيعه: python3 raad.py resume")
        return
    c = candidate("BTCUSDT")
    if not c:
        print("no candidate — silence")
        return
    cid = log_call(c)
    opinion = llm_opinion(c)
    side_ar = "شراء ورقي 🟢" if c["side"] == "long" else "بيع ورقي 🔴"
    msg = (f"⚡ رعد — بطاقة ورقي #{cid}\n"
           f"{c['symbol']} {c['tf']} — {side_ar}\n"
           f"الدخول ~{c['entry']:.2f} | الوقف {c['stop']:.2f} | الهدف {c['target']:.2f}\n"
           f"النظام: {c['regime']} | الثقة {c['confidence']}/100\n"
           f"ليش: {c['reason']}\n"
           f"العقل: {opinion}") + DISCLAIMER
    telegram_send(msg)

def report():
    resolve_all()
    s = stats()
    state = load_state()
    try:
        reg, atrp, e20, e50 = regime(klines("BTCUSDT", "4h", 100))
        px = price_now("BTCUSDT")
        market = f"BTC {px:,.2f} | {reg} | ATR% {atrp:.2f} | EMA20 {e20:,.0f} / EMA50 {e50:,.0f}"
    except Exception as e:  # noqa: BLE001
        market = f"(السوق تعذر جلبه: {e})"
    head = "⏸ رعد متوقف بالطوارئ" if state.get("paused") else "📊 تقرير رعد الصباحي (ورقي)"
    perf = (f"آخر {s['n']} صفقة مقفلة — فوز {s['win_rate']}% | expectancy {s['expectancy_r']}R | "
            f"profit factor {s['pf']} | max DD {s['max_dd']}R") if s["n"] else "الدفتر لسا فاضي — ما في أرقام، وهاذا طبيعي أول أسبوع."
    news = news_brief()
    msg = f"{head}\n{market}\n{perf}"
    if news:
        msg += f"\n{news}"
    msg += "\n(ما رح توصلك بطاقة إلا إذا المرشح اجتاز الفلتر — الصمت موقف مقصود.)" + DISCLAIMER
    telegram_send(msg)

def news_brief():
    key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not key:
        return ""
    try:
        body = json.dumps({"api_key": key, "query": "bitcoin crypto market today",
                           "max_results": 3, "search_depth": "basic"}).encode()
        req = urllib.request.Request("https://api.tavily.com/search", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
        items = data.get("results") or []
        return "📰 " + " ؛ ".join((it.get("title") or "").strip() for it in items[:3])
    except Exception as e:  # noqa: BLE001
        return f"(الأخبار تعذرت: {e})"

def resume():
    s = load_state()
    s["paused"] = False
    save_state(s)
    telegram_send("⚡ رعد رجّع للشغل — الدفتر بيظل الحكم.")

def backtest(symbol="BTCUSDT", limit=1000):
    bars = klines(symbol, "4h", limit)
    if len(bars) < 120:
        print("بيانات غير كافية"); return
    results = []
    i = 80
    while i < len(bars) - 1:
        window = bars[: i + 1]
        closes = [b["c"] for b in window]
        vols = [b["v"] for b in window]
        e20, e50 = ema(closes, 20), ema(closes, 50)
        a = atr(window)[-1]
        reg, _, _, _ = regime(window)
        side = None
        if reg != "عاصفة تذبذب":
            if e20[-2] <= e50[-2] and e20[-1] > e50[-1] and pct_rank(vols[-60:], vols[-1]) >= 60:
                side = "long"
            elif e20[-2] >= e50[-2] and e20[-1] < e50[-1] and pct_rank(vols[-60:], vols[-1]) >= 60:
                side = "short"
        if side:
            entry = closes[-1]
            if side == "long":
                stop, target = entry - 1.5 * a, entry + 2.5 * a
            else:
                stop, target = entry + 1.5 * a, entry - 2.5 * a
            outcome = None
            for b in bars[i + 1:]:
                if side == "long":
                    if b["l"] <= stop: outcome = ("loss", stop); break
                    if b["h"] >= target: outcome = ("win", target); break
                else:
                    if b["h"] >= stop: outcome = ("loss", stop); break
                    if b["l"] <= target: outcome = ("win", target); break
            if outcome:
                res, exit_p = outcome
                risk = abs(entry - stop) or 1e-9
                direction = 1 if side == "long" else -1
                results.append((res, ((exit_p - entry) * direction) / risk))
            i += 6  # لا نتداخل الصفقات
        else:
            i += 1
    n = len(results)
    if n == 0:
        print("ما في صفقات بالمدة — المرشح نادر وهي ميزة مو عيب."); return
    wr = 100 * sum(1 for r, _ in results if r == "win") / n
    exp_r = sum(r_ for _, r_ in results) / n
    wins = sum(max(r_, 0) for _, r_ in results)
    pain = -sum(min(r_, 0) for _, r_ in results)
    pf = wins / pain if pain else 999.0
    print(f"BACKTEST {symbol} — {n} صفقة على آخر ~{limit} شمعة 4h")
    print(f"فوز {wr:.1f}% | expectancy {exp_r:.2f}R | profit factor {pf:.2f}")
    print("ملاحظة: عينة الماضي ≠ ضمان المستقبل. الدفتر الحين هو الحكم.")

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "setup":
        setup()
    elif cmd == "once":
        once(); resolve_all()
    elif cmd == "resolve":
        print("resolved:", resolve_all())
    elif cmd == "report":
        report()
    elif cmd == "resume":
        resume()
    elif cmd == "backtest":
        backtest(sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT",
                 int(sys.argv[3]) if len(sys.argv) > 3 else 1000)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
