# Local LiveKit Voice Session

This folder provides the room and browser stage of the Aurora workshop. It runs against a self-contained LiveKit development server and does not require LiveKit Cloud credentials.

## Install

```bash
cd FDE-01-assignments/Assignment_2_voice_agent/livekit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
```

## Run

Terminal 1:

```bash
./start_local_server.sh
```

Terminal 2:

```bash
source .venv/bin/activate
python create_room.py
python talk_server.py
```

Open `http://localhost:5173`, click **Start call**, and allow microphone access. Caller Demo and Aurora Agent join `aurora-demo-room` automatically.

The browser shows:

- LiveKit participants and published audio state
- Caller and agent activity
- Automatic turn detection
- Playback barge-in with candidate pre-roll so the first interrupted word is retained
- English and Spanish routing
- RAG sources
- STT, LLM, tool, server, first-audio, and interruption timing
- Adjustable endpoint silence and speech sensitivity

Language state changes only after an explicit request that names the target
language, such as `Please speak Spanish` or `Switch back to English`. Multilingual
speech by itself does not change the configured response language.

## Local Defaults

```env
LIVEKIT_URL=http://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_ROOM=aurora-demo-room
```

Override these values in `livekit/.env` when using another server. The scripts also read `pipeline/.env` for the selected agent provider.

## Provider Behavior

`PROVIDER=openai` or `PROVIDER=groq` transcribes the recorded browser turn and runs the live hotel agent. `PROVIDER=mock` uses scripted transcripts, deterministic tools, and no paid calls.

`TTS_BACKEND=provider` generates WAV audio through the selected provider using `TTS_MODEL` and `TTS_VOICE`. `TTS_BACKEND=system` uses browser speech synthesis in the LiveKit UI and avoids provider TTS cost. The browser falls back to its installed voice if provider synthesis or playback fails.

The talk server stores independent agent state per browser session and writes structured telemetry to `../logs/voice-events.jsonl`.

## Architecture Boundary

The two identities are real room participants, but the AI processing path is a workshop bridge:

```text
browser microphone -> local endpointing -> HTTP /voice-agent -> STT and agent -> provider WAV or browser TTS
```

A room-native production worker would subscribe directly to the caller audio track, stream audio through STT or a realtime model, publish an agent audio track, and coordinate distributed cancellation.

## SIP Extension

```text
phone caller -> carrier -> SIP trunk -> SIP edge or SBC -> LiveKit room -> agent worker
```

A real SIP deployment requires a trunk, dispatch rule, internet-reachable signaling and media endpoints, authentication, codec negotiation, and transfer handling. A SIP REFER maps to Aurora's transfer action, while SIP BYE maps to the end-call action.

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Could not establish PC connection | Confirm `./start_local_server.sh` is still running on port 7880 |
| UI loads but Start call fails | Confirm both the LiveKit server and `talk_server.py` are running |
| No microphone activity | Allow browser microphone access and check the Caller Demo mute state |
| Background noise starts turns | Increase Speech sensitivity |
| Aurora interrupts itself | Reload the latest UI, use headphones if available, and increase Speech sensitivity |
| Turns commit too quickly | Increase Endpoint silence |
| Turns feel slow | Decrease Endpoint silence carefully |
| No real transcription in mock mode | Set a live provider in `pipeline/.env` |
| Voice still sounds like the system voice | Set `TTS_BACKEND=provider`, restart `talk_server.py`, and confirm the UI shows `TTS: <voice>` |
