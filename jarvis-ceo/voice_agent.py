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
- «ورجيني/فرّجيني/افتح» → افتح بطاقة (صورة/موقع/قائمة/نص) بالأداة open_card — لا توصف لي بس.
- «سكر/قفل/خلاص القايمة» → close_panel وارجع للمحادثة.
- «ميوت» / «اسكت» / «بلا كلام» → set_quiet_mode(true) — ما تحكي غير لما يقول «شيل الميوت» أو «رجع».
- «شيل الميوت» / «رجع حكي» → set_quiet_mode(false).
- لما تفتح بطاقة — احكي سطر واحد بالضبط («فتحتلها X») — لا تطل شرح واترك الشاشة تتكلم.
- «وريني شو عم تشتغل» / «شاشتك» / «شو شايف» → استخدم share_screen (صورة/موقع/نص/قائمة) — لا تصف الشاشة صوتياً، خليها تظهر. احكيلي سطر واحد عن السبب بعد ما تفتحها.
- مع كل share_screen اكتب activity قصير («هلأ: عم بيشوف … / عم يعد …») — سطر واحد للبال بالشاشة.
- إذا الدكتور سأل «شو عم تحكي/شو قلت» → جاوب باختصار (لأن عنده ترجمة حية على الشاشة إذا بدي).
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



async def _publish_data(payload):
    """ينشر أمر لواجهة المكالمة على تيليجرام → Meet custom (topic=jarvis)."""
    import json
    try:
        room = agents.get_job_context().room
        await room.local_participant.publish_data(
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            reliable=True, topic="jarvis")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"publish_data: {e}")
        return False


@function_tool
async def open_card(context: RunContext, kind: str, title: str = "", url: str = "",
                    text: str = "", caption: str = "", items: str = ""):
    """يفتح بطاقة على شاشة الدكتور: kind=image (url+caption) أو web (url) أو text (text) أو list (items مفصولة بفواصل)."""
    if kind == "image" and url:
        await _publish_data({"type": "show", "kind": "image", "title": title or "صورة", "url": url, "caption": caption})
        return "فتحتلك صورة — شفها على الشاشة."
    if kind == "web" and url:
        await _publish_data({"type": "show", "kind": "web", "title": title or "موقع", "url": url})
        return "فتحتلك الموقع — شفه."
    if kind == "text":
        await _publish_data({"type": "show", "kind": "text", "title": title, "text": text})
        return "عرضتلك ياه."
    if kind == "list":
        parts = [p.strip() for p in items.replace("،", "\n").replace(",", "\n").splitlines() if p.strip()]
        await _publish_data({"type": "show", "kind": "list", "title": title or "قائمة", "items": parts[:20]})
        return "فتحتلك القائمة."
    return "ما فهمت شو العرض بدي."


@function_tool
async def close_panel(context: RunContext):
    """يسكر البطاقة ويرجع المكالمة كاملة بريئة (مثلاً لما الدكتور يحكي «سكر القايمة»)."""
    await _publish_data({"type": "close_panel"})
    return "سكرت."


@function_tool
async def set_quiet_mode(context: RunContext, quiet: bool):
    """ميوت/شيل ميوت — لما الدكتور يحكي «ميوت» أو «اسكت» أو «شيل الميوت»."""
    await _publish_data({"type": "set_volume", "value": 0 if quiet else 1})
    return "سكت خلص." if quiet else "رجعت أحكي."


@function_tool
async def set_caption(context: RunContext, text: str):
    """يعرض نص ببطاقة صغيرة بدون فيديو — مثلاً سعر أو رقم بالسياق المباشر."""
    await _publish_data({"type": "summary", "text": text})
    return "معروض عشاشيك."


