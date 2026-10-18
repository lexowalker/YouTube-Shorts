"""Delivery tables from the EDL: source timestamps in order, and the image log (also -> shorts/<slug>/images.json).

  python3 -I pipeline/notes.py <slug>     (paste the printed tables into shorts/<slug>/DELIVERY.md)
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, short_dir


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


slug = sys.argv[1]
edl = json.load(open(os.path.join(work_dir(slug), "edl.json")))
print("| # | Source | Short | Opens with |\n|---|---|---|---|")
p = 0.0
for k, s in enumerate(edl["segments"]):
    d = s["src_end"] - s["src_start"]
    first = next((c["words"][0]["w"] + " " + " ".join(w["w"] for w in c["words"][1:]) for c in edl["captions"] if c["words"][0]["s"] >= p - 0.01), "")
    print(f"| {k + 1} | {mmss(s['src_start'])} – {mmss(s['src_end'])} | {mmss(p)} – {mmss(p + d)} | \"{first}…\" |")
    p += d
print(f"| — | — | {mmss(p)} – {mmss(p + edl['endcard']['dur'])} | End card |\n")

rows = []
print("| Short (s) | Work | Artist / culture | Date | License | Source |\n|---|---|---|---|---|---|")
for s in edl["shots"]:
    if s["kind"] != "image":
        continue
    m = json.load(open(s["file"] + ".json"))
    who = ", ".join(c for c in m["creators"] if c) or ("Unknown, " + ", ".join(m.get("culture") or []))
    rows.append({"short_start_s": s["t0"], "short_end_s": s["t1"], "accession": m["accession"], "title": m["title"],
                 "artist": who, "date": m["date"], "license": m["license"], "source_page": m["page"],
                 "image_file_url": m["image_url"], "crop_xywh_px": s["crop"],
                 "motion": (f"horizontal pan {s['pan']} px, " if s.get("pan") else "") + "zoom-out %.2fx→%.2fx, linear" % tuple(s["zoom"])})
    print(f"| {s['t0']:.2f}–{s['t1']:.2f} | {m['title']} | {who} | {m['date']} | {m['license']} | {m['page']} |")
json.dump(rows, open(os.path.join(short_dir(slug), "images.json"), "w"), indent=1, ensure_ascii=False)
