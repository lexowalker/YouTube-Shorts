"""Render the house end card (pipeline/render.py: build_endcard) as a silent clip, with its 1.03x -> 1.00x zoom-out.

  python3 -I shorts/tao-ch1-gateway-of-marvels/endcard.py <seconds> <out.mp4>
"""
import os, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "pipeline"))
import numpy as np
from common import W, H, FPS
from render import build_endcard, endcard_frame

dur, out = float(sys.argv[1]), sys.argv[2]
card = build_endcard({"endcard": {"dur": dur}})
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", out],
                       stdin=subprocess.PIPE)
n = round(dur * FPS)
for f in range(n):
    enc.stdin.write(np.ascontiguousarray(endcard_frame(card, f / n)).astype(np.uint8).tobytes())
enc.stdin.close()
enc.wait()
