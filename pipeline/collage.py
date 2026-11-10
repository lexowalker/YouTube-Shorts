"""Animated paper collage for a 9:16 Short.

A collage is a dark ground with torn paper scraps of pictures laid on it. It is built up: a couple of pieces
first, then a couple more, then a couple more, each arriving on the spoken word it illustrates. Pieces slide a
short way into place, then drift very slightly. Black-and-white and colour pieces are mixed.

Spec (under "collages" in short.json):
  {"ground": "#15120f",                       dark ground colour (grain and a soft vignette are added)
   "pieces": [
     {"img": "met-45434",                     image key (pipeline/museum.py), or omit for a plain paper shape
      "box": [x0, y0, x1, y1],                the scrap, as fractions of the image
      "tone": "bw" | "color",                 black-and-white (default) or the picture's own colour
      "shape": "torn" | "disc" | "paper",     torn scrap (default); a cut paper disc; a plain torn sheet of colour
      "color": "#B8372B",                     for disc / paper
      "pos": [cx, cy], "w": 0.5,              centre and width as fractions of the frame; "h" too for paper
      "rot": -4,                              degrees
      "at": 1.2 | {"word": "scare"},          when it arrives: seconds after the collage starts, or a spoken word
      "from": "left|right|up|down",           the side it slides in from (a short way)
      "border": 8}]}                          white torn-paper edge in px (0 for none)

Rules the layout must keep (checked by eye on the draft sheet): nothing important below 72% of the height (the
subtitles sit there), and no piece over a face in another piece. A scrap is a whole torn rectangle of its picture:
never a cut-out with holes.
"""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw
from common import W, H, image_path

Image.MAX_IMAGE_PIXELS = None
PAPER = np.array([236, 230, 217], np.float32)
ARRIVE, FADE = 0.7, 0.3   # seconds a piece takes to settle / to fade in
TRAVEL = 90               # px a piece slides


