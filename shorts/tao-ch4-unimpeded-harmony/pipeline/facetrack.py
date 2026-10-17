"""Face-centre track for the 9:16 crop: python3 -I facetrack.py <video> <start> <end> -> JSON list of [t, cx] (source px)."""
import sys, json, subprocess
import numpy as np
import cv2

SW, SH = 1280, 720
RATE = 6.0


def track(video, start, end):
    n = SW * SH * 3
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-i", video, "-t", f"{end - start:.3f}",
                          "-vf", f"fps={RATE}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    front = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    prof = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    out, i, prev = [], 0, None
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        g = cv2.cvtColor(np.frombuffer(b, np.uint8).reshape(SH, SW, 3), cv2.COLOR_BGR2GRAY)
        g = cv2.equalizeHist(g)
        cands = []
        for (x, y, w, h) in front.detectMultiScale(g, 1.1, 5, minSize=(120, 120)):
            cands.append((x + w / 2, w))
        for (x, y, w, h) in prof.detectMultiScale(g, 1.1, 5, minSize=(120, 120)):
            cands.append((x + w / 2, w))
        for (x, y, w, h) in prof.detectMultiScale(cv2.flip(g, 1), 1.1, 5, minSize=(120, 120)):
            cands.append((SW - (x + w / 2), w))
        cands = [c for c in cands if 420 < c[0] < 1100]  # ignore the bust on the left shelf
        cx = None
        if cands:
            # largest face, preferring one near the previous detection
            cands.sort(key=lambda c: (-c[1] + (abs(c[0] - prev) * 0.5 if prev is not None else 0)))
            cx = float(cands[0][0])
            prev = cx
        out.append([start + i / RATE, cx])
        i += 1
    return out


if __name__ == "__main__":
    print(json.dumps(track(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))))
