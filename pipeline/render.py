"""Compose the vertical Short frame by frame (no audio).

  python3 -I pipeline/render.py <slug> [--jobs N]   -> .work/<slug>/video_master.mp4 (intermediate, CRF 12) and endcard_preview.png

Renders N contiguous chunks at once (default: up to 4, one per core) and joins them with a stream copy. Run
draft.py first: it shows the frames that matter in about a minute.

The EDL holds:
  segments: [{src_start, src_end}]          audio/video pieces of the source, in program order
  shots:    [{t0, t1, kind: head|image, ...}] program-time shots (image: file, crop [x,y,w,h], zoom [a,b], pan [dx])
  captions: [{words: [{w, s, e, key}], lines: [n_first_line_words]}] program-time words
  title:    {text, t0, t1}
  endcard:  {dur, fade_frames}
"""
import json, subprocess, sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
Image.MAX_IMAGE_PIXELS = None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, FPS, FONT_SEMI, FONT_MED, OFFWHITE, OCHRE, CINNABAR, INK, work_dir, head_source, source_info

CAP_SIZE = 70
CAP_CENTER_Y = 0.70  # fraction of H; a Short can set "caption_y" (a 4K close-up puts his beard here, so 0.83)
CAP_LINE_GAP = 1.12
WORD_FADE = 3 / FPS
DISSOLVE = 8  # frames


def load_edl(p):
    return json.load(open(p))


# ---------------------------------------------------------------- head track
class HeadReader:
    """Serves the talking-head frame for each program frame, frame-exact to the audio edit.

    Source frames are decoded at their native rate and picked by source time; the 9:16 crop
    follows the smoothed face track with sub-pixel precision."""

    def __init__(self, edl, src, t0=0.0):
        import cv2
        self.cv2 = cv2
        self.src, self.t0 = src, t0  # source time t is at t - t0 in src (a high-resolution window, see fetch_hires.py)
        info = source_info(src)
        self.fps, self.sw, self.sh = info["fps"], info["w"], info["h"]
        self.cw = round(self.sh * 9 / 16)
        self.segs = edl["segments"]
        self.track = json.load(open(edl["crop_track"]))
        # each segment is decoded already cropped to the band its face crop travels within (+2 px), so only that
        # strip of a 4K frame crosses the pipe and gets warped; the result is identical to cropping the full frame
        self.bands, f0 = [], 0
        for seg in self.segs:
            f1 = f0 + round((seg["src_end"] - seg["src_start"]) * FPS)
            lefts = self.track[f0:f1 + 1] or [0.0]  # + 1: a segment's last frame can read the next one's track value
            bx0 = max(0, int(math.floor(min(lefts))) - 2) // 2 * 2  # even: crop on 4:2:0 video snaps x to even
            bx1 = min(self.sw, (int(math.ceil(max(lefts))) + self.cw + 4) // 2 * 2)
            self.bands.append((bx0, bx1 - bx0))
            f0 = f1
        self.si, self.proc, self.idx, self.cur, self.f = -1, None, None, None, 0
        self.last = np.zeros((H, W, 3), np.uint8)

    def seek(self, f):
        """Start at program frame f (a chunked render starts mid-way)."""
        self.f = f

    def _open(self, si, ts=None):
        if self.proc:
            self.proc.kill()
        a, b = self.segs[si]["src_start"] - self.t0, self.segs[si]["src_end"] - self.t0
        self.first = math.ceil(a * self.fps - 1e-6)
        start = max(self.first, math.floor(ts * self.fps + 1e-6)) if ts is not None else self.first
        self.bx, self.bw = self.bands[si]
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start / self.fps:.4f}", "-i", self.src,
                                      "-t", f"{b - start / self.fps + 1:.3f}", "-vf", f"crop={self.bw}:{self.sh}:{self.bx}:0",
                                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                     stdout=subprocess.PIPE)
        self.si, self.idx, self.cur = si, start - 1, None

    def next(self):
        """Advance one program frame and return the cropped, upscaled head frame."""
        t, acc = self.f / FPS, 0.0
        for si, seg in enumerate(self.segs):
            d = seg["src_end"] - seg["src_start"]
            if t < acc + d or si == len(self.segs) - 1:
                break
            acc += d
        ts = seg["src_start"] - self.t0 + (t - acc)
        if si != self.si:
            self._open(si, ts)
        want = max(math.floor(ts * self.fps + 1e-6), self.first)
        n = self.bw * self.sh * 3
        while self.idx < want:
            b = self.proc.stdout.read(n)
            if len(b) < n:
                break
            self.cur, self.idx = np.frombuffer(b, np.uint8).reshape(self.sh, self.bw, 3), self.idx + 1
        left = self.track[min(self.f, len(self.track) - 1)]
        self.f += 1
        if self.cur is None:
            return self.last
        # sub-pixel crop then a clean Lanczos upscale (no sharpening)
        m = np.float32([[1, 0, -(left - self.bx)], [0, 1, 0]])
        crop = self.cv2.warpAffine(self.cur, m, (self.cw, self.sh), flags=self.cv2.INTER_CUBIC, borderMode=self.cv2.BORDER_REPLICATE)
        self.last = self.cv2.resize(crop, (W, H), interpolation=self.cv2.INTER_LANCZOS4)
        return self.last


