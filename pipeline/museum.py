"""Search and fetch open-access artworks from The Met, the Art Institute of Chicago and the Cleveland Museum of Art.

  python3 -I pipeline/museum.py search "<query>" [--src met,aic,cma] [--n 12] [--dept "Asian Art"]
      Lists public-domain hits with an image, and writes a contact sheet of them to .work/img/sheet.jpg.
  python3 -I pipeline/museum.py get met-45434 aic-7691 cma-1967.145 ...
      Downloads the full image to .work/img/<key>_full.jpg and its metadata to .work/img/<key>.json.
  python3 -I pipeline/museum.py proxy <key> ...
      A 10%-grid proxy of each image at .work/img/proxy/<key>.jpg, for choosing crops.

A key is <source>-<id>: the Met object ID, the AIC artwork ID or the CMA accession number. All three collections
publish these works as CC0 / public domain; the .json keeps the title, maker, date, page URL and licence.
"""
import io, json, os, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import IMG_DIR, image_path

Image.MAX_IMAGE_PIXELS = None
UA = {"User-Agent": "Mozilla/5.0 (compatible; shorts-pipeline/1.0)"}
MET = "https://collectionapi.metmuseum.org/public/collection/"
AIC = "https://api.artic.edu/api/v1/artworks"
CMA = "https://openaccess-api.clevelandart.org/api/artworks/"


def fetch(url, timeout=120):
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:
            err = e
    raise err


def api(url):
    return json.loads(fetch(url, 60))


def met_obj(oid):
    try:
        d = api(f"{MET}v1/objects/{oid}")
    except Exception:
        return None
    if not d.get("isPublicDomain") or not d.get("primaryImage"):
        return None
    return {"key": f"met-{oid}", "title": d["title"], "maker": d.get("artistDisplayName") or d.get("culture", ""),
            "date": d.get("objectDate", ""), "medium": d.get("medium", ""), "full": d["primaryImage"],
            "thumb": d.get("primaryImageSmall") or d["primaryImage"], "page": d.get("objectURL", ""),
            "more": d.get("additionalImages", []),
            "license": "Public domain (The Met Open Access, CC0)", "credit": "The Metropolitan Museum of Art"}


def met_search(q, n, dept=None):
    url = f"{MET}v1.1/search?q={urllib.parse.quote(q)}&hasImages=true&isPublicDomain=true&limit={n * 2}"
    if dept:
        ids = {"Asian Art": 6}.get(dept, dept)
        url += f"&departmentId={ids}"
    ids = (api(url).get("objectIDs") or [])[:n * 2]
    with ThreadPoolExecutor(8) as ex:
        return [o for o in ex.map(met_obj, ids) if o][:n]


def aic_row(d):
    iid = d["image_id"]
    return {"key": f"aic-{d['id']}", "title": d["title"], "maker": (d.get("artist_display") or "").replace("\n", ", "),
            "date": d.get("date_display", ""), "medium": d.get("medium_display", ""),
            "full": f"https://www.artic.edu/iiif/2/{iid}/full/max/0/default.jpg",
            "thumb": f"https://www.artic.edu/iiif/2/{iid}/full/400,/0/default.jpg",
            "page": f"https://www.artic.edu/artworks/{d['id']}",
            "license": "Public domain (Art Institute of Chicago, CC0)", "credit": "Art Institute of Chicago"}


AIC_FIELDS = "id,title,artist_display,date_display,medium_display,image_id,is_public_domain"


def aic_search(q, n, dept=None):
    url = f"{AIC}/search?q={urllib.parse.quote(q)}&limit={n * 2}&fields={AIC_FIELDS}&query[term][is_public_domain]=true"
    return [aic_row(d) for d in api(url)["data"] if d.get("image_id")][:n]


def cma_row(a):
    im = a["images"]
    full = im.get("full") or im.get("print")
    return {"key": f"cma-{a['accession_number']}", "title": a["title"],
            "maker": "; ".join(c.get("description", "") for c in a.get("creators", [])) or ", ".join(a.get("culture") or []),
            "date": a.get("creation_date", ""), "medium": a.get("technique", ""), "full": full["url"],
            "thumb": im["web"]["url"], "page": a.get("url", ""),
            "license": "CC0 (Cleveland Museum of Art Open Access)", "credit": "The Cleveland Museum of Art"}


