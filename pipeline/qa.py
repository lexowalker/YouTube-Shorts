"""Checks before delivery.

  python3 -I pipeline/qa.py <slug>              full check of shorts/<slug>/<slug>.mp4
  python3 -I pipeline/qa.py <slug> --audio-only  caption check on .work/<slug>/program_audio.wav, before rendering

- Format: 1080x1920, 30 fps, H.264 + AAC, 60-120 s.
- Audio: integrated loudness and true peak (must be <= -1 dBTP).
- Captions: re-transcribes the finished audio and diffs it against every caption word; lists words whose caption
  appears more than 0.08 s before, or 0.25 s after, the re-transcribed onset, with the audio envelope so you can see
  which side is right. Fix real misses with onset_fixes in short.json.
- Contact sheet of 20 frames -> .work/<slug>/qa_sheet.jpg (look at it: framing, captions, crops, end card).
"""
import difflib, json, os, re, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, short_dir
from words import norm

slug = sys.argv[1]
audio_only = "--audio-only" in sys.argv
wd = work_dir(slug)
mp4 = os.path.join(wd, "program_audio.wav") if audio_only else os.path.join(short_dir(slug), f"{slug}.mp4")
edl = json.load(open(os.path.join(wd, "edl.json")))

probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,r_frame_rate:format=duration",
                                   "-of", "json", mp4], capture_output=True, text=True).stdout)
dur = float(probe["format"]["duration"])
print("streams:", [(s["codec_name"], s.get("width"), s.get("height"), s.get("r_frame_rate")) for s in probe["streams"]], f"duration {dur:.2f}s",
      "" if 60 <= dur <= 120 else "  <-- OUTSIDE 60-120 s")
r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
s = r[r.rindex("Summary"):]
tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))
lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1))
print(f"loudness {lufs} LUFS, true peak {tp} dBTP", "" if tp <= -1.0 else "  <-- TOO HOT")

wav = os.path.join(wd, "final16k.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-ac", "1", "-ar", "16000", wav], check=True)
from faster_whisper import WhisperModel
model = WhisperModel("medium.en", device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
wf = wave.open(wav)
x = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
segs, _ = model.transcribe(x, language="en", word_timestamps=True, beam_size=5)
fw = [{"w": w.word.strip(), "s": w.start} for sg in segs for w in sg.words]
merged = []
for w in fw:  # "self" + "-interest"
    if w["w"].startswith("-") and merged:
        merged[-1]["w"] += w["w"]
    else:
        merged.append(w)
# fillers ("~you ~know") are spoken but deliberately not shown; they still count as matched speech
cw = sorted([w for c in edl["captions"] for w in c["words"] + c.get("fillers", [])], key=lambda w: w["s"])
a, b = [norm(w["w"]) for w in merged], [norm(w["w"]) for w in cw]
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
print(f"spoken {len(a)} words, captioned {len(b)}, match ratio {sm.ratio():.3f}")


def db(t):
    seg = x[int(t * 16000):int((t + 0.01) * 16000)]
    return 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)


for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != "equal":
        print(f"  WORD MISMATCH {op}: heard {a[i1:i2]} vs caption {b[j1:j2]} near {merged[min(i1, len(merged) - 1)]['s']:.2f}s")
        continue
    for k in range(i2 - i1):
        c, f = cw[j1 + k], merged[i1 + k]
        d = c["s"] - f["s"]
        if d < -0.08 or d > 0.25:
            env = " ".join(f"{db(t):.0f}" for t in np.arange(min(c["s"], f["s"]) - 0.05, max(c["s"], f["s"]) + 0.1, 0.03))
            print(f"  onset {c['w']:15s} caption {c['s']:.2f} heard {f['s']:.2f} ({d:+.2f}) | dB {env}")

if audio_only:
    sys.exit(0)
times = np.linspace(0.8, dur - 0.5, 20)
tiles = []
for i, t in enumerate(times):
    p = os.path.join(wd, f"qa_{i:02d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", "-vf", "scale=270:480", p], check=True)
    tiles.append(p)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(wd, "qa_%02d.png"), "-vf", "tile=10x2", "-frames:v", "1",
                os.path.join(wd, "qa_sheet.jpg")], check=True)
for p in tiles:
    os.remove(p)
print("contact sheet:", os.path.join(wd, "qa_sheet.jpg"), "at", ", ".join(f"{t:.1f}" for t in times))
