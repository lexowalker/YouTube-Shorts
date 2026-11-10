"""Scene-based Shorts: talking head, museum images, animated collages, captions and the end card.

  python3 -I pipeline/scenes.py build <slug>     spec -> .work/<slug>/edl.json (+ a portable copy in shorts/<slug>/)
  python3 -I pipeline/scenes.py draft <slug>     -> .work/<slug>/draft_*.jpg: the frames that matter, composed exactly
                                                    as the render will (each scene start/middle/end, each collage piece)
  python3 -I pipeline/scenes.py render <slug>    -> .work/<slug>/video_master.mp4 (then audio.py and encode.py)

Order of work: prog.py (word timings on the cut) -> build -> head.py (head master) -> draft -> audio.py -> render -> encode.py.

short.json keys:
  segments        [[src_start, src_end], ...] source pieces in program order (cut in pauses)
  phrases         caption phrases as in build_edl.py ("|" line break, "*" key word, "~" spoken but not shown).
                  Lines he reads from the book carry quotation marks in the phrase text.
  word_fixes / word_overrides   corrections to .work/<slug>/words.json, in PROGRAM time (see words.py)
  scenes          in order: {"at": <anchor>, "head": true} | {"at": ..., "image": {...}} | {"at": ..., "collage": "<name>"}
                  anchors: seconds | {"seg": i} (start of segment i) | {"word": "tok", "after": s, "lead": s}
                  image: {"key", "x0", "y0", "h"} 9:16 crop as fractions (top-left, height); "zoom": [from, to]
                  (default [1.0, 1.035]); "pan": [dx, dy] as fractions of the crop (needs zoom > 1)
  collages        {"<name>": {...}} (see collage.py)
  caption_y, endcard

House rules built in: every scene change is a soft 0.4 s dissolve; a dissolve never shows the head from the wrong
side of an audio join; image moves are eased and tiny (about 3.5% over the whole shot).
"""
import json, math, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, FPS, FONT_MED, load_spec, work_dir, short_dir, image_path
from words import load_words, Env, refine_onsets, norm
from render import Captions, build_endcard, endcard_frame
from collage import Collage

Image.MAX_IMAGE_PIXELS = None
XF = 12        # frames of dissolve between scenes
MIN_SCENE = 3.0


# ---------------------------------------------------------------- build
def snap_after_pauses(words, env, quiet=-46.0, loud=-41.0, gap=0.18, reach=0.5):
    """Whisper is loose (0.2-0.5 s) on the first word after a pause. Where the voice starts again after a real
    silence, put the nearest word's onset exactly there, so the caption appears as he starts to speak."""
    db, step = env.db, env.step
    onsets, run = [], 0
    for i, d in enumerate(db):
        if d < quiet:
            run += 1
        elif d > loud:
            if run * step >= gap:
                onsets.append(i * step)
            run = 0
    for v in onsets:
        k = min(range(len(words)), key=lambda j: abs(words[j]["s"] - v))
        w = words[k]
        if abs(w["s"] - v) > reach or abs(w["s"] - v) < 0.03:
            continue
        if k > 0 and words[k - 1]["s"] > v - 0.12:
            continue  # another word already starts here
        if k + 1 < len(words) and words[k + 1]["s"] < v + 0.05:
            continue
        w["s0"], w["s"] = w.get("s0", w["s"]), round(v, 3)
        if k > 0 and words[k - 1]["e"] > v:
            words[k - 1]["e"] = round(v, 3)
    return words


