"""Add a public-domain image from outside the Cleveland Museum of Art (NASA, a banknote scan) to the image cache, so
a Short's spec can use it like any CMA image (by its id in "acc").

  python3 -I pipeline/ext_image.py <id> <file-or-url> --title "…" --creator "…" --date "…" --license "…" --page <url>
        [--crop x0,y0,x1,y1] [--upscale N] [--canvas W:H --fill F --cy F] [--grain S] [--desat F] [--gain F]
        [--arrow X,Y --label "Earth"]

Writes .work/img/<id>_full.jpg and its .json (the same fields cma.py writes, which notes.py reads). Steps run in
this order: crop (fractions of the source), upscale (Lanczos), place on a black canvas (W:H, the image scaled to
F of the canvas width, its centre at F of the height), desaturate, brightness gain (white paper under captions
needs about 0.5), film grain (Gaussian, S in 0-255 units), then a
white arrow pointing at X,Y (fractions of the result) with a label, drawn in EB Garamond at the result's resolution.

The style guide prefers classical artworks; use this only where the user asks for something only a photograph or a
document can show (Pluto, the Pale Blue Dot, a hundred-dollar bill). Log the exact command in the Short's DELIVERY.md.
"""
import argparse, json, math, os, subprocess, sys, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import IMG_DIR, image_path, FONT_MED

Image.MAX_IMAGE_PIXELS = None


def load(src):
    if src.startswith("http"):
        tmp = os.path.join(IMG_DIR, "ext", os.path.basename(src.split("?")[0]))
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        req = urllib.request.Request(src, headers={"User-Agent": "youtube-shorts-pipeline/1.0"})
        open(tmp, "wb").write(urllib.request.urlopen(req, timeout=300).read())
        src = tmp
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def arrow(im, x, y, label):
    """A clean white arrow from the upper left down to (x, y), with the label at its tail."""
    W, H = im.size
    d = ImageDraw.Draw(im)
    s = W / 1080  # sizes are tuned for a 1080-wide frame
    tip = (x * W, y * H)
    gap, length, ang = 28 * s, 260 * s, math.radians(225)  # the arrow comes in from the upper left
    ux, uy = math.cos(ang), math.sin(ang)
    end = (tip[0] + ux * gap, tip[1] + uy * gap)  # the arrowhead's point stops just short of the target
    tail = (tip[0] + ux * (gap + length), tip[1] + uy * (gap + length))
    head = 38 * s
    base = (end[0] + ux * head, end[1] + uy * head)
    d.line([tail, base], fill=(255, 255, 255), width=round(7 * s))
    px, py = -uy, ux  # perpendicular
    d.polygon([end, (base[0] + px * head * 0.5, base[1] + py * head * 0.5), (base[0] - px * head * 0.5, base[1] - py * head * 0.5)],
              fill=(255, 255, 255))
    font = ImageFont.truetype(FONT_MED, round(64 * s))
    tw = d.textlength(label, font=font)
    d.text((tail[0] - tw / 2, tail[1] - 90 * s), label, font=font, fill=(255, 255, 255))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("src")
    for k in ("title", "creator", "date", "license", "page"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--crop")
    ap.add_argument("--upscale", type=float, default=1.0)
    ap.add_argument("--canvas")
    ap.add_argument("--fill", type=float, default=0.9)
    ap.add_argument("--cy", type=float, default=0.5)
    ap.add_argument("--grain", type=float, default=0.0)
    ap.add_argument("--desat", type=float, default=0.0)
    ap.add_argument("--gain", type=float, default=1.0)
    ap.add_argument("--arrow")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    im = load(a.src)
    if a.crop:
        x0, y0, x1, y1 = map(float, a.crop.split(","))
        W, H = im.size
        im = im.crop((round(x0 * W), round(y0 * H), round(x1 * W), round(y1 * H)))
    if a.upscale != 1.0:
        im = im.resize((round(im.width * a.upscale), round(im.height * a.upscale)), Image.LANCZOS)
    if a.canvas:
        cw, ch = map(int, a.canvas.split(":"))
        canvas = Image.new("RGB", (cw, ch), (0, 0, 0))
        w = round(cw * a.fill)
        h = round(im.height * w / im.width)
        canvas.paste(im.resize((w, h), Image.LANCZOS), ((cw - w) // 2, round(ch * a.cy - h / 2)))
        im = canvas
    arr = np.asarray(im).astype(np.float32)
    if a.desat:
        g = arr @ np.array([0.299, 0.587, 0.114], np.float32)
        arr = arr * (1 - a.desat) + g[..., None] * a.desat
    arr = arr * a.gain
    if a.grain:
        rng = np.random.default_rng(1)
        arr = arr + rng.normal(0, a.grain, arr.shape[:2])[..., None]
    im = Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8))
    if a.arrow:
        x, y = map(float, a.arrow.split(","))
        im = arrow(im, x, y, a.label)

    out = image_path(a.id)
    im.save(out, quality=95)
    json.dump({"accession": a.id, "title": a.title, "creators": [a.creator], "culture": [], "date": a.date,
               "license": a.license, "page": a.page, "image_url": a.src if a.src.startswith("http") else a.page},
              open(out + ".json", "w"), indent=1, ensure_ascii=False)
    print(out, im.size)


if __name__ == "__main__":
    main()
