"""HDR (HLG, BT.2020) to SDR (BT.709) conversion for the 4K source files.

The phone records 10-bit HLG. Decoded as ordinary video it looks grey and washed out, because HLG code values are
not BT.709 code values. This converts properly instead of boosting saturation:

  HLG signal -> scene light (inverse OETF) -> display light (the HLG OOTF, gamma 1.2 at 1000 nits)
  -> BT.2020 to BT.709 primaries -> SDR white set at LREF nits -> a tone curve on luminance (hue kept) with a
  soft highlight shoulder -> BT.709 / gamma 2.4 encoding.

The numbers are not taste: they are fitted so the result matches the original video as it looks on YouTube. Two
earlier settings were rejected by the user as pale and faded (a darker rendering at 750 and 900 nits white): the
original is a bright, warm, high-key picture.

make_lut() bakes the conversion into a 65-point 3D LUT (.cube) that ffmpeg applies with lut3d on full-range R'G'B'.
"""
import os
import numpy as np

A, B, C = 0.17883277, 0.28466892, 0.55991073
M2020_709 = np.array([[1.660491, -0.587641, -0.072850],
                      [-0.124550, 1.132900, -0.008349],
                      [-0.018151, -0.100579, 1.118730]], np.float32)
LW, GAMMA = 1000.0, 2.4
# Fitted to the original video as the user sees it (their screenshot of 10 Nov 2026): skin, sweater, chair, hair,
# beard and the dark shelves of the same shot land within about 2% of that picture.
LREF = 386.0    # nits shown as SDR white
CON, PIVOT = 0.98, 0.17   # contrast about a pivot, on luminance
KNEE, WMAX = 0.35, 0.79   # highlight shoulder: luminance above KNEE rolls off towards WMAX
SAT = 1.065     # colourfulness after the shoulder, so bright skin keeps its warmth
LUM709 = np.array([0.2126, 0.7152, 0.0722], np.float32)


def hlg_to_sdr(v):
    """v: HLG BT.2020 R'G'B' signal, float 0..1, shape (..., 3) -> SDR BT.709 R'G'B', float 0..1."""
    v = np.clip(v, 0, 1).astype(np.float32)
    e = np.where(v <= 0.5, v * v / 3.0, (np.exp((v - C) / A) + B) / 12.0)       # inverse OETF: scene light
    ys = (e @ np.array([0.2627, 0.6780, 0.0593], np.float32))[..., None]
    d = LW * np.power(np.maximum(ys, 1e-6), 0.2) * e                            # OOTF: display light, nits
    x = np.maximum(d @ M2020_709.T, 0) / LREF                                   # BT.709 primaries, SDR white
    y = (x @ LUM709)[..., None]
    y2 = PIVOT * np.power(np.maximum(y, 1e-6) / PIVOT, CON)
    y2 = np.where(y2 <= KNEE, y2, KNEE + (WMAX - KNEE) * (1 - np.exp(-(y2 - KNEE) / (WMAX - KNEE))))
    x = x * (y2 / np.maximum(y, 1e-6))                                          # tone curve, hue kept
    x = y2 + (x - y2) * SAT
    return np.power(np.clip(x, 0, 1), 1 / GAMMA)


def make_lut(path, n=65):
    g = np.linspace(0, 1, n, dtype=np.float32)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")  # .cube order: red changes fastest
    out = hlg_to_sdr(np.stack([r, gg, b], -1).reshape(-1, 3))
    with open(path, "w") as f:
        f.write(f"TITLE \"HLG BT.2020 to SDR BT.709\"\nLUT_3D_SIZE {n}\n")
        f.write("\n".join(f"{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}" for p in out) + "\n")
    return path


# ffmpeg filters: limited-range BT.2020 Y'CbCr -> full-range R'G'B' (still HLG), then the LUT
def ffmpeg_filter(lut):
    return f"zscale=min=2020_ncl:rin=tv:m=gbr:r=pc,format=gbrp16le,lut3d=file={lut}:interp=tetrahedral,scale=out_color_matrix=bt709:out_range=tv,format=yuv444p16le"


def is_hdr(path):
    import subprocess
    t = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout
    # (csv output can carry a trailing comma: that once made this return False, and three renders went out
    # unconverted and washed out)
    return t.strip().strip(",").strip() in ("arib-std-b67", "smpte2084")


def check(slug):
    """python3 -I pipeline/hdr.py check <slug>
    Proves the head shots were converted: puts the user's reference of the original, the raw decode and the
    rendered head master side by side (.work/<slug>/colour_check.jpg) and compares their colourfulness. The raw
    HLG decode is pale (mean saturation about 0.12 on this set); the original and a correct conversion sit near
    0.19-0.20. Look at the sheet as well: skin should be warm, the sweater mid grey, the shelves black."""
    import os, subprocess, sys
    from PIL import Image
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import work_dir, head_source, load_spec, REPO
    wd = work_dir(slug)
    src, t0 = head_source(slug)
    a, b = load_spec(slug)["segments"][0]

    def grab(args, vf):
        raw = subprocess.run(["ffmpeg", "-v", "error"] + args + ["-frames:v", "1", "-vf", vf, "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.uint8).reshape(960, 540, 3)

    def sat(x):
        x = x.astype(np.float32) / 255
        return float(((x.max(-1) - x.min(-1)) / np.maximum(x.max(-1), 1e-6)).mean())
    t = min(2.5, (b - a) / 2)
    done = grab(["-ss", f"{t:.2f}", "-i", os.path.join(wd, "head_master.mp4")], "scale=540:960")
    # the raw decode, cropped roughly where he sits (only for the comparison picture)
    rawf = grab(["-ss", f"{a + t - t0:.2f}", "-i", src], "crop=1216:2160:1700:0,scale=540:960")
    ref = Image.open(os.path.join(REPO, "docs", "reference", "head-colour-original.webp")).convert("RGB")
    ref = np.asarray(ref.crop((455, 0, 1100, 1146)).resize((540, 960)))
    sheet = Image.fromarray(np.concatenate([ref, rawf, done], 1))
    out = os.path.join(wd, "colour_check.jpg")
    sheet.save(out, quality=90)
    s_ref, s_raw, s_done = sat(ref), sat(rawf), sat(done)
    print(f"{out}: original (reference) | raw decode | rendered head master")
    print(f"mean saturation: reference {s_ref:.3f}, raw decode {s_raw:.3f}, rendered {s_done:.3f}")
    if is_hdr(src) and s_done < s_raw * 1.25:
        sys.exit("FAIL: the rendered head shots are as pale as the raw HDR decode. The conversion was not applied.")
    print("OK: the head shots are converted" if is_hdr(src) else "SDR source: nothing to convert")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "check":
        check(sys.argv[2])
