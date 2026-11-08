"""Animated paper collages for the trial style (docs/style.md: Collages).

A collage is a dark ground plus paper pieces that arrive in small groups, each settling into place with a short
eased slide and then drifting very slightly, so the picture builds up while he speaks.

Spec (short.json "collages": {name: {...}}), positions are fractions of the 1080x1920 frame:
  ground   {"color": [r,g,b], "image": {"id", "box": [x0,y0,x1,y1], "opacity", "bw"}}   optional faint image under all
  pieces   [{...}] in arrival order; each one is:
    source   "id": image id in .work/img (images.py), with "box": [x0,y0,x1,y1] crop as fractions of the image
             "cut": true    the subject cut out of its background (rembg), with a rough white paper edge
             (default)      a torn paper scrap of the box
             or "shape": "disc" | "plane" | "phone" | "tv" | "film", filled with "color" or with the image "id"/"box"
    place    "x", "y" (centre), "w" (width as a fraction of the frame width), "rot" (degrees)
    look     "bw": true (black and white), "edge": paper edge width in px (default 9; 0 for none)
    motion   "at": arrival, seconds after the collage starts or an anchor resolved by build_edl.py ("t" holds the
             result); "enter": "left" | "right" | "up" | "down" | "settle" (default "up"); "drift" px (default 5)
    "z": draw order (default: arrival order)

python3 -I pipeline/collage.py <slug> <name> [t ...]   writes preview frames to .work/<slug>/collage_<name>_<t>.png
"""
import hashlib, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, IMG_DIR, image_path

Image.MAX_IMAGE_PIXELS = None
CACHE = os.path.join(IMG_DIR, "collage_cache")
ENTER_DUR = 0.9      # seconds for a piece to slide into place
ENTER_DIST = 150     # px it travels
SHADOW = (10, 16, 18, 0.55)  # dx, dy, blur, opacity


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- paper edges
def jagged_polygon(w, h, rng, amp=9.0, step=7):
    """A rectangle whose edges are torn: a random walk plus fine jitter along each side."""
    pts = []

    def side(p0, p1, normal):
        n = max(2, int(math.dist(p0, p1) / step))
        walk = 0.0
        for k in range(n):
            u = k / n
            walk = 0.82 * walk + rng.normal(0, amp * 0.45)
            off = walk + rng.normal(0, amp * 0.25)
            x = p0[0] + (p1[0] - p0[0]) * u + normal[0] * off
            y = p0[1] + (p1[1] - p0[1]) * u + normal[1] * off
            pts.append((x, y))

    side((0, 0), (w, 0), (0, 1))
    side((w, 0), (w, h), (-1, 0))
    side((w, h), (0, h), (0, -1))
    side((0, h), (0, 0), (1, 0))
    return pts


