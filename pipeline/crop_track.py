"""Smoothed, face-centred 9:16 crop path for every program frame.

  python3 -I pipeline/crop_track.py <slug>     (after build_edl.py)

Writes .work/<slug>/crop_track.json: the crop's left edge in source pixels, one value per output frame.
A segment where a quick glance pulls the face off-centre can be pinned with "crop_fixes": [{"seg": i, "left": px}]
in short.json (a fixed crop for that whole segment).
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FPS, work_dir, source_path, source_info, load_spec, head_source
from facetrack import track, RATE

slug = sys.argv[1]
edl = json.load(open(os.path.join(work_dir(slug), "edl.json")))
info = source_info(source_path(slug))
sw, sh = info["w"], info["h"]
# faces are found on source.mp4 (fast); the crop is in the pixels of the picture actually cut, which may be a
# high-resolution window of the same shot (fetch_hires.py)
hinfo = source_info(head_source(slug)[0])
scale = hinfo["w"] / sw
cw = round(hinfo["h"] * 9 / 16)
spec = load_spec(slug)
band = tuple(spec.get("face_x_band", (0.33, 0.86)))
pinned = {f["seg"]: f["left"] for f in spec.get("crop_fixes", [])}
out = []
for i, seg in enumerate(edl["segments"]):
    a, b = seg["src_start"], seg["src_end"]
    pts = track(source_path(slug), a - 1.0, b + 1.0, sw, sh, band)
    t = np.array([p[0] for p in pts])
    c = np.array([np.nan if p[1] is None else p[1] for p in pts])
    ok = ~np.isnan(c)
    c = (np.interp(t, t[ok], c[ok]) if ok.any() else np.full_like(t, sw / 2)) * scale
    # heavy gaussian smoothing (sigma 1.5 s) so the frame drifts gently rather than following every nod
    sig = 1.5 * RATE
    k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2)
    k /= k.sum()
    cs = np.convolve(np.pad(c, len(k) // 2, mode="edge"), k, mode="valid")
    n = round((b - a) * FPS)
    left = np.clip(np.interp(a + np.arange(n) / FPS, t, cs) - cw / 2, 0, hinfo["w"] - cw)
    if i in pinned:
        left = np.full(n, float(pinned[i]))
    out += [round(float(x), 2) for x in left]
    print(f"segment {a:.1f}-{b:.1f}: face found in {ok.sum()}/{len(ok)} samples, crop left {left.min():.0f}..{left.max():.0f}")
json.dump(out, open(edl["crop_track"], "w"))