# ---------------------------------------------------------------- images
def warm_grade(img):
    """One gentle warm paper tone across all paintings."""
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    paper = np.array([0xF4, 0xEC, 0xDC], np.float32) / 255.0
    ink = np.array([0x24, 0x1F, 0x1A], np.float32) / 255.0
    toned = ink + (paper - ink) * lum
    a = a * 0.72 + toned * 0.28
    a = 0.02 + a * 0.97  # lift the blacks a touch
    return Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))


class ImageShot:
    def __init__(self, shot):
        self.shot = shot
        src = Image.open(shot["file"]).convert("RGB")
        x, y, w, h = shot["crop"]
        pan = shot.get("pan", 0)  # horizontal travel in source px across the shot (handscrolls only)
        self.zoom = shot.get("zoom", [1.08, 1.0])
        zmax = max(self.zoom)
        # oversample so the largest zoom still has >= 1:1 detail where possible
        self.scale = (W * zmax) / w
        ext_w = w + abs(pan)
        region = src.crop((min(x, x + pan), y, min(x, x + pan) + ext_w, y + h))
        self.base = warm_grade(region.resize((max(1, round(ext_w * self.scale)), round(h * self.scale)), Image.LANCZOS))
        self.base_np = np.ascontiguousarray(np.asarray(self.base))
        self.w, self.h, self.pan = w * self.scale, h * self.scale, pan * self.scale
        self.x0 = 0 if pan >= 0 else -self.pan
        ax, ay = shot.get("anchor", [0.5, 0.5])
        self.ax, self.ay = ax, ay

    def frame(self, t):
        s0, s1 = self.shot["t0"], self.shot["t1"]
        u = min(max((t - s0) / max(s1 - s0, 1e-6), 0.0), 1.0)
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * u  # linear, no easing
        vw, vh = self.w / z, self.h / z
        cx = self.x0 + self.pan * u + self.w * self.ax
        cy = self.h * self.ay
        left = cx - vw * self.ax
        top = cy - vh * self.ay
        left = min(max(left, 0), self.base.width - vw)
        top = min(max(top, 0), self.base.height - vh)
        import cv2
        # output pixel (x, y) samples the base at (left + (x + 0.5) * vw / W - 0.5, ...), as PIL's EXTENT transform does
        sx, sy = vw / W, vh / H
        m = np.float32([[sx, 0, left + 0.5 * sx - 0.5], [0, sy, top + 0.5 * sy - 0.5]])
        return cv2.warpAffine(self.base_np, m, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_REPLICATE)


