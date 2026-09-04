"""
run_bench.py — drive BOTH voice servers with ONE neutral stopwatch.

Why a neutral stopwatch: each server times itself, but from different zero points
(the cascade counts its speech->text step in its total; S2S starts its clock only
after it has already understood the audio). Comparing their self-reported totals is
biased. So this harness ignores those totals for the head-to-head and runs its OWN
stopwatch, identically for both:

    start  = the instant we finish sending the clip's audio   (same event, both archs)
    ttfa   = first response-audio byte arrives    (time-to-first-audio)
    total  = the turn's "done" signal arrives      (audio fully MADE, not played)

Both sides count whatever they actually do after the audio is delivered — the
cascade's real STT, S2S's real (tiny) recognition tail — truthfully and symmetrically.

We STILL save each server's own timing/cost events verbatim (under "raw") as the
"why" behind the number, but the comparison uses latency_measured.* only.

Feeding differs by design (each server wants its native input style):
  * cascade: the whole clip as ONE burst  -> one STT pass -> 1.5s settle -> answer
  * s2s:     realtime-paced PCM chunks     -> Live VAD ends the turn -> answer

Run one clip first to sanity-check the record, then scale up:
    python run_bench.py --arch s2s     --only q01 --repeats 1
    python run_bench.py --arch cascade --only q01 --repeats 1
    python run_bench.py --arch both --reseed      --repeats 3

Prereqs: the relevant server(s) running (cascade web :8000, s2s voice :8001), the
stack up (Postgres, Toolbox :5000, A2A :10002), MASK=false, and a clean per-pass
baseline. This harness reseeds the DB automatically BETWEEN the two passes of an
`--arch both` run so each architecture starts identical; pass --reseed to also seed
before the first pass (or seed by hand with ./run.sh seed).

Deps:  pip install websockets psycopg2-binary
"""

import argparse
import asyncio
import json
import socket
import time
import urllib.request
import wave
from pathlib import Path

import websockets
import psycopg2

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
# Skip any query id listed in the manifest's `exclude` list (normally empty — all 15 run).
_EXCLUDE = set(MANIFEST.get("exclude", []))
MANIFEST["queries"] = [q for q in MANIFEST["queries"] if q["id"] not in _EXCLUDE]

TARGETS = {
    "cascade": {
        "http": "http://127.0.0.1:8000",
        "ws":   "ws://127.0.0.1:8000/voice/ws",
        "proto": "cascade",
        "end":  "turn_end",
        "feed": "burst",       # whole clip in one frame
        "settle_s": 1.5,       # router.py _SETTLE_MS: silence wait before it starts (system knob)
    },
    "s2s": {
        "http": "http://127.0.0.1:8001",
        "ws":   "ws://127.0.0.1:8001/api/voice",
        "proto": "s2s",
        "end":  "turn_complete",
        "feed": "realtime",    # paced chunks for the Live VAD
        "settle_s": 0.0,       # S2S has NO settle timer; its Live-VAD wait is TODO when we run it
    },
}

DB = dict(dbname="toolbox_db", user="toolbox_user",
          password="mysecretpassword", host="127.0.0.1", port=5432)

# seed.sql is the ground-truth baseline the manifest is built from. It lives in a capstone's
# (generated, gitignored) mcp_toolbox/ — prefer the cascade capstone, fall back to the s2s one.
# reseed() runs it to rebaseline the DB between architecture passes.
_SEED_CANDIDATES = [
    HERE.parent / "advance-customer-support-agent-feature-A2A-MCP-ADK_cascading" / "mcp_toolbox" / "seed.sql",
    HERE.parent / "advance-customer-support-agent-feature-A2A-MCP-ADK-s2s" / "mcp_toolbox" / "seed.sql",
]

_CHUNK = 3200          # bytes = 1600 samples @16k s16 = 100 ms
_RECV_TIMEOUT = 90.0   # seconds to wait for the turn to finish


def password_for(email: str) -> str:
    """Seeded password = the first name, lowercase (e.g. alice.jones@… -> alice)."""
    return email.split("@")[0].split(".")[0].lower()


def read_pcm(wav_path: Path) -> bytes:
    with wave.open(str(wav_path), "rb") as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2, \
            f"{wav_path.name}: expected 16 kHz mono PCM16"
        return w.readframes(w.getnframes())