def cma_search(q, n, dept=None):
    url = f"{CMA}?q={urllib.parse.quote(q)}&has_image=1&cc0=1&limit={n}"
    if dept:
        url += "&department=" + urllib.parse.quote(dept)
    return [cma_row(a) for a in api(url)["data"] if a.get("images", {}).get("web")]


SEARCH = {"met": met_search, "aic": aic_search, "cma": cma_search}


def lookup(key):
    src, oid = key.split("-", 1)
    if src == "met":
        return met_obj(oid)
    if src == "aic":
        return aic_row(api(f"{AIC}/{oid}?fields={AIC_FIELDS}")["data"])
    return cma_row(api(CMA + oid)["data"])


def sheet(rows, out):
    def thumb(r):
        try:
            im = Image.open(io.BytesIO(fetch(r["thumb"], 60))).convert("RGB")
            im.thumbnail((380, 380))
            return im
        except Exception:
            return Image.new("RGB", (380, 380), "gray")
    with ThreadPoolExecutor(8) as ex:
        ims = list(ex.map(thumb, rows))
    cols = 5
    s = Image.new("RGB", (cols * 400, ((len(ims) + cols - 1) // cols) * 430), "white")
    d = ImageDraw.Draw(s)
    for i, (im, r) in enumerate(zip(ims, rows)):
        x, y = (i % cols) * 400, (i // cols) * 430
        s.paste(im, (x + 10, y + 30))
        d.text((x + 10, y + 8), r["key"], fill="black")
    s.save(out, quality=85)


def get(key):
    os.makedirs(IMG_DIR, exist_ok=True)
    fn = image_path(key)
    r = lookup(key)
    assert r, f"{key}: not public domain or no image"
    if not os.path.exists(fn) or os.path.getsize(fn) == 0:
        open(fn, "wb").write(fetch(r["full"], 900))
    im = Image.open(fn)
    r["size"] = list(im.size)
    json.dump(r, open(os.path.join(IMG_DIR, f"{key}.json"), "w"), indent=1, ensure_ascii=False)
    print(f"{key}: {r['title'][:60]} | {r['maker'][:40]} | {r['date']} | {im.size[0]}x{im.size[1]}")


def proxy(key):
    im = Image.open(image_path(key)).convert("RGB")
    im.thumbnail((1600, 1600))
    d = ImageDraw.Draw(im)
    for k in range(1, 10):
        d.line([(im.width * k / 10, 0), (im.width * k / 10, im.height)], fill=(255, 0, 0), width=1)
        d.line([(0, im.height * k / 10), (im.width, im.height * k / 10)], fill=(255, 0, 0), width=1)
        d.text((im.width * k / 10 + 3, 3), f".{k}", fill=(255, 255, 0))
        d.text((3, im.height * k / 10 + 3), f".{k}", fill=(255, 255, 0))
    os.makedirs(os.path.join(IMG_DIR, "proxy"), exist_ok=True)
    out = os.path.join(IMG_DIR, "proxy", f"{key}.jpg")
    im.save(out, quality=88)
    print(out)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "get", "proxy"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--src", default="met,aic,cma")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--dept")
    ap.add_argument("--out", default=os.path.join(IMG_DIR, "sheet.jpg"))
    a = ap.parse_args()
    if a.cmd == "search":
        rows = []
        for s in a.src.split(","):
            try:
                rows += SEARCH[s](a.args[0], a.n, a.dept)
            except Exception as e:
                print(f"{s}: search failed ({e})")
        for r in rows:
            print(f"{r['key']:16s} | {r['title'][:56]:56s} | {r['maker'][:32]:32s} | {r['date'][:22]}")
        os.makedirs(IMG_DIR, exist_ok=True)
        sheet(rows, a.out)
    else:
        for k in a.args:
            (get if a.cmd == "get" else proxy)(k)
