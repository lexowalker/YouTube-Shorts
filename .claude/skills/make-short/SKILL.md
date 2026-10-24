---
name: make-short
description: Make a vertical YouTube Short from one of David E. Arredondo's Tao Te Ching reading videos, in this repo's house style (EB Garamond captions, CMA ink paintings, rice-paper end card, untouched voice), plus two thumbnails and 10 title suggestions. Use whenever the user points to a video (usually a release asset in this repo) and asks for a Short, or asks to re-cut or fix an existing one. Not for "the reading of ch N" (use reading-short).
---

# Make a Short

The house style is in `docs/style-guide.md`, so read it first. `shorts/tao-ch1-passionless-subtle/` is the reference Short: its `short.json` is a complete, working spec to copy from, and its `DELIVERY.md` notes why each image and cut was chosen. (The first Short, `tao-ch4-unimpeded-harmony`, still has an opening title and the older 480p head shots.) Everything runs from the repo root, and scripts are run with `python3 -I pipeline/<script>.py <slug> …`.

## Deliverables
1. `shorts/<slug>/<slug>.mp4`, 1080×1920, 60–120 s (aim for 70–90 s). Not committed (`*.mp4` is git-ignored); send it to the user with SendUserFile.
2. Ten title suggestions that would grip a general YouTube audience, with one recommended (in chat and in `DELIVERY.md`; see "Titles" in the style guide).
3. A one-sentence statement of the teaching, with its chapter.
4. The source timestamps used, in order.
5. The image list: file, source URL, license and timestamp in the Short (`images.json` plus the table).
6. A short note on what was chosen and why.
7. `thumbnails/thumbnail_face.jpg` and `thumbnails/thumbnail_book_cover.jpg`.

## 0. Environment (once per session)
- `pip install -r pipeline/requirements.txt`. OpenCV must stay at 4.10, because 5.x has no Haar cascades.
- The network policy must allow `huggingface.co`, `*.hf.co` (Xet CDN: `us.aws.cdn.hf.co`, `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co`, `transfer.xethub.hf.co`), `openaccess-api.clevelandart.org`, `openaccess-cdn.clevelandart.org` and `m.media-amazon.com` (book cover). If a download fails with a proxy 403, tell the user exactly which host to add. Don't work around it.
- Fonts are committed in `assets/fonts`, so there's nothing to fetch.

## 1. Source
- The user usually names a release tag on this repo. Find the asset's `browser_download_url` and `digest` with the GitHub MCP `get_release_by_tag`, then:
  `python3 -I pipeline/fetch_source.py <slug> <url> <sha256>`.
- Pick a short, descriptive slug, such as `tao-ch5-straw-dogs`.
- If the source is one of the channel's archive.org items (`pipeline/reading.py find <N>` locates a chapter's), link or download its 480p MP4 as `.work/<slug>/source.mp4`. Once the segments are chosen, fetch the 4K window for sharp head shots: `python3 -I pipeline/fetch_hires.py <slug> <webm url> <from_s> <to_s>`, with a few seconds of margin. Render, preview, audio, crop_track and the face thumbnail then use it automatically. Set `"caption_y": 0.83` in the spec, because the 4K close-up puts his beard at the default 70%.

## 2. Read the whole video
- `python3 -I pipeline/transcribe.py <slug> full` (small.en, a few minutes; use `--model medium.en` for accuracy, about 30 min for 20 min of audio). Run it in the background and read `.work/<slug>/transcript.txt` as it fills.
- Look at a few frames (`ffmpeg -ss T -i .work/<slug>/source.mp4 -frames:v 1`) for the set, framing and the moment David holds up the book.

## 3. Choose the teaching (ask)
Propose 2–3 candidate teachings, each with a rough cut (source ranges, hook line, ending line, about how many seconds), and recommend one. Use AskUserQuestion. Also confirm anything unusual, but don't re-ask settled house-style questions such as font, accent, ambient bed or end card.

Once the user picks a teaching, write out the **full proposed transcript**: every line in order, as it will be heard, with its source time, and what's left out. The user reviews it for coherence and for whether it captures the essence of the teaching. Don't cut, choose images or render until they approve it.

