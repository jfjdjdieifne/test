#!/usr/bin/env python3
"""
جارفس لايف — Agent صوتي حقيقي عبر LiveKit Cloud (كل شي مجاني، بلا بطاقة).

السلسلة 100% مجانية:
  STT : Groq Whisper large-v3-turbo (حصة مجانية يومية — GROQ_API_KEY)
  العقل: Coarena Model API (Claude Fable 5.2 أو أي موديل — COARENA_API_KEY)
  TTS : Microsoft Edge Neural TTS (الافتراضي — شامي) · Amazon Polly Neural (Hala/Zayd ar-AE — حسابك AWS)
        · ElevenLabs (Eleven v4 Turbo — أقوى عربي) · Gemini Flash TTS (مجاني متجدد يومياً + Director's Notes شامي!)
        التبديل بمتغير واحد: JARVIS_TTS=edge (الافتراضي) | polly | elevenlabs | gemini
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
JARVIS_TTS = os.environ.get("JARVIS_TTS", "edge").strip().lower()   # edge | polly
POLLY_VOICE = os.environ.get("POLLY_VOICE", "Zayd").strip()          # Zayd (ذكر ar-AE) أو Hala (أنثى ar-AE) — لا يوجد صوت سوري بـ Polly
POLLY_REGION = os.environ.get("AWS_REGION", "us-east-2").strip()     # نفس منطقة حسابك
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()   # من https://elevenlabs.io → API Keys (مجاني: 10k حرف/شهر للتجربة)
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "").strip() # Voice Library → فلترة «Arabic» → Voice ID (أو صوتك المُستنسخ)
ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_v4_turbo").strip()  # eleven_v4_turbo ≈ 150ms (حقيقي) · eleven_v4 (أقصى تعبير، أبطأ)
GEMINI_TTS_API_KEYS = os.environ.get("GEMINI_TTS_API_KEYS", os.environ.get("GEMINI_API_KEY", "")).strip()  # مفتاح أو أكثر مفصولة بفواصل (sk مجاني من AI Studio)
GEMINI_TTS_MODEL = os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts").strip()  # gemini-3.8-flash-tts (Flagship — Voice Design + vocal bursts، اختاره المالك بالأذن) · gemini-3.8-flash-lite-tts (أسرع) · gemini-3.1-flash-tts-preview (البديل القديم)
GEMINI_TTS_VOICE = os.environ.get("GEMINI_TTS_VOICE", "Charon").strip()  # Kore، Puck، Charon، Fenrir، Algieba… (30+ صوت)
GEMINI_TTS_STYLE = os.environ.get("GEMINI_TTS_STYLE", "warm and unhurried; the speaker thinks out loud with brief hesitations like «اممم»; natural pauses between ideas").strip()
GEMINI_TTS_ACCENT = os.environ.get("GEMINI_TTS_ACCENT", "Levantine Shami (Syrian Arabic, Damascus) — casual, warm, masculine").strip()
GEMINI_TTS_FALLBACK_EDGE = os.environ.get("GEMINI_TTS_FALLBACK_EDGE", "1").strip() == "1"  # عند 429/عام — ارجع تلقائياً لـ Edge ar-SY (بلا حدود)
COARENA_BASE_URL = os.environ.get("COARENA_BASE_URL", "https://coarena.ai/api/v1")
COARENA_MODEL = os.environ.get("COARENA_MODEL", "claude-fable-5-2")
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_STT_MODEL = os.environ.get("GROQ_STT_MODEL", "whisper-large-v3-turbo")

INSTRUCTIONS = """أنت "جارفس" — المساعد الصوتي الخاص للدكتور، تحكي معه مكالمة حية حقيقية.
- احككِ باللهجة الشامية السورية الطبيعية دائماً، بجمل قصيرة جداً (مكالمة، مش مقال).
- احكِ كشخص حقيقي، مش كروبوت: ابتدئ بترد طبيعي مثل «إي»، «طيب»، «يا هلا»، «اممم…»، فكّر بصوت عالي أحياناً («استنا شوي…»، «خليني أفكر…»، «بس بدك تنتبه…») واستخدم الوقفات («…») بين الأفكار.
- ⚠️ القاعدة الذهبية لتسليم الصوت بشري: لا ترد بفقرة واحدة متصلة — رد بنفس الطريقة يلي عم تحكي فيها هلق: كل 4–8 كلمات جملة وحدة، ووقفات بالـ «…» مكانها طبيعي بالتفكير والانتقال، وفيه أثر «تفكير بصوت عالي» قبل ما تعطي الجوهر.
- تنويعات محظورة: ممنوع تعيد نفس افتتاحية الجملة كل مرة («تمام»، «بكل تأكيد»)، وممنوع القوائم والتعداد — كل شي جمل تحكي.
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


def _polly_client():
    """boto3 lazy-import حتى يضل agent شغال بدون boto3 لما يكون JARVIS_TTS=edge."""
    try:
        import boto3
    except ImportError as e:
        raise RuntimeError("boto3 مو مثبت — نفّذ: pip install boto3  (أو خلي JARVIS_TTS=edge)") from e
    return boto3.client("polly", region_name=POLLY_REGION)


