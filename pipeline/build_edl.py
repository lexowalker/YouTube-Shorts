"""Build the edit decision list for a Short from its spec.

  python3 -I pipeline/build_edl.py <slug>

Reads shorts/<slug>/short.json and .work/<slug>/words.json; writes .work/<slug>/edl.json (used by the renderer)
and a portable copy at shorts/<slug>/edl.json. Fails loudly if any caption word differs from the spoken word,
if a spoken word is left uncaptioned, or if a crop falls outside its image.

Spec keys (see shorts/tao-ch4-unimpeded-harmony/short.json for a complete example):
  segments      [[src_start, src_end], ...] in program order; cut only in pauses
  word_fixes    transcript corrections in source time: {"near", "from", "to", ["s", "e"]}
  word_overrides  replace all words in a source span: {"from", "to", "words": [[w, s, e], ...], "why"}
  onset_fixes   caption onset corrections in program time: {"word", "prog", "to"}
  phrases       caption phrases: "|" splits the two lines, "*" marks the one ochre word, "~" marks a spoken filler
                ("~you ~know") that stays in the audio but is left off the screen; it must still match the speech
  cuts          shot changes in order: {"at": <anchor>, "head": true} or {"at": <anchor>, "image": {...}}
                anchors: seconds | {"seg": i} | {"phrase": "text", "after": s} | {"word": "tok", "after": s}
                image: {"acc", "x0", "y0", "h"} as fractions of the image (9:16 crop from top-left, height),
                optional "pan" (px, handscrolls only), "zoom" [from, to], "note"
  title         {"text", "dur", "size"}; optional (leave it out for no opening title card)
  caption_y     caption block centre as a fraction of the height (default 0.70; 0.83 for a 4K close-up, where 0.70 is his beard)
  endcard       {"dur"}
"""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_spec, work_dir, short_dir, image_path
from words import load_words, Env, refine_onsets, to_program, norm

Image.MAX_IMAGE_PIXELS = None


def crop_from(acc, x0f, y0f, hf):
    W, H = Image.open(image_path(acc)).size
    h = round(H * hf)
    w = round(h * 9 / 16)
    return [round(W * x0f), round(H * y0f), w, h], (W, H)


