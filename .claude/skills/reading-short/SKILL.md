---
name: reading-short
description: Make a "reading" Short, in the exact look of the approved Chapter 1 Short (blurred backdrop, centred speaker, title block, line-by-line captions synced to his voice, house end card). The Short is one Tao Te Ching chapter read straight through by David E. Arredondo, found on the archive.org channel. Use when the user asks for "a short of the reading of ch N", "the reading of chapter N", or to fix or re-render a reading Short. Not for teaching Shorts with paintings (that's make-short).
---

# Make a reading Short

Read `docs/reading-style.md` first. The look is fixed and lives in `pipeline/reading.py`, so don't restyle a single Short. The reference is `shorts/tao-ch1-gateway-of-marvels/`. Everything runs from the repo root.

## 0. Environment (once per session)
- `pip install -r pipeline/requirements.txt` (faster-whisper, OpenCV 4.10, numpy, pillow).
- Fonts: Inter and Caladea must be installed system fonts (`fc-list | grep -E "Inter|Caladea"`), and EB Garamond is in `assets/fonts` for the end card. `render` stops if a font is missing.
- Network: `archive.org` (search, metadata, download), plus `huggingface.co` and `*.hf.co` for the whisper models. If a download gets a proxy 403, tell the user which host to allow.

## 1. Find and download
```
python3 -I pipeline/reading.py find <N>
```
- This searches the channel's Tao Te Ching items and picks the one whose description has `Chapter N | Title` with its text. It prefers the chapter-by-chapter series ("Chap." / "Chaps.") and lists any other item that also reads the chapter. Downloads go to `.work/<slug>/source.mp4` (about 100–300 MB).
- If several items read the chapter, the series video is the default. Mention the alternatives, and use `--item <identifier>` if the user wants another.
- It writes `shorts/<slug>/reading.json`: the slug, title, Cleary text and section times. The title is a single-chapter video's own quoted title, otherwise the chapter title.

## 2. Align
```
python3 -I pipeline/reading.py align <slug>
```
- This finds the read-through (small.en), times it (medium.en), snaps every caption onset to the voice, picks the clip and the face crop, and prints the captions next to what was heard. It takes about 2 minutes.
- Read the table:
  - **Coverage under 85%** or **`<- CHECK`** lines: he skipped, repeated or changed words, or read the chapter in pieces with commentary between. If he only paraphrases a word, the caption keeps Cleary's text. If he reads a different line, or the reading isn't continuous, tell the user what you found and ask before going on.
  - **Header:** check whether "Chapter N" and the title caption were added. They're added only when he announces it within about 12 s before the first line. If he announced it with an aside, starting on the first line is right.
  - **Captions:** check the splits and line breaks read naturally. Edit `captions[].text` in `reading.json` if a break is clumsy (`\N` is the line break).
- A locked spec (`"locked": true`, an approved Short) refuses to align. Use `--force` only if the user wants it re-timed.

## 3. Render and QA
```
python3 -I pipeline/reading.py render <slug>     # about 1-2 min
python3 -I pipeline/reading.py qa <slug>
```
- `qa` prints every caption as `ok`, `early` (it opens on room tone) or `late` (his voice started well before it). For each flagged line:
  - Look at the envelope and the words around it.
  - Transcribe a short stretch around it (`reading.whisper(slug, "small.en", lo, hi)`), since context changes where whisper puts words.
  - Set the right `t` in `reading.json`, then render again.
  - Repeat until `qa` says all captions are on the voice.
- Look at `.work/<slug>/qa_sheet.jpg`:
  - his face is centred in the crop
  - the title fits, with no overlap
  - two-line captions sit cleanly
  - the dissolve is clean, with no leftover caption
  - the end card shows @DavidEArredondo and @davidarredondo
- You can't hear the audio. Say so, and ask the user to watch it once with sound.

## 4. Deliver and commit
- Send `shorts/<slug>/<slug>.mp4` with SendUserFile.
- In the message, give the source video, the timestamps used, the length, and anything you had to decide (another item, a header skipped, a fixed onset).
- Commit `shorts/<slug>/reading.json` (the mp4 is git-ignored) and push to the session's branch. Once the user approves the Short, set `"locked": true` in its spec and commit again.
