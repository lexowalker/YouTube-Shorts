"""Storyboard: the exact composed frame (picture plus subtitles) at chosen times, as one contact sheet.

  python3 -I pipeline/storyboard.py <slug> [t ...]        (after build_edl.py and crop_track.py)

With no times, it takes one frame near the end of every scene (where a collage is fully built). Frames come
from render.py's own Composer, so they are what the render will show. Head frames are decoded singly, with the
same crop and HDR conversion as the render. Writes .work/<slug>/storyboard.jpg.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, FPS, work_dir, head_source, source_info, hdr_filter
from render import Composer


def head_frame(edl, src, t0, track, t):
    """The head frame at program time t: same segment mapping, crop and colour as render.HeadReader."""
    acc = 0.0
    for seg in edl["segments"]:
        d = seg["src_end"] - seg["src_start"]
        if t < acc + d:
            break
        acc += d
    ts = seg["src_start"] - t0 + (t - acc)
    info = source_info(src)
    cw = round(info["h"] * 9 / 16)
    left = int(round(track[min(round(t * FPS), len(track) - 1)]))
    vf = f"crop={cw}:{info['h']}:{left}:0"
    hdr = hdr_filter(src)
    vf += (f",{hdr}" if hdr else "") + f",scale={W}:{H}:flags=lanczos,format=rgb24"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ts:.3f}", "-i", src, "-frames:v", "1", "-vf", vf,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3)


def main():
    slug = sys.argv[1]
    wd = work_dir(slug)
    edl = json.load(open(os.path.join(wd, "edl.json")))
    comp = Composer(edl)
    src, t0 = head_source(slug)
    track = json.load(open(edl["crop_track"]))
    times = [float(x) for x in sys.argv[2:]] or [max(s["t0"] + 0.5, s["t1"] - 0.6) for s in edl["shots"]]
    cells = []
    for t in times:
        k = comp.shot_at(t)
        hf = head_frame(edl, src, t0, track, t) if comp.shots[k]["kind"] == "head" or t - comp.shots[k]["t0"] < 0.5 else np.zeros((H, W, 3), np.uint8)
        fr = Image.fromarray(np.clip(comp.frame(t, hf) + 0.5, 0, 255).astype(np.uint8))
        c = fr.resize((360, 640), Image.LANCZOS)
        ImageDraw.Draw(c).text((6, 6), f"{t:.1f}s {comp.shots[k]['kind']}", fill=(255, 255, 0))
        cells.append(c)
        print(f"{t:.1f}s {comp.shots[k]['kind']} {comp.shots[k].get('note', '')[:60]}", flush=True)
    cols = min(6, len(cells))
    rows = math.ceil(len(cells) / cols)
    sheet = Image.new("RGB", (cols * 364, rows * 644), "white")
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * 364, (i // cols) * 644))
    out = os.path.join(wd, "storyboard.jpg")
    sheet.save(out, quality=88)
    print(out)


if __name__ == "__main__":
    main()
