#!/usr/bin/env python3
"""Build Short 4 'You Can Be Bigoted on the Right, Left or Center'.
Usage: build.py SOURCE.mp4 WORDS.json OUTDIR
WORDS.json: [[start, end, word], ...] word timestamps (source timeline)."""
import json, re, subprocess, sys, os

SRC, WORDS, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
words = json.load(open(WORDS))

# (source in, source out, caption text) -- bracketed audio words omitted from captions
SEGS = [
 (1105.8, 1110.0, "So, you can be bigoted on the right, you can be bigoted on the left, and you can be bigoted in the center."),
 (1038.6, 1053.5, "When it is forgotten that conventional conceptions are conventional conceptions, and they are taken for objective facts that everyone knows and no one questions, then narrow-minded bigotry and blind prejudice can develop unopposed."),
 (1092.4, 1105.3, "That arrogance, that prejudice, that bias, and bigotry means having a closed mind it also means whatever you think, exactly what you think it means, but it also means just having a closed mind."),
 (1110.5, 1132.7, "because what it means is you're not open to new ways of thinking or conceptions. And so when people get locked into one fixed way of conceptualizing things, then the person, the nation, the world starts to degenerate, because we're locked into one way of conceiving things."),
 (1188.9, 1219.3, "So, in my grandfather's time, smoking was thought to be good for you. Before my grandfather's time, if you didn't spank your child, something was wrong with you. Now these two attitudes have changed, and attitudes that came thereafter also have changed. And the attitudes we have now will also change. So if you get locked into one way of looking at things, and you don't realize that your attitudes, your whole way of looking at the world, is totally"),
 (1220.8, 1223.5, "conditioned and determined by your environment,"),
 (1225.7, 1246.3, "what you see on Instagram, what you see on TV, what you see on TikTok and X, and what books you've read and what movies you've seen. See, we look at a very tiny, tiny, tiny little slice of the world, and we call it the world, and that's a mistake. And so anybody who can get out of that and look more holistically"),
 (1252.9, 1256.3, "can do better because they can see more clearly."),
]
END_CARD = 4.0
norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower().replace("-", ""))

# ---- align caption tokens to whisper words, map to output timeline ----
cap = []  # (out_start, out_end, token)
t0 = 0.0
for a, b, text in SEGS:
    ws = [w for w in words if w[1] > a - 0.3 and w[0] < b + 0.3]
    toks = text.split()
    j = 0; timed = []
    for tok in toks:
        n = norm(tok); hit = None
        for k in range(j, min(j + 6, len(ws))):
            wn = norm(ws[k][2])
            if wn == n or (n and wn and (wn.startswith(n) or n.startswith(wn))):
                hit = k; break
        if hit is not None:
            timed.append([ws[hit][0], ws[hit][1], tok]); j = hit + 1
        else:
            timed.append([None, None, tok])
    # interpolate missing
    for i, t in enumerate(timed):
        if t[0] is None:
            prev = next((timed[p][1] for p in range(i - 1, -1, -1) if timed[p][1] is not None), a)
            nxt = next((timed[p][0] for p in range(i + 1, len(timed)) if timed[p][0] is not None), b)
            t[0], t[1] = prev, max(prev + 0.05, min(nxt, prev + 0.3))
    for s, e, tok in timed:
        s = min(max(s, a), b); e = min(max(e, s + 0.05), b)
        cap.append((t0 + s - a, t0 + e - a, tok))
    t0 += b - a
SPEECH = t0
TOTAL = SPEECH + END_CARD

# ---- group into caption chunks (<=3 words, break on punctuation / gaps) ----
chunks, cur = [], []
for c in cap:
    if cur and (len(cur) >= 3 or c[0] - cur[-1][1] > 0.6 or re.search(r"[.,?!]$", cur[-1][2])):
        chunks.append(cur); cur = []
    cur.append(c)
if cur: chunks.append(cur)

