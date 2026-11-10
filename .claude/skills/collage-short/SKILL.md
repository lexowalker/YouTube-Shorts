---
name: collage-short
description: Make a 2:00–3:00 teaching Short of David E. Arredondo with talking head, museum images keyed to his words, animated paper collages, house subtitles and end card (the style of "Government of Sages", shorts/tao-ch3-sage-government). Use when the user asks for a teaching or Discussion Short, gives a video and time range with a teaching to focus on, mentions the moodboard, images or collages, or asks to fix or re-cut one of these. Transcript first for the user's approval, then the build. Not for "the reading of ch N" (use reading-short).
---

# Image-and-collage teaching Short

Read `docs/collage-style.md` first. It holds the user's brief, the process, the few fixed rules, and what is left
to your own judgment. `shorts/tao-ch3-sage-government/` is the approved reference: copy the shape of its
`short.json`, and read its `DELIVERY.md` for the choices made.

## The two stages

**1. Transcript.** Fetch the 480p source, transcribe the range the user gave, and propose a 2:00–3:00 transcript
(source times, words as heard, seconds, what's left out, optional lines). If an excerpt quotes the chapter, it
opens the Short. Then stop: build nothing until the user approves the transcript.

**2. Build.** From the repo root, `python3 -I pipeline/<script>.py <slug>`:

```
fetch_hires.py <slug> <4K webm url> <from_s> <to_s>
# write "segments" in shorts/<slug>/short.json (cuts in real pauses), then:
prog.py <slug>                 # word timings on the assembled cut; re-run after any change to segments
# write "phrases", "scenes", "collages" (images via museum.py search / get / proxy), then:
scenes.py build <slug>
head.py <slug>
hdr.py check <slug>            # must pass; look at .work/<slug>/colour_check.jpg
scenes.py draft <slug>         # look at every sheet before rendering
audio.py <slug>
scenes.py render <slug>        # background; about 10-15 min
encode.py <slug>
```

## Do not skip

- **Natural colour.** The 4K source is HDR. Run `hdr.py check` after `head.py`, and compare a head frame of the
  final mp4 with `docs/reference/head-colour-original.webp`. Measure; don't judge small stills by eye.
- **Subtitles at 73%** (`"caption_y": 0.73`), quotation marks around what he reads from the book, collage pieces
  above 64% of the height.
- **Check the cut** by re-transcribing it, and tell the user which joins to listen to: you can't hear audio.
- **Finish:** `DELIVERY.md`, `images.json`, the release schedule (`schedule.py mark` and `status`, see
  `CLAUDE.md`), commit and push, send the mp4, and report differences from the approved transcript.

Everything else (which lines get an image or a collage, which artworks, layouts, motion) is your call. If the
brief and the guide don't cover something, ask the user.
