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

from anthropic import AsyncAnthropic

MODEL_DEFAULT = os.getenv("MODEL", "claude-sonnet-4-6")

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    # Lazy init: app.py's load_dotenv() runs after this module is imported,
    # so building the client at import time would miss ANTHROPIC_API_KEY.
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's English text into "
    "natural, conversational MEXICAN Spanish (es-MX) — not generic or Castilian "
    "Spanish. Return ONLY the translation, with no preamble, no notes, and no "
    "surrounding quotes. Keep numbers, prices (with their currency symbols), "
    "and product/model codes unchanged."
)


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into `target` (Mexican Spanish by default)."""
    msg = await _get_client().messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    return msg.content[0].text.strip().strip('"').strip("'")
