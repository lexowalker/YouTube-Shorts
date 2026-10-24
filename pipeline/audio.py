"""Program audio: the source's own sound, cut together cleanly. No denoise, EQ or compression.

  python3 -I pipeline/audio.py <slug> [--no-declick]

- Each piece is cut from the source at the EDL's times (all cuts fall in natural pauses).
- Every join gets a 12 ms fade out / fade in, so no edge can pop or click.
- Mouth clicks and pops in the pauses between words are removed (ffmpeg adeclick), and only there: the words
  themselves are left exactly as recorded (on speech, adeclick also nibbles at consonants, so it is never applied
  inside a word's span).
- One static gain, set so the true peak lands at -1 dBTP. Nothing else touches the dynamics or tone, so the
  voice sounds as it does in the original video, only louder.
Writes .work/<slug>/program_audio.wav (48 kHz, 24-bit, the source's channel layout) including the end card's silence.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, head_source

SR = 48000
FADE = 0.012
PEAK_TARGET = -1.0   # dBTP
WORD_GUARD = 0.04    # keep de-click this far away from every spoken word
RAMP = 0.01          # crossfade between untouched words and de-clicked pauses


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    s = r[r.rindex("Summary"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))


def channels(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip())


def render(inputs, graph, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error"] + inputs + ["-filter_complex", graph + "[o]", "-map", "[o]",
                          "-f", "f32le", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def write(x, path, ch):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-",
                    "-c:a", "pcm_s24le", path], input=x.astype(np.float32).tobytes(), check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--no-declick", action="store_true")
    a = ap.parse_args()
    wd = work_dir(a.slug)
    edl = json.load(open(os.path.join(wd, "edl.json")))
    src, t0 = head_source(a.slug)
    ch = channels(src)
    inputs, parts = [], []
    for i, s in enumerate(edl["segments"]):
        d = s["src_end"] - s["src_start"]
        inputs += ["-ss", f"{s['src_start'] - t0:.3f}", "-t", f"{d:.3f}", "-i", src]
        parts.append(f"[{i}:a]aresample={SR},atrim=0:{d:.4f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={FADE},afade=t=out:st={d - FADE:.4f}:d={FADE}[a{i}]")
    n = len(parts)
    graph = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1"
    graph += f",apad=pad_dur={edl['endcard']['dur']:.3f}"

    plain = render(inputs, graph, ch)
    x = plain
    if not a.no_declick:
        cleaned = render(inputs, graph + ",adeclick", ch)
        m = min(len(plain), len(cleaned))
        plain, cleaned = plain[:m], cleaned[:m]
        # mask = 1 in pauses, 0 on (and near) every spoken word
        mask = np.ones(m, np.float32)
        for c in edl["captions"]:
            for w in c["words"] + c.get("fillers", []):
                mask[max(0, int((w["s"] - WORD_GUARD) * SR)):int((w["e"] + WORD_GUARD) * SR)] = 0.0
        r = int(RAMP * SR)
        mask = np.convolve(mask, np.ones(r, np.float32) / r, mode="same")[:, None]
        x = plain * (1 - mask) + cleaned * mask
        diff = np.abs(x - plain).max(axis=1)
        changed = (diff.reshape(-1, SR // 100)[: len(diff) // (SR // 100)].max(axis=1) > 10 ** (-60 / 20)).sum()
        print(f"de-click: changed {changed} of {len(diff) // (SR // 100)} 10 ms windows, all in pauses")

    tmp = os.path.join(wd, "program_audio_unity.wav")
    write(x, tmp, ch)
    i0, tp0 = measure(tmp)
    gain = PEAK_TARGET - tp0
    out = os.path.join(wd, "program_audio.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={gain:.2f}dB", "-c:a", "pcm_s24le", out], check=True)
    os.remove(tmp)
    i1, tp1 = measure(out)
    print(f"joined: {i0} LUFS, {tp0} dBTP -> static gain {gain:+.2f} dB -> {i1} LUFS integrated, {tp1} dBTP true peak")


if __name__ == "__main__":
    main()