def ts(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"
def esc(s): return s.replace("{", "(").replace("}", ")")

ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
 "[V4+ Styles]",
 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
 "Style: Cap,Inter,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1",
 "Style: Title,Inter,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,5,70,70,0,1",
 "Style: Src,Inter,40,&H00D8D8D8,&H00FFFFFF,&H00000000,&H00000000,0,-1,0,0,100,100,0,0,1,3,0,5,70,70,0,1",
 "Style: End,Inter,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,5,80,80,0,1",
 "Style: EndSm,Inter,48,&H00E0E0E0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,5,80,80,0,1",
 "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
HL = r"{\c&H3CD7FF&}"  # warm yellow highlight (BGR)
CAP_POS = r"{\pos(540,1520)}"
for ch in chunks:
    for i, w in enumerate(ch):
        s = w[0]; e = ch[i + 1][0] if i + 1 < len(ch) else ch[-1][1] + 0.15
        nxt_chunk_start = chunks[chunks.index(ch) + 1][0][0] if ch is not chunks[-1] else SPEECH
        if i == len(ch) - 1: e = min(max(e, s + 0.1), nxt_chunk_start)
        txt = " ".join((HL + esc(x[2]) + r"{\c&HFFFFFF&}") if k == i else esc(x[2]) for k, x in enumerate(ch))
        ass.append(f"Dialogue: 1,{ts(s)},{ts(e)},Cap,,0,0,0,,{CAP_POS}{txt}")
title = r"You can be bigoted on the\N{\c&H3CD7FF&}right, left{\c&HFFFFFF&} or {\c&H3CD7FF&}center"
ass.append(f"Dialogue: 0,{ts(0)},{ts(SPEECH)},Title,,0,0,0,,{{\\pos(540,215)}}{title}")
# label over the Cleary passage (segment 2)
s2a = SEGS[0][1] - SEGS[0][0]; s2b = s2a + SEGS[1][1] - SEGS[1][0]
ass.append(f"Dialogue: 0,{ts(s2a)},{ts(s2b)},Src,,0,0,0,,{{\\pos(540,1365)\\fad(200,200)}}Thomas Cleary, notes on Tao Te Ching ch. 2")
ass.append(f"Dialogue: 0,{ts(SPEECH)},{ts(TOTAL)},End,,0,0,0,,{{\\pos(540,820)\\fad(300,0)}}Tao Te Ching\\NChapters 2 & 3")
ass.append(f"Dialogue: 0,{ts(SPEECH)},{ts(TOTAL)},EndSm,,0,0,0,,{{\\pos(540,1040)\\fad(300,0)}}\"When Everyone Knows Beauty Is Beauty\"")
ass.append(f"Dialogue: 0,{ts(SPEECH)},{ts(TOTAL)},EndSm,,0,0,0,,{{\\pos(540,1200)\\fad(300,0)}}Full talk linked below")
open(f"{OUT}/captions.ass", "w").write("\n".join(ass) + "\n")

# ---- ffmpeg graph ----
parts, n = [], len(SEGS)
for i, (a, b, _) in enumerate(SEGS):
    d = b - a
    parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                 f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d-0.03:.3f}:d=0.03[a{i}];")
fc = "".join(parts)
fc += "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca];"
fc += f"[cv]tpad=stop_mode=clone:stop_duration={END_CARD},split[c1][c2];"
fc += "[c1]crop=480:480:265:0,scale=1080:1080:flags=lanczos,eq=contrast=1.04:saturation=1.05[fg];"
fc += "[c2]crop=270:480:292:0,scale=1080:1920,boxblur=30:3,eq=brightness=-0.22[bg];"
fc += "[bg][fg]overlay=0:360,"
# end card: darken fully over last 4 s
fc += f"drawbox=x=0:y=0:w=iw:h=ih:color=black@0.82:t=fill:enable='gte(t,{SPEECH})',"
fc += f"ass={OUT}/captions.ass,format=yuv420p[v];"
fc += f"[ca]apad=pad_dur={END_CARD},loudnorm=I=-14:TP=-1.5:LRA=11[a]"
cmd = ["ffmpeg", "-y", "-v", "error", "-i", SRC, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
       "-t", f"{TOTAL:.3f}", "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", f"{OUT}/short4-closed-mind.mp4"]
subprocess.run(cmd, check=True)
print(f"speech {SPEECH:.1f}s + end card {END_CARD}s = {TOTAL:.1f}s")