# ---------------------------------------------------------------- text
def text_sprite(text, font, color, halo_alpha=0.6, pad=40):
    """RGBA sprite of text with a soft dark halo plus a close shadow (no stroke)."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    sw, sh = tw + 2 * pad, th + 2 * pad
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=255)
    halo = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
    near = Image.new("L", (sw, sh), 0)
    near.paste(mask, (0, 2))
    near = near.filter(ImageFilter.GaussianBlur(3))
    h = np.asarray(halo, np.float32) / 255 * halo_alpha
    n = np.asarray(near, np.float32) / 255 * 0.65
    shade = 1 - (1 - h) * (1 - n)
    out = Image.new("RGBA", (sw, sh), (20, 16, 12, 0))
    out.putalpha(Image.fromarray(np.clip(shade * 255, 0, 255).astype(np.uint8)))
    fill = Image.new("RGBA", (sw, sh), color + (255,))
    out = Image.composite(fill, out, mask)
    return out, pad - bbox[0], pad - bbox[1]


def title_sprite(text, font):
    """The opening title: ink text on a thin rice-paper box."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    px, py = 34, 20
    out = Image.new("RGBA", (tw + 2 * px, th + 2 * py), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([0, 0, out.width - 1, out.height - 1], radius=6, fill=OFFWHITE + (232,))
    d.text((px - bbox[0], py - bbox[1]), text, font=font, fill=INK)
    return out


def alpha_over(frame, sprite, x, y, opacity=1.0):
    """frame: float32 HxWx3 0..255; sprite RGBA PIL at (x,y) top-left."""
    sx0, sy0 = max(0, -x), max(0, -y)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + sprite.width), min(H, y + sprite.height)
    if x1 <= x0 or y1 <= y0:
        return
    s = np.asarray(sprite, dtype=np.float32)[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = s[..., 3:4] / 255.0 * opacity
    frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - a) + s[..., :3] * a


class Captions:
    def __init__(self, caps, center_y=CAP_CENTER_Y):
        self.font = ImageFont.truetype(FONT_SEMI, CAP_SIZE)
        self.center_y = int(H * center_y)
        asc, desc = self.font.getmetrics()
        self.line_h = int((asc + desc) * CAP_LINE_GAP)
        self.items = []  # (t_on, t_off, sprite, x, y)
        space = self.font.getlength(" ")
        for cap in caps:
            words = cap["words"]
            n1 = cap["lines"][0]
            lines = [words[:n1], words[n1:]] if n1 < len(words) else [words]
            total_h = self.line_h * len(lines)
            top = self.center_y - total_h // 2
            t_off = cap.get("t_off", words[-1]["e"])
            for li, line in enumerate(lines):
                widths = [self.font.getlength(w["w"]) for w in line]
                lw = sum(widths) + space * (len(line) - 1)
                assert lw <= 900, f"caption line too wide ({lw:.0f}px): {' '.join(w['w'] for w in line)}"
                x = (W - lw) / 2
                baseline_y = top + li * self.line_h
                for w, ww in zip(line, widths):
                    col = OCHRE if w.get("key") else OFFWHITE
                    spr, ox, oy = text_sprite(w["w"], self.font, col)
                    # the text origin sits at (ox, oy) inside the sprite; put it at (x, line top)
                    self.items.append((w["s"], t_off, spr, round(x - ox), round(baseline_y - oy)))
                    x += ww + space

    def draw(self, frame, t):
        for t_on, t_off, spr, x, y in self.items:
            if t_on <= t < t_off:
                op = min(1.0, (t - t_on) / WORD_FADE)
                alpha_over(frame, spr, x, y, op)


# ---------------------------------------------------------------- icons / end card
def youtube_icon(size, color):
    s = 4
    im = Image.new("L", (size * s, int(size * 0.72) * s), 0)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=int(im.height * 0.28), fill=255)
    cx, cy, r = im.width * 0.52, im.height / 2, im.height * 0.24
    d.polygon([(cx - r * 0.8, cy - r), (cx - r * 0.8, cy + r), (cx + r * 1.0, cy)], fill=0)
    im = im.resize((size, int(size * 0.72)), Image.LANCZOS)
    out = Image.new("RGBA", im.size, color + (0,))
    out.putalpha(im)
    return out


def x_icon(size, color):
    s = 4
    n = size * s
    im = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(im)
    # the X mark: one bold diagonal, one thin diagonal
    t = n * 0.16
    d.polygon([(0, 0), (n * 0.33, 0), (n, n), (n * 0.67, n)], fill=255)
    d.polygon([(n - t * 0.5, 0), (n, 0), (t * 0.5, n), (0, n)], fill=255)
    d.polygon([(n * 0.07, n * 0.03), (n * 0.30, n * 0.03), (n * 0.93, n * 0.97), (n * 0.70, n * 0.97)], fill=0)
    im = im.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", im.size, color + (0,))
    out.putalpha(im)
    return out


