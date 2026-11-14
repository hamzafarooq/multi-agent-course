"""
demo_call.py  -  a FULL end-to-end simulated inbound phone call, offline.

Ties Layer C (SIP signaling) to Layer A/B (the agent loop). Prints the SIP
INVITE/200/ACK handshake, runs a scripted caller conversation through the REAL
Agent on the mock provider (no network/key), shows tools + RTP audio markers,
then tears the call down with BYE (or REFER on a transfer). Nothing here dials a
real phone  -  it's the "watch a whole call happen" demo for the SIP segment.

    python demo_call.py            # hotel booking -> caller hangs up (BYE)
    python demo_call.py --transfer # caller asks for a human -> REFER
"""

import argparse
import os
import sys

# Reach the pipeline package (agent + mock provider) from mocks/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
os.environ["PROVIDER"] = "mock"  # force the offline backend

from agent import Agent            # noqa: E402
from providers import make_provider  # noqa: E402

CALL_ID = "9c8b7a6d-0f1e-2d3c-4b5a-60718293a4b5@203.0.113.10"
CALLER = "+15551230000"

# Two scripted caller conversations. The mock LLM routes these to tools.
SCRIPTS = {
    "default": [
        "Hi, I need a room from August 12 to August 14 for two guests.",
        "Yes, book it for Priya Shah at priya@example.com.",
        "Great, thanks. That's all, goodbye.",
    ],
    "transfer": [
        "I need to change a reservation, but I do not have the confirmation number.",
        "This is confusing, can I just talk to a person?",
    ],
}


def sig(direction: str, msg: str) -> None:
    """Print a SIP signaling line."""
    arrow = "──▶" if direction == "out" else "◀──"
    print(f"  SIP {arrow} {msg}")


def media(direction: str, who: str, text: str) -> None:
    """Print an RTP media (audio) line."""
    arrow = "═══▶" if direction == "out" else "◀═══"
    print(f"  RTP {arrow} [{who}] {text}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Simulated inbound call (offline)")
    ap.add_argument("--transfer", action="store_true",
                    help="run the 'talk to a human' scenario (ends in SIP REFER)")
    args = ap.parse_args()
    script = SCRIPTS["transfer" if args.transfer else "default"]

    print(f"\n=== INBOUND CALL  from {CALLER}  Call-ID {CALL_ID[:8]}… ===\n")

    # --- SIP setup (Layer C) ---
    sig("in", f"INVITE sip:agent@voice.demo  (from {CALLER}, SDP offer: PCMU/Opus)")
    sig("out", "100 Trying")
    sig("out", "180 Ringing")
    sig("out", "200 OK  (SDP answer: PCMU, RTP port 40000)")
    sig("in", "ACK  → call established, media flowing\n")

    agent = Agent(make_provider())
    action = None

    # Agent greets first, like an IVR.
    greeting = "Thanks for calling Aurora Hotel reservations. How can I help?"
    media("out", "agent", greeting)

    # --- Conversation (Layer A/B) ---
    for line in script:
        media("in", "caller", line)          # RTP audio in
        print("        │ VAD: endpoint detected → STT → agent")
        reply, action = agent.respond(line)  # real Agent + mock LLM/tools
        media("out", "agent", reply)         # TTS out
        if action:
            print(f"        │ tool action: {action}")
        if action in ("transfer", "hangup"):
            break

    print()
    # --- SIP teardown (Layer C) ---
    if action == "transfer":
        sig("out", "REFER  Refer-To: sip:front-desk@voice.demo  → warm transfer")
        sig("in", "202 Accepted  → caller re-INVITEd to human queue")
    else:
        sig("in", "BYE  (caller hung up)")
        sig("out", "200 OK  → media stops")

    print("\n  [call ended] transcript saved · duration logged · "
          f"{len(script)} caller turns\n")


if __name__ == "__main__":
    main()
