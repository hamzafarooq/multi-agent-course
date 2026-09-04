"""Normalize the raw benchmark audio into the format the cascade expects.

The provided files were MP3 (48 kHz mono) with a misleading `.wav` extension.
The cascade STT (cs_agent/voice/stt.py) wants RAW 16-bit PCM @ 16 kHz mono
(it bolts a WAV header on with pcm16_to_wav). So we:

  1. decode each MP3  ->  2. downmix to mono + resample to 16 kHz  ->
  3. write a real PCM-16 WAV named qNN.wav (aligned to manifest ids)

Originals are preserved (as real .mp3) under audio/source_mp3/ for provenance.
Then manifest.json is updated with `audio` / `audio_source` paths per query.

Run:  python convert_audio.py
Deps: miniaudio (self-contained mp3 decoder, no ffmpeg required)
"""

import json
import shutil
import wave
from pathlib import Path

import miniaudio

HERE = Path(__file__).resolve().parent
AUDIO = HERE / "audio"
SRC = AUDIO / "source_mp3"
MANIFEST = HERE / "manifest.json"

TARGET_SR = 16000  # matches cs_agent/voice/stt.py pcm16_to_wav default

WORD2NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
}


def convert() -> dict[str, dict]:
    SRC.mkdir(exist_ok=True)
    results: dict[str, dict] = {}

    for word, num in sorted(WORD2NUM.items(), key=lambda kv: kv[1]):
        original = AUDIO / f"question_{word}.wav"
        if not original.exists():
            print(f"  MISSING: {original.name}")
            continue

        qid = f"q{num:02d}"

        # 1-3: decode mp3 -> mono 16 kHz signed-16, in one miniaudio call
        decoded = miniaudio.decode_file(
            str(original),
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=1,
            sample_rate=TARGET_SR,
        )

        out_wav = AUDIO / f"{qid}.wav"
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)          # 16-bit
            w.setframerate(TARGET_SR)
            w.writeframes(decoded.samples.tobytes())

        # preserve the original as a correctly-named .mp3
        src_mp3 = SRC / f"{qid}.mp3"
        shutil.copyfile(original, src_mp3)

        dur = len(decoded.samples) / TARGET_SR
        results[qid] = {
            "audio": f"audio/{qid}.wav",
            "audio_source": f"audio/source_mp3/{qid}.mp3",
            "duration_s": round(dur, 2),
        }
        print(f"  {original.name:24} -> {out_wav.name}  ({dur:.1f}s, 16 kHz mono PCM16)")

    # remove the mislabeled originals from audio/ (kept in source_mp3/)
    for word in WORD2NUM:
        stale = AUDIO / f"question_{word}.wav"
        if stale.exists():
            stale.unlink()

    return results


def update_manifest(results: dict[str, dict]) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for q in data["queries"]:
        meta = results.get(q["id"])
        if meta:
            # keep audio fields first-ish by rebuilding with them up front
            q["audio"] = meta["audio"]
            q["audio_source"] = meta["audio_source"]
            q["audio_duration_s"] = meta["duration_s"]
    data["audio_format"] = "16kHz mono PCM WAV (converted from source_mp3/ via convert_audio.py)"
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"\nUpdated {MANIFEST.name} with audio paths for {len(results)} queries.")


if __name__ == "__main__":
    print("Converting benchmark audio -> 16 kHz mono PCM WAV ...")
    res = convert()
    update_manifest(res)
    print("Done.")
