"""Merge word transcripts, refine onsets against the audio envelope, and map to program time."""
import json, wave, numpy as np

def load_words(paths_and_ranges):
    words = []
    for p, lo, hi in paths_and_ranges:
        words += [w for w in json.load(open(p)) if lo <= w["s"] < hi]
    words.sort(key=lambda w: w["s"])
    merged = []
    for w in words:
        if w["w"].startswith("-") and merged:
            merged[-1]["w"] += w["w"]; merged[-1]["e"] = w["e"]
        else:
            merged.append(dict(w))
    return merged

class Env:
    def __init__(self, wav, step=0.01):
        wf = wave.open(wav); a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        n = int(16000 * step); k = len(a) // n
        self.db = 20 * np.log10(np.sqrt((a[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
        self.step = step
    def at(self, t):
        return self.db[int(t / self.step)]

def refine_onsets(words, env, quiet=-44.0, loud=-38.0):
    """If whisper put a word's start in silence, move it to where the voice actually begins."""
    for w in words:
        if env.at(w["s"]) < quiet:
            t = w["s"]
            while t < w["e"] - 0.02 and env.at(t) < loud:
                t += env.step
            w["s0"], w["s"] = w["s"], round(t, 3)
    return words

def to_program(words, segments):
    out, p = [], 0.0
    for seg in segments:
        for w in words:
            if seg["src_start"] <= w["s"] < seg["src_end"]:
                out.append(dict(w, ps=round(p + w["s"] - seg["src_start"], 3), pe=round(p + min(w["e"], seg["src_end"]) - seg["src_start"], 3)))
        p += seg["src_end"] - seg["src_start"]
    return out