def build(slug):
    spec, wd = load_spec(slug), work_dir(slug)
    segs = [{"src_start": a, "src_end": b} for a, b in spec["segments"]]
    dur = sum(s["src_end"] - s["src_start"] for s in segs)
    words = load_words(os.path.join(wd, "words.json"), spec.get("word_fixes", []), spec.get("word_overrides", []))
    env = Env(os.path.join(wd, "prog16k.wav"))
    words = snap_after_pauses(refine_onsets(words, env), env)
    P = [dict(w, ps=w["s"], pe=min(w["e"], dur)) for w in words]

    caps, i = [], 0
    for line in spec["phrases"]:
        parts = [p.split() for p in line.split("|")]
        shown, fillers = [], []
        for t in [t for p in parts for t in p]:
            hidden, key = t.startswith("~"), t.startswith("*")
            t = t.lstrip("~*")
            assert i < len(P), f"caption has more words than were spoken, at '{t}'"
            w = P[i]
            assert norm(w["w"]) == norm(t), f"caption mismatch at {w['ps']:.2f}: spoken '{w['w']}' vs caption '{t}'"
            (fillers if hidden else shown).append({"w": t, "s": w["ps"], "e": w["pe"], "key": key})
            i += 1
        caps.append({"words": shown, "fillers": fillers, "lines": [len([t for t in parts[0] if not t.startswith("~")])]})
    assert i == len(P), f"{len(P) - i} spoken words not captioned: {[w['w'] for w in P[i:]]}"
    for k, c in enumerate(caps):
        end = c["words"][-1]["e"]
        nxt = caps[k + 1]["words"][0]["s"] if k + 1 < len(caps) else end + 0.6
        c["t_off"] = round(min(nxt, end + 0.5), 3)

    joins = [0.0]
    for s in segs:
        joins.append(joins[-1] + s["src_end"] - s["src_start"])

    def anchor(a):
        if isinstance(a, (int, float)):
            return float(a)
        if "seg" in a:
            return joins[a["seg"]]
        after = a.get("after", 0)
        return next(w["ps"] for w in P if w["ps"] >= after and norm(w["w"]) == norm(a["word"])) - a.get("lead", 0.0)

    scenes = []
    for k, c in enumerate(spec["scenes"]):
        t0 = anchor(c["at"])
        t1 = anchor(spec["scenes"][k + 1]["at"]) if k + 1 < len(spec["scenes"]) else dur
        s = {"t0": round(t0, 3), "t1": round(t1, 3), "note": c.get("note", "")}
        if c.get("head"):
            s["kind"] = "head"
        elif "image" in c:
            im = dict(c["image"])
            iw, ih = Image.open(image_path(im["key"])).size
            h = round(ih * im["h"])
            w = round(h * 9 / 16)
            x, y = round(iw * im["x0"]), round(ih * im["y0"])
            assert x >= 0 and y >= 0 and x + w <= iw and y + h <= ih, f"crop outside image: {im} ({iw}x{ih})"
            s.update(kind="image", key=im["key"], file=image_path(im["key"]), crop=[x, y, w, h],
                     zoom=im.get("zoom", [1.0, 1.035]), pan=im.get("pan", [0, 0]))
        else:
            col = json.loads(json.dumps(spec["collages"][c["collage"]]))
            for p in col["pieces"]:
                at = p.get("at", 0.0)
                p["at"] = round((at if isinstance(at, (int, float)) else anchor(at) - t0), 3)
            s.update(kind="collage", name=c["collage"], collage=col)
        scenes.append(s)
    for s in scenes:
        assert s["t1"] > s["t0"], f"empty or reversed scene: {s}"

    edl = {"slug": slug, "segments": segs, "joins": [round(j, 4) for j in joins], "scenes": scenes, "captions": caps,
           "endcard": {"dur": spec.get("endcard", {}).get("dur", 4.0), "fade_frames": 15},
           "caption_y": spec.get("caption_y", 0.83)}
    json.dump(edl, open(os.path.join(wd, "edl.json"), "w"), indent=1, ensure_ascii=False)
    portable = json.loads(json.dumps(edl))
    for s in portable["scenes"]:
        if "file" in s:
            s["file"] = ".work/img/" + os.path.basename(s["file"])
    json.dump(portable, open(os.path.join(short_dir(slug), "edl.json"), "w"), indent=1, ensure_ascii=False)

    kinds = {"head": 0.0, "image": 0.0, "collage": 0.0}
    for s in scenes:
        d = s["t1"] - s["t0"]
        kinds[s["kind"]] += d
        inner = [j for j in joins[1:-1] if s["t0"] + 0.02 < j < s["t1"] - 0.02]
        flags = ("  SHORT" if d < MIN_SCENE else "") + (f"  joins inside head: {[round(j, 2) for j in inner]}" if s["kind"] == "head" and inner else "")
        print(f"{s['t0']:7.2f}-{s['t1']:7.2f} ({d:5.2f}) {s['kind']:7s} {s.get('key') or s.get('name') or ''} {s['note']}{flags}")
    print(f"program {dur:.2f} s + end card {edl['endcard']['dur']} s = {dur + edl['endcard']['dur']:.1f} s; captions {len(caps)}; "
          + ", ".join(f"{k} {v:.0f} s ({100 * v / dur:.0f}%)" for k, v in kinds.items()))


