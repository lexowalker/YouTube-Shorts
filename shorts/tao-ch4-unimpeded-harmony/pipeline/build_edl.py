"""Build the EDL for cut A (Unimpeded harmony)."""
import sys, json, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from words import load_words, Env, refine_onsets, to_program

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WK = os.path.join(S, "work")
RAW = os.path.join(S, "img", "raw")

SEGMENTS = [
    {"src_start": 313.84, "src_end": 323.30},   # hook: no hard lines in nature
    {"src_start": 65.55, "src_end": 67.80},     # Cleary: "The way is unimpeded harmony."
    {"src_start": 71.60, "src_end": 127.55},    # everything working together ... you see unimpeded harmony
    {"src_start": 428.10, "src_end": 437.30},   # it blunts your edges ... very, very simple
]

# Caption phrases: "|" splits the two lines, "*" marks the one highlighted word.
PHRASES = """
There's no hard | *lines in nature
because nothing | is *separate
Everything's | *interdependent
Everything depends | on everything else
The way is | unimpeded *harmony
When you look | out at *nature
what you see is
everything | working *together
The *birds sit | in the trees
The *trees produce | seeds or nuts
for the | *squirrels
The squirrels | produce fertilizers
for the *grass
The grass produces | a substrate
for the *worms
The worms | produce *food
for the birds
And the worms | also *aerate
the *ground
so that the | *water can get in
And so on | and so forth
*forever and ever
on this planet
this *marvelous | planet
Everything works | *together
in an incredible | *harmony
Now, from a | *human point of view
we may think | oh, well
there's a *storm
That's not | harmonious
There's an | *earthquake
That's not | harmonious
But in fact | it *is
It just doesn't | seem that way
from our limited | little *self-interest
But if you look | at the *planet
and the evolution | of its *consciousness
you see something | very, very *different
You see | unimpeded *harmony
It *blunts | your edges
and it resolves | your complications
It's not that | complicated
in one way | of looking at it
It's very, very | *simple in a way
"""

def norm(s):
    return re.sub(r"[^a-z']", "", s.lower().replace("’", "'"))

def frac_crop(W, H, x0f, y0f, hf):
    """9:16 crop given top-left as fractions and height as a fraction of image height."""
    h = round(H * hf); w = round(h * 9 / 16)
    return [round(W * x0f), round(H * y0f), w, h]

IM = {  # accession: (W, H)
    "1967.145": (4848, 6576), "1982.53": (2255, 4421), "1979.70": (2670, 6462), "1975.71.1": (3337, 7777),
    "1953.126": (28075, 4336), "1970.76": (3997, 6513), "1966.366": (3038, 6587), "2015.482.1": (17166, 7462),
    "1997.88": (9684, 9034), "1987.186": (3202, 7891),
}

def img(acc, x0f, y0f, hf, **kw):
    W, H = IM[acc]
    d = {"kind": "image", "acc": acc, "file": os.path.join(RAW, acc + "_full.jpg"), "crop": frac_crop(W, H, x0f, y0f, hf)}
    d.update(kw)
    x, y, w, h = d["crop"]
    assert x >= 0 and y >= 0 and x + w + max(0, d.get("pan", 0)) <= W and y + h <= H, (acc, d["crop"])
    return d

