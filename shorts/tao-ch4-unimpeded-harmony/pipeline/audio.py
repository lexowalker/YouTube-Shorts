"""Program audio: join the source pieces with tiny fades, clean gently, normalise to about -14 LUFS / <= -1 dBTP."""
import sys, json, subprocess, os, re
edl = json.load(open(sys.argv[1])); out = sys.argv[2]
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "source.mp4")
tail = edl["endcard"]["dur"]
DN_LATENCY = 0.025  # afftdn delays its output by ~25 ms; trimmed so lips and captions stay in sync
parts, inputs = [], []
for i, s in enumerate(edl["segments"]):
    d = s["src_end"] - s["src_start"]
    inputs += ["-ss", f"{s['src_start']:.3f}", "-t", f"{d:.3f}", "-i", SRC]
    # 12 ms fades at every join so no word or breath is clicked off
    parts.append(f"[{i}:a]aresample=48000,pan=mono|c0=0.5*c0+0.5*c1,atrim=0:{d:.4f},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.012,afade=t=out:st={d - 0.012:.4f}:d=0.012[a{i}]")
n = len(edl["segments"])
chain = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[cat]"
clean = (f"[cat]highpass=f=80,afftdn=nr=12:nf=-50:tn=1,atrim=start={DN_LATENCY},asetpts=PTS-STARTPTS,"
         f"apad=pad_dur={tail + DN_LATENCY:.3f}")

def run(extra, dst):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-v", "error", "-y"] + inputs + [
        "-filter_complex", chain + ";" + clean + extra + "[o]", "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s24le", dst]
    subprocess.run(cmd, check=True)

def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = r[r.rindex("Summary"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))

tmp = out + ".clean.wav"
run("", tmp)
i0, tp0 = measure(tmp)
print(f"cleaned speech: {i0} LUFS, true peak {tp0} dBTP")
# gain toward -14, a gentle 2:1 compressor on the loudest syllables, then an oversampled limiter for true peak
extra_gain = 0.0
for _ in range(7):
    g = -14.0 - i0 + extra_gain
    post = (f",volume={g:.2f}dB,acompressor=threshold=-10dB:ratio=3:attack=2:release=80:knee=4:detection=peak,"
            f"aresample=192000,alimiter=limit=0.83:attack=3:release=60:level=false:asc=1,aresample=48000")
    run(post, out)
    i1, tp1 = measure(out)
    print(f"gain {g:.2f} dB -> {i1} LUFS, true peak {tp1} dBTP")
    if abs(i1 + 14.0) <= 0.3:
        break
    extra_gain += (-14.0 - i1) * 1.6  # the compressor takes back part of each step
os.remove(tmp)