def build_endcard(edl):
    ec = edl["endcard"]
    bg = Image.new("RGB", (int(W * 1.03) + 2, int(H * 1.03) + 2), OFFWHITE)
    if ec.get("bg_image"):
        b = ImageShot({"file": ec["bg_image"], "crop": ec["bg_crop"], "zoom": [1.0, 1.0], "t0": 0, "t1": 1}).frame(0)
        b = Image.fromarray(b).resize(bg.size, Image.LANCZOS)
        bg = Image.blend(bg, b, ec.get("bg_strength", 0.12))
    d = ImageDraw.Draw(bg)
    ox, oy = (bg.width - W) // 2, (bg.height - H) // 2
    cx = ox + W // 2
    name_f = ImageFont.truetype(FONT_SEMI, 84)
    sub_f = ImageFont.truetype(FONT_MED, 36)
    h_f = ImageFont.truetype(FONT_MED, 42)
    y = oy + int(H * 0.36)
    # seal: small cinnabar square with a thin inner frame
    seal = 54
    d.rectangle([cx - seal // 2, y - 150, cx + seal // 2, y - 150 + seal], fill=CINNABAR)
    d.rectangle([cx - seal // 2 + 7, y - 143, cx + seal // 2 - 7, y - 150 + seal - 7], outline=OFFWHITE, width=2)
    d.text((cx, y), "David E. Arredondo", font=name_f, fill=INK, anchor="mm")
    y += 82
    d.text((cx, y), "Readings from the Tao Te Ching · Thomas Cleary translation", font=sub_f, fill=(0x6B, 0x62, 0x56), anchor="mm")
    y += 70
    d.line([cx - 60, y, cx + 60, y], fill=(0xB9, 0xAE, 0x9C), width=2)
    y += 90
    ink_icon = (0x3A, 0x34, 0x2D)
    for icon, handle in [(youtube_icon(56, ink_icon), "@DavidEArredondo"), (x_icon(40, ink_icon), "@davidarredondo")]:
        tw = d.textlength(handle, font=h_f)
        gap = 22
        total = 56 + gap + tw
        x0 = cx - total / 2
        bg.paste(icon, (int(x0 + (56 - icon.width) / 2), int(y - icon.height / 2)), icon)
        d.text((x0 + 56 + gap, y), handle, font=h_f, fill=INK, anchor="lm")
        y += 86
    return bg


def endcard_frame(card, u):
    """The card is drawn at 1.03x; the view widens from W x H to the whole card, a 1.03x -> 1.00x zoom-out."""
    z = 1.03 + (1.0 - 1.03) * u
    cw, ch = card.width, card.height
    vw, vh = cw / z, ch / z
    left, top = (cw - vw) / 2, (ch - vh) / 2
    return np.asarray(card.transform((W, H), Image.EXTENT, (left, top, left + vw, top + vh), Image.BICUBIC))


# ---------------------------------------------------------------- compose
class Composer:
    """Builds the program frame at any time t from the EDL. render.py calls it for every frame in order; draft.py
    calls it at a few chosen times, so a draft frame is exactly what the full render will show."""

    def __init__(self, edl, card=None):
        self.edl, self.shots = edl, edl["shots"]
        self.prog_dur = sum(s["src_end"] - s["src_start"] for s in edl["segments"])
        self.ec = edl["endcard"]
        self.caps = Captions(edl["captions"], edl.get("caption_y", CAP_CENTER_Y))
        self.title = edl.get("title")
        self.title_spr = None
        if self.title:
            self.title_spr = title_sprite(self.title["text"], ImageFont.truetype(FONT_MED, self.title.get("size", 50)))
        self.card = card if card is not None else build_endcard(edl)
        self.img_cache = {}

    def shot_at(self, t):
        for i, s in enumerate(self.shots):
            if s["t0"] <= t < s["t1"]:
                return i
        return len(self.shots) - 1

    def render_shot(self, i, t, head_frame):
        s = self.shots[i]
        if s["kind"] == "head":
            return head_frame.astype(np.float32)
        if i not in self.img_cache:
            self.img_cache.clear() if len(self.img_cache) > 3 else None
            self.img_cache[i] = ImageShot(s)
        return self.img_cache[i].frame(t).astype(np.float32)

    def frame(self, t, hf, captions=True):
        """float32 HxWx3 frame at program time t; hf is the head frame for t (any frame once the card is up)."""
        shots, title = self.shots, self.title
        if t < self.prog_dur:
            i = self.shot_at(t)
            fr = self.render_shot(i, t, hf)
            # soft cross-dissolve into / out of images: blend over the first DISSOLVE frames of a shot
            s = shots[i]
            if i > 0 and s.get("dissolve_in", shots[i - 1]["kind"] != s["kind"]):
                k = (t - s["t0"]) * FPS
                if k < DISSOLVE:
                    prev = self.render_shot(i - 1, t, hf)
                    a = (k + 1) / (DISSOLVE + 1)
                    fr = prev * (1 - a) + fr * a
            if self.title_spr is not None and title["t0"] <= t < title["t1"]:
                fi = min(1.0, (t - title["t0"]) / 0.4, (title["t1"] - t) / 0.4)
                alpha_over(fr, self.title_spr, (W - self.title_spr.width) // 2, int(H * 0.15) - self.title_spr.height // 2, max(fi, 0))
            if captions:
                self.caps.draw(fr, t)
            return fr
        u = (t - self.prog_dur) / self.ec["dur"]
        cardf = endcard_frame(self.card, min(u, 1.0)).astype(np.float32)
        k = (t - self.prog_dur) / (self.ec.get("fade_frames", 15) / FPS)
        if k < 1.0:
            # keep the final image settling (no captions) while dissolving
            return self.render_shot(len(shots) - 1, t, hf) * (1 - k) + cardf * k
        return cardf


# ---------------------------------------------------------------- main
def render_range(slug, f0, f1, out):
    """Frames [f0, f1) of the program to out. An intermediate: CRF 12 (finer than the final file) at a fast preset,
    since encode.py re-encodes it with the slow 2-pass settings."""
    edl = load_edl(os.path.join(work_dir(slug), "edl.json"))
    comp = Composer(edl)
    head = HeadReader(edl, *head_source(slug))
    head.seek(f0)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        t = f / FPS
        hf = head.next() if t < comp.prog_dur else head.last
        enc.stdin.write(np.clip(comp.frame(t, hf) + 0.5, 0, 255).astype(np.uint8).tobytes())
        if (f - f0) % 150 == 0:
            print(f"frame {f}/{f1}", flush=True)
    enc.stdin.close()
    enc.wait()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="render this many chunks at once")
    ap.add_argument("--range", help=argparse.SUPPRESS)  # "f0:f1:out" (one chunk; used by the parallel render)
    a = ap.parse_args()
    if a.range:
        f0, f1, out = a.range.split(":", 2)
        return render_range(a.slug, int(f0), int(f1), out)
    work = work_dir(a.slug)
    edl = load_edl(os.path.join(work, "edl.json"))
    comp = Composer(edl)
    comp.card.save(os.path.join(work, "endcard_preview.png"))
    total = round((comp.prog_dur + comp.ec["dur"]) * FPS)
    prog_frames = round(comp.prog_dur * FPS)
    # contiguous chunks, one per job; the last starts before the end card so its head reader has a last frame
    bounds = [round(total * k / a.jobs) for k in range(a.jobs + 1)]
    bounds[-2] = min(bounds[-2], prog_frames - 1)
    chunks = [(bounds[k], bounds[k + 1], os.path.join(work, f"chunk_{k}.mp4")) for k in range(a.jobs) if bounds[k + 1] > bounds[k]]
    procs = [subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), a.slug, "--range", f"{f0}:{f1}:{out}"])
             for f0, f1, out in chunks]
    if any(p.wait() for p in procs):
        sys.exit("a render chunk failed")
    lst = os.path.join(work, "chunks.txt")
    open(lst, "w").write("".join(f"file '{out}'\n" for _, _, out in chunks))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(work, "video_master.mp4")], check=True)
    for _, _, out in chunks:
        os.remove(out)
    print(f"{os.path.join(work, 'video_master.mp4')}: {total} frames in {len(chunks)} chunks")


if __name__ == "__main__":
    main()
