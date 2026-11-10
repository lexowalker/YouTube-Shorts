"""Program-time word timings: cut the analysis audio as the Short is cut, then transcribe the result.

  python3 -I pipeline/prog.py <slug> [--model medium.en]
      -> .work/<slug>/prog16k.wav (the cut, 16 kHz mono) and .work/<slug>/words.json (words in PROGRAM time)

For Shorts cut from many small pieces (pauses, stutters and restarts trimmed out), whisper times words far better on
the assembled cut than on the source, where it stretches a word across every long pause. scenes.py then treats the
program as one segment for captions. Re-run after any change to "segments"; word_overrides are in program time.
"""
import argparse, json, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, load_spec
from transcribe import load_audio, PROMPT

SR = 16000


def assemble(slug):
    spec = load_spec(slug)
    audio = load_audio(slug)
    fade = int(0.012 * SR)
    ramp = np.linspace(0, 1, fade, dtype=np.float32)
    parts = []
    for a, b in spec["segments"]:
        x = audio[int(round(a * SR)):int(round(b * SR))].copy()
        x[:fade] *= ramp
        x[-fade:] *= ramp[::-1]
        parts.append(x)
    x = np.concatenate(parts)
    out = os.path.join(work_dir(slug), "prog16k.wav")
    w = wave.open(out, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--model", default="medium.en")
    ap.add_argument("--out", default="words.json")
    ap.add_argument("--no-prompt", action="store_true")
    a = ap.parse_args()
    x = assemble(a.slug)
    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
    segs, _ = m.transcribe(x, language="en", word_timestamps=True, beam_size=5, initial_prompt=None if a.no_prompt else PROMPT)
    words = []
    for s in segs:
        print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
        words += [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for w in s.words]
    json.dump(words, open(os.path.join(work_dir(a.slug), a.out), "w"), indent=0)
    print(f"{len(x) / SR:.2f} s, {len(words)} words")


if __name__ == "__main__":
    main()