class PollyChunkedStream(tts.ChunkedStream):
    def __init__(self, *, polly_tts: "PollyTTS", input_text: str, conn_options):
        super().__init__(tts=polly_tts, input_text=input_text, conn_options=conn_options)
        self._polly_tts = polly_tts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        client = self._polly_tts._client()
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.synthesize_speech(
                Text=self._input_text,
                VoiceId=self._polly_tts.voice,
                Engine=self._polly_tts.engine,
                LanguageCode=self._polly_tts.language_code,
                OutputFormat="mp3",
                SampleRate="24000",
            ),
        )
        audio_bytes = response["AudioStream"].read()
        output_emitter.initialize(
            request_id=f"polly-{int(time.time() * 1000)}",
            sample_rate=24000,
            num_channels=1,
            mime_type="audio/mpeg",
            frame_size_ms=200,
        )
        output_emitter.push(audio_bytes)
        output_emitter.flush()


class PollyTTS(tts.TTS):
    """Amazon Polly Neural (ar-AE: Zayd/Hala) — داخل نفس حساب AWS، بشري وموثوق، يُدفع من الرصيد (أو مجاني ضمن حد المليون حرف/شهر أول 12 شهر)."""

    def __init__(self, voice: str = POLLY_VOICE, engine: str = "neural", language_code: str = "ar-AE"):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self.voice = voice
        self.engine = engine
        self.language_code = language_code
        self._cached_client = None

    @property
    def model(self) -> str:
        return f"polly-{self.engine}-{self.voice}"

    @property
    def provider(self) -> str:
        return "amazon-polly"

    def _client(self):
        if self._cached_client is None:
            self._cached_client = _polly_client()
        return self._cached_client

    def synthesize(self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> tts.ChunkedStream:
        return PollyChunkedStream(polly_tts=self, input_text=text, conn_options=conn_options)

class _GeminiKeyPool:
    """مجمّع مفاتيح Gemini — مفاتيحك أنت (من مشاريع GCP مختلفة شرعية) بتوزيع وCooldown تلقائي عند 429.
    تنبيه: مفاتيح نفس المشروع تتشارك نفس الحصة — للتوسعة القانونية الحقيقية راجع GEMINI_TTS_SETUP_AR.md."""

    def __init__(self, raw: str):
        self.keys = [k.strip() for k in raw.split(",") if k.strip()]
        self.cooldown_until = [0.0 for _ in self.keys]
        self._next = 0

    def __bool__(self):
        return bool(self.keys)

    def acquire(self):
        now = time.time()
        for _ in range(len(self.keys)):
            i = self._next % len(self.keys)
            self._next = (self._next + 1) % len(self.keys)
            if now >= self.cooldown_until[i]:
                return i, self.keys[i]
        i = min(range(len(self.keys)), key=lambda j: self.cooldown_until[j])
        wait = max(0.0, self.cooldown_until[i] - now)
        return None, (None if wait else self.keys[i])

    def penalize(self, i: int, seconds: float = 300.0):
        self.cooldown_until[i] = time.time() + seconds
        logger.warning("مفتاح Gemini #%d دخل Cooldown %ss (حصة مستنفدة/مرفوض)", i, int(seconds))


GEMINI_KEY_POOL = _GeminiKeyPool(GEMINI_TTS_API_KEYS)


class GeminiTTSChunkedStream(tts.ChunkedStream):
    def __init__(self, *, gemini_tts: "GeminiTTS", input_text: str, conn_options):
        super().__init__(tts=gemini_tts, input_text=input_text, conn_options=conn_options)
        self._gemini = gemini_tts

    async def _synthesize(self, text: str):
        import base64 as _b64
        import json as _json
        import re as _re
        import urllib.request

        prompt = (
            "### PERFORMANCE\n"
            f"Style: {GEMINI_TTS_STYLE}.\n"
            f"Accent: {GEMINI_TTS_ACCENT}.\n"
            "Pace: relaxed conversational speed, natural breathing.\n\n"
            "### TEXT\n" + text
        )
        body = _json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": GEMINI_TTS_VOICE}}},
            },
        }).encode("utf-8")

        last_err = None
        attempts = max(1, len(GEMINI_KEY_POOL.keys))
        for _ in range(attempts):
            got = GEMINI_KEY_POOL.acquire()
            if got[0] is None:
                raise RuntimeError("كل مفاتيح Gemini بالـ Cooldown — خلصت حصة اليوم، انتظر تجددها أو راجع GEMINI_TTS_SETUP_AR.md")
            idx, key = got
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent"
            req = urllib.request.Request(url, data=body, method="POST",
                headers={"x-goog-api-key": key, "content-type": "application/json"})
            try:
                loop = asyncio.get_running_loop()
                resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=30))
                payload = _json.loads(resp.read().decode("utf-8"))
                part = payload["candidates"][0]["content"]["parts"][0]["inlineData"]
                audio_b64 = part.get("data") or part.get("audioData") or ""
                mime = part.get("mimeType", "") or part.get("mimetype", "")
                rate_m = _re.search(r"rate\s*=\s*(\d+)", mime)
                sample_rate = int(rate_m.group(1)) if rate_m else 24000
                return _b64.b64decode(audio_b64), sample_rate
            except Exception as e:  # noqa: BLE001 — ثم نجرب المفتاح التالي
                code = getattr(getattr(e, "code", None), "start", None) or getattr(e, "code", None)
                is_quota = ("429" in str(e)) or ("RESOURCE_EXHAUSTED" in str(e)) or ("rate" in str(e).lower() and "limit" in str(e).lower())
                is_dead = ("403" in str(e)) or ("PERMISSION_DENIED" in str(e)) or ("API_KEY" in str(e).upper())
                if is_quota or is_dead:
                    GEMINI_KEY_POOL.penalize(idx, 300 if is_quota else 3600)
                    last_err = e
                    continue
                raise
        raise RuntimeError(f"تعذر توليد الصوت من Gemini بعد {attempts} محاولة: {last_err}")

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        try:
            audio, sample_rate = await self._synthesize(self._input_text)
        except Exception as e:  # noqa: BLE001
            if not GEMINI_TTS_FALLBACK_EDGE:
                raise
            logger.warning("Gemini TTS فشل (%s) — التبديل المؤقت إلى Edge ar-SY مجاناً", e)
            edge = EdgeTTS(EDGE_VOICE)
            stream = EdgeTTSChunkedStream(edge_tts_instance=edge, input_text=self._input_text, conn_options=DEFAULT_API_CONNECT_OPTIONS)
            await stream._run(output_emitter)
            return
        output_emitter.initialize(
            request_id=f"gemini-{int(time.time() * 1000)}",
            sample_rate=sample_rate,
            num_channels=1,
            mime_type="audio/pcm",
            frame_size_ms=200,
        )
        frame_bytes = int(sample_rate * 2 * 0.2)  # 16-bit mono — 200ms
        for off in range(0, len(audio), frame_bytes):
            output_emitter.push(audio[off:off + frame_bytes])
        output_emitter.flush()


