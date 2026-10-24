"""Thumbnails.

  python3 -I pipeline/thumbs.py faces <slug> [--step 2] [--top 24]
      Scores frames (frontal face, both eyes found, sharpness) and writes a labelled contact sheet of the best
      -> .work/<slug>/face_sheet.jpg. Then look around the best few at 0.25 s steps for eyes open, mouth at rest.
  python3 -I pipeline/thumbs.py face <slug> <seconds> [--text "Readings from the|Tao Te Ching"]
      House face thumbnail: 9:16 crop centred on the face, rice-paper band with the text in EB Garamond and the seal
      -> shorts/<slug>/thumbnails/thumbnail_face.jpg
  python3 -I pipeline/thumbs.py cover <slug> <image>
      Book cover, scaled to fill 1080x1920 (centre-cropped), nothing added -> shorts/<slug>/thumbnails/thumbnail_book_cover.jpg
"""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, FONT_SEMI, FONT_MED, OFFWHITE, INK, CINNABAR, work_dir, short_dir, source_path, source_info


def grab(src, t, info):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", src, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(info["h"], info["w"], 3)


def faces(slug, step, top):
    import cv2
    src, info = source_path(slug), source_info(source_path(slug))
    sw, sh = info["w"], info["h"]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=1/{step}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    eyes = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
    res, i = [], 0
    while True:
        b = p.stdout.read(sw * sh * 3)
        if len(b) < sw * sh * 3:
            break
        g = cv2.cvtColor(np.frombuffer(b, np.uint8).reshape(sh, sw, 3), cv2.COLOR_BGR2GRAY)
        fs = [f for f in face.detectMultiScale(g, 1.1, 6, minSize=(sh // 5, sh // 5)) if 0.33 * sw < f[0] + f[2] / 2 < 0.86 * sw]
        if fs:
            x, y, w, h = max(fs, key=lambda f: f[2])
            if len(eyes.detectMultiScale(g[y:y + 2 * h // 3, x:x + w], 1.1, 6, minSize=(w // 10, w // 10))) >= 2:
                res.append((cv2.Laplacian(g[y:y + h, x:x + w], cv2.CV_64F).var(), i * step, x + w / 2))
        i += 1
    res.sort(reverse=True)
    tiles = []
    for k, (sharp, t, cx) in enumerate(res[:top]):
        cw = round(sh * 9 / 16)
        left = int(min(max(cx - cw / 2, 0), sw - cw))
        im = Image.fromarray(grab(src, t, info)).crop((left, 0, left + cw, sh)).resize((270, 480))
        ImageDraw.Draw(im).text((6, 6), f"{t:.1f}s", fill=(255, 255, 0))
        tiles.append(im)
        print(f"{t:.1f}s sharp={sharp:.0f}")
    cols = 8
    sheet = Image.new("RGB", (270 * cols, 480 * ((len(tiles) + cols - 1) // cols)))
    for k, im in enumerate(tiles):
        sheet.paste(im, (270 * (k % cols), 480 * (k // cols)))
    out = os.path.join(work_dir(slug), "face_sheet.jpg")
    sheet.save(out, quality=85)
    print(out)


def face_thumb(slug, t, text):
    import cv2
    from facetrack import track
    src, info = source_path(slug), source_info(source_path(slug))
    sw, sh = info["w"], info["h"]
    cw = round(sh * 9 / 16)
    cxs = [c for _, c in track(src, t - 0.5, t + 0.5, sw, sh) if c is not None]
    cx = float(np.median(cxs)) if cxs else sw / 2
    left = int(min(max(cx - cw / 2, 0), sw - cw))
    img = Image.fromarray(grab(src, t, info)).crop((left, 0, left + cw, sh)).resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=40, threshold=2))  # still image: a touch of crispness
    # rice-paper band in the middle of the frame, so the text survives any crop YouTube applies
    d = ImageDraw.Draw(img, "RGBA")
    top, bot = 1150, 1520
    d.rectangle([0, top, W, bot], fill=OFFWHITE + (238,))
    for y in (top, bot):
        d.line([0, y, W, y], fill=(0xB9, 0xAE, 0x9C, 255), width=2)
    small_line, big_line = text.split("|")
    d.text((W // 2, top + 88), small_line, font=ImageFont.truetype(FONT_MED, 64), fill=(0x55, 0x4C, 0x42), anchor="mm")
    d.text((W // 2, top + 205), big_line, font=ImageFont.truetype(FONT_SEMI, 150), fill=INK, anchor="mm")
    s = 40
    sx, sy = W // 2 - s // 2, bot - 70
    d.rectangle([sx, sy, sx + s, sy + s], fill=CINNABAR)
    d.rectangle([sx + 6, sy + 6, sx + s - 6, sy + s - 6], outline=OFFWHITE, width=2)
    out_dir = os.path.join(short_dir(slug), "thumbnails")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "thumbnail_face.jpg")
    img.save(out, quality=95)
    print(out, f"frame {t}s, crop left {left}")


def cover_thumb(slug, path):
    im = Image.open(path).convert("RGB")
    big = im.resize((max(W, round(im.width * H / im.height)), max(H, round(im.height * W / im.width))), Image.LANCZOS)
    x, y = (big.width - W) // 2, (big.height - H) // 2
    out_dir = os.path.join(short_dir(slug), "thumbnails")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "thumbnail_book_cover.jpg")
    big.crop((x, y, x + W, y + H)).save(out, quality=95)
    print(out, f"source {im.size}", "(low resolution: will look soft at full size)" if im.height < 1200 else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["faces", "face", "cover"])
    ap.add_argument("slug")
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--step", type=float, default=2.0)
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--text", default="Readings from the|Tao Te Ching")
    a = ap.parse_args()
    if a.cmd == "faces":
        faces(a.slug, a.step, a.top)
    elif a.cmd == "face":
        face_thumb(a.slug, float(a.arg), a.text)
    else:
        cover_thumb(a.slug, a.arg)
