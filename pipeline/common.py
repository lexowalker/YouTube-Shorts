"""Shared paths, house-style constants and helpers for the Shorts pipeline.

Layout:
  shorts/<slug>/short.json   the edit spec for one Short (committed)
  .work/<slug>/              per-Short intermediates: source.mp4, transcripts, EDL, renders (git-ignored)
  .work/img/                 museum image cache shared by all Shorts (git-ignored)
  assets/fonts/              EB Garamond static instances (OFL)
"""
import json, os, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_ROOT = os.environ.get("SHORTS_WORK", os.path.join(REPO, ".work"))
IMG_DIR = os.path.join(WORK_ROOT, "img")

FONT_SEMI = os.path.join(REPO, "assets", "fonts", "EBGaramond-600.ttf")
FONT_MED = os.path.join(REPO, "assets", "fonts", "EBGaramond-500.ttf")

# output format
W, H, FPS = 1080, 1920, 30
DISSOLVE = 12  # frames (0.4 s) of the soft dissolve between scenes

# house palette: one serif family, one accent in captions, cinnabar only on the end card
OFFWHITE = (0xF4, 0xEF, 0xE4)   # captions, rice paper
OCHRE = (0xD9, 0xB2, 0x6F)      # the one highlighted word per phrase
CINNABAR = (0xA8, 0x47, 0x3A)   # seal
INK = (0x2B, 0x27, 0x22)        # text on rice paper


def short_dir(slug):
    return os.path.join(REPO, "shorts", slug)


def work_dir(slug):
    d = os.path.join(WORK_ROOT, slug)
    os.makedirs(d, exist_ok=True)
    return d


def source_path(slug):
    return os.path.join(work_dir(slug), "source.mp4")


def head_source(slug):
    """The picture (and sound) to cut from: a high-resolution window fetched by fetch_hires.py if there is one,
    else source.mp4. Returns (path, t0): source time t is at t - t0 in that file."""
    meta = os.path.join(work_dir(slug), "hires.json")
    if os.path.exists(meta):
        m = json.load(open(meta))
        return m["path"], m["t0"]
    return source_path(slug), 0.0


def load_spec(slug):
    return json.load(open(os.path.join(short_dir(slug), "short.json")))


def source_info(path):
    """Width, height and frame rate of the source's video stream."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return {"w": s["width"], "h": s["height"], "fps": num / den}


# The archive.org 4K files are HDR (10-bit HLG, BT.2020, from the phone that films him). Read as ordinary video
# they look washed out: flat contrast, pale skin, drained colour. This converts them properly to SDR BT.709
# (linearise, BT.2020 -> BT.709 primaries, Mobius tone map at 260 nits reference white, no desaturation).
# Approved by eye against the raw decode, 2026-11-08 (docs/style.md: Talking head).
HDR_TO_SDR = ("zscale=tin={tin}:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=260,format=gbrpf32le,zscale=p=bt709,"
              "tonemap=mobius:param=0.3:desat=0,zscale=t=bt709:m=bt709:r=pc,format=rgb24")


def hdr_filter(path):
    """The HDR->SDR filter for a source, or None if it's already SDR."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout.strip()
    if out in ("arib-std-b67", "smpte2084"):
        return HDR_TO_SDR.format(tin=out)
    return None


def image_path(acc):
    return os.path.join(IMG_DIR, f"{acc}_full.jpg")
