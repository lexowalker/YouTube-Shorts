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


def image_path(acc):
    return os.path.join(IMG_DIR, f"{acc}_full.jpg")
