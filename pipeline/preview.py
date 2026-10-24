"""Quick look before the full render: first frame of every image shot, plus head-crop samples.

  python3 -I pipeline/preview.py <slug>     -> .work/<slug>/preview_images.jpg, preview_heads.jpg
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, source_path
import render

slug = sys.argv[1]
wd = work_dir(slug)
edl = json.load(open(os.path.join(wd, "edl.json")))
tiles = [Image.fromarray(render.ImageShot(s).frame(s["t0"])).resize((216, 384))
         for s in edl["shots"] if s["kind"] == "image"]
sheet = Image.new("RGB", (216 * len(tiles), 384))
for i, t in enumerate(tiles):
    sheet.paste(t, (216 * i, 0))
sheet.save(os.path.join(wd, "preview_images.jpg"), quality=85)

if os.path.exists(edl["crop_track"]):
    head = render.HeadReader(edl, source_path(slug))
    total = len(json.load(open(edl["crop_track"])))
    want = set(np.linspace(0, total - 1, 10).astype(int))
    heads = []
    for f in range(total):
        fr = head.next()
        if f in want:
            heads.append(Image.fromarray(fr).resize((216, 384)))
    hs = Image.new("RGB", (216 * len(heads), 384))
    for i, t in enumerate(heads):
        hs.paste(t, (216 * i, 0))
    hs.save(os.path.join(wd, "preview_heads.jpg"), quality=85)
print(os.path.join(wd, "preview_images.jpg"))
