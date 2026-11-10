"""Talking-head master: every head frame of the program, cropped and framed the same way, in natural colour.

  python3 -I pipeline/head.py <slug> [--jobs 3]     -> .work/<slug>/head_master.mp4 (1080x1920, 30 fps, all-intra)

- Every head scene is framed the same way: the same full-height 9:16 crop, centred on his face. The crop stays
  fixed while he sits still and follows him slowly when he leans in to read (see face_tracks).
- The 4K source is HDR (HLG). It is converted to SDR with pipeline/hdr.py, not by raising saturation.
- Frame f of head_master.mp4 is program frame f: segments are laid end to end exactly as the audio is cut.
Each segment is cached in .work/<slug>/head/, keyed by its times and crop, so changing one cut re-renders one piece.
"""
import argparse, hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import W, H, FPS, work_dir, source_path, source_info, load_spec, head_source
import hdr


def face_tracks(slug, spec, hinfo, cw):
    """Per segment: (times, crop-left px) samples. The crop is always the same size and always centred on his face.
    While he sits still the crop is fixed for the whole segment (his median position); when he leans in to read
    or shifts in his chair it follows him on a heavily smoothed path, so the frame drifts and never snaps."""
    from facetrack import track, RATE
    info = source_info(source_path(slug))
    scale = hinfo["w"] / info["w"]
    out = []
    for a, b in spec["segments"]:
        pts = track(source_path(slug), a - 1.0, b + 1.0, info["w"], info["h"], tuple(spec.get("face_x_band", (0.33, 0.86))))
        t = np.array([p[0] for p in pts])
        c = np.array([np.nan if p[1] is None else p[1] for p in pts])
        ok = ~np.isnan(c)
        c = (np.interp(t, t[ok], c[ok]) if ok.any() else np.full_like(t, info["w"] / 2)) * scale
        inside = (t >= a) & (t <= b)
        spread = np.percentile(c[inside], 95) - np.percentile(c[inside], 5)
        if spread < 0.08 * cw:
            c = np.full_like(c, np.median(c[inside]))
        else:
            sig = 1.5 * RATE
            k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2)
            k /= k.sum()
            c = np.convolve(np.pad(c, len(k) // 2, mode="edge"), k, mode="valid")
        left = np.clip(c - cw / 2, 0, hinfo["w"] - cw)
        out.append((t, left, spread >= 0.08 * cw))
        print(f"  {a:.2f}-{b:.2f}: face spread {spread:.0f}px -> {'follows' if spread >= 0.08 * cw else 'fixed'}, left {left.min():.0f}..{left.max():.0f}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    spec, wd = load_spec(a.slug), work_dir(a.slug)
    src, t0 = head_source(a.slug)
    hinfo = source_info(src)
    sh = hinfo["h"]
    cw = round(sh * 9 / 16) // 2 * 2
    hd = os.path.join(wd, "head")
    os.makedirs(hd, exist_ok=True)
    grade = (hdr.ffmpeg_filter(hdr.make_lut(os.path.join(wd, "hlg_to_sdr.cube"))) + ",") if hdr.is_hdr(src) else ""
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "13", "-g", "1", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    tracks = face_tracks(a.slug, spec, hinfo, cw)

    jobs, p = [], 0.0
    for (s, e), (tt, left, moving) in zip(spec["segments"], tracks):
        f0, f1 = round(p * FPS), round((p + e - s) * FPS)
        p += e - s
        lefts = np.interp(s + np.arange(f1 - f0) / FPS, tt, left)
        key = hashlib.md5(f"{s:.3f}-{e:.3f}-{f1 - f0}-{hdr.LREF}-{hdr.KNEE}-{np.round(lefts).tobytes().hex()[:4000]}".encode()).hexdigest()[:10]
        jobs.append((s, e, f1 - f0, os.path.join(hd, f"{key}.mp4"), lefts, moving))

    def run(j):
        s, e, n, out, lefts, moving = j
        if os.path.exists(out):
            return
        tmp = out + ".tmp.mp4"
        inp = ["ffmpeg", "-v", "error", "-y", "-ss", f"{s - t0:.4f}", "-i", src, "-t", f"{e - s + 0.5:.3f}", "-an"]
        if not moving:
            x = int(round(lefts[0])) // 2 * 2
            vf = f"crop={cw}:{sh}:{x}:0,{grade}scale={W}:{H}:flags=lanczos,fps={FPS},tpad=stop_mode=clone:stop_duration=1"
            subprocess.run(inp + ["-vf", vf, "-frames:v", str(n)] + enc + [tmp], check=True)
        else:
            import cv2
            bx0 = max(0, int(lefts.min()) - 2) // 2 * 2
            bw = min(hinfo["w"], (int(np.ceil(lefts.max())) + cw + 4) // 2 * 2) - bx0
            vf = f"crop={bw}:{sh}:{bx0}:0,{grade}fps={FPS},tpad=stop_mode=clone:stop_duration=1"
            dec = subprocess.Popen(inp + ["-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            out_p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                                      "-i", "-"] + enc + [tmp], stdin=subprocess.PIPE)
            for k in range(n):
                buf = dec.stdout.read(bw * sh * 3)
                if len(buf) < bw * sh * 3:
                    break
                fr = np.frombuffer(buf, np.uint8).reshape(sh, bw, 3)
                m = np.float32([[1, 0, -(lefts[k] - bx0)], [0, 1, 0]])
                crop = cv2.warpAffine(fr, m, (cw, sh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                out_p.stdin.write(cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4).tobytes())
            out_p.stdin.close()
            out_p.wait()
            dec.wait()
        os.replace(tmp, out)
        print(f"  rendered {s:.2f}-{e:.2f}: {n} frames", flush=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(run, jobs))
    lst = os.path.join(hd, "list.txt")
    open(lst, "w").write("".join(f"file '{j[3]}'\n" for j in jobs))
    out = os.path.join(wd, "head_master.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                            "stream=nb_read_packets", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip().strip(","))
    want = sum(j[2] for j in jobs)
    assert n == want, f"head master has {n} frames, expected {want}"
    print(f"{out}: {n} frames")


if __name__ == "__main__":
    main()
