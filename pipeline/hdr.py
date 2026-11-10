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
