"""Voice cascade (STT -> existing security/agent pipeline -> TTS) over WebSocket.

Everything voice-related lives in this package so the text agent stays untouched.
web.py mounts the router with make_voice_router() and serves /voice/ui.js, which
injects the mic button into the existing chat UI.
"""