def main():
    W = load_words([(f"{WK}/words_A.json", 0, 65), (f"{WK}/words_fix.json", 55, 72), (f"{WK}/words_A.json", 72, 1e9)])
    # whisper heard the final "harmony" at 106.6 as "whole"; the clean re-run has it right
    fix = {round(w["s"], 2): w for w in json.load(open(f"{WK}/words_fix.json"))}
    for w in W:
        if w["w"].startswith("whole") and 106 < w["s"] < 107:
            w.update(w=fix[106.58]["w"].capitalize() + ".", s=fix[106.58]["s"], e=fix[106.58]["e"])
    W = refine_onsets(W, Env(f"{WK}/audio16k.wav"), quiet=-46, loud=-42)
    P = to_program(W, SEGMENTS)
    # onsets checked by ear-proxy (envelope) and a second transcription pass of the finished audio
    ONSET_FIX = {("Everything's", 5.90): 5.58, ("interdependent.", 6.67): 6.58, ("The", 9.49): 9.84, ("now", 47.23): 47.83}
    for w in P:
        for (tok, t), new in ONSET_FIX.items():
            if norm(w["w"]) == norm(tok) and abs(w["ps"] - t) < 0.05:
                w["ps"] = new

    caps, i = [], 0
    for line in [l for l in PHRASES.strip().splitlines() if l.strip()]:
        parts = [p.split() for p in line.split("|")]
        toks = [t for p in parts for t in p]
        words = []
        for t in toks:
            key = t.startswith("*"); t = t.lstrip("*")
            w = P[i]
            assert norm(w["w"]) == norm(t), f"caption mismatch at {w['ps']:.2f}: spoken '{w['w']}' vs caption '{t}'"
            words.append({"w": t, "s": w["ps"], "e": w["pe"], "key": key})
            i += 1
        caps.append({"words": words, "lines": [len(parts[0])]})
    assert i == len(P), f"{len(P) - i} spoken words not captioned: {[w['w'] for w in P[i:]]}"
    # each phrase stays until the next begins, but clears during long pauses
    for k, c in enumerate(caps):
        end = c["words"][-1]["e"]
        nxt = caps[k + 1]["words"][0]["s"] if k + 1 < len(caps) else end + 0.6
        c["t_off"] = round(min(nxt, end + 0.5), 3)

    prog_dur = sum(s["src_end"] - s["src_start"] for s in SEGMENTS)
    on = lambda text, after=0: next(c["words"][0]["s"] for c in caps if c["words"][0]["s"] >= after and
                                     " ".join(w["w"] for w in c["words"]).startswith(text))
    word_on = lambda tok, after=0: next(w["ps"] for w in P if w["ps"] >= after and norm(w["w"]) == norm(tok))

    cuts = [
        (0.0, {"kind": "head"}),
        # on the join itself, so the dissolve hides the jump and completes as "The way..." begins
        (SEGMENTS[0]["src_end"] - SEGMENTS[0]["src_start"], img("1967.145", 0.40, 0.56, 0.42)),  # rushing stream
        (on("When you look"), {"kind": "head"}),
        (on("The birds"), img("1982.53", 0.05, 0.12, 0.725)),                          # magpie on a willow branch
        (on("The trees"), img("1979.70", 0.12, 0.06, 0.551)),                          # chestnuts and squirrel
        (on("The squirrels"), img("1979.70", 0.0, 0.44, 0.551)),                       # squirrel on the ground
        (on("The grass produces"), {"kind": "head"}),
        (on("And the worms"), img("1975.71.1", 0.15, 0.53, 0.457)),                    # rain into rocks and earth
        (on("And so on"), img("1953.126", 0.185, 0.05, 0.90, pan=900, zoom=[1.04, 1.0])),  # handscroll, endless
        (on("Now, from a"), {"kind": "head"}),
        (word_on("there's", 50.0), img("1970.76", 0.25, 0.20, 0.628)),                  # rainstorm
        (word_on("There's", 52.0), img("1966.366", 0.05, 0.03, 0.513)),                 # upheaved crags
        (on("But in fact"), {"kind": "head"}),
        (word_on("look", 60.0), img("2015.482.1", 0.508, 0.17, 0.63)),                  # misty mountains and water
        (on("You see"), img("1997.88", 0.45, 0.08, 0.85)),                              # scholar, pine, stream
        (on("It blunts"), {"kind": "head"}),
        (on("It's very, very"), img("1987.186", 0.0, 0.15, 0.72)),                      # bamboo in moonlight
    ]
    shots = []
    for k, (t0, s) in enumerate(cuts):
        t1 = cuts[k + 1][0] if k + 1 < len(cuts) else prog_dur
        shots.append(dict(s, t0=round(t0, 3), t1=round(t1, 3)))
    for s in shots:
        if s["kind"] == "image":
            dur = s["t1"] - s["t0"]
            s.setdefault("zoom", [1.12, 1.0] if dur >= 8 else [1.08, 1.0])
    # the final image keeps settling under the end-card dissolve
    shots[-1]["t1_render"] = prog_dur + 4.0

    edl = {"segments": SEGMENTS, "shots": shots, "captions": caps,
           "title": {"text": "Nothing in nature is separate", "t0": 0.0, "t1": 3.6, "size": 52},
           "endcard": {"dur": 4.0, "fade_frames": 15}, "crop_track": f"{WK}/crop_track.json"}
    json.dump(edl, open(f"{WK}/edl.json", "w"), indent=1)
    for s in shots:
        print(f"{s['t0']:6.2f}-{s['t1']:6.2f} ({s['t1'] - s['t0']:5.2f}) {s['kind']:5s} {s.get('acc', '')} {s.get('zoom', '')}")
    print("program", round(prog_dur, 2), "captions", len(caps))

main()