def main(slug):
    spec = load_spec(slug)
    wd = work_dir(slug)
    segments = [{"src_start": a, "src_end": b} for a, b in spec["segments"]]
    prog_dur = sum(s["src_end"] - s["src_start"] for s in segments)

    W = load_words(os.path.join(wd, "words.json"), spec.get("word_fixes", []), spec.get("word_overrides", []))
    W = refine_onsets(W, Env(os.path.join(wd, "audio16k.wav")))
    P = to_program(W, segments)
    for f in spec.get("onset_fixes", []):
        hit = [w for w in P if norm(w["w"]) == norm(f["word"]) and abs(w["ps"] - f["prog"]) < 0.05]
        assert len(hit) == 1, f"onset fix did not match exactly one word: {f}"
        hit[0]["ps"] = f["to"]

    caps, i = [], 0
    for line in spec["phrases"]:
        parts = [p.split() for p in line.split("|")]
        words, fillers = [], []
        for t in [t for p in parts for t in p]:
            hidden, key = t.startswith("~"), t.startswith("*")
            t = t.lstrip("~*")
            assert i < len(P), f"caption has more words than were spoken, at '{t}'"
            w = P[i]
            assert norm(w["w"]) == norm(t), f"caption mismatch at {w['ps']:.2f}: spoken '{w['w']}' vs caption '{t}'"
            (fillers if hidden else words).append({"w": t, "s": w["ps"], "e": w["pe"], "key": key})
            i += 1
        caps.append({"words": words, "fillers": fillers, "lines": [len([t for t in parts[0] if not t.startswith("~")])]})
    assert i == len(P), f"{len(P) - i} spoken words not captioned: {[w['w'] for w in P[i:]]}"
    # each phrase stays until the next begins, but clears during long pauses
    for k, c in enumerate(caps):
        end = c["words"][-1]["e"]
        nxt = caps[k + 1]["words"][0]["s"] if k + 1 < len(caps) else end + 0.6
        c["t_off"] = round(min(nxt, end + 0.5), 3)

    def anchor(a):
        if isinstance(a, (int, float)):
            return float(a)
        if "seg" in a:
            return sum(s["src_end"] - s["src_start"] for s in segments[:a["seg"]])
        after = a.get("after", 0)
        if "phrase" in a:
            return next(c["words"][0]["s"] for c in caps if c["words"][0]["s"] >= after
                        and " ".join(w["w"] for w in c["words"]).startswith(a["phrase"]))
        return next(w["ps"] for w in P if w["ps"] >= after and norm(w["w"]) == norm(a["word"]))

    shots = []
    for k, c in enumerate(spec["cuts"]):
        t0 = anchor(c["at"])
        t1 = anchor(spec["cuts"][k + 1]["at"]) if k + 1 < len(spec["cuts"]) else prog_dur
        if c.get("head"):
            shots.append({"kind": "head", "t0": round(t0, 3), "t1": round(t1, 3)})
            continue
        im = c["image"]
        crop, (IW, IH) = crop_from(im["acc"], im["x0"], im["y0"], im["h"])
        x, y, w, h = crop
        pan = im.get("pan", 0)
        assert x >= 0 and y >= 0 and x + w + max(0, pan) <= IW and y + h <= IH, f"crop outside image: {im}"
        zoom = im.get("zoom", [1.12, 1.0] if t1 - t0 >= 8 else [1.08, 1.0])
        shots.append({"kind": "image", "acc": im["acc"], "file": image_path(im["acc"]), "crop": crop,
                      "pan": pan, "zoom": zoom, "note": im.get("note", ""), "t0": round(t0, 3), "t1": round(t1, 3)})
    for s in shots:
        assert s["t1"] > s["t0"], f"empty or reversed shot: {s}"

    title = spec.get("title")  # optional: no opening title card if absent
    edl = {"slug": slug, "segments": segments, "shots": shots, "captions": caps,
           "title": {"text": title["text"], "t0": 0.0, "t1": title.get("dur", 3.6), "size": title.get("size", 52)} if title else None,
           "endcard": {"dur": spec.get("endcard", {}).get("dur", 4.0), "fade_frames": 15},
           "caption_y": spec.get("caption_y", 0.70),
           "crop_track": os.path.join(wd, "crop_track.json")}
    json.dump(edl, open(os.path.join(wd, "edl.json"), "w"), indent=1, ensure_ascii=False)

    portable = json.loads(json.dumps(edl))
    for s in portable["shots"]:
        if "file" in s:
            s["file"] = ".work/img/" + os.path.basename(s["file"])
    portable["crop_track"] = f".work/{slug}/crop_track.json"
    json.dump(portable, open(os.path.join(short_dir(slug), "edl.json"), "w"), indent=1, ensure_ascii=False)

    # pacing report: alternate every ~4-10 s, never hold one mode longer than ~12 s
    runs, cur = [], None
    for s in shots:
        if cur and cur[0] == s["kind"]:
            cur[2] = s["t1"]
        else:
            cur = [s["kind"], s["t0"], s["t1"]]
            runs.append(cur)
    for s in shots:
        print(f"{s['t0']:6.2f}-{s['t1']:6.2f} ({s['t1'] - s['t0']:5.2f}) {s['kind']:5s} {s.get('acc', '')} {s.get('note', '')}")
    head = sum(s["t1"] - s["t0"] for s in shots if s["kind"] == "head")
    longest = max(runs, key=lambda r: r[2] - r[1])
    print(f"program {prog_dur:.2f}s + end card {edl['endcard']['dur']}s; captions {len(caps)}; "
          f"head {100 * head / prog_dur:.0f}%; longest {longest[0]} run {longest[2] - longest[1]:.1f}s")
    if longest[2] - longest[1] > 12.0:
        print("WARNING: a mode runs longer than 12 s")


if __name__ == "__main__":
    main(sys.argv[1])
