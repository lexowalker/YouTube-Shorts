"""Reading Shorts: one Tao Te Ching chapter, read aloud by David, captioned line by line (docs/reading-style.md).

  python3 -I pipeline/reading.py find <chapter> [--item <archive identifier>]
      Find the chapter on the archive.org channel, download the video to .work/<slug>/source.mp4 and write
      shorts/<slug>/reading.json with the chapter's Cleary text (from the item description) and its section times.
  python3 -I pipeline/reading.py align <slug> [--take N]
      Find every complete read-through (small.en) and use take N (default: the last; when he reads a chapter
      twice the later take is the one he prefers). Time it (medium.en), snap every caption onset to where the voice rises in the audio
      envelope, choose the clip and the face position, and write the captions into reading.json.
  python3 -I pipeline/reading.py render <slug>
      shorts/<slug>/<slug>.mp4: full-frame 9:16 crop of the item's 4K video, title box, captions, house end card.
  python3 -I pipeline/reading.py qa <slug>
      Sync table (dB just before and after every caption onset) and .work/<slug>/qa_sheet.jpg.

reading.json is the spec. align writes it and render only reads it, so hand edits (caption text, a line break,
an onset, the title) survive a re-render. Re-running align overwrites them, so an approved Short is marked
"locked": true and align refuses it.
"""
import argparse, difflib, json, os, re, subprocess, sys, urllib.parse, urllib.request, wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REPO, W, H, FPS, short_dir, work_dir, source_path, source_info

ARCHIVE = "https://archive.org"
SEARCH_Q = "identifier:arredondo-* AND title:(Tao Te Ching)"

# look (docs/reading-style.md); the Chapter 1 Short is the reference
CAP_FONT = ("Inter", "ExtraBold", 68)
CAP_MAX_W = 900           # wider than this wraps onto two lines
SPLIT_WORDS = 8           # a phrase this long (or wider than SPLIT_W) becomes two captions
SPLIT_W = 1400
# title box: rounded, semi-transparent, kicker over title, equal padding above the kicker's caps and below the
# title's baseline. Ink offsets of libass text below its \an8 anchor, as fractions of the font size (measured).
BOX_X, BOX_Y, BOX_W, BOX_R = 100, 110, 880, 22
BOX_PAD, BOX_GAP = 56, 34
BOX_ALPHA = "60"          # ASS alpha (hex): 0x60 of 0xFF transparent, about 62% opaque black
KICK_SIZE, KICK_TOP, KICK_BASE = 40, 0.20, 0.775
TITLE_TOP, TITLE_BASE, TITLE_LINE = 0.267, 0.802, 1.20
TITLE_MAX_W = BOX_W - 2 * BOX_PAD
LEAD = 0.04               # captions start this far ahead of the onset (100 ms fade-in)
PRE_ROLL = 0.75           # clip starts this long before the first caption
SETTLE = 2.3              # clip runs this long past the last voiced frame
CARD = 4.0                # house end card, silent
CUT_XF = 0.2              # 6-frame dissolve over a cut (a misread removed); the audio joins in the pause
XF = 0.5                  # 15-frame dissolve into the card over the held last frame
CONNECTIVES = {"but", "and", "the", "is", "as", "when", "so", "then", "thereby", "yet", "or", "to", "if", "because",
               "therefore", "by", "into", "while", "where", "who", "which", "that", "not", "without"}
