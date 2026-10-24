"""Download a source video into .work/<slug>/source.mp4 and verify it.

  python3 -I pipeline/fetch_source.py <slug> <url> [sha256]

Sources usually arrive as a GitHub release asset on this repo (e.g. tag tao45); its browser_download_url and
sha256 digest are in the release listing.
"""
import hashlib, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import source_path, source_info

slug, url = sys.argv[1], sys.argv[2]
dst = source_path(slug)
subprocess.run(["curl", "-sSL", "--retry", "4", "-C", "-", "-o", dst, url], check=True)
h = hashlib.sha256()
with open(dst, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
print("sha256", h.hexdigest())
if len(sys.argv) > 3:
    assert h.hexdigest() == sys.argv[3].removeprefix("sha256:"), "checksum mismatch"
    print("checksum OK")
print(source_info(dst))
