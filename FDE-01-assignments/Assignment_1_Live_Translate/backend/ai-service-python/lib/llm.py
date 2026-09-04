"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is your choice. The default example below is Anthropic Claude
(`pip install anthropic`, set ANTHROPIC_API_KEY). Hamza's launched version
used Google Gemini — either is fine. Whatever you pick:

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

MODEL_DEFAULT = os.getenv("MODEL", "claude-sonnet-4-6")


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default)."""
    # -----------------------------------------------------------------------
    # TODO (YOU):
    #   1. Build a system/user prompt that enforces Mexican Spanish and asks
    #      for the translation only.
    #   2. Call your LLM (async if the client supports it).
    #   3. Clean and return the string.
    #
    # --- Example: Anthropic Claude -----------------------------------------
    # from anthropic import AsyncAnthropic
    # client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY
    # msg = await client.messages.create(
    #     model=model,
    #     max_tokens=1024,
    #     system=(
    #         "You are a professional translator. Translate the user's English text "
    #         "into natural MEXICAN Spanish (es-MX). Return ONLY the translation — no "
    #         "quotes, no notes. Keep numbers, prices, and product codes unchanged."
    #     ),
    #     messages=[{"role": "user", "content": text}],
    # )
    # return msg.content[0].text.strip()
    # -----------------------------------------------------------------------
    raise NotImplementedError("Implement translate_text() in lib/llm.py")
