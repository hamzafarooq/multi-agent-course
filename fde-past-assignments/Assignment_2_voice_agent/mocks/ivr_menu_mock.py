#!/usr/bin/env python3
"""
Fake IVR menu  -  Layer C demo, no telephony required.

Simulates a caller giving input by DTMF keypress ("1") OR natural speech
("I need a room"), routes to the matching branch, and prints which
AGENT TOOL would fire in the real system. This is the bridge between
mocks/sip-ivr-call-flow.md and the Layer B agent tools.

Run:  python ivr_menu_mock.py
Then type a digit (1/2/3/0), a phrase, or 'q' to quit.
"""

GREETING = (
    "Thanks for calling Aurora Hotel. Tell me what you need, or press a key:\n"
    "  1 or 'book'     → new reservation\n"
    "  2 or 'change'   → change or cancel reservation\n"
    "  3 or 'hours'    → front desk hours\n"
    "  0 or 'human'    → talk to the front desk\n"
)

# Each branch: which agent tool it maps to, and the spoken response.
BRANCHES = {
    "booking": {
        "keys": {"1"},
        "phrases": ("book", "room", "reservation", "stay", "availability", "guests"),
        "tool": "check_availability(check_in, check_out, guests)",
        "say": "Sure  -  what dates and how many guests?",
    },
    "change": {
        "keys": {"2"},
        "phrases": ("change", "cancel", "modify", "confirmation", "reservation number"),
        "tool": "transfer_to_human()  → SIP REFER to front-desk",
        "say": "I can help start that. If you do not have the confirmation number, I'll connect you to the front desk.",
    },
    "hours": {
        "keys": {"3"},
        "phrases": ("hours", "open", "close", "when"),
        "tool": None,  # answered inline, no tool call
        "say": "The front desk is available 24 hours. Anything else about your stay?",
    },
    "human": {
        "keys": {"0"},
        "phrases": ("human", "agent", "person", "representative", "someone"),
        "tool": "transfer_to_human()  → SIP REFER to front-desk",
        "say": "No problem  -  connecting you to the front desk now.",
    },
}


def route(raw: str):
    """Map a keypress or phrase to a branch name, or None if no match."""
    text = raw.strip().lower()
    if not text:
        return None
    for name, branch in BRANCHES.items():
        if text in branch["keys"]:          # DTMF digit
            return name
    for name, branch in BRANCHES.items():
        if any(p in text for p in branch["phrases"]):  # speech intent
            return name
    return None


def main():
    print(GREETING)
    misses = 0
    while True:
        try:
            raw = input("caller> ")
        except (EOFError, KeyboardInterrupt):
            print("\n[call ended]  → end_call()")
            break

        if raw.strip().lower() in {"q", "quit", "exit", "bye"}:
            print("[caller hung up]  → BYE / end_call()")
            break

        name = route(raw)
        if name is None:
            misses += 1
            if misses >= 2:
                # Safety net: never dead-end a caller.
                print("  [no match ×2] → falling back to a human")
                print("  TOOL: transfer_to_human()  → SIP REFER to front-desk")
                break
            print("  Sorry, I didn't catch that. Try again, or press 0 for a person.")
            continue

        misses = 0
        branch = BRANCHES[name]
        print(f"  → branch: {name}")
        print(f"  agent says: {branch['say']}")
        if branch["tool"]:
            print(f"  TOOL FIRES: {branch['tool']}")
        else:
            print("  (answered inline  -  no tool call)")
        print()


if __name__ == "__main__":
    main()
