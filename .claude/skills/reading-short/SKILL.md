---
name: reading-short
description: Make a "reading" Short, in the exact look of the approved Chapter 1 Short (full-frame 4K close-up, rounded title box, line-by-line captions synced to his voice, house end card). The Short is one Tao Te Ching chapter read straight through by David E. Arredondo, found on the archive.org channel. Use when the user asks for "a short of the reading of ch N", "the reading of chapter N", or to fix or re-render a reading Short. Not for teaching Shorts with paintings (that's make-short).
---

# Make a reading Short

Read `docs/reading-style.md` first. The look is fixed and lives in `pipeline/reading.py`, so don't restyle a single Short. The reference is `shorts/tao-ch1-gateway-of-marvels/`. Everything runs from the repo root.

## 0. Environment (once per session)
- `pip install -r pipeline/requirements.txt` (faster-whisper, OpenCV 4.10, numpy, pillow).
- Fonts: Inter and Caladea must be installed system fonts (`fc-list | grep -E "Inter|Caladea"`), and EB Garamond is in `assets/fonts` for the end card. `render` stops if a font is missing.
- Network: `archive.org` (search, metadata, download, and HTTP range reads of the 4K WebM), plus `huggingface.co` and `*.hf.co` for the whisper models. If a download gets a proxy 403, tell the user which host to allow.

## 1. Find and download
```
python3 -I pipeline/reading.py find <N>
```
- This searches the channel's Tao Te Ching items and picks the one whose description has `Chapter N | Title` with its text. It prefers the chapter-by-chapter series ("Chap." / "Chaps.") and lists any other item that also reads the chapter. Downloads go to `.work/<slug>/source.mp4` (about 100–300 MB).
- If several items read the chapter, the series video is the default. Mention the alternatives, and use `--item <identifier>` if the user wants another.
- It writes `shorts/<slug>/reading.json`: the slug, title, Cleary text and section times. The title is a single-chapter video's own quoted title, otherwise the chapter title.

## 2. Align
```
python3 -I pipeline/reading.py align <slug> [--take N]
```
- This transcribes the chapter's whole section (small.en), lists every complete read-through as `take 1`, `take 2`…, and uses the last one: he usually reads a chapter twice and prefers the later reading (`--take N` picks another). If there's only one take, it uses that. Line-by-line passes with commentary don't count as takes. Tell the user which take you used.
- It then times the take (medium.en), snaps every caption onset to the voice, picks the clip and the face position, and prints the captions next to what was heard. It takes about 3–5 minutes per chapter (the section is transcribed once and cached).
- Read the table:
  - **Coverage under 85%** or **`<- CHECK`** lines: he skipped, repeated or changed words. Transcribe the stretch on its own (`reading.whisper(slug, "small.en", lo, hi)`) to tell a harmless slip from a misread he stops and corrects (cut that, below).
  - **A dropped or reordered word:** expected, and fine. The caption always keeps the official text from the description, and there's nothing to raise.
  - **A misread he corrects** (a long gap between two captions is the sign): cut it. Add `"cuts": [[a, b]]` in source seconds, with `a` in the pause after the last good line (leave about 1 s of pause) and `b` in the gap just before the corrected line, checked on the envelope. Record why in `notes`.
  - **Header:** "Chapter N" and the title caption are added only when he announces the chapter within about 12 s before the first line.
  - **Captions:** check the splits and line breaks read naturally. Edit `captions[].text` if a break is clumsy (`\N` is the line break).
  - **The ending:** check that the clip ends after his last word and before he speaks again.
- A locked spec (`"locked": true`, an approved Short) refuses to align. Use `--force` only if the user wants it re-timed. `cuts` and `notes` survive a re-align.

## 3. Render and QA
```
python3 -I pipeline/reading.py render <slug>     # fetches the clip's window of the 4K WebM (~100 MB), about 2 min
python3 -I pipeline/reading.py qa <slug>
```
- `qa` prints every caption as `ok`, `early` (it opens on room tone) or `late` (his voice started well before it). For each flagged line:
  - Look at the envelope and the words around it.
  - Transcribe a short stretch around it (`reading.whisper(slug, "small.en", lo, hi)`), since context changes where whisper puts words.
  - Set the right `t` in `reading.json`, then render again.
  - Repeat until `qa` says all captions are on the voice.
- Look at `.work/<slug>/qa_sheet.jpg`:
  - his face is centred in the crop, and his head stays in frame through the whole clip
  - the title box is symmetric and the title fits
  - any cut's dissolve is clean
  - two-line captions sit cleanly
  - the dissolve is clean, with no leftover caption
  - the end card shows @DavidEArredondo and @davidarredondo
- You can't hear the audio. Say so, and ask the user to watch it once with sound.

## 4. Deliver and commit
- Send `shorts/<slug>/<slug>.mp4` with SendUserFile.
- In the message, give the source video, the timestamps used, the length, and anything you had to decide (another item, a header skipped, a fixed onset).
- Commit `shorts/<slug>/reading.json` (the mp4 is git-ignored) and push to the session's branch. Once the user approves the Short, set `"locked": true` in its spec and commit again.
