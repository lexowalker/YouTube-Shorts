"""Transcribe a Short's source with word timestamps (faster-whisper).

  python3 -I pipeline/transcribe.py <slug> full   [--model small.en]
      Whole video -> .work/<slug>/transcript.txt (readable, one segment per line) + transcript.json.
      Used to choose the teaching. small.en is quick; medium.en is more accurate (~30 min for 20 min of audio on 4 CPUs).
  python3 -I pipeline/transcribe.py <slug> words a:b [c:d ...] [--model medium.en]
      Word timings for the chosen source ranges (seconds) -> .work/<slug>/words.json, appended and de-duplicated.

The 16 kHz mono WAV (.work/<slug>/audio16k.wav) is created on first use.
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, source_path

PROMPT = "David E. Arredondo reads the Tao Te Ching, Thomas Cleary translation. Tao, Taoist, straw dogs."


def load_audio(slug):
    wav = os.path.join(work_dir(slug), "audio16k.wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", source_path(slug), "-ac", "1", "-ar", "16000", wav], check=True)
    wf = wave.open(wav)
    return np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("mode", choices=["full", "words"])
    ap.add_argument("ranges", nargs="*")
    ap.add_argument("--model", default=None)
    ap.add_argument("--no-prompt", action="store_true",
                    help="drop the initial prompt (whisper sometimes skips a sentence that repeats the prompt)")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model or ("small.en" if a.mode == "full" else "medium.en"), device="cpu",
                         compute_type="int8", cpu_threads=os.cpu_count())
    audio = load_audio(a.slug)
    wd = work_dir(a.slug)
    prompt = None if a.no_prompt else PROMPT

    if a.mode == "full":
        segs, _ = model.transcribe(audio, language="en", word_timestamps=True, beam_size=5, initial_prompt=prompt)
        out = []
        with open(os.path.join(wd, "transcript.txt"), "w") as txt:
            for s in segs:
                out.append({"start": s.start, "end": s.end, "text": s.text,
                            "words": [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)} for w in s.words]})
                txt.write(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}\n")
                txt.flush()
        json.dump(out, open(os.path.join(wd, "transcript.json"), "w"), indent=0)
        return

    path = os.path.join(wd, "words.json")
    words = json.load(open(path)) if os.path.exists(path) else []
    for rng in a.ranges:
        lo, hi = map(float, rng.split(":"))
        segs, _ = model.transcribe(audio[int(lo * 16000):int(hi * 16000)], language="en", word_timestamps=True,
                                   beam_size=5, initial_prompt=prompt)
        new = [{"w": w.word.strip(), "s": round(w.start + lo, 3), "e": round(w.end + lo, 3), "p": round(w.probability, 3)}
               for s in segs for w in s.words]
        # the new pass replaces whatever was there for this range
        words = [w for w in words if not (lo <= w["s"] < hi)] + new
        for w in new:
            print(f"{w['s']:8.2f} {w['e']:8.2f} {w['p']:.2f} {w['w']}")
    words.sort(key=lambda w: w["s"])
    json.dump(words, open(path, "w"), indent=0)


if __name__ == "__main__":
    main()
