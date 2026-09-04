# SIP / IVR Call Flow  -  Mocks

Layer C of the workshop. **Nothing here requires a carrier, a phone number, or a SIP trunk.**
It's sample payloads + diagrams so people understand how a real phone call becomes the audio
frames that the voice loop (Layer A) consumes.

---

## 1. The two protocols (say this first)

A phone call is **two separate things** on the wire:

| | **SIP** (Session Initiation Protocol) | **RTP** (Real-time Transport Protocol) |
|---|---|---|
| Job | *Signaling*  -  set up, change, tear down the call | *Media*  -  carry the actual audio packets |
| Analogy | The waiter taking your order | The food being carried to the table |
| Payload | Text messages (INVITE, 200 OK, BYE…) | Encoded audio frames (e.g. G.711 / Opus), ~every 20 ms |
| Port | Usually 5060/5061 | Negotiated dynamically (see SDP below) |

The classic gotcha: **SIP sets up the call, but the audio flows over RTP on a different
port that SIP negotiates via SDP.** Signaling ≠ media.

---

## 2. Where the voice agent actually sits

```
 ┌────────┐   PSTN     ┌──────────────┐   SIP trunk   ┌───────────────┐
 │ Caller │ ─────────▶ │   Carrier    │ ────────────▶ │      SBC      │   (edge / security)
 │ phone  │            │ (telco/PSTN) │               │ Session Border│
 └────────┘            └──────────────┘               │   Controller  │
                                                       └───────┬───────┘
                                       SIP (signaling)         │
                                       ───────────────────────▶│
                                                       ┌───────▼────────┐
                                                       │ Media server / │  ← RTP audio in/out
                                                       │  SIP endpoint  │
                                                       │ (Asterisk /    │
                                                       │  FreeSWITCH /  │
                                                       │  LiveKit /     │
                                                       │  Twilio, etc.) │
                                                       └───────┬────────┘
                                             audio frames      │  (this is the boundary:
                                             (PCM 8/16 kHz)     ▼   telephony → your code)
                                                       ┌────────────────┐
                                                       │  VOICE AGENT   │  ← Layer A loop
                                                       │  VAD▶STT▶LLM▶  │
                                                       │  TTS           │
                                                       └────────────────┘
```

**Key teaching point:** you almost never write raw SIP yourself. A platform
(Twilio / LiveKit / Vonage) or a media server (Asterisk / FreeSWITCH) terminates SIP+RTP
and hands your agent a clean audio stream (or a WebSocket of PCM frames). Your code lives to
the *right* of the media server.

---

## 3. Annotated SIP call setup (sample messages)

A normal successful call is the **INVITE / 200 OK / ACK … BYE** dance. These are real-shaped
SIP messages with fake identifiers  -  safe to show on a slide.

### 3.1 Caller → agent: `INVITE` (I want to start a call)

```
INVITE sip:agent@voice.demo.internal SIP/2.0
Via: SIP/2.0/UDP 203.0.113.10:5060;branch=z9hG4bK-524287-1
Max-Forwards: 70
From: "Caller" <sip:+15551230000@carrier.example>;tag=aa11bb22
To: <sip:agent@voice.demo.internal>
Call-ID: 9c8b7a6d-0f1e-2d3c-4b5a-60718293a4b5@203.0.113.10
CSeq: 1 INVITE
Contact: <sip:+15551230000@203.0.113.10:5060>
Content-Type: application/sdp
Content-Length: 213

v=0
o=caller 2890844526 2890844526 IN IP4 203.0.113.10
s=call
c=IN IP4 203.0.113.10
t=0 0
m=audio 49170 RTP/AVP 0 8 96          ← "I'll send/receive audio on port 49170"
a=rtpmap:0 PCMU/8000                  ← offered codecs: G.711 µ-law,
a=rtpmap:8 PCMA/8000                  ←   G.711 A-law,
a=rtpmap:96 opus/48000/2              ←   Opus
```

- The **`m=` and `a=rtpmap` lines are SDP** (Session Description Protocol)  -  the offer of
  *what audio, which codecs, which port*. This is how RTP gets negotiated.
- `Call-ID` uniquely identifies this call for its whole life. Great correlation key for logs.

### 3.2 Agent → caller: provisional + `200 OK` (ringing, then answered)

```
SIP/2.0 100 Trying
SIP/2.0 180 Ringing
SIP/2.0 200 OK
Via: SIP/2.0/UDP 203.0.113.10:5060;branch=z9hG4bK-524287-1
From: "Caller" <sip:+15551230000@carrier.example>;tag=aa11bb22
To: <sip:agent@voice.demo.internal>;tag=zz99yy88
Call-ID: 9c8b7a6d-0f1e-2d3c-4b5a-60718293a4b5@203.0.113.10
CSeq: 1 INVITE
Contact: <sip:agent@voice.demo.internal:5060>
Content-Type: application/sdp
Content-Length: 179

v=0
o=agent 0 0 IN IP4 198.51.100.20
s=call
c=IN IP4 198.51.100.20
t=0 0
m=audio 40000 RTP/AVP 0                ← "agreed: G.711 µ-law, send RTP to my port 40000"
a=rtpmap:0 PCMU/8000
```

The agent's `200 OK` **answers the SDP offer**: it picks one codec (`PCMU`) and gives its own
RTP port. Now both sides know where to send audio.

### 3.3 Caller → agent: `ACK` (three-way handshake done → media flows)

```
ACK sip:agent@voice.demo.internal:5060 SIP/2.0
Call-ID: 9c8b7a6d-0f1e-2d3c-4b5a-60718293a4b5@203.0.113.10
CSeq: 1 ACK
```

**At this moment RTP audio starts flowing** (caller:49170 ⇄ agent:40000). This is the point
where your VAD/STT begins receiving frames.