## 4. Word timings and cut points
- `python3 -I pipeline/transcribe.py <slug> words a:b c:d …` (medium.en) over the chosen ranges with a little margin.
- Scan for low-probability words and mis-hearings, such as "whole." for "harmony.". Fix them with `word_fixes`, or re-run a range with `--no-prompt` if whisper skipped a sentence that repeats the prompt.
- Before writing the phrases, cross-check each chosen passage with `large-v3` (`WhisperModel("large-v3")`, `condition_on_previous_text=False`, no prompt). It hears stutters ("where where", "the the"), false starts ("But you can, there's a way") and fillers that medium.en smooths over. Take its *text*, not its timings (they run early), and record each correction as a `word_overrides` entry with the timings read off `env.py`. When the passes disagree on a word you'd have to show, prefer cutting or hiding over guessing.
- Range transcriptions can stretch one word over a filler they missed. On the reference Short, "hard" swallowed "you know". `qa.py --audio-only` (step 6) catches this with an independent long-context pass. When it does, re-run that stretch with `transcribe.py words <wider range> --no-prompt` and confirm with `env.py`.
- Fillers ("you know", "um") that sit inside a sentence stay in the audio when cutting them would leave a jump. Leave them off the captions with `~` tokens in the phrase (`"There's no ~you ~know hard | *lines in nature"`), so the shown words still appear on their true onsets.
- Place every cut in a real pause: `python3 -I pipeline/env.py <slug> <t> …`. Leave about 0.3 s of room tone around each join and a little more where a line should land.
- Drop ums, false starts and asides. Never cut mid-word.

## 5. Images
- Search with `pipeline/cma.py search "<subject>" --type Painting` (or `--dept "Chinese Art"`) or `cma.py title "<title>"`. Compare candidates with `cma.py sheet <acc> …` (print-size previews, no full download; some masters are over a gigabyte). Then fetch the chosen ones with `cma.py get <accession> …` and look at `cma.py proxy <accession>` (it has a 10% grid) to choose crops.
- **Plan the images from the words first.** Before searching, list each line you'll put an image on, the concrete thing it names, and the picture of that thing (see "Images" in `docs/style-guide.md`). Search for that picture, not for a mood. The user's rule: what he's saying must match what's on screen. A lust line gets lovers, a bell line gets a bell, a study line gets someone reading, not a landscape.
- Scrolls are the default (Taoist, simple, natural). If none shows the thing, use another simple, natural artwork rather than a scroll that doesn't fit. Search beyond `--type Painting` (`cma.py search "bell"` finds bronzes and prints too).
- Worldly states (anger, passion, lust, anxiety, striving) get turbulent or worldly imagery that contrasts with the Way; quiet imagery returns when he returns to stillness.
- Modern subjects (a car, a bus, a phone) get a classical stand-in that keeps the meaning, such as a groomed horse for "my beautiful car" or stampeding horses for "run over by a bus", or stay on David's face.
- Place each image on the word that names its subject (`"at": {"word": "...", "after": <phrase index>}`), not at the start of the phrase, and end it when he moves on to something else.
- Check the date and culture (classical only), and that the crop lands on the subject with negative space and avoids screen-panel seams.
- No shot under about 1.2 s, and no head shot that is only a pause between two images: extend the image or merge the shots.
- Fewer, longer images: let one image carry consecutive lines on the same idea instead of cutting to a new picture for each noun (the user dropped the bell in the Ch1 Discussion 1 Short and let the watching scholar carry "hear that bell").
- Centre the subject and keep its focal point (an eye, the faces) at least about 10% inside every edge, since the zoom starts 1.08× in. Check each crop on the proxy with the start-of-zoom box drawn on it before building.
- Crops in `short.json` are fractions of the image: `x0`, `y0` (top-left) and `h` (crop height). Width follows from 9:16.

## 6. Spec and EDL
Write `shorts/<slug>/short.json`, copying the reference: `segments`, `phrases` (2-line chunks with one `*key` word), `cuts` (anchored to phrases, words or segment joins), `title` (optional), `endcard`, `word_fixes` and `onset_fixes`. Then:

```
python3 -I pipeline/build_edl.py <slug>     # asserts every caption word == spoken word; prints pacing
python3 -I pipeline/crop_track.py <slug>    # smoothed face-following crop
python3 -I pipeline/preview.py <slug>       # look at preview_images.jpg and preview_heads.jpg before rendering
python3 -I pipeline/audio.py <slug>         # untouched voice, clean joins, pause-only de-click, peak -1 dBTP
python3 -I pipeline/qa.py <slug> --audio-only   # re-transcribe the assembled audio: fix every caption miss before rendering
python3 -I pipeline/draft.py <slug>         # ~1.5 min: the exact frames at every caption, shot and join, with flags
python3 -I pipeline/render.py <slug>        # ~4 min for 90 s from 4K (4 chunks in parallel); run in the background
python3 -I pipeline/encode.py <slug>
python3 -I pipeline/qa.py <slug>
```