# ---------------------------------------------------------------- scenes
class HeadFrames:
    """Frames of head_master.mp4 (frame f = program frame f; all-intra, so it can start anywhere)."""

    def __init__(self, slug):
        self.path = os.path.join(work_dir(slug), "head_master.mp4")
        self.proc, self.idx, self.cur = None, -1, None

    def get(self, f):
        if self.proc is None or f < self.idx or f > self.idx + 90:
            if self.proc:
                self.proc.kill()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{f / FPS:.4f}", "-i", self.path, "-f", "rawvideo",
                                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            self.idx = f - 1
        n = W * H * 3
        while self.idx < f:
            b = self.proc.stdout.read(n)
            if len(b) < n:
                break
            self.cur, self.idx = np.frombuffer(b, np.uint8).reshape(H, W, 3), self.idx + 1
        return self.cur


class ImageScene:
    def __init__(self, s):
        self.s = s
        x, y, w, h = s["crop"]
        src = Image.open(s["file"]).convert("RGB").crop((x, y, x + w, y + h))
        k = min(max(w / W, 1.0), 1.25)  # keep some extra detail for the zoom, where the picture has it
        self.base = np.ascontiguousarray(np.asarray(src.resize((round(W * k), round(H * k)), Image.LANCZOS)))
        self.bw, self.bh = self.base.shape[1], self.base.shape[0]

    def frame(self, t):
        s = self.s
        u = min(max((t - s["t0"]) / max(s["t1"] - s["t0"], 1e-6), 0.0), 1.0)
        u = u * u * (3 - 2 * u)  # eased in and out
        z = s["zoom"][0] + (s["zoom"][1] - s["zoom"][0]) * u
        vw, vh = self.bw / z, self.bh / z
        px, py = s.get("pan", [0, 0])
        cx = self.bw / 2 + px * self.bw * (u - 0.5)
        cy = self.bh / 2 + py * self.bh * (u - 0.5)
        left = min(max(cx - vw / 2, 0), self.bw - vw)
        top = min(max(cy - vh / 2, 0), self.bh - vh)
        sx, sy = vw / W, vh / H
        m = np.float32([[sx, 0, left + 0.5 * sx - 0.5], [0, sy, top + 0.5 * sy - 0.5]])
        return cv2.warpAffine(self.base, m, (W, H), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)


class Composer:
    def __init__(self, slug, edl):
        self.edl, self.scenes = edl, edl["scenes"]
        self.dur = edl["joins"][-1]
        self.ec = edl["endcard"]
        self.caps = Captions(edl["captions"], edl.get("caption_y", 0.83))
        self.card = build_endcard(edl)
        self.head = HeadFrames(slug)
        self.cache = {}
        self.nframes = round(self.dur * FPS)

    def scene_obj(self, i):
        if i not in self.cache:
            for k in [k for k in self.cache if k < i - 1]:
                del self.cache[k]
            s = self.scenes[i]
            self.cache[i] = ImageScene(s) if s["kind"] == "image" else \
                Collage(s["collage"], s["t0"], s["t1"], None) if s["kind"] == "collage" else None
        return self.cache[i]

    def draw(self, i, t):
        s = self.scenes[i]
        if s["kind"] == "head":
            return self.head.get(min(max(int(round(t * FPS)), 0), self.nframes - 1)).astype(np.float32)
        return self.scene_obj(i).frame(t).astype(np.float32)

    def window(self, i):
        """Dissolve window (start, end) for the change from scene i-1 to scene i. The head is only ever shown on its
        own side of the boundary, so a dissolve never flashes the head from across an audio join."""
        b, x = self.scenes[i]["t0"], XF / FPS
        a, c = self.scenes[i - 1]["kind"], self.scenes[i]["kind"]
        if a == "head" and c != "head":
            return b - x, b
        if a != "head" and c == "head":
            return b, b + x
        return b - x / 2, b + x / 2

    def frame(self, t, captions=True):
        if t >= self.dur:
            u = (t - self.dur) / self.ec["dur"]
            cardf = endcard_frame(self.card, min(u, 1.0)).astype(np.float32)
            k = (t - self.dur) / (self.ec.get("fade_frames", 15) / FPS)
            if k < 1.0:
                return self.draw(len(self.scenes) - 1, self.dur - 1 / FPS) * (1 - k) + cardf * k
            return cardf
        i = next((k for k, s in enumerate(self.scenes) if s["t0"] <= t < s["t1"]), len(self.scenes) - 1)
        fr = None
        for j in (i, i + 1):  # the change into this scene, or into the next one
            if 0 < j < len(self.scenes):
                w0, w1 = self.window(j)
                if w0 <= t < w1:
                    a = (t - w0) / (w1 - w0)
                    a = a * a * (3 - 2 * a)
                    fr = self.draw(j - 1, t) * (1 - a) + self.draw(j, t) * a
                    break
        if fr is None:
            fr = self.draw(i, t)
        if captions:
            self.caps.draw(fr, t)
        return fr