### 3.4 Either side: `BYE` (hang up)

```
BYE sip:agent@voice.demo.internal:5060 SIP/2.0
Call-ID: 9c8b7a6d-0f1e-2d3c-4b5a-60718293a4b5@203.0.113.10
CSeq: 2 BYE
```
```
SIP/2.0 200 OK        ← call torn down, RTP stops, log final transcript + duration
```

---

## 4. Full call sequence (the diagram for the slide)

```
 Caller            SBC / Media server              Voice Agent            STT/LLM/TTS
   │                      │                              │                      │
   │──── INVITE (SDP) ───▶│                              │                      │
   │◀──── 100 Trying ─────│                              │                      │
   │◀──── 180 Ringing ────│                              │                      │
   │                      │─── new call event ──────────▶│                      │
   │◀──── 200 OK (SDP) ───│                              │                      │
   │───── ACK ───────────▶│                              │                      │
   │                      │                              │                      │
   │═══ RTP audio ═══════▶│═══ PCM frames ══════════════▶│─ transcribe ────────▶│
   │                      │                              │◀─ partial/final txt ─│
   │                      │                              │─ prompt + tools ────▶│
   │                      │                              │◀─ reply tokens ──────│
   │◀══ RTP audio ════════│◀══ TTS audio chunks ═════════│─ synthesize ────────▶│
   │                      │      (barge-in: caller talks → cut TTS, listen)     │
   │───── BYE ───────────▶│                              │                      │
   │◀──── 200 OK ─────────│─── call ended ──────────────▶│─ save transcript ───▶│
```

`═══` = media (RTP/audio), `───` = signaling/control. Note media and signaling are
**different arrows**  -  that's the whole point of Section 1.

---

## 5. IVR  -  the menu layer on top

**IVR (Interactive Voice Response)** is the "press 1 to book a room" logic. Two ways the caller
gives input:

1. **DTMF**  -  the beep tones from pressing keypad digits (carried as RFC 2833 events, not
   audio you transcribe).
2. **Speech**  -  "I need a room for two guests" → STT → intent. Modern voice agents lean on
   this; DTMF is the reliable fallback.

### A sample IVR intent tree

```
 Incoming call
   │
   ▼
 [Greeting]  "Thanks for calling. You can say what you need, or press a key."
   │
   ├─ "book"      / press 1 ─▶ Booking flow        ─▶ (tool: check_availability)
   ├─ "change"    / press 2 ─▶ Front desk flow     ─▶ (tool: transfer_to_human)
   ├─ "hours"     / press 3 ─▶ Play front desk hours, then re-prompt
   ├─ "agent"/"human" / 0   ─▶ transfer_to_human  ─▶ SIP REFER / warm transfer
   └─ (no match ×2)         ─▶ transfer_to_human   (safety net  -  never dead-end a caller)
```

### How this maps to the agent's tools
The LLM agent from Layer B exposes exactly these as tools:

| IVR branch | Agent tool | What it does |
|-----------|-----------|--------------|
| book / 1 | `check_availability(check_in, check_out, guests)` | Fetch matching room options from a mock backend |
| confirm booking | `create_booking(...)` | Create a mock hotel reservation |
| change / 2 | `transfer_to_human()` | Route complex reservation changes to the front desk |
| human / 0 | `transfer_to_human()` | Signals telephony to **SIP REFER** the call to a queue |
| hang up | `end_call()` | Agent triggers `BYE` |

So the "IVR menu" isn't a separate rigid tree in a modern agent  -  it's the **system prompt +
tools**. The mock tree above is what product/ops people expect to see; show it, then show
that the agent achieves the same thing more flexibly.

### Transfer to a human = SIP `REFER`
When the agent gives up (or the caller asks), telephony sends a **`REFER`** telling the SBC to
route the call to a human queue:

```
REFER sip:agent@voice.demo.internal SIP/2.0
Refer-To: <sip:front-desk@voice.demo.internal>
Call-ID: 9c8b7a6d-0f1e-2d3c-4b5a-60718293a4b5@203.0.113.10
CSeq: 3 REFER
```

Say out loud: **"transfer to human is the correct error handler for a voice agent."**

---

## 6. Run the mocks (no telephony required)

**Watch a whole call end to end**  -  SIP handshake → agent turns → tool call → teardown  -  all
offline, driving the real `Agent`:

```bash
python demo_call.py             # balance lookup, caller hangs up (SIP BYE)
python demo_call.py --transfer  # caller asks for a human (SIP REFER)
```

**Interactive IVR menu**  -  simulate DTMF/speech input and see which agent tool would fire:

```bash
python ivr_menu_mock.py
```

`demo_call.py` is the bridge between this doc and the pipeline: the SIP frames are printed
here, and the conversation in between is the same `Agent` attendees built (on the mock
provider, so no key/network).

---

## 7. Cheat-sheet of terms (for the appendix slide)

| Term | One-liner |
|------|-----------|
| **PSTN** | The old-school public phone network |
| **SIP** | Text protocol that sets up / tears down calls (signaling) |
| **RTP** | Carries the actual audio packets in real time |
| **SDP** | The "offer/answer" inside SIP that negotiates codec + ports for RTP |
| **SBC** | Session Border Controller  -  the security/edge gateway for SIP |
| **SIP trunk** | The connection from a carrier that delivers phone calls to you |
| **DTMF** | Keypad tones ("press 1"), sent as events not audio |
| **Codec** | Audio compression (G.711 = simple/telephone, Opus = modern/wideband) |
| **REFER** | The SIP message that transfers a call elsewhere |
| **Barge-in** | Caller talks over the agent → stop TTS and listen |
| **Endpointing** | Detecting the caller has finished their turn |
