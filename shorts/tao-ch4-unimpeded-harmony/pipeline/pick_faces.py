"""Score frames for a thumbnail: frontal face, both eyes found, sharp. Prints the best timestamps."""
import sys, subprocess, numpy as np, cv2
src, step = sys.argv[1], float(sys.argv[2])
SW, SH = 1280, 720
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"fps=1/{step}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eyes = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml")
res, i = [], 0
while True:
    b = p.stdout.read(SW * SH * 3)
    if len(b) < SW * SH * 3:
        break
    img = np.frombuffer(b, np.uint8).reshape(SH, SW, 3)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    fs = [f for f in face.detectMultiScale(g, 1.1, 6, minSize=(160, 160)) if 450 < f[0] + f[2] / 2 < 1050]
    if fs:
        x, y, w, h = max(fs, key=lambda f: f[2])
        roi = g[y:y + h // 2 + h // 6, x:x + w]
        es = eyes.detectMultiScale(roi, 1.1, 6, minSize=(w // 10, w // 10))
        sharp = cv2.Laplacian(g[y:y + h, x:x + w], cv2.CV_64F).var()
        if len(es) >= 2:
            res.append((sharp, i * step, int(x + w / 2), int(y + h / 2), int(w)))
    i += 1
res.sort(reverse=True)
for r in res[:int(sys.argv[3])]:
    print(f"{r[1]:.1f} sharp={r[0]:.0f} cx={r[2]} cy={r[3]} w={r[4]}")
