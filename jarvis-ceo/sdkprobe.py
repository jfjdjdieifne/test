#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""«تجربة الحلقة» — فحص حي: هل كوارينا تمرر tool-calling النظيف لـ OpenAI Agents SDK؟
معزولة عن مسار البوت — نتيجة واحدة مفيدة، صفر مخاطرة على النواة.
النتيجة الوحيدة المهمة: ✅ «الحلقة الرسمية شغالة مع كوارينا» أو ❌ واضح مع السبب."""
import asyncio
import json
import os

PROBE_MODEL_DEFAULT = "gpt-6-1-sol"


def _coarena_key():
    raw = os.environ.get("COARENA_API_KEYS") or os.environ.get("COARENA_API_KEY", "")
    keys = [k.strip().strip("\"'") for k in raw.replace(";", ",").split(",") if k.strip()]
    return keys[0] if keys else ""


def probe(model=None):
    model = model or os.environ.get("SDK_PROBE_MODEL") or PROBE_MODEL_DEFAULT
    key = _coarena_key()
    base = os.environ.get("COARENA_BASE_URL", "https://coarena.ai/api/v1").rstrip("/")
    if not key:
        return False, "لا يوجد مفتاح كوارينا مضبوط على السيرفر."
    os.environ["OPENAI_API_KEY"] = key
    os.environ["OPENAI_BASE_URL"] = base
    try:
        from agents import Agent, Runner, function_tool
    except Exception as e:  # noqa: BLE001
        return False, f"openai-agents مو منصب بعد ({type(e).__name__}) — «تحديث» ثم جرّب مرة تانية."

    @function_tool
    def add_numbers(a: int, b: int) -> int:
        """يجمع رقمين صحيحين."""
        return a + b

    agent = Agent(name="jarvis-probe",
                  model=model,
                  instructions="إذا بدك جمع رقمين — استخدم أداة add_numbers حصرًا، ما تحسب بنفسك. ارجع الرقم بس.",
                  tools=[add_numbers])

    async def _run():
        return await Runner.run(agent, "كم ناتج 345 + 678؟ استخدم الأداة.", max_turns=3)

    try:
        result = asyncio.run(_run())
    except Exception as e:  # noqa: BLE001
        err = str(e)
        low = err.lower()
        if ("400" in err and "tool" in low) or ("tools" in low and "not supported" in low):
            return False, f"كوارينا بترفض الأدوات على هالموديل — {err[:200]}"
        if "401" in err or "403" in err:
            return False, f"كوارينا رفضت المفتاح للبروتوكول الرسمي — {err[:120]}"
        return False, f"{type(e).__name__}: {err[:200]}"

    final = str(getattr(result, "final_output", "") or "")
    blob = final + json.dumps(getattr(result, "new_items", []), default=str)
    if "1023" in blob:
        return True, f"Agents SDK + «{model}» — tool-calling شغال، الجواب صح (345+678 = 1023) ✅"
    return False, (f"الحلقة اشتغلت بس الجواب غير المتوقع: «{final[:80]}» — "
                   f"يعني كوارينا ما بتمرر استدعاء الأدوات بشكل موثوق على «{model}»")
