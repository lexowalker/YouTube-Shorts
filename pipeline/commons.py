"""Find and fetch freely licensed photos, documents and illustrations from Wikimedia Commons.

  python3 -I pipeline/commons.py search "pack of thalidomide tablets" [--n 20]
      File names from Commons' media search (the HTML page; the API is rate-limited from here).
  python3 -I pipeline/commons.py info "Pack of Thalidomide tablets.jpg"
      Licence, author and size, read from the file page.
  python3 -I pipeline/commons.py get <id> "Pack of Thalidomide tablets.jpg" [--width 2400]
      Downloads a rendering (Special:FilePath, at most --width px wide; Wikimedia only serves its standard thumbnail widths, e.g. 960 or 1280; larger or odd widths get 429) to .work/img/<id>_full.jpg with the same
      .json metadata cma.py writes, so a spec can use it as "acc": "<id>". Refuses files whose licence it can't
      read as free (public domain, CC0, CC BY, CC BY-SA).
"""
import html, json, os, re, sys, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import IMG_DIR, image_path

UA = {"User-Agent": "youtube-shorts-pipeline/1.0"}
BASE = "https://commons.wikimedia.org"
FREE = re.compile(r"public domain|\bPD\b|CC0|CC BY|CC-BY|Creative Commons Attribution", re.I)


def fetch(url, binary=False):
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
    return data if binary else data.decode("utf-8", "replace")


def search(q, n=20):
    page = fetch(f"{BASE}/w/index.php?search={urllib.parse.quote(q)}&title=Special:MediaSearch&type=image")
    seen = []
    for m in re.finditer(r'File:([^"<>]+?\.(?:jpe?g|png|tiff?|gif|webp))', page, re.I):
        name = html.unescape(urllib.parse.unquote(m.group(1))).replace("_", " ")
        if name not in seen:
            seen.append(name)
    return seen[:n]


def info(name):
    page = fetch(f"{BASE}/wiki/File:{urllib.parse.quote(name.replace(' ', '_'))}")
    lic = re.findall(r'class="licensetpl(?:_|&#95;)short"[^>]*>(.*?)<', page)
    lic = re.split(r"\\u003C|<|\"", lic[0])[0].strip() if lic else ""
    if not lic:
        m = re.search(r"(public domain|Creative Commons [^<]{0,60}|CC0[^<]{0,20})", page, re.I)
        lic = re.split(r"\\u003C|<|\"", m.group(1))[0].strip() if m else "unknown"
    au = re.search(r'id="fileinfotpl(?:_|&#95;)aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', page, re.S)
    author = re.sub(r"<[^>]+>", "", au.group(1)).strip()[:120] if au else ""
    dt = re.search(r'id="fileinfotpl(?:_|&#95;)date"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', page, re.S)
    date = re.sub(r"<[^>]+>", "", dt.group(1)).strip()[:60] if dt else ""
    size = re.search(r"([\d,]+) × ([\d,]+) pixels", page)
    return {"license": html.unescape(lic), "author": html.unescape(author), "date": html.unescape(date),
            "size": [int(size.group(1).replace(",", "")), int(size.group(2).replace(",", ""))] if size else None,
            "page": f"{BASE}/wiki/File:{urllib.parse.quote(name.replace(' ', '_'))}"}


def get(acc, name, width=1280):
    meta = info(name)
    assert FREE.search(meta["license"]), f"licence not recognised as free: {meta['license']!r} ({meta['page']})"
    os.makedirs(IMG_DIR, exist_ok=True)
    # upload.wikimedia.org directly: Special:FilePath redirects to thumb.wikimedia.org, which this environment can't reach
    import hashlib, io
    from PIL import Image
    fn = name.replace(" ", "_"); h = hashlib.md5(fn.encode()).hexdigest(); q = urllib.parse.quote(fn)
    orig = f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{q}"
    url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"
    data = None
    for w in (width, 960):  # thumbnails only: full-size originals are rate-limited from here
        url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}"
        try:
            data = fetch(url, binary=True)
            break
        except Exception as e:
            err = e
    if data is None:
        raise err
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.save(image_path(acc), quality=95)
    json.dump({"accession": acc, "title": os.path.splitext(name)[0], "creators": [meta["author"]] if meta["author"] else [],
               "culture": None, "date": meta["date"], "license": meta["license"], "page": meta["page"],
               "image_url": url, "w": im.width, "h": im.height}, open(image_path(acc) + ".json", "w"), indent=1, ensure_ascii=False)
    print(acc, im.size, meta["license"], "|", meta["author"][:60], "|", meta["page"])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "search":
        n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 20
        for f in search(sys.argv[2], n):
            print(f)
    elif cmd == "info":
        print(json.dumps(info(sys.argv[2]), indent=1, ensure_ascii=False))
    elif cmd == "get":
        w = int(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else 1280
        get(sys.argv[2], sys.argv[3], w)