def login(http: str, email: str) -> dict:
    body = json.dumps({"email": email, "password": password_for(email)}).encode()
    req = urllib.request.Request(http + "/api/login", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def actions_max_id() -> int:
    conn = psycopg2.connect(**DB)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM actions_log")
        return cur.fetchone()[0]
    finally:
        conn.close()


def actions_since(min_id: int, email: str) -> list:
    conn = psycopg2.connect(**DB)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT action_type, parameters FROM actions_log "
            "WHERE id > %s AND user_email = %s ORDER BY id",
            (min_id, email))
        return [{"action_type": a, "parameters": p} for a, p in cur.fetchall()]
    finally:
        conn.close()


def reseed():
    """Reset the DB to the manifest's known baseline: run seed.sql, which DROPs and recreates
    users / customer_orders / actions_log — so actions_log starts empty and every order
    id/status/amount matches the ground truth. This is the DB half of `./run.sh seed`, done
    in-process so an --arch both run can rebaseline BETWEEN the two architecture passes.
    Connects as the same toolbox_user the harness uses; in the standard Docker setup
    toolbox_user owns the tables, so the DROP/CREATE succeeds."""
    seed = next((p for p in _SEED_CANDIDATES if p.exists()), None)
    if seed is None:
        raise RuntimeError(
            "reseed: seed.sql not found in either capstone mcp_toolbox/ folder "
            f"({[str(p) for p in _SEED_CANDIDATES]}). Seed the DB manually (./run.sh seed "
            "or your Docker equivalent) and run one --arch at a time.")
    conn = psycopg2.connect(**DB)
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(seed.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"reseed failed running {seed.name} as {DB['user']}: {exc}. If this is a "
            "table-ownership error, reseed manually (./run.sh seed) and run each --arch "
            "separately.") from exc
    finally:
        conn.close()
    print(f"  reseeded from {seed.name} (actions_log emptied, orders restored)")


async def _send_audio(ws, pcm: bytes, feed: str):
    """Send the clip; return the perf_counter the moment the LAST byte of REAL audio
    is out (= end of speech = the neutral stopwatch t0)."""
    if feed == "burst":
        await ws.send(pcm)                       # whole clip = one speech burst
    else:  # realtime
        for i in range(0, len(pcm), _CHUNK):
            await ws.send(pcm[i:i + _CHUNK])
            await asyncio.sleep(_CHUNK / 2 / 16000)   # ~1x real time (bytes/2 = samples)
    return time.perf_counter()                   # <-- t0 (silence sent AFTER this, not counted)


async def _send_silence(ws, seconds: float = 3.0):
    """Stream trailing silence so the Live-API VAD detects end-of-speech and answers.
    Runs CONCURRENTLY with the recv loop, so it never delays t0 or the measured total."""
    frame = b"\x00" * _CHUNK
    for _ in range(int(seconds / 0.1)):
        try:
            await ws.send(frame)
        except Exception:
            return
        await asyncio.sleep(0.1)


