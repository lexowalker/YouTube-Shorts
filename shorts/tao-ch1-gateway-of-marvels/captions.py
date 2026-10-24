"""Write captions.ass for the Chapter 1 Short.

  python3 -I shorts/tao-ch1-gateway-of-marvels/captions.py <clip_start> <clip_dur> <out.ass>

Each line appears on its spoken onset: medium.en word starts checked against the 10 ms RMS envelope of the
source (where whisper put a start in silence, the onset is where the voice actually rises). Line breaks are
explicit (WrapStyle 2) so a caption never reflows while it is on screen.
"""
import sys

# (source onset in seconds, caption text; \N is a manual line break)
LINES = [
    (177.37, "Chapter One"),
    (178.12, "A way can be a guide…"),
    (181.12, "A way can be a guide,"),
    (182.45, "but not a fixed path;"),
    (185.55, "Names can be given,"),
    (187.10, "but not permanent labels."),
    (190.00, "Nonbeing is called"),
    (191.52, "the beginning of\\Nheaven and earth;"),
    (194.70, "Being is called"),
    (196.08, "the mother of all things."),
    (199.12, "Always passionless,"),
    (201.80, "thereby observe\\Nthe subtle;"),
    (205.55, "ever intent,"),
    (207.55, "thereby observe\\Nthe apparent."),
    (210.90, "These two come from\\Nthe same source"),
    (212.72, "but differ in name;"),
    (215.50, "both are considered\\Nmysteries."),
    (217.94, "The mystery of mysteries"),
    (219.32, "is the gateway of marvels."),
]
LEAD = 0.04  # start the 100 ms fade-in just before the onset so the text is fully up as the word lands

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kicker,Inter SemiBold,40,&H00A8D8F0,&H00000000,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,0,2,8,60,60,130,1
Style: Title,Caladea,86,&H00FFFFFF,&H00000000,&H00000000,&H78000000,1,0,0,0,100,100,0,0,1,0,3,8,60,60,190,1
Style: Credit,Inter,32,&H00D0D0D0,&H00000000,&H00000000,&H64000000,0,1,0,0,100,100,1,0,1,0,2,8,60,60,300,1
Style: Cap,Inter ExtraBold,68,&H00FFFFFF,&H00000000,&H00101010,&H96000000,1,0,0,0,100,100,0,0,1,6,3,2,70,70,400,1
Style: CapGold,Inter ExtraBold,68,&H0060D8FF,&H00000000,&H00101010,&H96000000,1,0,0,0,100,100,0,0,1,6,3,2,70,70,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ts(x):
    x = max(0.0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def main():
    start, dur, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    end = dur - 0.1  # captions and title are gone before the held frame dissolves into the end card
    ev = [f"Dialogue: 0,{ts(0)},{ts(end)},{style},,0,0,0,,{{\\fad(400,300)}}{text}" for style, text in [
        ("Kicker", "TAO TE CHING  ·  CHAPTER 1"),
        ("Title", "The Gateway of Marvels"),
        ("Credit", "read by dr.a  ·  trans. Thomas Cleary"),
    ]]
    for i, (s, text) in enumerate(LINES):
        t0 = s - start - LEAD
        t1 = (LINES[i + 1][0] - start - LEAD) if i + 1 < len(LINES) else end
        style = "CapGold" if i in (0, len(LINES) - 1) else "Cap"
        fade_out = 300 if i + 1 == len(LINES) else 0
        ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\fad(100,{fade_out})}}{text}")
    open(out, "w").write(HEADER + "\n".join(ev) + "\n")


if __name__ == "__main__":
    main()
