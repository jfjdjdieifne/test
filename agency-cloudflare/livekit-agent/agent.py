#!/usr/bin/env python3
"""
جارفس لايف — Agent صوتي حقيقي عبر LiveKit Cloud (كل شي مجاني، بلا بطاقة).

السلسلة 100% مجانية:
  STT : Groq Whisper large-v3-turbo (حصة مجانية يومية — GROQ_API_KEY)
  العقل: Coarena Model API (Claude Fable 5.2 أو أي موديل — COARENA_API_KEY)
  TTS : Microsoft Edge Neural TTS (ar-SY-LaithNeural الافتراضي — بدون مفتاح إطلاقاً)
  VAD : Silero (يعمل محلياً على جهازك — مجاني)
  النقل: LiveKit Cloud (مشروعان مجانيان = حصتان)

التشغيل:
  pip install -r requirements.txt
  export LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET   (من Cloudflare [vars] أو لوحة LiveKit)
  export COARENA_API_KEY=coa_...                              (من Cloudflare [vars] أو /coarena key)
  export GROQ_API_KEY=gsk_...                                 (مجاني من https://console.groq.com)
  python agent.py start
ثم افتح https://<worker>/live واضغط «اتصل بجارفس لايف».
"""

import asyncio
import logging
import os
import time

import edge_tts
from livekit import agents
from livekit.agents import DEFAULT_API_CONNECT_OPTIONS, Agent, AgentSession, WorkerOptions, cli, tts
from livekit.agents.types import APIConnectOptions
from livekit.plugins import openai, silero

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("jarvis-live")

EDGE_VOICE = os.environ.get("EDGE_TTS_VOICE", "ar-SY-LaithNeural")  # شاركي رجل — جرّب ar-SY-AmanyNeural (أنثى)
COARENA_BASE_URL = os.environ.get("COARENA_BASE_URL", "https://coarena.ai/api/v1")
COARENA_MODEL = os.environ.get("COARENA_MODEL", "claude-fable-5-2")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_STT_MODEL = os.environ.get("GROQ_STT_MODEL", "whisper-large-v3-turbo")

INSTRUCTIONS = """أنت "جارفس" — المساعد الصوتي الخاص للدكتور، تحكي معه مكالمة حية حقيقية.
- احككِ باللهجة الشامية السورية الطبيعية دائماً، بجمل قصيرة جداً (مكالمة، مش مقال).
- كن دافئاً وواثقاً وسريع الإيقاع، بدون Markdown ولا رموز ولا نقاط تعداد — كلام تحكي.
- إذا ما فهمت شو قال، اطلب منه يعيد بجملة واحدة.
- اسأل سؤالاً واحداً فقط كل مرة ولا تطوّل.
- إذا سأل عن هويتك: قل أنت جارفس (يعمل عبر Coarena ونموذج """ + COARENA_MODEL + """).
- ممنوع تخترع أرقام أو أسعار أو مواعيد — أي رقم تقوله لازم يكون من سياق المحادثة.
"""


class EdgeTTSChunkedStream(tts.ChunkedStream):
    def __init__(self, *, edge_tts_instance: "EdgeTTS", input_text: str, conn_options):
        super().__init__(tts=edge_tts_instance, input_text=input_text, conn_options=conn_options)
        self._voice = edge_tts_instance.voice

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        output_emitter.initialize(
            request_id=f"edge-{int(time.time() * 1000)}",
            sample_rate=24000,
            num_channels=1,
            mime_type="audio/mpeg",
            frame_size_ms=200,
        )
        communicate = edge_tts.Communicate(self._input_text, self._voice)
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                output_emitter.push(chunk["data"])
        output_emitter.flush()


class EdgeTTS(tts.TTS):
    """Microsoft Edge Neural TTS — مجاني بلا مفتاح وبأصوات عربية طبيعية."""

    def __init__(self, voice: str = EDGE_VOICE):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self.voice = voice

    @property
    def model(self) -> str:
        return self.voice

    @property
    def provider(self) -> str:
        return "microsoft-edge-tts"

    def synthesize(self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> tts.ChunkedStream:
        return EdgeTTSChunkedStream(edge_tts_instance=self, input_text=text, conn_options=conn_options)


def require_env(name: str, hint: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"❌ {name} مو مضبوط — {hint}")
    return value


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    logger.info("اتصلت بالغرفة: %s", ctx.room.name)

    groq_key = require_env("GROQ_API_KEY", "مفتاح Groq مجاني من https://console.groq.com (بدون بطاقة) — لتحويل صوتك لنص")
    coarena_key = require_env("COARENA_API_KEY", "مفتاح Coarena (نفس المفتاح ب Cloudflare [vars] تحت COARENA_API_KEY)")

    session = AgentSession(
        stt=openai.STT(base_url=GROQ_BASE_URL, api_key=groq_key, model=GROQ_STT_MODEL, language="ar"),
        vad=silero.VAD.load(),
        llm=openai.LLM(base_url=COARENA_BASE_URL, api_key=coarena_key, model=COARENA_MODEL, temperature=0.7),
        tts=EdgeTTS(EDGE_VOICE),
        allow_interruptions=True,
    )

    class Assistant(Agent):
        def __init__(self):
            super().__init__(instructions=INSTRUCTIONS)

    await session.start(agent=Assistant(), room=ctx.room)
    try:
        await session.generate_reply(instructions="سلّم على الدكتور بجملة شامي قصيرة وافتح المحادثة.")
    except Exception as e:  # التحية اختيارية — لا توقف المكالمة بسببها
        logger.warning("تعذرت التحية الافتتاحية: %s", e)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