NUM = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
       "seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n):
    return NUM[n] if n < 20 else TENS[n // 10] + ("" if n % 10 == 0 else NUM[n % 10])


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def spec_path(slug):
    return os.path.join(short_dir(slug), "reading.json")


def load(slug):
    return json.load(open(spec_path(slug)))


def save(slug, spec):
    os.makedirs(short_dir(slug), exist_ok=True)
    with open(spec_path(slug), "w") as f:
        json.dump(spec, f, indent=1, ensure_ascii=False)
        f.write("\n")


def font_file(family, style):
    return subprocess.run(["fc-match", "-f", "%{file}", f"{family}:style={style}"], capture_output=True, text=True).stdout


def text_w(text, family, style, size):
    from PIL import ImageFont
    return ImageFont.truetype(font_file(family, style), size).getlength(text)


def hms(s):
    p = [float(x) for x in s.split(":")]
    return sum(v * 60 ** i for i, v in enumerate(reversed(p)))


# ---------------------------------------------------------------- find
def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "youtube-shorts-pipeline"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def parse_sections(desc):
    """[{chapter, title, t, lines}] from an item description ("2:17 Chapter 1 | A Way Can Be a Guide" + lines)."""
    heads = list(re.finditer(r"^(\d+(?::\d+){1,2})\s+(.+)$", desc, re.M))
    out = []
    for i, m in enumerate(heads):
        body = desc[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(desc)].split("____")[0]
        c = re.match(r"Chapter\s+(\d+)\s*\|\s*(.+)", m.group(2))
        out.append({"chapter": int(c.group(1)) if c else None, "title": (c.group(2) if c else m.group(2)).strip(),
                    "t": hms(m.group(1)), "lines": [l.strip() for l in body.strip().splitlines() if l.strip()]})
    return out


def index():
    """Every Tao Te Ching item on the channel with its parsed sections, cached in .work/archive_index.json."""
    path = os.path.join(REPO, ".work", "archive_index.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    q = urllib.parse.urlencode({"q": SEARCH_Q, "fl[]": ["identifier", "title"], "rows": 500, "output": "json"}, doseq=True)
    for d in get_json(f"{ARCHIVE}/advancedsearch.php?{q}")["response"]["docs"]:
        if d["identifier"] not in cache:
            md = get_json(f"{ARCHIVE}/metadata/{d['identifier']}")
            mp4 = [f for f in md["files"] if f["name"].lower().endswith(".mp4") and f.get("source") == "original"] or \
                  [f for f in md["files"] if f["name"].lower().endswith(".mp4")]
            cache[d["identifier"]] = {"title": md["metadata"]["title"], "date": md["metadata"].get("date", ""),
                                      "duration": float(mp4[0].get("length", 0)) if mp4 else 0,
                                      "file": mp4[0]["name"] if mp4 else None, "size": int(mp4[0].get("size", 0)) if mp4 else 0,
                                      "sections": parse_sections(md["metadata"].get("description", ""))}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(cache, open(path, "w"), indent=0, ensure_ascii=False)
    return cache


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def cmd_find(a):
    idx = index()
    hits = [(i, it, s) for i, it in idx.items() for s in it["sections"] if s["chapter"] == a.chapter and s["lines"]]
    if a.item:
        hits = [h for h in hits if h[0] == a.item]
    if not hits:
        sys.exit(f"Chapter {a.chapter} not found with its text in any item description" + (f" of {a.item}" if a.item else ""))
    # prefer the chapter-by-chapter series ("Chap. 1", "Chaps. 2 & 3") over introductions and talks
    hits.sort(key=lambda h: (not re.search(r"\bChaps?\.", h[1]["title"]), h[1]["date"]))
    for i, it, s in hits:
        print(f"  {i}\n      {it['title']}  ({it['date'][:10]}, section at {s['t']:.0f}s)")
    ident, it, sec = hits[0]
    print(f"using {ident}" + ("  <- several items read this chapter; pass --item to choose another" if len(hits) > 1 else ""))
    secs = sorted(it["sections"], key=lambda s: s["t"])
    nxt = [s["t"] for s in secs if s["t"] > sec["t"]]
    # the overlay title: a single-chapter video's own quoted title, else the chapter's title from the description
    quoted = re.search(r"[“\"](.+?)[”\"]", it["title"])
    single = sum(1 for s in it["sections"] if s["chapter"]) == 1
    title = quoted.group(1) if quoted and single else sec["title"]
    slug = a.slug or f"tao-ch{a.chapter}-{slugify(title)}"
    spec = {"slug": slug, "chapter": a.chapter, "title": title, "chapter_title": sec["title"],
            "source": {"item": ident, "file": it["file"], "video_title": it["title"],
                       "url": f"{ARCHIVE}/details/{ident}"},
            "section": [sec["t"], nxt[0] if nxt else it["duration"]], "text": sec["lines"]}
    if os.path.exists(spec_path(slug)):
        old = load(slug)
        old.update({k: spec[k] for k in ("source", "section", "text", "chapter_title")})
        spec = old
    save(slug, spec)
    dst = source_path(slug)
    url = f"{ARCHIVE}/download/{ident}/{urllib.parse.quote(it['file'])}"
    if not (os.path.exists(dst) and os.path.getsize(dst) == it["size"]):
        print(f"downloading {it['size'] / 1e6:.0f} MB …", flush=True)
        subprocess.run(["curl", "-sSL", "--retry", "4", "-C", "-", "-o", dst, url], check=True)
    print(f"slug {slug}\ntitle {title}\nsection {spec['section'][0]:.0f}-{spec['section'][1]:.0f}s, {len(sec['lines'])} lines")
    print(source_info(dst))


# ---------------------------------------------------------------- align
def audio(slug, lo, hi):
    wav = os.path.join(work_dir(slug), f"a_{lo:.2f}_{hi:.2f}.wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lo:.3f}", "-t", f"{hi - lo:.3f}", "-i", source_path(slug),
                        "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    wf = wave.open(wav)
    return np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def whisper(slug, name, lo, hi):
    """Word timings for [lo, hi], cached in .work/<slug>/words_<model>_<lo>_<hi>.json."""
    path = os.path.join(work_dir(slug), f"words_{name}_{lo:.2f}_{hi:.2f}.json")
    if os.path.exists(path):
        return json.load(open(path))
    from faster_whisper import WhisperModel
    if name not in MODELS:
        MODELS[name] = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
    segs, _ = MODELS[name].transcribe(audio(slug, lo, hi), language="en", word_timestamps=True, beam_size=5,
                                      condition_on_previous_text=False)
    out = [{"w": w.word.strip(), "s": round(w.start + lo, 3), "e": round(w.end + lo, 3)} for s in segs for w in s.words]
    json.dump(out, open(path, "w"))
    return out


MODELS = {}


def merge_hyphens(words):
    out = []
    for w in words:
        if w["w"].startswith("-") and out:
            out[-1] = dict(out[-1], w=out[-1]["w"] + w["w"], e=w["e"])
        else:
            out.append(dict(w))
    return out


def chars(tokens):
    """Normalised letters of a token list, and for each letter the index of its token."""
    s, owner = [], []
    for i, t in enumerate(tokens):
        n = norm(t)
        s.append(n)
        owner += [i] * len(n)
    return "".join(s), owner


def align_words(body, words):
    """For every body word, the index of the transcript word it was heard in (None if unmatched)."""
    bs, bo = chars(body)
    ts, to = chars([w["w"] for w in words])
    m = difflib.SequenceMatcher(None, bs, ts, autojunk=False)
    hit = [None] * len(body)
    for blk in m.get_matching_blocks():
        for k in range(blk.size):
            bi = bo[blk.a + k]
            if hit[bi] is None:
                hit[bi] = to[blk.b + k]
    return hit, sum(b.size for b in m.get_matching_blocks()) / max(1, len(bs))


def locate(body, words, start=0):
    """First place from word index `start` where the whole chapter is read through:
    (first, last) transcript word index and coverage, or the best partial match."""
    n = len(body)
    head = norm(" ".join(body[:5]))
    best = None
    for i in range(start, len(words)):
        cand = norm(" ".join(w["w"] for w in words[i:i + 7]))
        if difflib.SequenceMatcher(None, head, cand[:len(head) + 4], autojunk=False).ratio() < 0.6:
            continue
        lo = max(start, i - 2)
        hit, cov = align_words(body, words[lo: i + int(n * 1.4) + 4])
        got = [h for h in hit if h is not None]
        if not got:
            continue
        r = (lo + min(got), lo + max(got), cov)
        if best is None or cov > best[2] + 0.05:
            best = r
        if cov >= 0.85:
            return r
    return best


def takes(body, words):
    """Every complete read-through (coverage >= 85%), in order. Line-by-line passes with commentary between the
    lines don't count: the lines are too far apart to cover the chapter within one reading's length."""
    out, start = [], 0
    while True:
        r = locate(body, words, start)
        if not r or r[2] < 0.85:
            return out
        out.append(r)
        start = r[1] + 1


class Env:
    """10 ms RMS envelope (dBFS, 30 ms smoothing) of a region, with a speech threshold from its own levels."""

    def __init__(self, a, lo):
        n = 160
        k = len(a) // n
        db = 20 * np.log10(np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
        self.db = np.convolve(db, np.ones(3) / 3, "same")
        self.lo = lo
        floor, speech = np.percentile(self.db, 10), np.percentile(self.db, 90)
        self.loud = floor + 0.6 * (speech - floor)    # clearly speaking (clip ends, pauses)
        self.voice = floor + 0.4 * (speech - floor)   # a word onset, soft ones ("but") included
        self.quiet = floor + 0.3 * (speech - floor)   # room tone

    def at(self, t):
        i = int(round((t - self.lo) * 100))
        return self.db[min(max(i, 0), len(self.db) - 1)]

    def voiced(self, t):
        """Speaking at t: 70 ms around it above the speaking level, so a breath or room-noise blip doesn't count."""
        return self.mean(t - 0.03, 7) >= self.loud

    def mean(self, t, n):
        return np.mean([self.at(t + k * 0.01) for k in range(n)])

    def sustained(self, t):
        return self.mean(t, 5) >= self.voice

    def gap(self, t):
        """100 ms of room tone from t."""
        return self.mean(t, 10) < self.quiet + 2

    def onset(self, s, e):
        """Where the voice of a word whisper placed at [s, e] really begins. Whisper's start can sit in the silence
        before the word (up to ~1.2 s early) or on the tail of the word before it. Tuned on Chapters 1-3 (26 onsets,
        hand-timed or read off the envelope): mean error 0.07 s, never more than 0.06 s early, worst 0.34 s late."""
        t = s
        if self.mean(t, 5) < self.loud:
            # started in silence: find the word's clearly voiced core (80 ms above the speaking level, which room
            # noise blips never reach), then step back over its soft start (up to 0.15 s)
            while t < max(e, s + 0.3) + 0.6 and self.mean(t, 8) < self.loud:
                t += 0.01
            k = 0
            while k < 15 and self.at(t - 0.01) >= self.voice:
                t -= 0.01
                k += 1
            return round(t - 0.02, 2)
        # started on the previous word's tail (under 0.2 s of voice, then room tone inside the span): move past it
        u = s + 0.04
        while u < min(e, s + 0.9):
            if self.gap(u):
                if sum(self.at(s + k * 0.01) >= self.voice for k in range(int((u - s) * 100))) * 0.01 >= 0.2:
                    break  # the word itself was spoken before this pause
                while u < e and self.at(u) >= self.quiet:
                    u += 0.01  # into the room tone, past the tail's last voice
                while u < e + 0.6 and not (self.mean(u, 8) >= self.voice and self.at(u) >= self.voice):
                    u += 0.01
                return round(u - 0.02, 2)
            u += 0.01
        # started a little late: step back through voiced frames to a real gap within 0.3 s
        k = 0
        while k < 30 and self.at(t - 0.01) >= self.voice:
            t -= 0.01
            k += 1
        if k < 30 and all(self.at(t - (j + 1) * 0.01) < self.quiet for j in range(8)):
            return round(t, 2)
        return round(s, 2)

    def check(self, t):
        """'early' if a caption at t opens on room tone, 'late' if the voice rose after a pause well before t."""
        if self.gap(t + 0.02):
            return "early"
        u = t
        while u > t - 1.0 and not self.gap(u - 0.1):
            u -= 0.01
        if u > t - 1.0 and t - u > 0.3 and all(self.at(u + k * 0.01) >= self.voice for k in range(int((t - u) * 100))):
            return "late"
        return "ok"

    def pause(self, a, b):
        """Seconds below the speech threshold in [a, b]."""
        return sum(0.01 for i in range(int(a * 100), int(b * 100)) if not self.voiced(i / 100))

    def last_voiced(self, a, b):
        t = b
        while t > a and not self.voiced(t):
            t -= 0.01
        return t

    def next_voiced(self, a, b):
        t = a
        while t < b and not self.voiced(t):
            t += 0.01
        return t


def phrases_of(lines):
    """Description lines -> phrases, splitting a line at an inner , ; : when both sides have two or more words."""
    out = []
    for line in lines:
        parts = re.split(r"(?<=[,;:])\s+", line)
        cur = []
        for i, p in enumerate(parts):
            cur.append(p)
            if len(" ".join(cur).split()) >= 2 and len(" ".join(parts[i + 1:]).split()) >= 2:
                out.append(" ".join(cur))
                cur = []
        if cur:
            out.append(" ".join(cur))
    return out


def wrap(text):
    """One line if it fits CAP_MAX_W, else the most balanced two-line break."""
    if text_w(text, *CAP_FONT) <= CAP_MAX_W:
        return text
    ws = text.split()
    best = min(range(1, len(ws)), key=lambda k: max(text_w(" ".join(ws[:k]), *CAP_FONT), text_w(" ".join(ws[k:]), *CAP_FONT)))
    return " ".join(ws[:best]) + "\\N" + " ".join(ws[best:])


def sentence_case(title):
    ws = title.split()
    # "the Way" (the Tao) keeps its capital; "A way can be a guide" does not
    keep = lambda i, w: w in ("Tao", "I") or (w == "Way" and ws[i - 1].lower() == "the")
    return " ".join([ws[0]] + [w if keep(i, w) else w.lower() for i, w in enumerate(ws) if i])


def cmd_align(a):
    slug = a.slug
    spec = load(slug)
    if spec.get("locked") and not a.force:
        sys.exit(f"{slug} is locked (an approved Short); pass --force to re-align it and lose its timings")
    lo, hi = spec["section"]
    # 1. find every read-through in the section (small.en) and take the one asked for (default: the last; when he
    #    reads a chapter twice the later take is the one he prefers)
    phrases = phrases_of(spec["text"])
    body = " ".join(phrases).split()
    words, t = [], max(0.0, lo - 5)
    while t < hi:
        t1 = min(hi + 5, t + 180)
        words += merge_hyphens(whisper(slug, "small.en", t, t1))
        print(f"  heard {t:.0f}-{t1:.0f}s", flush=True)
        t = t1
    found = takes(body, words)
    for k, r in enumerate(found, 1):
        print(f"  take {k}: {words[r[0]]['s']:.1f}-{words[r[1]]['e']:.1f}s (coverage {r[2]:.0%})")
    if not found:
        r = locate(body, words)
        if not r:
            sys.exit("Could not find the chapter read through in its section. Read .work/<slug> transcripts and ask the user.")
        print(f"  WARNING: no complete read-through; best partial {words[r[0]]['s']:.1f}s at {r[2]:.0%}. He may read it in "
              "pieces or change words. Check before rendering.")
        found = [r]
    take = min(a.take or len(found), len(found))
    if a.take and take != a.take:
        print(f"  only {len(found)} take(s); using take {take}")
    r = found[take - 1]
    r0, r1 = words[r[0]]["s"] - 12, words[r[1]]["e"] + 6
    print(f"using take {take}: {words[r[0]]['s']:.1f}-{words[r[1]]['e']:.1f}s")
    spec["take"] = take

    # 2. time it (medium.en) and snap onsets to the envelope
    mw = merge_hyphens(whisper(slug, "medium.en", r0, r1))
    env = Env(audio(slug, r0, r1), r0)
    hit, cov = align_words(body, mw)
    print(f"medium.en coverage {cov:.0%}")

    def word_time(i, fwd=True):
        rng = range(i, len(body)) if fwd else range(i, -1, -1)
        for j in rng:
            if hit[j] is not None:
                return mw[hit[j]]
        return None

    caps, k = [], 0
    for p in phrases:
        n = len(p.split())
        idx = list(range(k, k + n))
        k += n
        heard = [mw[hit[i]]["w"] for i in idx if hit[i] is not None]
        ratio = difflib.SequenceMatcher(None, norm(p), norm(" ".join(dict.fromkeys(heard))), autojunk=False).ratio()
        groups = [(p.split(), idx)]
        if n >= SPLIT_WORDS or text_w(p, *CAP_FONT) > SPLIT_W:
            # two captions, split where he pauses (or before a connective), keeping the halves balanced
            def score(j):
                a_, b_ = word_time(idx[j - 1], False), word_time(idx[j])
                gap = env.pause(a_["e"] - 0.1, b_["s"] + 0.15) if a_ and b_ else 0
                conn = 0.15 if p.split()[j].lower().strip(",;:.") in CONNECTIVES else 0
                return gap + conn - 0.08 * abs(j - n / 2)
            j = max(range(2, n - 1), key=score)
            groups = [(p.split()[:j], idx[:j]), (p.split()[j:], idx[j:])]
        for ws, ix in groups:
            w0, w1 = word_time(ix[0]), word_time(ix[-1], False)
            caps.append({"t": env.onset(w0["s"], w0["e"]), "text": wrap(" ".join(ws)), "heard": " ".join(dict.fromkeys(heard)),
                         "match": round(ratio, 2), "_end": w1["e"] if w1 else None})

    # 3. the spoken header: "Chapter N" and, if he reads it, the chapter's title
    first = caps[0]["t"]
    pre = [w for w in mw if first - 12 <= w["s"] < first - 0.05]
    ch = [i for i, w in enumerate(pre) if norm(w["w"]) == "chapter"]
    head = []
    if ch:
        c = pre[ch[-1]]
        head.append({"t": env.onset(c["s"], c["e"]), "text": f"Chapter {num_words(spec['chapter']).capitalize()}"})
        rest = [w for w in pre[ch[-1] + 1:] if norm(w["w"]) not in (str(spec["chapter"]), num_words(spec["chapter"]))]
        if len(rest) >= 2 and difflib.SequenceMatcher(None, norm(spec["chapter_title"]),
                                                      norm(" ".join(w["w"] for w in rest))).ratio() >= 0.6:
            head.append({"t": env.onset(rest[0]["s"], rest[0]["e"]), "text": sentence_case(spec["chapter_title"]) + "…"})
    caps = head + caps

    # 4. the clip: a short pre-roll with no earlier speech, and a settle after the last word
    start = caps[0]["t"] - PRE_ROLL
    prev_voice = env.last_voiced(start - 0.01, caps[0]["t"] - 0.2)
    if prev_voice > start:
        start = prev_voice + 0.25
    last_end = caps[-1]["_end"] or caps[-1]["t"] + 2
    voice_end = env.last_voiced(caps[-1]["t"], last_end + 0.3)
    nxt = env.next_voiced(voice_end + 0.4, r1)
    end = min(voice_end + SETTLE, nxt - 0.2)  # stop before he speaks again (the 0.4 s audio fade ends on room tone)
    for c in caps:
        c.pop("_end", None)

    # 5. face crop
    from facetrack import track
    si = source_info(source_path(slug))
    sw, sh = si["w"], si["h"]
    cx = [c for _, c in track(source_path(slug), start, end, sw, sh) if c is not None]
    face_x = round(float(np.median(cx)) / sw, 4) if cx else 0.55

    spec.update({"start": round(start, 2), "dur": round(end - start, 2), "face_x": face_x, "captions": caps})
    spec.pop("crop_x", None)
    save(slug, spec)
    print(f"clip {start:.2f}+{end - start:.2f}s, face_x {face_x}  ->  {spec_path(slug)}\n")
    for c in caps:
        flag = "  <- CHECK" if c.get("match", 1) < 0.8 else ""
        print(f"{c['t']:8.2f}  {c['text'].replace(chr(92) + 'N', ' / '):42s} heard: {c.get('heard', '')}{flag}")


# ---------------------------------------------------------------- render
ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Box,Inter,20,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Kicker,Inter SemiBold,40,&H00A8D8F0,&H00000000,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,0,2,8,60,60,130,1
Style: Title,Caladea,86,&H00FFFFFF,&H00000000,&H00000000,&H78000000,1,0,0,0,100,100,0,0,1,0,3,8,60,60,190,1
Style: Cap,Inter ExtraBold,68,&H00FFFFFF,&H00000000,&H00101010,&H96000000,1,0,0,0,100,100,0,0,1,6,3,2,70,70,265,1
Style: CapGold,Inter ExtraBold,68,&H0060D8FF,&H00000000,&H00101010,&H96000000,1,0,0,0,100,100,0,0,1,6,3,2,70,70,265,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def rounded_rect(w, h, r):
    """ASS vector drawing of a w x h rectangle with corner radius r."""
    k = r * 0.45  # bezier handle for a near-circular corner
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} b {w} {h - k} {w - k} {h} {w - r} {h} "
            f"l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} l 0 {r} b 0 {k} {k} 0 {r} 0")


def segments(spec):
    """The source ranges that make up the Short: the clip minus any "cuts" ([[a, b], …] source seconds removed,
    e.g. a misread line he then corrects)."""
    segs, t = [], spec["start"]
    for a, b in sorted(spec.get("cuts", [])):
        segs.append((t, a))
        t = b
    return segs + [(t, spec["start"] + spec["dur"])]


def prog_time(spec, t):
    """Source seconds -> seconds into the Short."""
    off = 0.0
    for a, b in segments(spec):
        if t < b:
            return off + max(0.0, t - a)
        off += b - a
    return off


def prog_dur(spec):
    return sum(b - a for a, b in segments(spec))


def write_ass(spec, path):
    end = prog_dur(spec) - 0.1  # titles and captions are gone before the held frame dissolves
    title = spec["title"]
    fade = "\\fad(400,300)"
    # a long title shrinks to fit the box (down to 64 px), then takes two lines and the box grows
    size, lines = 86, 1
    while text_w(title, "Caladea", "Bold", size) > TITLE_MAX_W and size > 64:
        size -= 2
    if text_w(title, "Caladea", "Bold", size) > TITLE_MAX_W:
        ws = title.split()
        k = min(range(1, len(ws)), key=lambda k: max(text_w(" ".join(ws[:k]), "Caladea", "Bold", size),
                                                    text_w(" ".join(ws[k:]), "Caladea", "Bold", size)))
        title, lines = " ".join(ws[:k]) + "\\N" + " ".join(ws[k:]), 2
    kick_y = BOX_Y + BOX_PAD - KICK_TOP * KICK_SIZE
    title_y = kick_y + KICK_BASE * KICK_SIZE + BOX_GAP - TITLE_TOP * size
    base = title_y + TITLE_BASE * size + (lines - 1) * TITLE_LINE * size
    box_h = round(base + 0.07 * size + BOX_PAD - BOX_Y)
    cx = BOX_X + BOX_W // 2
    ev = [f"Dialogue: 0,{ts(0)},{ts(end)},Box,,0,0,0,,{{{fade}\\an7\\pos({BOX_X},{BOX_Y})\\1a&H{BOX_ALPHA}&\\blur1\\p1}}"
          f"{rounded_rect(BOX_W, box_h, BOX_R)}{{\\p0}}",
          f"Dialogue: 1,{ts(0)},{ts(end)},Kicker,,0,0,0,,{{{fade}\\an8\\pos({cx},{kick_y:.0f})}}TAO TE CHING  ·  CHAPTER {spec['chapter']}",
          f"Dialogue: 1,{ts(0)},{ts(end)},Title,,0,0,0,,{{{fade}\\an8\\pos({cx},{title_y:.0f})\\fs{size}}}{title}"]
    caps = spec["captions"]
    for i, c in enumerate(caps):
        t0 = prog_time(spec, c["t"]) - LEAD
        t1 = prog_time(spec, caps[i + 1]["t"]) - LEAD if i + 1 < len(caps) else end
        style = "CapGold" if c.get("gold", i in (0, len(caps) - 1)) else "Cap"
        ev.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\fad(100,{300 if i + 1 == len(caps) else 0})}}{c['text']}")
    open(path, "w").write(ASS_HEAD + "\n".join(ev) + "\n")


