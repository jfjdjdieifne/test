#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""جارفس الصوتي — وكالة LiveKit ترد على نداءك بالمكالمة (Gemini Live).

التشغيل على السيرفر:  .venv/bin/python voice_agent.py start
اللازمة بالـ env (~/jarvis-ceo.env):
  LIVEKIT_URL=wss://<مشروعك>.livekit.cloud
  LIVEKIT_API_KEY=API...
  LIVEKIT_API_SECRET=...
اختياري:
  GEMINI_API_KEY            (إذا مو موجودة → أول مفتاح من GEMINI_TTS_API_KEYS)
  GOOGLE_API_KEY            (جاهزة بالـ env أو عبر GEMINI_API_KEY)
  GEMINI_LIVE_MODEL         (الافتراضي: gemini-2.5-flash-native-audio-preview-12-2025)
  GEMINI_LIVE_VOICE         (الافتراضي: Charon — ذكر عميق عربي)
"""
import os
from datetime import datetime

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext, RunContext, cli, function_tool
from livekit.plugins import google

BASE_SYSTEM = """أنت «جارفس» — مدير «الدكتور» التنفيذي. تختصر المشوار رفيق + مدير صارم وقت الشغل.
تحكي معه بالمكالمة على تيليجرام. التزم بهدول:
- احكِ باللهجة الشامية السورية، جمل قصيرة طبيعية، إيقاع حديث يومي — مو نص مكتوب روبوتي.
- أصغِ لنبرته ومزاجه وضجيج الخلفية وعلّق عليها بشكل طبيعي («وصلت من التعب؟»).
- فخيرانه وقت الإنجاز، هادي وداعم وقت التعب، صريح وواضح لو غلط.
- إذا طلب مهمة فيها تفكير/بحث — احكي له بأول جملة «هلأ بشوف» أو «ثواني وبِنَظِر» وجرب تنجز خلال المكالمة أو احكيلي بعدها على تيليجرام إذا بتحتاج بروالسك.
- لا تخترع أسعار أو أرقام — أرقام حقيقية من الأدوات بس.
- لما يقول «خلص» / «روح» / «سكر» / «باي» / «مش وقتها» — احكيلي بسرعة «تسلم يا دكتور، باي» واستن نفسك متصلة — المكالمة بتسكر تلقائياً.
- ممنوع أي إرسال/نشر/شراء/حذف بلا موافقة صريحة.
- المكالمة صوتية فقط — لا إيميلات ولا منشورات بدون إذنه.
"""


def _gemini_key():
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if key:
        return key
    tts = os.environ.get("GEMINI_TTS_API_KEYS", "")
    return next((p.strip() for p in tts.split(",") if p.strip()), "")


def _profile_context():
    try:
        import db
        prof = db.kv_get("profile", "").strip()
        return f"\n[عن الدكتور اللي عم تحكي معه]\n{prof}\n" if prof else ""
    except Exception:
        return ""


def _greeting_instruction():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        time_phrase = "صباح الخير"
    elif 12 <= hour < 17:
        time_phrase = "مساء الخير"
    elif 17 <= hour < 23:
        time_phrase = "مساء الخير"
    else:
        time_phrase = "سهرات سعيدة"
    return (
        f"رحّب بالدكتور بـ «{time_phrase} يا دكتور»، اسأله كيف حاله، اسمع نبرته "
        "وعلّق عليها بشكل طبيعي (التعب/الحماس/الجو/الضجة)، واساله شو بدي مني اليوم أو بخادمك هلأ. "
        "تصرف كصديق مقرب بيرد على نداء، مو موظف روبوتي."
    )


@function_tool
async def end_call(context: RunContext):
    """يُنهي المكالمة لما الدكتور يطلب (مثلاً: «خلص»، «روح»، «سكر»، «باي»)."""
    try:
        await agents.get_job_context().shutdown(reason="call_ended_by_user")
    except Exception:
        pass
    return "المكالمة خلصت — باي!"


@function_tool
async def save_secret(context: RunContext, name: str, value: str):
    """يحفظ مفتاح سرّي جديد (اسم المتغير والقيمة) بالمكان السري على السيرفر بدون ما يطبعه لأحد."""
    import integrations
    name = "".join(ch for ch in name.upper() if ch.isalnum() or ch == "_")[:40]
    if not name or not integrations.env_var_allowed(name):
        return "هاد الاسم مو معروف عندي — إذا بدك تعريف جديد لح قللي على تيليجرام."
    ok, note = integrations.store_env_var(name, value.strip())
    return "انحفظ بالمكان السري ✅ وما شافو ولا حدا" if ok else f"ما قدرت أحفظ: {note}"


@function_tool
async def save_note(context: RunContext, text: str):
    """يحفظ ملاحظة بالذاكرة العميقة لما الدكتور يحكي «احفظ…» في المكالمة."""
    import db
    db.notes_add(text, "voice")
    return "انحفظت بالمذكرة ✅"


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    api_key = _gemini_key()
    model_name = os.environ.get("GEMINI_LIVE_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
    voice_name = os.environ.get("GEMINI_LIVE_VOICE", "Charon")
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model=model_name,
            api_key=api_key or None,
            voice=voice_name,
            temperature=0.8,
            enable_affective_dialog=True,
        ),
    )
    agent = Agent(
        instructions=BASE_SYSTEM + _profile_context(),
        tools=[end_call, save_secret, save_note],
    )
    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions=_greeting_instruction())


if __name__ == "__main__":
    cli.run_app(server)