def rough(mask, rng, grow, amp=3.0):
    """Grow a mask by `grow` px with an irregular, fibrous outline (the white paper border of a cut-out)."""
    if grow <= 0:
        return mask
    m = mask.filter(ImageFilter.MaxFilter(2 * grow + 1)).filter(ImageFilter.GaussianBlur(amp))
    a = np.asarray(m, np.float32) / 255
    noise = rng.normal(0, 1, (mask.height // 6 + 2, mask.width // 6 + 2)).astype(np.float32)
    noise = np.asarray(Image.fromarray(noise).resize(mask.size, Image.BICUBIC), np.float32)
    a = np.clip((a - 0.5 + 0.18 * noise) * 6 + 0.5, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


def paper_grain(size, rng, base=(244, 240, 230), amt=7):
    n = rng.normal(0, amt, (size[1], size[0], 1)).astype(np.float32)
    a = np.clip(np.array(base, np.float32)[None, None, :] + n, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def to_bw(img):
    g = ImageOps.autocontrast(img.convert("L"), cutoff=0.5)
    a = np.asarray(g, np.float32) / 255
    a = np.clip((a - 0.5) * 1.12 + 0.5, 0, 1)
    warm = np.stack([a * 238 + 8, a * 234 + 8, a * 226 + 8], -1)  # a faintly warm black-and-white, like old paper
    return Image.fromarray(warm.astype(np.uint8))


# ---------------------------------------------------------------- shapes
def shape_mask(kind, w, h):
    s = 3
    m = Image.new("L", (w * s, h * s), 0)
    d = ImageDraw.Draw(m)
    W_, H_ = w * s, h * s
    if kind == "disc":
        d.ellipse([0, 0, W_ - 1, H_ - 1], fill=255)
    elif kind == "plane":  # a simple airliner seen from above, nose up
        cx = W_ / 2
        body = W_ * 0.085
        d.rounded_rectangle([cx - body, H_ * 0.02, cx + body, H_ * 0.98], radius=int(body), fill=255)
        d.polygon([(cx - body, H_ * 0.36), (0, H_ * 0.56), (0, H_ * 0.62), (cx - body, H_ * 0.52)], fill=255)
        d.polygon([(cx + body, H_ * 0.36), (W_, H_ * 0.56), (W_, H_ * 0.62), (cx + body, H_ * 0.52)], fill=255)
        d.polygon([(cx - body, H_ * 0.84), (cx - W_ * 0.3, H_ * 0.95), (cx - W_ * 0.3, H_ * 0.98), (cx - body, H_ * 0.93)], fill=255)
        d.polygon([(cx + body, H_ * 0.84), (cx + W_ * 0.3, H_ * 0.95), (cx + W_ * 0.3, H_ * 0.98), (cx + body, H_ * 0.93)], fill=255)
    elif kind == "phone":
        d.rounded_rectangle([0, 0, W_ - 1, H_ - 1], radius=int(W_ * 0.14), fill=255)
    elif kind == "tv":  # an old television: rounded screen in a cabinet, two antennae
        d.rounded_rectangle([0, H_ * 0.22, W_ - 1, H_ - 1], radius=int(W_ * 0.06), fill=255)
        d.line([(W_ * 0.5, H_ * 0.22), (W_ * 0.28, 0)], fill=255, width=int(W_ * 0.025))
        d.line([(W_ * 0.5, H_ * 0.22), (W_ * 0.72, 0)], fill=255, width=int(W_ * 0.025))
    elif kind == "film":
        d.rectangle([0, 0, W_ - 1, H_ - 1], fill=255)
    else:
        raise ValueError(kind)
    return m.resize((w, h), Image.LANCZOS)


def film_holes(img, w, h):
    """Sprocket holes punched in a film strip (drawn dark over the image)."""
    d = ImageDraw.Draw(img)
    band = int(w * 0.13)
    d.rectangle([0, 0, band, h], fill=(18, 16, 14))
    d.rectangle([w - band, 0, w, h], fill=(18, 16, 14))
    hole = band * 0.5
    y = hole * 0.6
    while y < h - hole:
        for x0 in (band * 0.25, w - band * 0.75):
            d.rounded_rectangle([x0, y, x0 + hole, y + hole * 0.75], radius=3, fill=(236, 232, 222))
        y += hole * 1.6
    for k in range(1, 3):  # frame lines
        yy = h * k / 3
        d.line([(band, yy), (w - band, yy)], fill=(18, 16, 14), width=max(2, int(w * 0.02)))


# ---------------------------------------------------------------- sprite build
def load_box(ident, box):
    im = Image.open(image_path(ident)).convert("RGB")
    if box:
        x0, y0, x1, y1 = box
        im = im.crop((round(x0 * im.width), round(y0 * im.height), round(x1 * im.width), round(y1 * im.height)))
    return im


def cutout_rgba(ident, box):
    """Subject on transparent (rembg), cached per image and box."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(json.dumps([ident, box]).encode()).hexdigest()[:10]
    p = os.path.join(CACHE, f"{ident}_{key}_cut.png")
    if not os.path.exists(p):
        from rembg import remove, new_session
        im = load_box(ident, box)
        im.thumbnail((2400, 2400))
        out = remove(im, session=new_session("isnet-general-use"))
        a = out.getchannel("A").point(lambda v: 0 if v < 40 else v)
        out.putalpha(a)
        out.crop(a.point(lambda v: 255 if v > 60 else 0).getbbox()).save(p)
    return Image.open(p).convert("RGBA")


def build_sprite(pc, seed):
    """RGBA sprite (paper edge and shadow included) and the offset of its centre."""
    rng = np.random.default_rng(seed)
    tw = max(8, round(pc["w"] * W))
    edge = pc.get("edge", 9)
    if pc.get("shape"):
        kind = pc["shape"]
        aspect = pc.get("aspect", {"disc": 1.0, "plane": 1.1, "phone": 2.0, "tv": 0.95, "film": 2.6}[kind])
        th = round(tw * aspect)
        mask = shape_mask(kind, tw, th)
        if pc.get("id"):
            fill = ImageOps.fit(load_box(pc["id"], pc.get("box")), (tw, th), Image.LANCZOS)
            if pc.get("bw"):
                fill = to_bw(fill)
        else:
            fill = paper_grain((tw, th), rng, tuple(pc.get("color", (200, 50, 40))), amt=5)
        if kind == "film":
            film_holes(fill, tw, th)
        if kind in ("phone", "tv"):  # a dark bezel around the picture
            inset = round(tw * (0.06 if kind == "phone" else 0.08))
            frame = Image.new("RGB", (tw, th), (24, 22, 20))
            top = round(th * 0.22) if kind == "tv" else 0
            inner = Image.new("L", (tw, th), 0)
            ImageDraw.Draw(inner).rounded_rectangle([inset, top + inset, tw - inset, th - inset], radius=int(tw * 0.08), fill=255)
            fill = Image.composite(fill, frame, inner)
        rgba = fill.convert("RGBA")
        rgba.putalpha(mask)
        edge = pc.get("edge", 0 if kind == "disc" else 9)
    elif pc.get("cut"):
        rgba = cutout_rgba(pc["id"], pc.get("box"))
        th = round(rgba.height * tw / rgba.width)
        rgba = rgba.resize((tw, th), Image.LANCZOS)
        if pc.get("bw"):
            a = rgba.getchannel("A")
            rgba = to_bw(rgba.convert("RGB")).convert("RGBA")
            rgba.putalpha(a)
    else:  # torn scrap
        im = load_box(pc["id"], pc.get("box"))
        th = round(im.height * tw / im.width)
        im = im.resize((tw, th), Image.LANCZOS)
        if pc.get("bw"):
            im = to_bw(im)
        pad = edge + 14
        mask = Image.new("L", (tw, th), 0)
        poly = jagged_polygon(tw - 2 * pad, th - 2 * pad, rng, amp=6.0)
        ImageDraw.Draw(mask).polygon([(x + pad, y + pad) for x, y in poly], fill=255)
        rgba = im.convert("RGBA")
        rgba.putalpha(mask.filter(ImageFilter.GaussianBlur(0.8)))
    # paper edge, then shadow, on a canvas with room for both
    m = 40 + edge
    cw, ch = rgba.width + 2 * m, rgba.height + 2 * m
    alpha = Image.new("L", (cw, ch), 0)
    alpha.paste(rgba.getchannel("A"), (m, m))
    paper_a = rough(alpha, rng, edge) if edge else alpha
    out = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    dx, dy, blur, op = SHADOW
    sh = Image.new("L", (cw, ch), 0)
    sh.paste(paper_a, (dx, dy))
    sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * op))
    out = Image.composite(Image.new("RGBA", (cw, ch), (6, 5, 4, 255)), out, sh)
    out.putalpha(sh)
    if edge:
        paper = paper_grain((cw, ch), rng).convert("RGBA")
        out = Image.alpha_composite(out, Image.composite(paper, Image.new("RGBA", (cw, ch), (0, 0, 0, 0)), paper_a))
    layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    layer.paste(rgba, (m, m))
    out = Image.alpha_composite(out, layer)
    return out


def premul(img):
    a = np.asarray(img, np.float32)
    al = a[..., 3:4] / 255
    return np.concatenate([a[..., :3] * al, al * 255], -1)


# ---------------------------------------------------------------- the collage
class Collage:
    def __init__(self, spec, t0, t1, name="collage"):
        self.t0, self.t1 = t0, t1
        g = spec.get("ground", {})
        col = np.array(g.get("color", (20, 18, 16)), np.float32)
        rng = np.random.default_rng(7)
        # a dark ground with a faint paper grain and a soft vignette, 4% larger than the frame for a slow push-in
        gw, gh = int(W * 1.04), int(H * 1.04)
        base = np.ones((gh, gw, 3), np.float32) * col
        base += rng.normal(0, 3.0, (gh, gw, 1)).astype(np.float32)
        if g.get("image"):
            gi = g["image"]
            im = ImageOps.fit(load_box(gi["id"], gi.get("box")), (gw, gh), Image.LANCZOS)
            if gi.get("bw", True):
                im = to_bw(im)
            base = base * (1 - gi.get("opacity", 0.15)) + np.asarray(im, np.float32) * gi.get("opacity", 0.15)
        yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
        v = ((xx / gw - 0.5) ** 2 + (yy / gh - 0.45) ** 2 * 0.6)
        base *= (1 - 0.55 * np.clip(v * 2.2, 0, 1))[..., None]
        self.ground = np.clip(base, 0, 255).astype(np.float32)
        self.pieces = []
        for k, pc in enumerate(spec["pieces"]):
            spr = build_sprite(pc, seed=hash((name, k)) % (2 ** 31))
            self.pieces.append({"pc": pc, "spr": premul(spr), "z": pc.get("z", k), "phase": k * 1.7,
                                "t": t0 + (pc["t"] if "t" in pc else float(pc.get("at", 0.0)))})
        self.pieces.sort(key=lambda p: p["z"])

    def ground_at(self, t):
        u = smooth((t - self.t0) / max(self.t1 - self.t0, 1e-6))
        z = 1.04 - 0.04 * u  # 4% slow pull-back over the whole collage
        gh, gw = self.ground.shape[:2]
        import cv2
        vw, vh = gw / z / 1.04, gh / z / 1.04
        left, top = (gw - vw) / 2, (gh - vh) / 2
        sx, sy = vw / W, vh / H
        m = np.float32([[sx, 0, left + 0.5 * sx - 0.5], [0, sy, top + 0.5 * sy - 0.5]])
        return cv2.warpAffine(self.ground, m, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)

    def frame(self, t):
        import cv2
        fr = self.ground_at(t)
        for p in self.pieces:
            pc, spr = p["pc"], p["spr"]
            u = (t - p["t"]) / ENTER_DUR
            if u <= 0:
                continue
            e = ease_out(u)
            op = smooth(u * 1.8)
            d = (1 - e) * ENTER_DIST
            enter = pc.get("enter", "up")
            ox, oy = {"left": (-d, 0), "right": (d, 0), "up": (0, d), "down": (0, -d)}.get(enter, (0, 0))
            sc = 1.0 + (0.08 * (1 - e) if enter == "settle" else 0.0)
            amp = pc.get("drift", 5.0)
            ph = p["phase"]
            tt = t - p["t"]
            ox += amp * math.sin(2 * math.pi * tt / 7.0 + ph) * e
            oy += amp * 0.8 * math.sin(2 * math.pi * tt / 9.0 + ph * 1.3) * e
            rot = pc.get("rot", 0.0) + 0.5 * math.sin(2 * math.pi * tt / 8.0 + ph) * e
            cx, cy = pc["x"] * W + ox, pc["y"] * H + oy
            h, w = spr.shape[:2]
            m = cv2.getRotationMatrix2D((w / 2, h / 2), -rot, sc)
            # place the sprite's centre at (cx, cy); warp only the bounding box of the rotated sprite
            r = math.radians(rot)
            bw = int(abs(w * math.cos(r)) * sc + abs(h * math.sin(r)) * sc) + 4
            bh = int(abs(w * math.sin(r)) * sc + abs(h * math.cos(r)) * sc) + 4
            x0, y0 = int(math.floor(cx - bw / 2)), int(math.floor(cy - bh / 2))
            m[0, 2] += (cx - x0) - w / 2
            m[1, 2] += (cy - y0) - h / 2
            warped = cv2.warpAffine(spr, m, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W, x0 + bw), min(H, y0 + bh)
            if fx1 <= fx0 or fy1 <= fy0:
                continue
            sub = warped[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
            a = sub[..., 3:4] / 255 * op
            fr[fy0:fy1, fx0:fx1] = fr[fy0:fy1, fx0:fx1] * (1 - a) + sub[..., :3] * op
        return fr


def main():
    from common import load_spec, work_dir
    slug, name = sys.argv[1], sys.argv[2]
    spec = load_spec(slug)["collages"][name]
    dur = max(float(p.get("at", 0)) for p in spec["pieces"] if not isinstance(p.get("at", 0), dict)) + 3
    c = Collage(spec, 0.0, dur, name)
    times = [float(x) for x in sys.argv[3:]] or [dur]
    for t in times:
        out = os.path.join(work_dir(slug), f"collage_{name}_{t:.1f}.png")
        Image.fromarray(np.clip(c.frame(t) + 0.5, 0, 255).astype(np.uint8)).save(out)
        print(out)


if __name__ == "__main__":
    main()