def hex_rgb(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def smooth_noise(n, rng, scale):
    """1-D noise of length n, smooth over about `scale` samples, roughly in -1..1."""
    k = max(2, int(n / scale) + 2)
    pts = rng.uniform(-1, 1, k)
    x = np.linspace(0, k - 1, n)
    i = np.floor(x).astype(int).clip(0, k - 2)
    f = x - i
    f = f * f * (3 - 2 * f)
    return pts[i] * (1 - f) + pts[i + 1] * f


def torn_mask(w, h, rng, rough=9.0):
    """Float mask (h, w) of a sheet with torn edges: a rectangle whose sides wander in and out."""
    s = 2
    W2, H2 = w * s, h * s
    m = rough * s

    def side(n):
        return (np.abs(smooth_noise(n, rng, 70 * s)) * 0.9 + np.abs(smooth_noise(n, rng, 14 * s)) * 0.45
                + np.abs(smooth_noise(n, rng, 4 * s)) * 0.2) * m + 1.5 * s
    step = 3 * s
    xs, ys = np.arange(0, W2, step), np.arange(0, H2, step)
    top, bot, lef, rig = side(len(xs)), side(len(xs)), side(len(ys)), side(len(ys))
    pts = [(x, top[i]) for i, x in enumerate(xs)] + [(W2 - rig[i], y) for i, y in enumerate(ys)]
    pts += [(x, H2 - bot[i]) for i, x in reversed(list(enumerate(xs)))] + [(lef[i], y) for i, y in reversed(list(enumerate(ys)))]
    im = Image.new("L", (W2, H2), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255.0


def grain(h, w, rng, amount):
    g = rng.normal(0, 1, (h, w)).astype(np.float32)
    return cv2.GaussianBlur(g, (0, 0), 0.8) * amount


def tone_bw(a):
    """Neutral black-and-white with a little more contrast, like a printed photograph."""
    y = a @ np.array([0.299, 0.587, 0.114], np.float32)
    lo, hi = np.percentile(y, [1.5, 98.5])
    y = np.clip((y - lo) / max(hi - lo, 1), 0, 1)
    y = y * y * (3 - 2 * y) * 0.35 + y * 0.65
    return (y[..., None] * np.array([238, 235, 228], np.float32) + 10).clip(0, 255)


class Piece:
    def __init__(self, spec, idx, t_on):
        self.t_on, self.idx = t_on, idx
        rng = np.random.default_rng(1000 + idx * 77 + int(spec.get("seed", 0)))
        shape = spec.get("shape", "torn")
        pw = int(round(spec["w"] * W))
        border = spec.get("border", 8 if shape == "torn" else 0)
        if shape == "disc":
            ph = pw
            rgb = np.ones((ph, pw, 3), np.float32) * hex_rgb(spec["color"])
            rgb += grain(ph, pw, rng, 5)[..., None]
            s = 4
            m = Image.new("L", (pw * s, ph * s), 0)
            ImageDraw.Draw(m).ellipse([2 * s, 2 * s, pw * s - 2 * s, ph * s - 2 * s], fill=255)
            alpha = np.asarray(m.resize((pw, ph), Image.LANCZOS), np.float32) / 255
        elif shape == "paper":
            ph = int(round(spec["h"] * H))
            rgb = np.ones((ph, pw, 3), np.float32) * hex_rgb(spec["color"])
            rgb += grain(ph, pw, rng, 6)[..., None] + cv2.GaussianBlur(rng.normal(0, 1, (ph, pw)).astype(np.float32), (0, 0), 25)[..., None] * 40
            alpha = torn_mask(pw, ph, rng, spec.get("rough", 10))
        else:
            src = Image.open(image_path(spec["img"])).convert("RGB")
            x0, y0, x1, y1 = spec["box"]
            reg = src.crop((round(x0 * src.width), round(y0 * src.height), round(x1 * src.width), round(y1 * src.height)))
            ph = int(round(pw * reg.height / reg.width))
            a = np.asarray(reg.resize((pw, ph), Image.LANCZOS), np.float32)
            a = tone_bw(a) if spec.get("tone", "bw") == "bw" else a
            alpha = torn_mask(pw, ph, rng, spec.get("rough", 9))
            if border:
                # the picture stops short of the torn edge, leaving the white of the paper showing
                k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * border + 1, 2 * border + 1))
                inner = cv2.erode(alpha, k)
                inner = cv2.GaussianBlur(inner, (0, 0), 1.2) + grain(ph, pw, rng, 0.25)
                inner = np.clip((inner - 0.5) * 6 + 0.5, 0, 1)[..., None]
                paper = PAPER + grain(ph, pw, rng, 4)[..., None]
                a = paper * (1 - inner) + a * inner
            rgb = a
        rgb = np.clip(rgb, 0, 255)
        pad = 40
        self.sprite = np.zeros((ph + 2 * pad, pw + 2 * pad, 4), np.float32)
        self.sprite[pad:-pad, pad:-pad, :3] = rgb * alpha[..., None]  # premultiplied
        self.sprite[pad:-pad, pad:-pad, 3] = alpha
        sh = np.zeros((ph + 2 * pad, pw + 2 * pad), np.float32)
        sh[pad:-pad, pad:-pad] = alpha
        self.shadow = cv2.GaussianBlur(sh, (0, 0), 11) * 0.55
        self.cx, self.cy = spec["pos"][0] * W, spec["pos"][1] * H
        self.rot = spec.get("rot", 0.0)
        d = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[spec.get("from", "down")]
        self.dx, self.dy = d[0] * TRAVEL, d[1] * TRAVEL
        self.phase = rng.uniform(0, 6.28)
        self.period = rng.uniform(7.0, 10.0)

    def draw(self, canvas, t):
        u = (t - self.t_on) / ARRIVE
        if u <= 0:
            return
        e = 1 - (1 - min(u, 1.0)) ** 3  # ease-out
        op = min(1.0, (t - self.t_on) / FADE)
        w = 2 * math.pi * (t - self.t_on) / self.period + self.phase
        x = self.cx + self.dx * (1 - e) + 4.0 * math.sin(w)
        y = self.cy + self.dy * (1 - e) + 3.0 * math.cos(w * 0.8)
        ang = self.rot + 3.0 * (1 - e) * (1 if self.idx % 2 else -1) + 0.3 * math.sin(w * 0.7)
        sh, sw = self.sprite.shape[:2]
        m = cv2.getRotationMatrix2D((sw / 2, sh / 2), ang, 1.0)
        diag = int(math.ceil(math.hypot(sw, sh))) + 4
        ox, oy = x - diag / 2, y - diag / 2
        ix, iy = int(math.floor(ox)), int(math.floor(oy))
        m[0, 2] += diag / 2 - sw / 2 + (ox - ix)
        m[1, 2] += diag / 2 - sh / 2 + (oy - iy)
        spr = cv2.warpAffine(self.sprite, m, (diag, diag), flags=cv2.INTER_LINEAR)
        ms = m.copy()
        ms[0, 2] += 9
        ms[1, 2] += 13
        shd = cv2.warpAffine(self.shadow, ms, (diag, diag), flags=cv2.INTER_LINEAR)
        x0, y0, x1, y1 = max(ix, 0), max(iy, 0), min(ix + diag, W), min(iy + diag, H)
        if x1 <= x0 or y1 <= y0:
            return
        s = spr[y0 - iy:y1 - iy, x0 - ix:x1 - ix]
        d = shd[y0 - iy:y1 - iy, x0 - ix:x1 - ix, None] * op
        reg = canvas[y0:y1, x0:x1]
        reg *= (1 - d)
        a = s[..., 3:4] * op
        reg *= (1 - a)
        reg += s[..., :3] * op


class Collage:
    def __init__(self, spec, t0, t1, resolve):
        """resolve(anchor) -> program time, for pieces keyed to a spoken word."""
        self.t0, self.t1 = t0, t1
        rng = np.random.default_rng(7)
        g = np.ones((H, W, 3), np.float32) * hex_rgb(spec.get("ground", "#15120f"))
        g += grain(H, W, rng, 3.0)[..., None]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = 1 - 0.35 * np.clip(np.hypot((xx - W / 2) / (W * 0.75), (yy - H * 0.42) / (H * 0.75)), 0, 1.4) ** 2
        self.ground = np.clip(g * v[..., None], 0, 255)
        self.pieces = []
        for i, p in enumerate(spec["pieces"]):
            at = p.get("at", 0.0)
            t_on = t0 + at if isinstance(at, (int, float)) else resolve(at)
            self.pieces.append(Piece(p, i, t_on))

    def frame(self, t):
        c = self.ground.copy()
        for p in self.pieces:
            p.draw(c, t)
        return c