def render_card(path):
    from render import build_endcard, endcard_frame
    card = build_endcard({"endcard": {"dur": CARD}})
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", path],
                           stdin=subprocess.PIPE)
    n = round(CARD * FPS)
    for f in range(n):
        enc.stdin.write(np.ascontiguousarray(endcard_frame(card, f / n)).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()


def hires(slug, spec):
    """The clip's window from the item's highest-resolution video (usually a 4K WebM), fetched over HTTP without the
    whole file. Returns (path, source time of its t=0) or None if the item has nothing sharper than source.mp4.
    Stream copy starts on the keyframe before the request, so t=0 is found by matching its audio to source.mp4."""
    lo, hi = max(0.0, spec["start"] - 5), spec["start"] + spec["dur"] + 5
    wd = work_dir(slug)
    meta = os.path.join(wd, "hires.json")
    if os.path.exists(meta):
        m = json.load(open(meta))
        if m["lo"] == lo and m["hi"] == hi and os.path.exists(m["path"]):
            return m["path"], m["t0"]
    ident = spec["source"]["item"]
    files = get_json(f"{ARCHIVE}/metadata/{ident}")["files"]
    vids = [f for f in files if f["name"].lower().endswith((".webm", ".mkv", ".mp4")) and f.get("source") == "original"]
    best = max(vids, key=lambda f: (int(f.get("height", 0) or 0), int(f.get("size", 0))))
    if best["name"] == spec["source"]["file"]:
        return None
    path = os.path.join(wd, "hires.mkv")
    url = f"{ARCHIVE}/download/{ident}/{urllib.parse.quote(best['name'])}"
    print(f"fetching {hi - lo:.0f}s of {best['name']} …", flush=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lo:.3f}", "-i", url, "-t", f"{hi - lo:.3f}", "-c", "copy", path], check=True)
    wav = os.path.join(wd, "hires16k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-t", "12", "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
    wf = wave.open(wav)
    hi_a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32)[16000 * 6:16000 * 10]
    ref = audio(slug, max(0.0, lo - 4), lo + 14) * 32768
    scores = [(float(np.dot(ref[o:o + len(hi_a)], hi_a) / (np.linalg.norm(ref[o:o + len(hi_a)]) * np.linalg.norm(hi_a) + 1e-9)), o)
              for o in range(0, len(ref) - len(hi_a), 4)]
    corr, o = max(scores)
    assert corr > 0.9, f"could not match the high-resolution clip to source.mp4 (corr {corr:.2f})"
    t0 = round(max(0.0, lo - 4) + o / 16000 - 6, 4)
    json.dump({"lo": lo, "hi": hi, "path": path, "t0": t0, "file": best["name"]}, open(meta, "w"))
    return path, t0


def cmd_render(a):
    slug = a.slug
    spec, wd = load(slug), work_dir(slug)
    for fam in ("Inter", "Caladea"):
        assert fam in subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout, f"font {fam} missing"
    write_ass(spec, os.path.join(wd, "captions.ass"))
    card = os.path.join(wd, "endcard.mp4")
    if not os.path.exists(card):
        render_card(card)
    start, dur = spec["start"], prog_dur(spec)
    total = dur + CARD
    out = os.path.join(short_dir(slug), f"{slug}.mp4")
    hr = hires(slug, spec)
    src, ss = (hr[0], start - hr[1]) if hr else (source_path(slug), start)
    if not hr:
        print("  WARNING: no higher-resolution file on the item; the full-height crop of source.mp4 will look soft")
    si = source_info(src)
    cw = round(si["h"] * 9 / 16 / 2) * 2  # full-height 9:16 crop, centred on his face
    x = int(min(max(spec.get("face_x", 0.55) * si["w"] - cw / 2, 0), si["w"] - cw))
    # join the segments: audio butts together in the pauses with 12 ms fades; video carries each segment
    # CUT_XF past its end and dissolves into the next, so picture and sound stay in sync
    segs = [(a - start, b - start) for a, b in segments(spec)]
    n = len(segs)
    if n == 1:
        join = "[0:v]null[vj];[0:a]anull[aj];"
    else:
        join = f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n)) + f";[0:a]asplit={n}" + "".join(f"[a{i}]" for i in range(n)) + ";"
        for i, (a, b) in enumerate(segs):
            vb = b + (CUT_XF if i < n - 1 else 0)
            join += f"[v{i}]trim=start={a:.3f}:end={vb:.3f},setpts=PTS-STARTPTS,fps={FPS}[w{i}];"
            fades = (",afade=t=in:d=0.012" if i else "") + (f",afade=t=out:st={b - a - 0.012:.3f}:d=0.012" if i < n - 1 else "")
            join += f"[a{i}]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS{fades}[b{i}];"
        prev, off = "w0", 0.0
        for i in range(1, n):
            off += segs[i - 1][1] - segs[i - 1][0]
            join += f"[{prev}][w{i}]xfade=transition=fade:duration={CUT_XF}:offset={off:.3f}[x{i}];"
            prev = f"x{i}"
        join += f"[{prev}]null[vj];" + "".join(f"[b{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[aj];"
    fc = (join + f"[vj]crop={cw}:{si['h']}:{x}:0,scale={W}:{H}:flags=lanczos,setsar=1,eq=contrast=1.04:saturation=1.05,"
          f"ass='{os.path.join(wd, 'captions.ass')}',fade=t=in:st=0:d=0.4,fps={FPS},format=yuv420p,"
          f"tpad=stop_mode=clone:stop_duration={XF},settb=AVTB[main];"
          f"[1:v]fps={FPS},format=yuv420p,settb=AVTB[card];"
          f"[main][card]xfade=transition=fade:duration={XF}:offset={dur}[v];"
          f"[aj]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.3,afade=t=out:st={dur - 0.4}:d=0.4,"
          f"apad=whole_dur={total}[aud]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ss:.3f}", "-t", str(spec["dur"]), "-i", src, "-i", card,
                    "-filter_complex", fc, "-map", "[v]", "-map", "[aud]", "-r", str(FPS), "-c:v", "libx264", "-preset", "slow",
                    "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
                    "-t", f"{total:.3f}", out], check=True)
    print(f"{out}  ({total:.1f}s)")
    if total > 180:
        print("  WARNING: over 3 minutes, YouTube will not treat it as a Short")


