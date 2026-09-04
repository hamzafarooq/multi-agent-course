"""Validated session-level language state for the Aurora hotel agent."""

from __future__ import annotations

from dataclasses import dataclass


LANGUAGES = {
    "en": {"name": "English", "locale": "en-US"},
    "es": {"name": "Spanish", "locale": "es-ES"},
}


@dataclass(frozen=True)
class Route:
    language: str
    locale: str
    changed: bool
    reason: str


class AgentRouter:
    """Keep validated language state selected by the agent's control tool."""

    def __init__(self, default_language: str = "en"):
        self.language = default_language if default_language in LANGUAGES else "en"

    def route(self) -> Route:
        """Return current session state; intent detection belongs to the LLM tool."""
        config = LANGUAGES[self.language]
        return Route(
            language=self.language,
            locale=config["locale"],
            changed=False,
            reason="session",
        )

    def set_language(self, language: str) -> Route:
        """Validate and persist a language requested through `set_language`."""
        if language not in LANGUAGES:
            raise ValueError(f"Unsupported language {language!r}")
        previous = self.language
        self.language = language
        config = LANGUAGES[self.language]
        return Route(
            language=self.language,
            locale=config["locale"],
            changed=self.language != previous,
            reason="set_language_tool",
        )

    def instruction(self) -> str:
        name = LANGUAGES[self.language]["name"]
        return (
            f"Current response language: {name}. Respond only in {name}. "
            "Keep hotel names, room names, prices, email addresses, and confirmation IDs unchanged."
        )
