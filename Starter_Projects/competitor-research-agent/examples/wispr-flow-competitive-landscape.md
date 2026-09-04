# Example output: Wispr Flow competitive landscape

This is the real output the `competitor-research` skill produced when run on
**Wispr Flow** (AI voice dictation for knowledge workers, Mac & Windows) in
May 2026. It's included verbatim as a reference for what the skill returns —
shape, depth, and tone.

The run used:
- 1 WebSearch (orchestrator) to identify the 4 competitors
- 4 parallel research passes — one per competitor — each combining homepage +
  pricing fetches with a delegated review-miner subagent

---

# Wispr Flow — Competitive Landscape

*Research date: 2026-05. 4 direct competitors. Sources cross-referenced; pricing observed and dated.*

### Superwhisper
- **Positioning**: Mac/Windows/iOS AI voice-to-text that drops polished, formatted text into any app you're already using.
- **Target customer**: Individual power users — developers (Cursor/Claude Code "vibe coders"), writers, privacy-first professionals; secondary enterprise tier.
- **Pricing**: Free (local Whisper only) → Pro $8.49/mo or $84.99/yr → **Lifetime $249.99 one-time** → Enterprise custom. Cloud LLMs are BYOK (extra API cost). [superwhisper.com](https://superwhisper.com)
- **Differentiators**: Runs fully offline; modular model choice (local Whisper *or* BYOK GPT/Claude/Gemini/Grok); per-app "modes" auto-reformat output for context.
- **Weaknesses**: Steep configuration learning curve (3+ sources); support backlog — Voibe found 93.5% of 476 feature requests unaddressed (3+ sources).
- **Source date**: 2026-05

### Aqua Voice
- **Positioning**: "Frontier voice input" with their own Avalon speech model — system-wide dictation that inserts cleaned-up text in ~1 second, tuned for technical/coding vocabulary.
- **Target customer**: Knowledge workers and prosumers — engineers (heavy Cursor/terminal emphasis), email/Slack-heavy professionals, accessibility users (RSI, dyslexia, ex-Dragon switchers). YC-backed: $4.5M raised, ~$450K ARR.
- **Pricing**: Free Starter (1,000 words *lifetime*) → Pro **$8/mo annual** ($96/yr) or ~$10/mo monthly → Team $12/seat/mo → iOS-only $119/yr → Enterprise custom. [aquavoice.com](https://aquavoice.com)
- **Differentiators**: Own speech model (not a Whisper wrapper); reads on-screen context to disambiguate jargon/code; ~50ms startup.
- **Weaknesses**: **Cloud-only — no offline mode** is the dominant complaint (~12 HN mentions); no Linux, no Android (3+ sources).
- **Source date**: 2026-05

### VoiceInk
- **Positioning**: Open-source, on-device Mac voice-to-text — explicitly framed as *"the best open-source alternative to Superwhisper & Wispr Flow with no subscription."*
- **Target customer**: Privacy-conscious Mac power users; budget-conscious users rejecting subscriptions; Apple Silicon Macs on macOS 14+. *Notably underserves developers* — no IDE/Cursor integration.
- **Pricing**: Free if self-built (GPL v3) → **Solo $25 / Personal $39 / Extended $49 — all one-time**, lifetime updates. [tryvoiceink.com/pricing](https://tryvoiceink.com/pricing)
- **Differentiators**: 100% on-device local AI; one-time purchase vs. all subscription rivals; GPL v3 (auditable + self-buildable); 4.8k GitHub stars, 118 releases.
- **Weaknesses**: iOS companion app reported as buggy/"a disaster" with wrong-language detection (3+ voices); no IDE/Cursor/VS Code integration (3 sources).
- **Source date**: 2026-05

### Willow Voice
- **Positioning**: AI dictation *"so powerful it can replace your keyboard"* — context-aware mid-sentence correction, style-matching, system-wide + iOS keyboard.
- **Target customer**: Knowledge workers with heavy typing loads — engineers, managers, sales; expanding into HIPAA-regulated healthcare. Customers cited: Uber, Heidi Health, Zego. YC S25, $4.5M raised (Box Group, Dharmesh Shah, Alexis Ohanian, others).
- **Pricing**: Free (2,000 words/week) → Individual **$12/mo (annual only)** → Team $10/seat/mo (3-seat min) → Enterprise custom (SOC 2, HIPAA, SSO). [willowvoice.com/pricing](https://willowvoice.com/pricing)
- **Differentiators**: Mid-sentence corrections applied (not transcribed verbatim); style-matching learns your writing voice; HIPAA-compliant tier with zero retention.
- **Weaknesses**: iOS keyboard UX friction — accidental sends in Messages, redirects to app to activate mic (3+ App Store + PH voices); fast mode auto-translates non-English speech to English (3+ sources).
- **Source date**: 2026-05

---

### Gap Analysis

- **What no competitor does well**: *Local-first transcription with polished, zero-config cloud refinement.* The offline-capable players (VoiceInk, Superwhisper local mode) require BYOK and heavy configuration that users repeatedly call overwhelming. The polished cloud players (Aqua, Willow) don't run offline at all. Nobody pairs local privacy with the no-config "press hotkey, talk, perfect text" experience that Aqua and Willow nailed for cloud.
- **Where pricing is underserved**: *Transparent published HIPAA + SOC 2 team tier under $20/seat.* Willow is the only competitor offering HIPAA, and it's hidden behind a "contact sales" enterprise tier. Healthcare and regulated teams of 5–20 seats currently have to either negotiate enterprise contracts or accept consumer-grade tools. A published $15/seat HIPAA tier is unoccupied.
- **Unclaimed positioning angle**: *"The dictation tool for AI coding agents."* Cursor/Claude Code/agentic-coding workflows are mentioned by Aqua and Superwhisper as a *segment they happen to serve*, but no competitor positions itself **as** the voice interface for agent prompting. The headline angle *"Stop typing prompts. Talk to your agents."* is unclaimed despite obvious demand.

---

**Based on this, which gap are you trying to own?**

---

## What this example demonstrates

- **6-bullet hard cap is enforced** — no card runs over, even when richer data was
  available. The constraint forces the orchestrator to pick what matters.
- **Pricing always cites a source URL inline** — every tier traces back to the
  page it was observed on, with the observation date.
- **Weaknesses are patterns, not anecdotes** — each weakness has a `(N+ sources)`
  qualifier. Single-source complaints were dropped.
- **Gap Analysis bullets are falsifiable** — *"$15/seat HIPAA tier is unoccupied"*
  is testable; "better UX" would not have been.
- **The closing question is the only thing after the gaps** — no summary
  paragraph, no "let me know if you want more." The user is forced to decide.
