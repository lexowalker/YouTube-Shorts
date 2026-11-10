"""HDR (HLG, BT.2020) to SDR (BT.709) conversion for the 4K source files.

The phone records 10-bit HLG. Decoded as ordinary video it looks grey and washed out, because HLG code values are
not BT.709 code values. This converts properly instead of boosting saturation:

  HLG signal -> scene light (inverse OETF) -> display light (the HLG OOTF, gamma 1.2 at 1000 nits)
  -> BT.2020 to BT.709 primaries -> SDR white set at LREF nits -> a soft shoulder on the highlights that keeps
  hue (the same gain on R, G and B) -> BT.709 / gamma 2.4 encoding.

LREF and KNEE were chosen by eye on this set: his skin, white hair and grey sweater sit where they would in a
normal SDR recording, and the forehead highlights keep their detail.

make_lut() bakes the conversion into a 65-point 3D LUT (.cube) that ffmpeg applies with lut3d on full-range R'G'B'.
"""
import os
import numpy as np

A, B, C = 0.17883277, 0.28466892, 0.55991073
M2020_709 = np.array([[1.660491, -0.587641, -0.072850],
                      [-0.124550, 1.132900, -0.008349],
                      [-0.018151, -0.100579, 1.118730]], np.float32)
LREF, KNEE, GAMMA, LW = 750.0, 0.55, 2.4, 1000.0


def hlg_to_sdr(v, lref=LREF, knee=KNEE, gamma=GAMMA, lw=LW):
    """v: HLG BT.2020 R'G'B' signal, float 0..1, shape (..., 3) -> SDR BT.709 R'G'B', float 0..1."""
    v = np.clip(v, 0, 1).astype(np.float32)
    e = np.where(v <= 0.5, v * v / 3.0, (np.exp((v - C) / A) + B) / 12.0)
    ys = (e @ np.array([0.2627, 0.6780, 0.0593], np.float32))[..., None]
    d = lw * np.power(np.maximum(ys, 1e-6), 0.2) * e
    x = np.maximum(d @ M2020_709.T, 0) / lref
    m = x.max(-1, keepdims=True)
    c = np.where(m <= knee, m, knee + (1 - knee) * (1 - np.exp(-(m - knee) / (1 - knee))))
    x = x * (c / np.maximum(m, 1e-6))
    return np.power(np.clip(x, 0, 1), 1 / gamma)


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
    return f"zscale=min=2020_ncl:rin=tv:m=gbr:r=pc,format=gbrp16le,lut3d=file={lut}:interp=tetrahedral"


def is_hdr(path):
    import subprocess
    t = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                        "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return t in ("arib-std-b67", "smpte2084")
