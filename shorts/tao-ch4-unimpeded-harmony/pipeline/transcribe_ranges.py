import sys, json, wave, numpy as np
from faster_whisper import WhisperModel
wf=wave.open(sys.argv[1]); audio=np.frombuffer(wf.readframes(wf.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
model = WhisperModel("medium.en", device="cpu", compute_type="int8", cpu_threads=4)
out=[]
for rng in sys.argv[3:]:
    a,b=map(float,rng.split(":"))
    segs,_=model.transcribe(audio[int(a*16000):int(b*16000)], language="en", word_timestamps=True, beam_size=5,
        initial_prompt=None)
    for s in segs:
        for w in s.words:
            out.append({"w":w.word.strip(),"s":round(w.start+a,3),"e":round(w.end+a,3),"p":round(w.probability,3)})
json.dump(out,open(sys.argv[2],"w"),indent=0)
for w in out: print(f"{w['s']:8.2f} {w['e']:8.2f} {w['p']:.2f} {w['w']}")