# ---------------------------------------------------------------- qa
def cmd_qa(a):
    slug = a.slug
    spec, wd = load(slug), work_dir(slug)
    out = os.path.join(short_dir(slug), f"{slug}.mp4")
    lo, hi = spec["start"], spec["start"] + spec["dur"]
    env = Env(audio(slug, lo - 1, hi + 1), lo - 1)
    print("each caption should open on his voice: 'early' = it opens on room tone, 'late' = he started after a pause well before")
    flagged = 0
    for c in spec["captions"]:
        v = env.check(c["t"])
        flagged += v != "ok"
        print(f"{c['t']:8.2f}  {v:5s}  {c['text'].replace(chr(92) + 'N', ' / ')}")
    print(f"{flagged} flagged" if flagged else "all captions on the voice")
    caps = spec["captions"]
    two = next((c for c in caps if "\\N" in c["text"]), caps[len(caps) // 2])
    pt = lambda c: prog_time(spec, c["t"]) + 0.3
    times = [pt(caps[0]), pt(two), pt(caps[len(caps) // 2]), pt(caps[-1]), prog_dur(spec) + XF * 0.5, prog_dur(spec) + CARD - 0.3]
    tiles = []
    for i, t in enumerate(times):
        p = os.path.join(wd, f"qa{i}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", out, "-frames:v", "1", "-vf", "scale=360:640", p], check=True)
        tiles.append(p)
    sheet = os.path.join(wd, "qa_sheet.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum([["-i", p] for p in tiles], []) +
                   ["-filter_complex", "[0][1][2]hstack=3[t];[3][4][5]hstack=3[b];[t][b]vstack", sheet], check=True)
    peak = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", peak)
    print(f"sheet {sheet}\ntrue peak {m[-1] if m else '?'} dBFS")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find")
    f.add_argument("chapter", type=int)
    f.add_argument("--item")
    f.add_argument("--slug")
    al = sub.add_parser("align")
    al.add_argument("slug")
    al.add_argument("--force", action="store_true", help="re-align a locked (approved) Short")
    al.add_argument("--take", type=int, help="which complete read-through to use (default: the last, his preferred take)")
    for name in ("render", "qa"):
        sub.add_parser(name).add_argument("slug")
    a = ap.parse_args()
    {"find": cmd_find, "align": cmd_align, "render": cmd_render, "qa": cmd_qa}[a.cmd](a)


if __name__ == "__main__":
    main()
