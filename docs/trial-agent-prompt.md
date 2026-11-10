# Prompt for an agent making a trial-style Short

Copy everything below the line into a new session, then paste the transcript where it says so.

---

You're making a vertical YouTube Short (1080×1920) of Dr. David E. Arredondo teaching from the Tao Te Ching
(Thomas Cleary translation). Use the **trial style** in the repo `lexowalker/YouTube-Shorts`, on branch
`claude/compassionate-brown-zu6btm` (not `main`). Check out that branch first. Then read `CLAUDE.md`,
`docs/style.md` and `shorts/tao-ch2-bigotry-trial/` (the first trial Short: `short.json` is a complete spec to
copy, `DELIVERY.md` shows the expected write-up). Don't use `main`'s old house style. On this branch, the only
things kept from it are the subtitles and the end card.

## The transcript

[PASTE THE TIMESTAMPED TRANSCRIPT HERE: one excerpt per line, with source timestamps (mm:ss.s–mm:ss.s), in the
order they should play, and the source video if it isn't obvious.]

If I give you teachings or ideas instead of a finished transcript, first suggest excerpts from the video that
embody each one, in the order they appear, and wait for me to finalise them.
- Leave out ums, ahs, false starts and long gaps.
- If an excerpt quotes the Tao Te Ching text (e.g. a couplet) or Cleary's note, the Short starts with that excerpt.
- Aim for 2:00–3:00 in total.

With a finished transcript, go straight to making the video.

## The rules (the user's own; they're also in docs/style.md)

Every Short has five elements:

1. **Talking head:** Dr. Arredondo speaking, as in the original video.
   - Every head shot is cropped, framed and centred the same way.
   - Restore the natural colour. The archive.org uploads look washed out.
2. **Images, with very slight zoom or pan:**
   - Follow the moodboard in `moodboard/`: ancient East Asian iconography, statuary, woodblock prints, scrolls.
     Images can come from anywhere, but they must be high quality.
   - **Most important: each image is keyed to its words.** Birds' simplicity → woodblock birds. Disarray in a
     populace → a crowded city in disarray. Inflamed passions → an angry dragon or yokai. Abiding by the Way
     like the wind → leaves or branches in the wind. Picture and audio must make sense together.
   - Any zoom or pan is very light, slow and tasteful. Too much, or too fast, disorients the viewer.
3. **Animated collages,** in the style of the video "Motion Graphic | Collage" (youtu.be/CMqw9usH8-8),
   simpler and smaller for a portrait Short.
   - Each collage runs 5–15 s.
   - Balance black-and-white and colour.
   - Use simple animated movements of the pieces.
   - Build the collage up: a background and a couple of pieces first, then a couple more, then a couple more.
   - Collages follow the same keyed-to-the-words rule, with more freedom in imagery; they needn't follow the
     moodboard tightly.
4. **Subtitles** timed to the audio, in the same style as the teaching Shorts on `main` (already built into
   `pipeline/render.py`).
5. **The end card,** the same as the previous Shorts (already built in).

**Pacing:** every scene lasts a few seconds or more (at least 3 s). No quick, disorienting cuts.

## How the pipeline does it

Run each script from the repo root as `python3 -I pipeline/<script>.py <slug>`. First install the requirements:
`pip install -r pipeline/requirements.txt` and `pip install yt-dlp`.

1. **Source.**
   - `fetch_source.py <slug> <archive.org mp4 url>` fetches the 480p source.
   - Make `.work/<slug>/audio16k.wav` with ffmpeg (mono, 16 kHz).
   - `fetch_hires.py <slug> <webm url> <from_s> <to_s>` fetches a window of the 4K WebM covering every excerpt.
   - Get each item's file names from `https://archive.org/metadata/<item>`.
2. **Words.**
   - `transcribe.py <slug> words a:b c:d … --model medium.en` transcribes the excerpts.
   - Check each cut point against the audio envelope (`env.py`) so every join falls in a real pause.
   - Trim long pauses inside excerpts by splitting them into several segments.
   - If the transcriber puts a word inside a trimmed pause, correct its time with a `word_overrides` entry.
3. **Spec** (`shorts/<slug>/short.json`): segments, `word_overrides`, subtitle `phrases` (`|` splits the two
   lines, `*` marks the one highlighted word, `~` hides a spoken filler), `cuts` (head / image / collage, each
   anchored to a phrase) and `collages`. A collage piece can arrive on a spoken word:
   `"at": {"word": "Instagram", "after": 133}`.
4. **Images.**
   - `images.py met-search | cma-search | artic-search "<query>"`, then `get met:<id> | cma:<acc> | artic:<id>`,
     then `sheet <ids…>` to look at them.
   - The Met, Cleveland and the Art Institute of Chicago are CC0 and high resolution.
   - Wikimedia rate-limits this environment, so treat it as a last resort.
   - Collages use torn scraps of an image box, cut-outs (`"cut": true`), or paper shapes
     (`disc`, `plane`, `phone`, `tv`, `film`) filled with a colour or an image.
5. **Check.**
   - `build_edl.py` builds the edit and warns about any scene under 3 s.
   - `crop_track.py` sets one fixed head crop for the whole Short.
   - `storyboard.py` writes one exact frame per scene. Look at it and fix crops, faces hidden by collage pieces,
     and anything in the bottom fifth of a collage, where the subtitles go.
6. **Make.**
   - `audio.py` cuts the original sound with clean joins and one static gain.
   - `render.py --jobs 4` renders the video (about 20 min).
   - `encode.py` writes the delivery file.
   - Then make a ~15 MB phone copy for sharing:
     `ffmpeg -i <slug>.mp4 -vf scale=720:1280 -c:v libx264 -b:v 650k -c:a aac -b:a 96k` (two-pass).

## Lessons from the first trial Short

- The 4K sources are HDR (HLG). That is the washed-out look. `common.HDR_TO_SDR` converts them, and the
  renderer applies it automatically, so don't add saturation boosts.
- YouTube blocks downloads from the cloud machine, so you can't watch the collage reference. Work from these
  rules and the first trial Short's collages.
- The cut-out tool can punch holes in busy subjects (a fruit bowl). Use a torn scrap instead when it does.
- Keep collage pieces off faces, and keep the bottom fifth of the frame clear for subtitles.

## Finishing

- Write `shorts/<slug>/DELIVERY.md`: the transcript with source and Short times, a scene table saying what each
  image or collage is keyed to, and full image credits.
- Add a storyboard image.
- Commit and push to `claude/compassionate-brown-zu6btm` (the mp4s are git-ignored).
- Send me the full file and the phone copy.
- List the audio joins I should listen to.
- Don't mark trial Shorts in the release schedule unless I say one is approved for release.
- If a rule is unclear or something isn't covered, ask me rather than guessing.
