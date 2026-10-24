# Style guide: Tao Te Ching reading Shorts

A reading Short is one chapter of the Tao Te Ching (Thomas Cleary's translation), read straight through by David E. Arredondo, captioned line by line. It is a different format from the teaching Shorts in `docs/style-guide.md`: no images, no re-cutting, just the reading. The reference is `shorts/tao-ch1-gateway-of-marvels/` (approved; its `reading.json` is locked). Every reading Short looks exactly like it, and `pipeline/reading.py` holds every value below. Change the look there and here together, never one Short at a time.

## Content
- The whole chapter, in one continuous take from the video, exactly as he reads it. Nothing is cut out of the middle.
- Source: the channel's archive.org items (`identifier:arredondo-*`, Tao Te Ching). Each item's description lists `M:SS Chapter N | Title` and then the chapter's Cleary text, line by line. That text is the caption text.
- If he announces the chapter right before reading ("Chapter one, a way can be a guide."), the Short opens on that, with a "Chapter One" caption and the chapter title as a caption ending in "…". If the announcement comes with an aside ("one of the best known, by the way… I'm sorry, When Everyone Knows"), the Short opens on the first line instead.
- It starts about 0.75 s before the first word, with no earlier speech, and ends about 2.3 s after the last word, before he speaks again.

## Frame (1080×1920, 30 fps)
- Background: the same shot, scaled to fill 9:16, Gaussian blur σ 30, brightness −0.18, saturation 0.8.
- Speaker: a 440×480 crop of the source (scaled to 480 px high), centred on his face (`crop_x`, from face detection), scaled to 1080×1178 (Lanczos) with contrast 1.04 and saturation 1.05. It's placed at y = 400, with its top 90 px and bottom 160 px feathered into the background.
- Title block, top-centred, for the whole reading:
  - kicker "TAO TE CHING  ·  CHAPTER N": Inter SemiBold 40 px, letter-spaced, pale gold
  - title: Caladea Bold 86 px, white, soft shadow. A single-chapter video's own quoted title ("The Gateway of Marvels"), otherwise the chapter title from the description. A long title shrinks to 64 px, then takes two lines.
  - credit "read by dr.a  ·  trans. Thomas Cleary": Inter Italic 32 px, light grey
- Fades in over 0.4 s at the start.

## Captions
- Inter ExtraBold 68 px, white, 6 px dark outline plus a 3 px shadow, bottom-aligned 400 px above the bottom of the frame (over his chest).
- The first and last captions are gold (#FFD860). All others are white.
- One caption per phrase: each description line, split at an inner `,` `;` or `:` when both sides have at least two words. A phrase of 8 or more words (or wider than 1400 px) becomes two captions, split where he pauses or before a connective ("the", "but", "is"…).
- A caption wider than 900 px takes two lines at the most balanced break. Line breaks are explicit (`\N`, WrapStyle 2), so a caption never reflows while it's on screen. There's no pop or scale animation, only a 100 ms fade-in.
- The text is the description's Cleary text verbatim (case and punctuation), apart from the spoken header captions.
- **Sync:** each caption appears on the moment his voice starts the phrase (40 ms lead for the fade) and stays until the next one. Whisper's word starts are not trusted on their own: they can sit up to 0.9 s early in the silence before a word, or on the tail of the word before. `Env.onset` snaps every caption to the rise in the audio envelope. `reading.py qa` re-checks every caption and flags any that open on room tone (early) or well after a rise (late).
- The title block and the last caption fade out 0.1 s before the reading ends, so the frame that dissolves into the end card is clean.

## Sound
- The original voice: loudness-normalised (loudnorm I −14 LUFS, true peak −1.5 dBTP, LRA 11), with a 0.3 s fade in and a 0.4 s fade out. No music. Silence on the end card.

## End card (house, 4 s)
- The held last frame dissolves into the rice-paper card over 15 frames. It's the same card as every Short (`pipeline/render.py: build_endcard`): the seal, "David E. Arredondo", "Readings from the Tao Te Ching · Thomas Cleary translation", and YouTube @DavidEArredondo / X @davidarredondo. It has a 1.03× to 1.00× zoom-out.

## Output
- `shorts/<slug>/<slug>.mp4`: H.264 CRF 18, AAC 192k at 48 kHz, faststart. It is git-ignored, so send it to the user directly. The commit is `shorts/<slug>/reading.json`.
- Most chapters run 40–90 s. YouTube treats anything up to 3 minutes as a Short. `render` warns if it's longer.
