"""Final delivery file: 2-pass H.264 at ~8 Mbps with AAC 256k, faststart.

  python3 -I pipeline/encode.py <slug>   -> shorts/<slug>/<slug>.mp4

~8 Mbps (about 80 MB for 80 s) looks clean after YouTube's re-encode. The mp4 is git-ignored: deliver it, don't commit it.
"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work_dir, short_dir

slug = sys.argv[1]
wd = work_dir(slug)
video, audio = os.path.join(wd, "video_master.mp4"), os.path.join(wd, "program_audio.wav")
out = os.path.join(short_dir(slug), f"{slug}.mp4")
log = os.path.join(wd, "x264pass")
v = ["-c:v", "libx264", "-preset", "slow", "-b:v", "8M", "-maxrate", "12M", "-bufsize", "16M", "-pix_fmt", "yuv420p",
     "-passlogfile", log]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video] + v + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a"] + v +
               ["-pass", "2", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
print(out, f"{os.path.getsize(out) / 1e6:.1f} MB")
