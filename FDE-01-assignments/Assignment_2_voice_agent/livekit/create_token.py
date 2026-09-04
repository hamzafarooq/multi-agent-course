"""Create a LiveKit room join token for a caller or agent participant.

Optional:
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET
    LIVEKIT_ROOM

Example:
    python create_token.py --identity caller-demo --name "Caller Demo"
    python create_token.py --identity aurora-agent --name "Aurora Agent"
"""

from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path

import jwt
from livekit import api

from env_loader import load_env_files

LOCAL_DEFAULTS = {
    "LIVEKIT_API_KEY": "devkey",
    "LIVEKIT_API_SECRET": "secret",
    "LIVEKIT_ROOM": "aurora-demo-room",
}


def _load_env_files() -> None:
    root = Path(__file__).resolve().parents[1]
    load_env_files((root / "pipeline" / ".env", root / "livekit" / ".env"))


def _setting(name: str) -> str:
    return os.getenv(name, LOCAL_DEFAULTS[name])


def main() -> None:
    _load_env_files()
    parser = argparse.ArgumentParser(description="Create a LiveKit room join token")
    parser.add_argument("--identity", required=True, help="Unique participant identity")
    parser.add_argument("--name", default=None, help="Human-readable participant name")
    parser.add_argument("--room", default=_setting("LIVEKIT_ROOM"))
    args = parser.parse_args()

    if _setting("LIVEKIT_API_SECRET") == LOCAL_DEFAULTS["LIVEKIT_API_SECRET"]:
        warnings.filterwarnings("ignore", category=jwt.InsecureKeyLengthWarning)

    token = (
        api.AccessToken(_setting("LIVEKIT_API_KEY"), _setting("LIVEKIT_API_SECRET"))
        .with_identity(args.identity)
        .with_name(args.name or args.identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=args.room,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    print(token)


if __name__ == "__main__":
    main()
