"""Audio envelope around candidate cut points, to place every cut in a real pause.

  python3 -I pipeline/env.py <slug> 313.84 323.30 ...

Prints 20 ms RMS levels (dBFS of the 16 kHz analysis WAV) from 0.6 s before to 0.6 s after each time, with the
time itself marked "|". Speech sits around -35..-15 dB, room tone around -50 and below. Cut where it is quiet,
leaving ~0.3 s of the source's own room tone either side of a join so the pause sounds natural.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir
from words import Env

slug = sys.argv[1]
env = Env(os.path.join(work_dir(slug), "audio16k.wav"), step=0.02)
for t in map(float, sys.argv[2:]):
    cells = []
    for k in range(-30, 31):
        tt = t + k * 0.02
        cells.append(("|" if k == 0 else "") + f"{env.at(tt):.0f}" if tt >= 0 else "")
    print(f"{t:8.2f}: " + " ".join(cells))
