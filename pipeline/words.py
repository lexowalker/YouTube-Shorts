"""Word timings: load, correct, refine onsets against the audio envelope, and map to program time."""
import json, re, wave
import numpy as np


def norm(s):
    return re.sub(r"[^a-z']", "", s.lower().replace("’", "'"))


def load_words(path, fixes=(), overrides=()):
    """Load words.json, apply overrides and fixes, and merge split hyphenations ("self" + "-interest").

    overrides: [{"from": s, "to": s, "words": [["oh,", 593.66, 593.86], ...], "why": "..."}] replace every word
               starting in [from, to) - for stretches where transcription passes disagree and the words were settled
               by a larger model (text) and the audio envelope (timing)
    fixes:     [{"near": source_seconds, "from": "whole.", "to": "harmony.", "s": optional, "e": optional}]"""
    words = json.load(open(path))
    for o in overrides:
        words = [w for w in words if not (o["from"] <= w["s"] < o["to"])]
        words += [{"w": w, "s": s, "e": e, "p": 1.0} for w, s, e in o["words"]]
    words.sort(key=lambda w: w["s"])
    merged = []
    for w in words:
        if w["w"].startswith("-") and merged:
            merged[-1]["w"] += w["w"]
            merged[-1]["e"] = w["e"]
        else:
            merged.append(dict(w))
    for f in fixes:
        hit = [w for w in merged if norm(w["w"]) == norm(f["from"]) and abs(w["s"] - f["near"]) < 0.5]
        assert len(hit) == 1, f"word fix did not match exactly one word: {f}"
        hit[0]["w"] = f["to"]
        for k in ("s", "e"):
            if k in f:
                hit[0][k] = f[k]
    return merged


class Env:
    """10 ms RMS envelope (dBFS) of the 16 kHz analysis WAV."""

    def __init__(self, wav, step=0.01):
        wf = wave.open(wav)
        a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        n = int(16000 * step)
        k = len(a) // n
        self.db = 20 * np.log10(np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
        self.step = step

    def at(self, t):
        return self.db[int(t / self.step)]


def refine_onsets(words, env, quiet=-46.0, loud=-42.0):
    """If whisper put a word's start in silence, move it to where the voice actually begins."""
    for w in words:
        if env.at(w["s"]) < quiet:
            t = w["s"]
            while t < w["e"] - 0.02 and env.at(t) < loud:
                t += env.step
            w["s0"], w["s"] = w["s"], round(t, 3)
    return words


def to_program(words, segments):
    """Words inside the kept segments, with program-time onsets ps / ends pe."""
    out, p = [], 0.0
    for seg in segments:
        for w in words:
            if seg["src_start"] <= w["s"] < seg["src_end"]:
                out.append(dict(w, ps=round(p + w["s"] - seg["src_start"], 3),
                                pe=round(p + min(w["e"], seg["src_end"]) - seg["src_start"], 3)))
        p += seg["src_end"] - seg["src_start"]
    return out
