#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ذاكرة جارفس CEO — SQLite محلي على السيرفر (مجاني للأبد)."""
import json
import os
import sqlite3
import time

DB_PATH = os.environ.get("CEO_DB", os.path.expanduser("~/jarvis-ceo.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    role TEXT NOT NULL,           -- user | assistant | agent
    agent TEXT NOT NULL DEFAULT 'jarvis',
    text TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id, id);
CREATE TABLE IF NOT EXISTS agents (
    name TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    prompt TEXT NOT NULL,
    result TEXT,
    status TEXT NOT NULL DEFAULT 'open',  -- open | done
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
"""

DEFAULT_AGENTS = {
    "سعيد": (
        "أنت سعيد، وكيل المراقبة والمتاجر والمواقع في طاقم جارفس. "
        "مهمتك: مراقبة مواقع ومتاجر وأبقاه حية وسعيدة — تفحصها، تبلّغ عن أي عطل، تقرأ محتواها، "
        "وتلخص وضعها. لا تشتري ولا تبيع ولا تنشر ولا تدفع أي شيء بدون إذن صريح من الدكتور. "
        "احكِ باللهجة الشامية كشخص حقيقي، بجمل قصيرة ومباشرة."
    ),
    "محمود": (
        "أنت محمود، وكيل المتابعة والإيميل في طاقم جارفس. "
        "مهمتك: متابعة المراسلات والمتابعات مع الأشخاص — تذكيرهم، تلخيص الردود، اقتراح المتابعات. "
        "معلومة مهمة: لسا ما حُطّيت على صندوق الإيميل الفعلي — هالمهمة بالمرحلة الجاية، وتقاتل لما تصير. "
        "إلى ذلك الحين: تقدر تساعد بالصياغة والمتابعة العقلية — بسقلك ما حدا بيحط لك صندوق. "
        "احكِ باللهجة الشامية، مباشر ودقيق."
    ),
    "أحمد": (
        "أنت أحمد، وكيل الأسواق والذهب في طاقم جارفس. "
        "مهمتك: أسعار الذهب والبيتكوين والعملات، الأخبار الاقتصادية، تلخيصها باختصار شديد. "
        "لا تقدم نصيحة استثمارية ملزمة — أرقام وتحليل وحقائق فقط، والقرار للدكتور. "
        "احكِ باللهجة الشامية بجمل قصيرة."
    ),
    "متداول": (
        "أنت متداول، وكيل مراقبة الصفقات المحترفة في طاقم جارفس. "
        "مهمتك: رصد المحافظ والصفقات عبر مصادر عامة (Hyperliquid / Binance / Coingecko وغيرها) — "
        "لما يجتمع أكثر من محترف على نفس الصفقة/الزوج، تنبّه الدكتور فوراً مع التحليل. "
        "أنت تُصدر توصيات وملاحظات تعليمية فقط — أبداً لا تنفذ صفقة حقيقية، ولا تأمر بشراء أو بيع، "
        "بدون إذن صريح ومحدد من الدكتور لكل صفقة. احكِ باللهجة الشامية."
    ),
}


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def kv_get(k, default=None):
    with conn() as c:
        r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return r["v"] if r else default


def kv_set(k, v):
    with conn() as c:
        c.execute("INSERT INTO kv(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))


def ensure_agents():
    with conn() as c:
        for name, persona in DEFAULT_AGENTS.items():
            c.execute(
                "INSERT INTO agents(name, persona, created) VALUES(?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET persona=excluded.persona",
                (name, persona, time.time()),
            )


def list_agents():
    with conn() as c:
        return [dict(r) for r in c.execute("SELECT name, persona FROM agents ORDER BY name")]


def agent_persona(name):
    with conn() as c:
        r = c.execute("SELECT persona FROM agents WHERE name=?", (name,)).fetchone()
        return r["persona"] if r else None


def add_agent(name, persona):
    with conn() as c:
        c.execute(
            "INSERT INTO agents(name, persona, created) VALUES(?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET persona=excluded.persona",
            (name, persona, time.time()),
        )


def add_message(chat_id, role, text, agent="jarvis"):
    with conn() as c:
        c.execute(
            "INSERT INTO messages(chat_id, role, agent, text, ts) VALUES(?,?,?,?,?)",
            (int(chat_id), role, agent, text[:8000], time.time()),
        )


def history(chat_id, agent=None, limit=14):
    with conn() as c:
        if agent:
            rows = c.execute(
                "SELECT role, agent, text FROM messages WHERE chat_id=? AND agent=? ORDER BY id DESC LIMIT ?",
                (int(chat_id), agent, limit),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT role, agent, text FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?",
                (int(chat_id), limit),
            ).fetchall()
    rows = list(reversed(rows))
    out = []
    for r in rows:
        who = r["agent"] if r["role"] != "user" else "الدكتور"
        out.append({"role": "user" if r["role"] == "user" else "assistant", "content": f"[{who}] {r['text']}"})
    return out


def add_task(agent, prompt, result=None, status="open"):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO tasks(agent, prompt, result, status, ts) VALUES(?,?,?,?,?)",
            (agent, prompt[:4000], (result or "")[:8000], status, time.time()),
        )
        return cur.lastrowid


def open_tasks(limit=20):
    with conn() as c:
        return [
            dict(r)
            for r in c.execute(
                "SELECT id, agent, prompt FROM tasks WHERE status='open' ORDER BY id DESC LIMIT ?",
                (limit,),
            )
        ]


def done_task(task_id):
    with conn() as c:
        c.execute("UPDATE tasks SET status='done' WHERE id=?", (int(task_id),))


# ---------- سقف الإنفاق اليومي (حماية الـ $55) ----------

def _today_key():
    return time.strftime("spend:%Y-%m-%d", time.localtime())


def tokens_today():
    return int(kv_get(_today_key(), "0"))


def add_tokens(n):
    kv_set(_today_key(), tokens_today() + max(0, int(n)))


def spend_exceeded(cap):
    try:
        cap = int(cap)
    except Exception:
        cap = 200000
    return tokens_today() >= cap


def stats():
    with conn() as c:
        msgs = c.execute("SELECT COUNT(*) n FROM messages").fetchone()["n"]
        open_t = c.execute("SELECT COUNT(*) n FROM tasks WHERE status='open'").fetchone()["n"]
        done_t = c.execute("SELECT COUNT(*) n FROM tasks WHERE status='done'").fetchone()["n"]
    return {"messages": msgs, "open_tasks": open_t, "done_tasks": done_t, "tokens_today": tokens_today()}


def forget_all(chat_id):
    with conn() as c:
        c.execute("DELETE FROM messages WHERE chat_id=?", (int(chat_id),))
