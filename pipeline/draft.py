"""Draft check before the full render: the exact frames at every caption, shot and join, plus automatic flags.

  python3 -I pipeline/draft.py <slug> [--hires]      (after build_edl.py and crop_track.py)

The full render builds all ~3000 frames in order and takes 10+ minutes; most mistakes (a caption on his beard or on
pale paper, a bad crop, an image on the wrong word, a visible jump cut) show in a handful of frames. This composes
those frames with render.py's own Composer, so they are exactly what the render will show, in about a minute:

  - every caption phrase, once all its words are up
  - every shot, just after its dissolve
  - every segment join, a few frames either side
  - the title and the end card

It writes .work/<slug>/draft_sheet_N.jpg (labelled contact sheets) and full-size PNGs of anything flagged in
.work/<slug>/draft/, and prints the flags:

  BRIGHT  a caption sits on a light background (his white beard, pale paper): move it (caption_y) or change the crop
  JUMP    a segment join falls on a head shot with no image or dissolve over it: the jump cut would show

Head shots come from source.mp4 (fast to seek); --hires uses the 4K window instead (slower, sharper).
Fix what it flags, rebuild, run it again, and only then run render.py.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, FPS, work_dir, source_path, source_info, head_source
from render import Composer, Captions, CAP_CENTER_Y, DISSOLVE, FONT_MED

BRIGHT_MEAN, BRIGHT_P85 = 150, 195   # luminance under a caption above either reads as "light background"


def grab(src, t, info):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", src, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(info["h"], info["w"], 3)


class HeadAt:
    """The head frame at any program time, cropped like HeadReader (from source.mp4 unless hires)."""

    def __init__(self, slug, edl, hires):
        import cv2
        self.cv2 = cv2
        self.segs, self.track = edl["segments"], json.load(open(edl["crop_track"]))
        hsrc, _ = head_source(slug)
        self.track_w = source_info(hsrc)["w"]  # the crop track is in the pixels of the head source
        self.src, self.t0 = (head_source(slug) if hires else (source_path(slug), 0.0))
        self.info = source_info(self.src)

    def __call__(self, t):
        acc = 0.0
        for seg in self.segs:
            d = seg["src_end"] - seg["src_start"]
            if t < acc + d:
                break
            acc += d
        ts = seg["src_start"] + min(t - acc, d - 0.01)
        sw, sh = self.info["w"], self.info["h"]
        cw = round(sh * 9 / 16)
        left = self.track[min(int(t * FPS), len(self.track) - 1)] * sw / self.track_w
        m = np.float32([[1, 0, -left], [0, 1, 0]])
        crop = self.cv2.warpAffine(grab(self.src, ts - self.t0, self.info), m, (cw, sh), flags=self.cv2.INTER_CUBIC,
                                   borderMode=self.cv2.BORDER_REPLICATE)
        return self.cv2.resize(crop, (W, H), interpolation=self.cv2.INTER_LANCZOS4)


def caption_box(cap, center_y):
    """Pixel box of a phrase's text (the sprites without their halo padding)."""
    c = Captions([cap], center_y)
    xs0 = [x + 40 for _, _, spr, x, y in c.items]
    ys0 = [y + 40 for _, _, spr, x, y in c.items]
    xs1 = [x + spr.width - 40 for _, _, spr, x, y in c.items]
    ys1 = [y + spr.height - 40 for _, _, spr, x, y in c.items]
    return max(min(xs0), 0), max(min(ys0), 0), min(max(xs1), W), min(max(ys1), H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--hires", action="store_true")
    a = ap.parse_args()
    wd = work_dir(a.slug)
    edl = json.load(open(os.path.join(wd, "edl.json")))
    comp = Composer(edl)
    head = HeadAt(a.slug, edl, a.hires)
    center_y = edl.get("caption_y", CAP_CENTER_Y)
    shots, prog = edl["shots"], comp.prog_dur

    # what to look at: (time, label, caption-or-None)
    looks = [(1.0, "title", None)]
    for c in edl["captions"]:
        t = c["words"][-1]["s"] + 0.15
        looks.append((min(t, c["t_off"] - 0.02), " ".join(w["w"] for w in c["words"]), c))
    for i, s in enumerate(shots):
        looks.append((s["t0"] + DISSOLVE / FPS + 0.05, f"shot {i}: {s['kind']} {s.get('acc', '')}", None))
    joins, acc = [], 0.0
    for seg in edl["segments"][:-1]:
        acc += seg["src_end"] - seg["src_start"]
        joins.append(acc)
        looks += [(acc - 0.1, f"join @{acc:.2f} before", None), (acc + 0.1, f"join @{acc:.2f} after", None)]
    looks.append((prog + edl["endcard"]["dur"] - 0.5, "end card", None))
    looks.sort(key=lambda x: x[0])

    flags = []
    # JUMP: a join must sit inside an image shot, or on a shot change where one side is an image (the dissolve hides it)
    for j in joins:
        before, after = comp.shot_at(j - 0.01), comp.shot_at(j + 0.01)
        kinds = {shots[before]["kind"], shots[after]["kind"]}
        inside_image = before == after and shots[before]["kind"] == "image"
        on_cut = before != after and "image" in kinds
        if not (inside_image or on_cut):
            flags.append((j, f"JUMP: join at {j:.2f}s is on a head shot with nothing over it"))

    os.makedirs(os.path.join(wd, "draft"), exist_ok=True)
    for f in os.listdir(os.path.join(wd, "draft")):  # flagged frames from an earlier run
        os.remove(os.path.join(wd, "draft", f))
    tiles, font = [], ImageFont.truetype(FONT_MED, 22)
    for t, label, cap in looks:
        hf = head(min(t, prog - 0.02))
        fr = comp.frame(t, hf, captions=False)
        note = ""
        if cap is not None and t < prog:
            x0, y0, x1, y1 = caption_box(cap, center_y)
            lum = fr[y0:y1, x0:x1] @ np.array([0.299, 0.587, 0.114], np.float32)
            mean, p85 = float(lum.mean()), float(np.percentile(lum, 85))
            if mean > BRIGHT_MEAN or p85 > BRIGHT_P85:
                note = f"BRIGHT (mean {mean:.0f}, p85 {p85:.0f})"
                flags.append((t, f"BRIGHT: '{label}' at {t:.2f}s sits on a light background (mean {mean:.0f}, p85 {p85:.0f})"))
        comp.caps.draw(fr, t) if t < prog else None
        img = Image.fromarray(np.clip(fr + 0.5, 0, 255).astype(np.uint8))
        if note:
            img.save(os.path.join(wd, "draft", f"{t:06.2f}.png"))
        tile = img.resize((270, 480))
        d = ImageDraw.Draw(tile)
        d.rectangle([0, 0, 270, 30], fill=(0, 0, 0))
        d.text((4, 4), f"{t:5.2f} {label}"[:34], font=font, fill=(255, 255, 255))
        if note:
            d.rectangle([0, 450, 270, 480], fill=(200, 0, 0))
            d.text((4, 454), note[:34], font=font, fill=(255, 255, 255))
        tiles.append(tile)

    per = 40
    for p in range(0, len(tiles), per):
        page = tiles[p:p + per]
        sheet = Image.new("RGB", (270 * 10, 480 * ((len(page) + 9) // 10)), (40, 40, 40))
        for k, tile in enumerate(page):
            sheet.paste(tile, (270 * (k % 10), 480 * (k // 10)))
        out = os.path.join(wd, f"draft_sheet_{p // per + 1}.jpg")
        sheet.save(out, quality=82)
        print(out)
    print(f"{len(looks)} frames checked; {len(flags)} flag(s)")
    for t, msg in sorted(flags):
        print("  " + msg)


if __name__ == "__main__":
    main()
