"""Fetch a high-resolution window of a Short's source video, for sharp head shots.

  python3 -I pipeline/fetch_hires.py <slug> <url> <from_s> <to_s>

The archive.org items carry the original 4K upload (a VP9 WebM, 3840x2160) next to the 480p MP4 that source.mp4 is.
A full-height 9:16 crop of 480p is only 270 px wide, so head shots are cut from the 4K instead. Only the window the
Short uses is fetched (ffmpeg range reads over HTTP, stream copy), to .work/<slug>/hires.mkv. Stream copy starts on
the keyframe before the request, so the window's true start is found by matching its audio against the source's
16 kHz analysis WAV, and written to .work/<slug>/hires.json as t0 (source time t is at t - t0 in hires.mkv).
render.py, preview.py, audio.py and crop_track.py use it automatically (common.head_source).
"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir

slug, url, lo, hi = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
wd = work_dir(slug)
out = os.path.join(wd, "hires.mkv")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lo:.3f}", "-i", url, "-t", f"{hi - lo:.3f}", "-c", "copy", out], check=True)


def load(path):
    w = wave.open(path)
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)


tmp = os.path.join(wd, "hires16k.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-t", "14", "-vn", "-ac", "1", "-ar", "16000", tmp], check=True)
probe = load(tmp)[16000 * 8:16000 * 12]
ref = load(os.path.join(wd, "audio16k.wav"))
a0 = int(max(0.0, lo - 4) * 16000)
best = max((float(np.dot(ref[a0 + o:a0 + o + len(probe)], probe) /
                  (np.linalg.norm(ref[a0 + o:a0 + o + len(probe)]) * np.linalg.norm(probe) + 1e-9)), o)
           for o in range(0, 16000 * 20, 2))
corr, o = best
assert corr > 0.9, f"could not match the window to the source audio (corr {corr:.2f})"
t0 = round((a0 + o) / 16000 - 8, 4)
json.dump({"path": out, "t0": t0, "url": url, "from": lo, "to": hi}, open(os.path.join(wd, "hires.json"), "w"), indent=1)
print(f"{out}: source time t is at t - {t0} (match {corr:.3f})")