# ---------------------------------------------------------------- draft / render
def load(slug):
    return json.load(open(os.path.join(work_dir(slug), "edl.json")))


def draft(slug, only=None):
    edl = load(slug)
    comp = Composer(slug, edl)
    shots = []
    for i, s in enumerate(edl["scenes"]):
        if only is not None and i not in only:
            continue
        ts = [s["t0"] + 0.45, (s["t0"] + s["t1"]) / 2, s["t1"] - 0.45]
        if s["kind"] == "collage":
            ts = sorted(set([round(s["t0"] + p["at"] + 0.9, 2) for p in s["collage"]["pieces"]] + [s["t1"] - 0.45]))
        shots += [(i, t) for t in ts]
    font = ImageFont.truetype(FONT_MED, 26)
    tw, th, cols = 360, 640, 6
    for page in range(0, len(shots), 18):
        part = shots[page:page + 18]
        sheet = Image.new("RGB", (cols * tw, ((len(part) + cols - 1) // cols) * (th + 34)), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for k, (i, t) in enumerate(part):
            fr = np.clip(comp.frame(t) + 0.5, 0, 255).astype(np.uint8)
            x, y = (k % cols) * tw, (k // cols) * (th + 34)
            sheet.paste(Image.fromarray(fr).resize((tw, th), Image.LANCZOS), (x, y + 34))
            d.text((x + 6, y + 2), f"#{i} {edl['scenes'][i]['kind']} {t:.2f}s", font=font, fill=(255, 255, 255))
        out = os.path.join(work_dir(slug), f"draft_{page // 18}.jpg")
        sheet.save(out, quality=88)
        print(out)


def render_range(slug, f0, f1, out):
    comp = Composer(slug, load(slug))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        enc.stdin.write(np.clip(comp.frame(f / FPS) + 0.5, 0, 255).astype(np.uint8).tobytes())
        if (f - f0) % 300 == 0:
            print(f"frame {f}/{f1}", flush=True)
    enc.stdin.close()
    enc.wait()


def render(slug, jobs):
    wd = work_dir(slug)
    edl = load(slug)
    total = round((edl["joins"][-1] + edl["endcard"]["dur"]) * FPS)
    bounds = [round(total * k / jobs) for k in range(jobs + 1)]
    chunks = [(bounds[k], bounds[k + 1], os.path.join(wd, f"chunk_{k}.mp4")) for k in range(jobs)]
    procs = [subprocess.Popen([sys.executable, "-I", os.path.abspath(__file__), "range", slug, f"{a}:{b}:{o}"]) for a, b, o in chunks]
    if any(p.wait() for p in procs):
        sys.exit("a render chunk failed")
    lst = os.path.join(wd, "chunks.txt")
    open(lst, "w").write("".join(f"file '{o}'\n" for _, _, o in chunks))
    out = os.path.join(wd, "video_master.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    for _, _, o in chunks:
        os.remove(o)
    print(f"{out}: {total} frames")


if __name__ == "__main__":
    cmd, slug = sys.argv[1], sys.argv[2]
    if cmd == "build":
        build(slug)
    elif cmd == "draft":
        draft(slug, [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None)
    elif cmd == "range":
        a, b, o = sys.argv[3].split(":", 2)
        render_range(slug, int(a), int(b), o)
    elif cmd == "render":
        render(slug, int(sys.argv[3]) if len(sys.argv) > 3 else 4)