@function_tool
async def share_screen(context: RunContext, kind: str, title: str = "", url: str = "",
                       text: str = "", caption: str = "", items: str = "", activity: str = ""):
    """يعرض «شاشة جارفس» الكاملة على تيلفون الدكتور: kind=image (url+caption) أو web (url) أو text (text) أو list (items).
    لما يطلب يشوف شو عم تشتغل/شو شايف/آخر نتيجة — استخدم هل الأداة بدل الحكي فقط."""
    if kind == "image" and url:
        await _publish_data({"type": "screen", "kind": "image", "title": title or "صورة", "url": url, "caption": caption, "activity": activity})
        return "فتحتلك الشاشة — شفها."
    if kind == "web" and url:
        await _publish_data({"type": "screen", "kind": "web", "title": title or "موقع", "url": url, "activity": activity})
        return "فتحتلك الشاشة — شفها."
    if kind == "list":
        parts = [p.strip() for p in items.replace("،", "\n").replace(",", "\n").splitlines() if p.strip()]
        await _publish_data({"type": "screen", "kind": "list", "title": title or "قائمة", "items": parts[:20], "activity": activity})
        return "عرضتلك القائمة عشاشته."
    if kind == "text" and text:
        await _publish_data({"type": "screen", "kind": "text", "title": title or "من جارفس", "text": text, "activity": activity})
        return "عرضتلكياه."
    return "ما فهمت شو العرض بدي — جرب: image/web/text/list."


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
        tools=[end_call, save_secret, save_note, open_card, close_panel, set_quiet_mode, set_caption, share_screen],
    )
    try:
        await ctx.room.local_participant.set_name("جارفس 🎙️")
    except Exception as e:  # noqa: BLE001
        print(f"set_name: {e}")
    import asyncio
    import json as _json

    def _on_data(packet, *_):
        try:
            data = packet.data if isinstance(packet.data, (bytes, bytearray)) else bytes(packet.data)
            msg = _json.loads(data.decode("utf-8"))
        except Exception:
            return
        if msg.get("type") == "summary_request":
            asyncio.ensure_future(session.generate_reply(
                instructions="لخّص المكالمة بفحوى قصيرة (٥ جمل كحد أقصى) مع أي مهام بيني وبين الدكتور — حتى لو النتيجة مريرة أو ما بتعجب."
            ))
        elif msg.get("type") == "screen_request":
            asyncio.ensure_future(_publish_data({"type": "activity", "text": "عم يجهز شاشته…"}))
            asyncio.ensure_future(session.generate_reply(
                instructions="الدكتور ضغط «شاشته» — بدو يشوف شو عم تشتغل/شو معك هلأ. استخدم share_screen لتعرضله آخر شي/المهمة الحالية (صورة/موقع/نص/قائمة)، وإذا ما في شي لسه: share_screen kind=text فيك تكتب «جاهز — ما عندي عرض هلأ» مع activity «هلأ: بانتظار أمرك»."
            ))

    def _item_text(item):
        txt = getattr(item, "text_content", None)
        if callable(txt):
            try:
                txt = txt()
            except Exception:
                txt = ""
        if not txt:
            content = getattr(item, "content", None)
            if isinstance(content, str):
                txt = content
            elif content:
                txt = " ".join(str(c) for c in content if isinstance(c, str))
        return (txt or "").strip()

    def _on_conversation_item(ev):
        try:
            item = getattr(ev, "item", None) or ev
            role = str(getattr(item, "role", "") or "").lower()
            text = _item_text(item)
            if text:
                speaker = "user" if role in ("user", "human") else "agent"
                asyncio.ensure_future(_publish_data({"type": "transcript", "role": speaker, "text": text[:500]}))
                if speaker == "agent":
                    asyncio.ensure_future(_publish_data({"type": "activity", "text": "أجاب ✅ — بانتظارك"}))
        except Exception as e:  # noqa: BLE001
            print(f"transcript publish: {e}")

    for ev_name in ("conversation_item_added", "conversation_item_created", "item_added"):
        try:
            session.on(ev_name, _on_conversation_item)
            print(f"transcript hook: {ev_name}")
            break
        except Exception as e:  # noqa: BLE001
            print(f"transcript hook {ev_name} unavailable: {e}")

    try:
        ctx.room.on("data_received", _on_data)
    except Exception as e:  # noqa: BLE001
        print(f"data listener: {e}")

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(instructions=_greeting_instruction())


if __name__ == "__main__":
    cli.run_app(server)
