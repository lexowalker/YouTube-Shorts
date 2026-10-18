"""Cleveland Museum of Art Open Access (CC0) search and download.

  python3 -I pipeline/cma.py search "bamboo" [--type Painting] [--dept "Chinese Art"]
  python3 -I pipeline/cma.py title "Ink Bamboo"
  python3 -I pipeline/cma.py get 1967.145 [1982.53 ...]        -> .work/img/<acc>_full.jpg (+ .json metadata)
  python3 -I pipeline/cma.py proxy 1967.145                    -> .work/img/proxy/<acc>.jpg, 10% grid, for choosing crops

Full masters are TIFFs (saved under a .jpg name; PIL reads them by content). Always check `date` and `culture`:
the brief wants classical work (Song masters, Zen ink, Joseon/Muromachi are fine), not 20th-century pieces.
"""
import json, os, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import IMG_DIR, image_path

API = "https://openaccess-api.clevelandart.org/api/artworks/"
UA = {"User-Agent": "youtube-shorts-pipeline/1.0"}


def api(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))


def show(rows):
    for a in rows:
        f = (a.get("images") or {}).get("full") or {}
        who = "; ".join(c.get("description", "")[:40] for c in a.get("creators", [])) or (a.get("culture") or [""])[0][:40]
        print(f"{a.get('accession_number'):14s} | {a['title'][:58]:58s} | {who:40s} | {a.get('creation_date')} | {f.get('width')}x{f.get('height')}")


def get(acc):
    os.makedirs(IMG_DIR, exist_ok=True)
    d = api(API + acc)["data"]
    im = d["images"]["full"]
    fn = image_path(acc)
    if not os.path.exists(fn) or os.path.getsize(fn) == 0:
        for attempt in range(4):  # big TIFFs occasionally drop mid-transfer
            try:
                data = urllib.request.urlopen(urllib.request.Request(im["url"], headers=UA), timeout=900).read()
                open(fn, "wb").write(data)
                break
            except Exception as e:
                print("retry", acc, e)
    meta = {"accession": acc, "title": d["title"], "creators": [c.get("description") for c in d.get("creators", [])],
            "culture": d.get("culture"), "date": d.get("creation_date"), "license": d.get("share_license_status"),
            "page": d.get("url"), "image_url": im["url"], "w": im["width"], "h": im["height"]}
    json.dump(meta, open(fn + ".json", "w"), indent=1, ensure_ascii=False)
    print(acc, im["width"], im["height"], d["title"], d.get("creation_date"), d.get("share_license_status"))


def proxy(acc):
    from PIL import Image, ImageDraw
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(image_path(acc))
    sc = 1000 / max(im.size) if im.width / im.height < 4 else 2400 / im.width
    p = im.convert("RGB").resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    d = ImageDraw.Draw(p)
    for i in range(1, 10):
        d.line([(p.width * i / 10, 0), (p.width * i / 10, p.height)], fill=(255, 0, 0))
        d.line([(0, p.height * i / 10), (p.width, p.height * i / 10)], fill=(255, 0, 0))
    os.makedirs(os.path.join(IMG_DIR, "proxy"), exist_ok=True)
    out = os.path.join(IMG_DIR, "proxy", acc + ".jpg")
    p.save(out, quality=85)
    print(out, im.size)


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "search":
        q = {"q": rest[0], "has_image": 1, "cc0": 1, "limit": 25}
        if "--type" in rest:
            q["type"] = rest[rest.index("--type") + 1]
        if "--dept" in rest:
            q["department"] = rest[rest.index("--dept") + 1]
        show(api(API + "?" + urllib.parse.urlencode(q))["data"])
    elif cmd == "title":
        show(api(API + "?" + urllib.parse.urlencode({"title": rest[0], "has_image": 1, "cc0": 1, "limit": 40}))["data"])
    elif cmd == "get":
        for acc in rest:
            get(acc)
    elif cmd == "proxy":
        for acc in rest:
            proxy(acc)
