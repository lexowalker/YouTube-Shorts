"""Find and cache high-quality public-domain images (The Met, Cleveland Museum of Art, Art Institute of Chicago,
Wikimedia Commons). Wikimedia rate-limits this environment's shared address, so prefer the museums..

  python3 -I pipeline/images.py met-search "woodblock bird" [--n 20]       Met Open Access, public-domain hits only
  python3 -I pipeline/images.py cma-search "dragon" [--n 20]               Cleveland Museum of Art (CC0)
  python3 -I pipeline/images.py artic-search "Hiroshige" [--n 20]                Art Institute of Chicago (CC0)
  python3 -I pipeline/images.py wiki-search "Itcho blind men elephant" [--n 20]
  python3 -I pipeline/images.py get met:45434 | cma:1976.123 | wiki:"File:Name.jpg"   [--id myname]
  python3 -I pipeline/images.py sheet id1 id2 ...                           contact sheet -> .work/img/sheet.jpg
  python3 -I pipeline/images.py cutout id [--model isnet-general-use]       subject on transparent -> .work/img/<id>_cut.png

Downloads land in .work/img/<id>_full.jpg (+ <id>.json: title, creator, date, license, page), which the render
and DELIVERY.md credits read. Search hits print one per line with the size of the image, so small files can be
skipped (the frame is 1080x1920).
"""
import argparse, json, os, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import IMG_DIR

UA = {"User-Agent": "tao-shorts-pipeline/1.0 (image research)"}
os.makedirs(IMG_DIR, exist_ok=True)


def fetch_json(url, tries=5):
    import time, urllib.error
    for k in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == tries - 1:
                raise
            time.sleep(4 * 2 ** k)  # rate limited (Wikimedia): back off


def download(url, dst):
    import time, urllib.error
    for k in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == 4:
                raise
            time.sleep(8 * 2 ** k)
    with r, open(dst, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)


# ---------------------------------------------------------------- The Met
MET = "https://collectionapi.metmuseum.org/public/collection/v1"


def met_obj(oid):
    return fetch_json(f"{MET}/objects/{oid}")


def met_search(q, n):
    # /v1/search was retired on 2026-10-01; /v1.1/search is paginated (offset, limit)
    ids = fetch_json(f"https://collectionapi.metmuseum.org/public/collection/v1.1/search?hasImages=true&limit={n * 3}"
                     f"&q={urllib.parse.quote(q)}").get("objectIDs") or []
    shown = 0
    for oid in ids[: n * 3]:
        try:
            o = met_obj(oid)
        except Exception:
            continue
        if not o.get("isPublicDomain") or not o.get("primaryImage"):
            continue
        print(f"met:{oid}\t{o.get('title','')[:70]}\t{o.get('artistDisplayName','')[:30]}\t{o.get('culture','')}\t{o.get('objectDate','')}\t{o.get('classification','')}")
        shown += 1
        if shown >= n:
            break


# ---------------------------------------------------------------- Cleveland
CMA = "https://openaccess-api.clevelandart.org/api/artworks/"


def cma_search(q, n):
    d = fetch_json(f"{CMA}?q={urllib.parse.quote(q)}&has_image=1&cc0=1&limit={n}")
    for a in d["data"]:
        img = (a.get("images") or {}).get("print") or {}
        print(f"cma:{a['accession_number']}\t{a['title'][:70]}\t{a.get('culture', [''])[0] if a.get('culture') else ''}\t{a.get('creation_date','')}\t{a.get('type','')}\t{img.get('width')}x{img.get('height')}")


# ---------------------------------------------------------------- Art Institute of Chicago
ARTIC = "https://api.artic.edu/api/v1/artworks"
ARTIC_F = "id,title,artist_title,image_id,is_public_domain,date_display,place_of_origin,classification_title,thumbnail"


def artic_search(q, n):
    d = fetch_json(f"{ARTIC}/search?q={urllib.parse.quote(q)}&query[term][is_public_domain]=true&fields={ARTIC_F}&limit={n}")
    for a in d["data"]:
        if not a.get("image_id"):
            continue
        t = a.get("thumbnail") or {}
        print(f"artic:{a['id']}\t{a['title'][:70]}\t{a.get('artist_title') or ''}\t{a.get('place_of_origin') or ''}\t{a.get('date_display')}\t{t.get('width')}x{t.get('height')}")


# ---------------------------------------------------------------- Wikimedia Commons
WIKI = "https://commons.wikimedia.org/w/api.php"


def wiki_info(title, width=None):
    p = {"action": "query", "titles": title, "prop": "imageinfo", "format": "json", "iiprop": "url|size|extmetadata"}
    if width:
        p["iiurlwidth"] = width  # a standard thumbnail size: Wikimedia rate-limits downloads of original files
    q = urllib.parse.urlencode(p)
    pages = fetch_json(f"{WIKI}?{q}")["query"]["pages"]
    return next(iter(pages.values()))


