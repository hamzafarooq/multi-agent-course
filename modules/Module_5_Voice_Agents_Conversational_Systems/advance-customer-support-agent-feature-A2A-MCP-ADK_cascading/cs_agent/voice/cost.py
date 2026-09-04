"""Cost accounting for the voice cascade — turn token counts into a USD estimate.

Every stage of the cascade calls a model, and each call has a price:

    STT  (gemini-*-flash-lite)        audio in  -> text out
    LLM  (gemini-2.5-flash: agent,    text in   -> text out
          + A2A Judge + A2A Masker)
    TTS  (gemini-*-flash-tts)         text in   -> audio out

We bill per token using `usage_metadata` where the model reports it (STT, the
agent, TTS) and a length-based ESTIMATE where it doesn't (the Judge and Masker
run as separate A2A services, so their token usage never crosses the wire).

Rates below are the published Google Gemini API list prices (paid tier, standard
inference) for the models this app uses, per ai.google.dev/gemini-api/docs/pricing
(fetched 2026-07). Override any rate with an env var (e.g. VOICE_PRICE_LLM_OUT=3.00)
to match your own contract/discount. All rates are USD per 1,000,000 tokens.

Caveat: TTS is really billed on *audio output* tokens; the token count we read
from usage_metadata is Google's, so the dollar figure tracks the real bill, but
list prices change — re-check the page and update if it's been a while.
"""

import os


def _price(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


# USD per 1M tokens (Gemini API list prices, 2026-07). Override via env for your rates.
PRICES = {
    # STT = gemini-*-flash-lite. Input is AUDIO ($0.30), output is the transcript ($0.40).
    "stt_in":  _price("VOICE_PRICE_STT_IN",  0.30),
    "stt_out": _price("VOICE_PRICE_STT_OUT", 0.40),
    # Text LLM = gemini-2.5-flash (the agent, plus the A2A Judge and Masker).
    "llm_in":  _price("VOICE_PRICE_LLM_IN",  0.30),
    "llm_out": _price("VOICE_PRICE_LLM_OUT", 2.50),
    # TTS = gemini-3.1-flash-tts-preview. Text in ($1.00), audio out ($20.00) dominates.
    "tts_in":  _price("VOICE_PRICE_TTS_IN",  1.00),
    "tts_out": _price("VOICE_PRICE_TTS_OUT", 20.00),
}


def usd(kind: str, tokens_in: int, tokens_out: int) -> float:
    """Cost in dollars for `tokens_in`/`tokens_out` at the `kind` rate (stt|llm|tts)."""
    price_in = PRICES.get(f"{kind}_in", 0.0)
    price_out = PRICES.get(f"{kind}_out", 0.0)
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


def estimate_tokens(text: str) -> int:
    """Rough token count for text we can't measure (~4 chars/token)."""
    return max(1, len(text or "") // 4)


def usage_tokens(usage) -> tuple[int, int]:
    """Pull (prompt_tokens, output_tokens) out of a google-genai usage_metadata object."""
    if not usage:
        return 0, 0
    tin = getattr(usage, "prompt_token_count", 0) or 0
    tout = getattr(usage, "candidates_token_count", 0) or 0
    return int(tin), int(tout)