async def run_one(arch: str, q: dict, repeat: int) -> dict:
    tgt = TARGETS[arch]
    email = q["user"]
    login(tgt["http"], email)                    # builds runner + fresh session
    base_id = actions_max_id()                   # DB snapshot for action queries
    pcm = read_pcm(HERE / q["audio"])

    rec = {
        "id": q["id"], "arch": arch, "repeat": repeat, "user": email,
        "transcript": "", "response": "", "tools": [], "blocked": False,
        "actions_logged": [], "latency_measured": {}, "raw": {},
    }
    t_first = None
    t_done = None
    url = f'{tgt["ws"]}?user_id={email}'

    async with websockets.connect(url, max_size=None, open_timeout=30) as ws:
        # Reader runs CONCURRENTLY with sending. For S2S the clip streams over ~3s and
        # the server may push results meanwhile — not draining the socket during the
        # send makes the server close the connection. So we always read in parallel.
        async def reader():
            nonlocal t_first, t_done
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=_RECV_TIMEOUT)
                if isinstance(msg, (bytes, bytearray)):
                    if t_first is None:
                        t_first = time.perf_counter()
                    continue
                ev = json.loads(msg)
                t = ev.get("type")
                if tgt["proto"] == "cascade":
                    if t == "partial_transcript":
                        rec["transcript"] = ev.get("text", rec["transcript"])
                    elif t == "tool_call":
                        rec["tools"].append({"name": ev.get("name"), "args": ev.get("args", {})})
                    elif t == "response_text":
                        rec["response"] = ev.get("text", rec["response"])
                    elif t == "timing":
                        rec["raw"]["timing"] = ev.get("stages")
                    elif t == "cost":
                        rec["raw"]["cost"] = {"total": ev.get("total"), "stages": ev.get("stages")}
                    elif t == "blocked":
                        rec["blocked"] = True
                        rec["response"] = ev.get("response", "")
                else:  # s2s
                    if t == "transcript":
                        if ev.get("role") == "user" and ev.get("mode") == "final":
                            rec["transcript"] = ev.get("text", rec["transcript"])
                        elif ev.get("role") == "agent" and ev.get("mode") == "append":
                            rec["response"] += ev.get("text", "")
                    elif t == "tool" and ev.get("phase") == "call":
                        # Same record shape as cascade: {name, args}. The S2S server now
                        # emits structured args, so grading is exact-match, identical to cascade.
                        rec["tools"].append({"name": ev.get("name"),
                                             "args": ev.get("args", {})})
                    elif t == "timing":
                        rec["raw"]["timing"] = ev
                    elif t == "blocked":
                        rec["blocked"] = True
                if t == tgt["end"]:
                    t_done = time.perf_counter()
                    return

        reader_task = asyncio.create_task(reader())
        if tgt["proto"] == "s2s":
            await asyncio.sleep(1.0)   # let the Live session finish setup before audio
        t0 = await _send_audio(ws, pcm, tgt["feed"])
        # S2S needs trailing silence to trip its VAD — sent CONCURRENTLY so t0 stays at
        # end-of-speech and the stopwatch is unaffected.
        silence_task = asyncio.create_task(_send_silence(ws)) if tgt["proto"] == "s2s" else None
        try:
            await reader_task
        finally:
            for tk in (silence_task, reader_task):
                if tk and not tk.done():
                    tk.cancel()
                    try:
                        await tk
                    except (asyncio.CancelledError, Exception):
                        pass   # CancelledError is a BaseException — must catch it explicitly

        if t_done is None:
            t_done = time.perf_counter()
        if tgt["proto"] == "s2s":
            try:
                await ws.send(json.dumps({"type": "end"}))
            except Exception:
                pass

    # --- turn the raw round-trip into the fair "processing" number ------------------
    # The outside stopwatch (t_done - t0) is the full PERCEIVED wait. Two chunks of it
    # are NOT pipeline work and must come out for a fair model-vs-model comparison:
    #
    #   judge  — a guardrail LLM. The cascade runs it SEQUENTIALLY (so it sits inside
    #            `total`); S2S runs it CONCURRENTLY (so it was never in `total`).
    #            Reported on the side, never in the core number.
    #
    #   settle — the cascade waits SETTLE_MS (1.5s of silence) after you stop talking
    #            before it even begins (router.py:_SETTLE_MS). That is OUR system's
    #            turn-detection knob — NOT the fault of STT, and not model/agent/TTS
    #            work. It's a tunable choice, so it must not count against the pipeline.
    #            We subtract it so `total_core` reflects pure STT + agent + TTS time.
    #            (S2S has its own turn-detection wait via the Live VAD; settle_s is 0
    #             for S2S here — when we benchmark S2S we must strip its equivalent
    #             wait too, or the comparison tips unfairly toward the cascade.)
    tim = rec["raw"].get("timing") or {}
    settle_s = tgt.get("settle_s", 0.0)
    total = round(t_done - t0, 3)
    if arch == "cascade":
        # judge is SEQUENTIAL -> it's inside `total` -> subtract it (and the settle).
        judge_s = tim.get("judge")
        total_core = round(total - (judge_s or 0.0) - settle_s, 3)
    else:
        # s2s: judge is CONCURRENT -> it was NEVER in `total` -> do NOT subtract it,
        # only report it. (No settle timer either; settle_s = 0.)
        judge_s = tim.get("judge_secs")
        total_core = round(total - settle_s, 3)
    rec["latency_measured"] = {
        "ttfa": round(t_first - t0, 3) if t_first else None,
        "total": total,            # full perceived wait (clip-sent -> response done)
        "judge_s": judge_s,        # guardrail time — side line, out of the comparison
        "settle_s": settle_s,      # system turn-detection wait — side line, out of the comparison
        "total_core": total_core,  # <-- FAIR number: STT + agent + TTS only
    }
    rec["actions_logged"] = actions_since(base_id, email)
    return rec


