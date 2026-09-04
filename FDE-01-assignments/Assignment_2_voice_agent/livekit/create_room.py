"""Create a LiveKit room for the optional room/session demo.

Optional:
    LIVEKIT_URL
    LIVEKIT_API_KEY
    LIVEKIT_API_SECRET
    LIVEKIT_ROOM
"""

from __future__ import annotations

import asyncio
import os
import sys
import warnings
from pathlib import Path

import jwt
from livekit import api

from env_loader import load_env_files

LOCAL_DEFAULTS = {
    "LIVEKIT_URL": "http://localhost:7880",
    "LIVEKIT_API_KEY": "devkey",
    "LIVEKIT_API_SECRET": "secret",
    "LIVEKIT_ROOM": "aurora-demo-room",
}


def _load_env_files() -> None:
    root = Path(__file__).resolve().parents[1]
    load_env_files((root / "pipeline" / ".env", root / "livekit" / ".env"))


def _setting(name: str) -> str:
    return os.getenv(name, LOCAL_DEFAULTS[name])


def _room_name() -> str:
    return _setting("LIVEKIT_ROOM")


async def main() -> None:
    _load_env_files()
    room_name = _room_name()
    if _setting("LIVEKIT_API_SECRET") == LOCAL_DEFAULTS["LIVEKIT_API_SECRET"]:
        warnings.filterwarnings("ignore", category=jwt.InsecureKeyLengthWarning)
    try:
        async with api.LiveKitAPI(
            url=_setting("LIVEKIT_URL"),
            api_key=_setting("LIVEKIT_API_KEY"),
            api_secret=_setting("LIVEKIT_API_SECRET"),
        ) as lkapi:
            room = await lkapi.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=10 * 60,
                    max_participants=10,
                )
            )
    except Exception as exc:
        print(f"failed to create room {room_name!r}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"created room: {room.name}")


if __name__ == "__main__":
    asyncio.run(main())