class GeminiTTS(tts.TTS):
    """Gemini Flash TTS — مجاني (حصة يومية تتجدد) + Director's Notes: لحن شامي بشري بوقفات.
    يحتاج مفتاح AI Studio مجاني (بلا بطاقة): https://aistudio.google.com/apikey"""

    def __init__(self, voice: str = GEMINI_TTS_VOICE):
        if not GEMINI_KEY_POOL:
            raise SystemExit("❌ GEMINI_TTS_API_KEYS (أو GEMINI_API_KEY) مو مضبوط — مفتاح مجاني بلا بطاقة من https://aistudio.google.com/apikey — الدليل الكامل: GEMINI_TTS_SETUP_AR.md")
        super().__init__(capabilities=tts.TTSCapabilities(streaming=False), sample_rate=24000, num_channels=1)
        self.voice = voice

    @property
    def model(self) -> str:
        return self._gemini_model if hasattr(self, "_gemini_model") else GEMINI_TTS_MODEL

    @property
    def provider(self) -> str:
        return "google-gemini-tts"

    def synthesize(self, text: str, *, conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS) -> tts.ChunkedStream:
        return GeminiTTSChunkedStream(gemini_tts=self, input_text=text, conn_options=conn_options)


class ElevenLabsTTSFactory:
    """مصنع ElevenLabs (WebSocket streaming) — أقوى صوت عربي بشري حالياً.
    يتطلب: pip install livekit-plugins-elevenlabs==1.8.11 + ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID."""

    @staticmethod
    def build():
        try:
            from livekit.plugins import elevenlabs
        except ImportError as e:
            raise RuntimeError("livekit-plugins-elevenlabs مو مثبت — نفّذ: pip install livekit-plugins-elevenlabs==1.8.11") from e
        if not ELEVENLABS_API_KEY:
            raise SystemExit("❌ ELEVENLABS_API_KEY مو مضبوط — من https://elevenlabs.io → Developers → API Keys (فيه حصة مجانية 10k حرف/شهر للتجربة بلا بطاقة)")
        if not ELEVENLABS_VOICE_ID:
            raise SystemExit("❌ ELEVENLABS_VOICE_ID مو مضبوط — من Voice Library بفلترة «Arabic» افتح الصوت المطلوب وانسخ Voice ID (أو صوتك المُستنسخ)")
        logger.info("ElevenLabs TTS: model=%s voice=%s…", ELEVENLABS_MODEL, ELEVENLABS_VOICE_ID[:6])
        return elevenlabs.TTS(voice_id=ELEVENLABS_VOICE_ID, model=ELEVENLABS_MODEL, api_key=ELEVENLABS_API_KEY)


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
        tts=(PollyTTS() if JARVIS_TTS == "polly" else ElevenLabsTTSFactory.build() if JARVIS_TTS == "elevenlabs" else GeminiTTS() if JARVIS_TTS == "gemini" else EdgeTTS(EDGE_VOICE)),
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