def write_record(rec: dict):
    out_dir = HERE / "runs" / rec["arch"]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'{rec["id"]}_r{rec["repeat"]}.json'
    path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    lm = rec["latency_measured"]
    print(f'  {rec["arch"]:7} {rec["id"]}  r{rec["repeat"]}  '
          f'total={lm.get("total")}s '
          f'(core={lm.get("total_core")}s, judge={lm.get("judge_s")}s, settle={lm.get("settle_s")}s)  '
          f'tools={[t["name"] for t in rec["tools"]]}'
          f'{"  BLOCKED" if rec["blocked"] else ""}')
    return path


def _port_up(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def preflight(archs: list) -> None:
    """Fail fast with a clear message if the live stack isn't up. Running to the charts
    depends on these being reachable — better to say exactly what's missing now than to
    hang or error cryptically mid-run."""
    checks = [("Postgres", DB["host"], DB["port"]),
              ("Toolbox", "127.0.0.1", 5000),
              ("A2A judge", "127.0.0.1", 10002)]
    for a in archs:
        host, port = TARGETS[a]["http"].split("//", 1)[1].split(":")
        checks.append((f"{a} server", host, int(port)))
    down = [(n, h, p) for n, h, p in checks if not _port_up(h, p)]
    if down:
        print("\nPREFLIGHT FAILED — the live stack isn't fully up. Start it first "
              "(README section 5):")
        for n, h, p in down:
            print(f"   [DOWN] {n}  ({h}:{p})")
        print("   Bring up Postgres, Toolbox :5000, A2A judge :10002, and BOTH capstone\n"
              "   servers (cascade :8000 + s2s :8001) with MASK=false, then re-run.")
        raise SystemExit(1)
    print("preflight OK — " + ", ".join(n for n, _, _ in checks) + " all reachable")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", choices=["cascade", "s2s", "both"], default="both")
    ap.add_argument("--only", help="run just one clip id, e.g. q01")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--reseed", action="store_true",
                    help="also reseed the DB before the FIRST pass (a reseed always runs "
                         "BETWEEN passes when --arch both, so each arch gets a clean baseline)")
    args = ap.parse_args()

    archs = ["cascade", "s2s"] if args.arch == "both" else [args.arch]
    clips = [q for q in MANIFEST["queries"] if not args.only or q["id"] == args.only]
    if not clips:
        raise SystemExit(f"no clip matches --only {args.only}")

    preflight(archs)   # verify servers/DB are reachable before doing anything

    for i, arch in enumerate(archs):
        # Each architecture must start from the SAME freshly-seeded DB or the comparison is
        # unfair. Between passes that reseed is automatic; before the first pass it's opt-in
        # via --reseed (people often seed by hand before starting).
        if i > 0 or args.reseed:
            print(f"\n--- reseeding DB from seed.sql (clean baseline for {arch}) ---")
            reseed()
        print(f"\n=== {arch} ===")
        # S2S's Live connection is flaky run-to-run, so retry it; skip runs already on disk.
        attempts = 6 if arch == "s2s" else 1
        for q in clips:
            for r in range(1, args.repeats + 1):
                out = HERE / "runs" / arch / f'{q["id"]}_r{r}.json'
                if out.exists():
                    print(f"  {arch:7} {q['id']}  r{r}  (skip — already done)")
                    continue
                for attempt in range(1, attempts + 1):
                    try:
                        rec = await run_one(arch, q, r)
                        write_record(rec)
                        break
                    except Exception as exc:
                        print(f"  {arch:7} {q['id']}  r{r}  ERROR "
                              f"(attempt {attempt}/{attempts}): {str(exc)[:70]}")
                        if attempt < attempts:
                            await asyncio.sleep(4)   # backoff before retry
                # Let the Live session fully tear down before opening the next one.
                if arch == "s2s":
                    await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
