"""Face-centre samples for the 9:16 crop (Haar cascades; frontal plus both profiles)."""
import subprocess
import numpy as np
import cv2

RATE = 6.0  # samples per second


def track(video, start, end, sw, sh, x_band=(0.33, 0.86)):
    """[[t, cx or None], ...] in source pixels. x_band limits where a face may be, as fractions of the width:
    David's set has a sculpted head on the left shelf that the detector would otherwise lock onto."""
    n = sw * sh * 3
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{max(start, 0):.3f}", "-i", video, "-t", f"{end - max(start, 0):.3f}",
                          "-vf", f"fps={RATE}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    front = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    prof = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    min_face = (sh // 6, sh // 6)
    out, i, prev = [], 0, None
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        g = cv2.equalizeHist(cv2.cvtColor(np.frombuffer(b, np.uint8).reshape(sh, sw, 3), cv2.COLOR_BGR2GRAY))
        cands = [(x + w / 2, w) for (x, y, w, h) in front.detectMultiScale(g, 1.1, 5, minSize=min_face)]
        cands += [(x + w / 2, w) for (x, y, w, h) in prof.detectMultiScale(g, 1.1, 5, minSize=min_face)]
        cands += [(sw - (x + w / 2), w) for (x, y, w, h) in prof.detectMultiScale(cv2.flip(g, 1), 1.1, 5, minSize=min_face)]
        cands = [c for c in cands if x_band[0] * sw < c[0] < x_band[1] * sw]
        cx = None
        if cands:
            # largest face, preferring one near the previous detection
            cands.sort(key=lambda c: -c[1] + (abs(c[0] - prev) * 0.5 if prev is not None else 0))
            cx = prev = float(cands[0][0])
        out.append([max(start, 0) + i / RATE, cx])
        i += 1
    return out