def wiki_search(q, n):
    p = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": q, "srnamespace": 6,
                                "srlimit": n, "format": "json"})
    for hit in fetch_json(f"{WIKI}?{p}")["query"]["search"]:
        try:
            ii = wiki_info(hit["title"])["imageinfo"][0]
        except Exception:
            continue
        lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
        print(f"wiki:\"{hit['title']}\"\t{ii['width']}x{ii['height']}\t{lic}")


# ---------------------------------------------------------------- get
def get(ref, ident=None):
    kind, key = ref.split(":", 1)
    if kind == "met":
        o = met_obj(key)
        assert o.get("isPublicDomain"), "not public domain"
        url = o["primaryImage"]
        meta = {"title": o.get("title"), "creator": o.get("artistDisplayName") or o.get("culture"),
                "date": o.get("objectDate"), "culture": o.get("culture"), "license": "CC0 (The Met Open Access)",
                "page": o.get("objectURL")}
    elif kind == "cma":
        a = fetch_json(f"{CMA}{urllib.parse.quote(key)}")["data"]
        imgs = a["images"]
        url = (imgs.get("full") or imgs.get("print"))["url"]
        meta = {"title": a["title"], "creator": ", ".join(c["description"] for c in a.get("creators", [])) or ", ".join(a.get("culture") or []),
                "date": a.get("creation_date"), "license": "CC0 (Cleveland Museum of Art)", "page": a.get("url")}
    elif kind == "artic":
        a = fetch_json(f"{ARTIC}/{key}?fields={ARTIC_F}")["data"]
        assert a["is_public_domain"], "not public domain"
        url = f"https://www.artic.edu/iiif/2/{a['image_id']}/full/3000,/0/default.jpg"
        meta = {"title": a["title"], "creator": a.get("artist_title") or a.get("place_of_origin"), "date": a.get("date_display"),
                "license": "CC0 (Art Institute of Chicago)", "page": f"https://www.artic.edu/artworks/{key}"}
    elif kind == "wiki":
        title = key.strip('"')
        info = wiki_info(title, 3840)
        ii = info["imageinfo"][0]
        em = ii.get("extmetadata", {})
        url = ii["url"]  # thumbnails come from thumb.wikimedia.org, which this environment cannot reach
        strip = lambda s: __import__("re").sub("<[^>]+>", "", s or "").strip()
        meta = {"title": strip(em.get("ObjectName", {}).get("value")) or title, "creator": strip(em.get("Artist", {}).get("value")),
                "date": strip(em.get("DateTimeOriginal", {}).get("value")), "license": em.get("LicenseShortName", {}).get("value"),
                "page": ii.get("descriptionurl")}
    else:
        sys.exit(f"unknown source {kind}")
    ident = ident or key.replace("/", "_").replace(" ", "_").strip('"').replace("File:", "")[:60]
    dst = os.path.join(IMG_DIR, f"{ident}_full.jpg")
    download(url, dst)
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(dst)
    meta.update({"id": ident, "ref": ref, "url": url, "size": im.size})
    json.dump(meta, open(os.path.join(IMG_DIR, f"{ident}.json"), "w"), indent=1)
    print(ident, im.size, meta["title"], "|", meta["creator"], "|", meta["date"], "|", meta["license"])


def sheet(ids, out=None, th=420):
    from PIL import Image, ImageDraw
    Image.MAX_IMAGE_PIXELS = None
    cells = []
    for i in ids:
        im = Image.open(os.path.join(IMG_DIR, f"{i}_full.jpg")).convert("RGB")
        im.thumbnail((int(th * 1.6), th))
        c = Image.new("RGB", (int(th * 1.6), th + 30), "white")
        c.paste(im, ((c.width - im.width) // 2, 0))
        ImageDraw.Draw(c).text((6, th + 6), i[:60], fill="black")
        cells.append(c)
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    s = Image.new("RGB", (cells[0].width * cols, cells[0].height * rows), "white")
    for k, c in enumerate(cells):
        s.paste(c, ((k % cols) * c.width, (k // cols) * c.height))
    out = out or os.path.join(IMG_DIR, "sheet.jpg")
    s.save(out, quality=85)
    print(out)


def cutout(ident, model):
    from PIL import Image
    from rembg import remove, new_session
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(os.path.join(IMG_DIR, f"{ident}_full.jpg")).convert("RGB")
    im.thumbnail((2400, 2400))
    out = remove(im, session=new_session(model))
    bb = out.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    out = out.crop(bb)
    dst = os.path.join(IMG_DIR, f"{ident}_cut.png")
    out.save(dst)
    print(dst, out.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="+")
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--id")
    ap.add_argument("--model", default="isnet-general-use")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "met-search":
        met_search(" ".join(a.args), a.n)
    elif a.cmd == "cma-search":
        cma_search(" ".join(a.args), a.n)
    elif a.cmd == "artic-search":
        artic_search(" ".join(a.args), a.n)
    elif a.cmd == "wiki-search":
        wiki_search(" ".join(a.args), a.n)
    elif a.cmd == "get":
        get(a.args[0], a.id)
    elif a.cmd == "sheet":
        sheet(a.args, a.out)
    elif a.cmd == "cutout":
        for i in a.args:
            cutout(i, a.model)


if __name__ == "__main__":
    main()
