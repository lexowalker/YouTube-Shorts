# Style guide: Tao Te Ching reading Shorts

A reading Short is one chapter of the Tao Te Ching (Thomas Cleary's translation), read straight through by David E. Arredondo, captioned line by line. It is a different format from the teaching Shorts in `docs/style-guide.md`: no images, no re-cutting, just the reading. The reference is `shorts/tao-ch1-gateway-of-marvels/` (approved in this full-frame look; its `reading.json` is locked). Every reading Short looks exactly like it, and `pipeline/reading.py` holds every value below. Change the look there and here together, never one Short at a time.

## Content
- The whole chapter in one continuous reading from the video, as he reads it.
- Source: the channel's archive.org items (`identifier:arredondo-*`, Tao Te Ching). Each item's description lists `M:SS Chapter N | Title` and then the chapter's Cleary text, line by line. That text is the caption text.
- **Takes:** when he reads the chapter through more than once, use the second complete take, which is usually his better one (`align --take`, default 2). Line-by-line passes with commentary between the lines aren't takes. In the videos checked so far (Chapters 1–3), each chapter has one complete read-through, followed by a line-by-line pass. The extra "takes" are false starts that he abandons and restarts, so the complete reading is the one to use.
- **Slips:** a misread that he corrects ("Action without contrivance… Actually, action being without contrivance…") is cut out (`cuts` in the spec). Each cut sits in a pause: the audio joins with 12 ms fades and the picture dissolves over 6 frames, so there's no jump on his face. Nothing else is cut.
- If he announces the chapter right before reading ("Chapter one, a way can be a guide."), the Short opens on that, with a "Chapter One" caption and the chapter title as a caption ending in "…". If the announcement comes with an aside ("one of the best known, by the way… I'm sorry, When Everyone Knows"), the Short opens on the first line instead.
- It starts about 0.75 s before the first word, with no earlier speech. It ends about 2.3 s after the last word, or 0.2 s before he speaks again if that comes sooner.

## Frame (1080×1920, 30 fps)
- **Picture:** full frame, with no blurred backdrop and no vignette. A full-height 9:16 crop of the item's 4K video (3840×2160 VP9 WebM, about 1215×2160 before scaling), centred on his face (`face_x`, from face detection), scaled to 1080×1920 (Lanczos) with contrast 1.04 and saturation 1.05. Only the clip's window is fetched (`ffmpeg -ss … -c copy` over HTTP). Its exact start is found by matching its audio against `source.mp4`, and it uses its own audio and picture together. If an item has no high-resolution file, the 480p crop is used, with a warning that it will look soft.
- **Title box:** a rounded rectangle (radius 22) of black at about 62% opacity, 880 px wide at x 100, top at y 110, fading with the text. Inside it, centred:
  - kicker "TAO TE CHING  ·  CHAPTER N": Inter SemiBold 40 px, letter-spaced, pale gold
  - title: Caladea Bold 86 px, white, soft shadow, 34 px below the kicker. A single-chapter video's own quoted title ("The Gateway of Marvels"), otherwise the chapter title from the description. A long title shrinks to fit 768 px (down to 64 px), then takes two lines and the box grows.
  - padding: 56 px above the kicker's capitals and 56 px below the title's baseline, so the box is symmetric.
- No credit line.
- Fades in over 0.4 s at the start.

## Captions
- Inter ExtraBold 68 px, white, 6 px dark outline plus a 3 px shadow, bottom-aligned 265 px above the bottom of the frame (on his sweater, below the beard).
- The first and last captions are gold (#FFD860). All others are white.
- One caption per phrase: each description line, split at an inner `,` `;` or `:` when both sides have at least two words. A phrase of 8 or more words (or wider than 1400 px) becomes two captions, split where he pauses or before a connective ("the", "but", "is"…).
- A caption wider than 900 px takes two lines at the most balanced break. Line breaks are explicit (`\N`, WrapStyle 2), so a caption never reflows while it's on screen. There's no pop or scale animation, only a 100 ms fade-in.
- The text is the description's Cleary text verbatim (case and punctuation), apart from the spoken header captions. If he drops or reorders a word (Chapter 3: "Not putting prices…", "dare not to contrive"), the caption keeps Cleary's text, and the change is reported to the user.
- **Sync:** each caption appears on the moment his voice starts the phrase (40 ms lead for the fade) and stays until the next one. Whisper's word starts are not trusted on their own: they can sit up to 1.2 s early in the silence before a word, or on the tail of the word before. `Env.onset` finds the word's clearly voiced core and steps back over its soft start. Noise blips in the room tone can't pass for speech. Across 26 checked onsets in Chapters 1–3 it averages 0.07 s, and no caption is more than 0.06 s early. `reading.py qa` re-checks every caption and flags any that open on room tone (early) or well after a rise (late).
- The title box and the last caption fade out 0.1 s before the reading ends, so the frame that dissolves into the end card is clean.

## Sound
- The original voice: loudness-normalised (loudnorm I −14 LUFS, true peak −1.5 dBTP, LRA 11), with a 0.3 s fade in and a 0.4 s fade out. No music. Silence on the end card.

## End card (house, 4 s)
- The held last frame dissolves into the rice-paper card over 15 frames. It's the same card as every Short (`pipeline/render.py: build_endcard`): the seal, "David E. Arredondo", "Readings from the Tao Te Ching · Thomas Cleary translation", and YouTube @DavidEArredondo / X @davidarredondo. It has a 1.03× to 1.00× zoom-out.

## Output
- `shorts/<slug>/<slug>.mp4`: H.264 CRF 18, AAC 192k at 48 kHz, faststart. It is git-ignored, so send it to the user directly. The commit is `shorts/<slug>/reading.json`.
- Most chapters run 40–90 s. YouTube treats anything up to 3 minutes as a Short. `render` warns if it's longer.
