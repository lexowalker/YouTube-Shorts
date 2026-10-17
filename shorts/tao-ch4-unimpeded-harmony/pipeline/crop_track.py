"""Smoothed 9:16 crop path (left edge in source px) for every program frame."""
import sys, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facetrack import track

FPS, CW, SW = 30, 405, 1280
edl = json.load(open(sys.argv[1]))
src = sys.argv[2]
out = []
for seg in edl["segments"]:
    a, b = seg["src_start"], seg["src_end"]
    pts = track(src, a - 1.0, b + 1.0)
    t = np.array([p[0] for p in pts]); c = np.array([np.nan if p[1] is None else p[1] for p in pts])
    ok = ~np.isnan(c)
    c = np.interp(t, t[ok], c[ok]) if ok.any() else np.full_like(t, 700.0)
    # heavy gaussian smoothing (sigma 1.5 s) so the frame drifts gently rather than following every nod
    sig = 1.5 * 6.0
    k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2); k /= k.sum()
    cs = np.convolve(np.pad(c, len(k) // 2, mode="edge"), k, mode="valid")
    n = round((b - a) * FPS)
    tf = a + np.arange(n) / FPS
    cx = np.interp(tf, t, cs)
    left = np.clip(cx - CW / 2, 0, SW - CW)
    out += [round(float(x), 2) for x in left]
    print(f"seg {a:.1f}-{b:.1f}: detections {ok.sum()}/{len(ok)}, left x {left.min():.0f}..{left.max():.0f}")
json.dump(out, open(edl["crop_track"], "w"))
