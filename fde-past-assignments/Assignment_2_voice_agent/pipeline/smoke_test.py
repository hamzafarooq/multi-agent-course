"""
smoke_test.py  -  full offline end-to-end check. No network, no key, no mic.

Forces PROVIDER=mock and drives scripted turns through the REAL Agent + adaptor,
asserting that tools fire and control actions (transfer/hangup) surface. Run
this in CI or before a workshop to confirm the loop is wired correctly.

    python smoke_test.py
"""

import os

os.environ["PROVIDER"] = "mock"          # offline backend
os.environ.setdefault("TTS_BACKEND", "print")

from agent import Agent                   # noqa: E402
from providers import make_provider        # noqa: E402


def main() -> None:
    agent = Agent(make_provider())
    ok = True

    def turn(user: str, expect_action=None, expect_in=None):
        nonlocal ok
        reply, action = agent.respond(user)
        print(f"you>   {user}")
        print(f"agent> {reply}")
        if action:
            print(f"[action: {action}]")
        if expect_action and action != expect_action:
            print(f"   expected action {expect_action!r}, got {action!r}"); ok = False
        if expect_in and expect_in.lower() not in reply.lower():
            print(f"   expected {expect_in!r} in reply"); ok = False
        print()

    # Guardrail path -> off-topic redirect
    turn("Can you tell me the weather?", expect_in="hotel reservations")

    # Tool call -> availability result -> spoken reply
    turn(
        "I need a room from August 12 to August 14 for two guests.",
        expect_in="Standard Queen",
    )
    # Booking path -> confirmation
    turn(
        "Yes, book it for Priya Shah at priya@example.com.",
        expect_in="AH-4827",
    )
    # Transfer path -> SIP REFER
    turn("Actually, connect me to a person", expect_action="transfer")

    # Fresh call for the hangup path (transfer ended the first one)
    agent2 = Agent(make_provider())
    reply, action = agent2.respond("Goodbye")
    print(f"you>   Goodbye\nagent> {reply}\n[action: {action}]\n")
    if action != "hangup":
        print(f"   expected hangup, got {action!r}"); ok = False

    print("RESULT:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