**Always run `draft.py` and look at its sheets before `render.py`.** It composes, with the renderer's own code, the
frames that show most mistakes, and flags these automatically:
- **BRIGHT:** a caption on a light background, such as his white beard or pale paper. Move it with `caption_y`, or change the crop.
- **JUMP:** a join on a head shot with nothing over it.
- **BLIP:** a shot under 1.2 s, a flash of him or of a painting that breaks the flow. Merge it into a neighbour.
- **DEAD:** more than 0.8 s with nothing said across a join (it shows as a stray shot of him silent). Tighten the segment ends.

Check the sheets yourself as well, for bad crops, a face cut off, or an image on the wrong word: read each image tile's caption against the picture and ask whether it shows what he is saying. Fix everything, rebuild and draft again. Only then run the full render. A full render costs minutes; finding the problem after it means a second render.

## 7. QA (fix before the user sees it)
- `qa.py` re-transcribes the finished audio, and its long context often hears fillers the range pass missed. Every caption word must match, and fillers marked `~` count as matched. For each flagged onset, read the dB envelope it prints: if the voice really starts where the caption does, it's fine; otherwise add an `onset_fixes` entry and rebuild.
- Look at `.work/<slug>/qa_sheet.jpg` and a few full-size frames, checking:
  - captions are legible on the sweater and on every image (pale paper is the usual culprit)
  - his face is well framed
  - no image arrives before its word
  - no visible jump cut
  - every image shows what he is saying at that moment, with its subject centred and its focal point (an eye, faces) well inside the frame
  - every fade from his face into an image plays over him still moving: no frozen frame, and no stray shot of him in between
  - no half-second flashes of him or of a painting, and no image changes the line doesn't need
  - the end card is correct, showing **@DavidEArredondo** and **@davidarredondo**
- Check that no mode runs over about 12 s (`build_edl.py` warns), the length is 60–120 s, and the true peak is ≤ −1 dBTP.
- You can't hear the audio. Say so in the delivery and ask the user to listen once.

## 8. Thumbnails
- `python3 -I pipeline/thumbs.py faces <slug>`, then view `face_sheet.jpg`. Step through the best few at 0.25 s for eyes open toward the camera and mouth at rest. Then run `thumbs.py face <slug> <seconds>`.
- Book cover: `curl -A "Mozilla/5.0" -o .work/<slug>/cover.jpg "https://m.media-amazon.com/images/P/0062502166.01.LZZZZZZZ.jpg"`, then `thumbs.py cover <slug> .work/<slug>/cover.jpg`. If David reads a different edition, find it from the frame where he shows the book.

## 9. Write-up and commit
- `python3 -I pipeline/notes.py <slug>` prints the timestamp and image tables and writes `images.json`. Write `shorts/<slug>/DELIVERY.md` in the same shape as the reference: hook title, the teaching, timestamps, images, notes on choices, and the 10 titles.
- Update the release schedule (see "Release schedule" in CLAUDE.md). A teaching Short is the chapter's Discussion 1 (its main teaching) or Discussion 2 (a second point, or another presentation of the first): `python3 -I pipeline/schedule.py mark <N> <d1|d2> <"In progress"|Ready> --title "<recommended title>" --note "<the teaching>"`, then `python3 -I pipeline/schedule.py status`. Tell the user the verdict, the buffer and what's due next.
- Commit `shorts/<slug>/` (the spec, EDL, images.json, DELIVERY.md and thumbnails; the mp4 is git-ignored) and `docs/release-schedule.xlsx`, and push to the session's branch. `.work/` is git-ignored too.
- Give the user the mp4 and thumbnails (SendUserFile) and the 10 titles in chat.

## Gotchas
- `pgrep -f`/`pkill -f` patterns match the shell running them. To wait on a job, use the background task notification, not a `pgrep` loop.
- Wikimedia Commons rate-limits (429) from here, so prefer CMA.
- Big CMA TIFFs sometimes drop mid-transfer. `cma.py get` retries, and you should check that the file opens.
- faster-whisper's own decoder breaks with the installed PyAV, so `transcribe.py` reads the 16 kHz WAV itself.
- A quick glance aside can pull his face off-centre faster than the smoothed crop follows (see the first QA frame). Pin that segment with `"crop_fixes": [{"seg": i, "left": px}]` in `short.json` and re-run `crop_track.py`.
- A jump cut between two head segments is never left visible. Put an image over it, or put the image cut on the join itself.
