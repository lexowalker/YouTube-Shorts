"""Thumbnail 1: David's face with 'Readings from the Tao Te Ching' in the end-card serif."""
import sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import FONT_SEMI, FONT_MED, OFFWHITE, INK, CINNABAR, SRC

W, H = 1080, 1920
t, left, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", SRC, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True, check=True).stdout
frame = Image.frombytes("RGB", (1280, 720), raw)
img = frame.crop((round(left), 0, round(left) + 405, 720)).resize((W, H), Image.LANCZOS)
img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=40, threshold=2))  # still image: a touch of crispness

# rice-paper panel in the middle band, so the text survives any crop YouTube applies
d = ImageDraw.Draw(img, "RGBA")
top, bot = 1150, 1520
d.rectangle([0, top, W, bot], fill=OFFWHITE + (238,))
d.line([0, top, W, top], fill=(0xB9, 0xAE, 0x9C, 255), width=2)
d.line([0, bot, W, bot], fill=(0xB9, 0xAE, 0x9C, 255), width=2)

small = ImageFont.truetype(FONT_MED, 64)
big = ImageFont.truetype(FONT_SEMI, 150)
cx = W // 2
d.text((cx, top + 88), "Readings from the", font=small, fill=(0x55, 0x4C, 0x42), anchor="mm")
d.text((cx, top + 205), "Tao Te Ching", font=big, fill=INK, anchor="mm")
# small cinnabar seal, the end card's only accent
s = 40
sx, sy = cx - s // 2, bot - 70
d.rectangle([sx, sy, sx + s, sy + s], fill=CINNABAR)
d.rectangle([sx + 6, sy + 6, sx + s - 6, sy + s - 6], outline=OFFWHITE, width=2)
img.save(out, quality=95)
