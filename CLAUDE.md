# YouTube Shorts: Tao Te Ching readings

This repo turns David E. Arredondo's long-form readings of the Tao Te Ching (Thomas Cleary translation) into vertical Shorts, all in one consistent house style.

## Start here: every Short is one of the two kinds below

When the user asks for "a short" in any wording, it is **always** either a Reading Short or a Teaching Short, made with that kind's skill, pipeline and style doc. Never design a new look, write a one-off build script, or start from scratch. If something the style can't handle comes up (e.g. a new source format), fix it in `pipeline/` and the style doc so every later Short gets it too.

- Pick the kind:
  - "reading of ch N", "chapter N read through" → **Reading Short** (`reading-short` skill).
  - A teaching, a discussion, a point he makes, a video or timestamp to cut from, "Discussion 1/2" → **Teaching Short** (`make-short` skill).
  - Just "make a short" or "the next short" → run `python3 -I pipeline/schedule.py status`, take the next Short due that isn't made, tell the user which one (chapter, Reading / D1 / D2, date) and make it with that kind's skill.
  - Still ambiguous → ask one question: "Reading of chapter N, or a teaching Short?"
- Load the skill first (Skill tool, or read its `SKILL.md`), then its style doc, then copy the reference Short's spec. Don't skip this even for a "quick" Short.
- Check `shorts/` before making a Short: if that chapter's Reading / D1 / D2 already exists, say so and ask before making another.
- Keep `main` the source of truth. New sessions start from `main`, so a Short or a style change that stays on a side branch is invisible to them. Once the user approves a Short or a style change, merge it into `main`.

- There are two kinds of Short:
  - **Reading Shorts:** "make a short of the reading of ch N". One chapter read straight through, captioned line by line, in the fixed look of `shorts/tao-ch1-gateway-of-marvels/`. Follow the `reading-short` skill (`.claude/skills/reading-short/SKILL.md`). The style is in `docs/reading-style.md` and the pipeline is `pipeline/reading.py`.
  - **Teaching Shorts:** one teaching cut from his commentary, opening with the quoted text, with imagery keyed to his words. Follow the `make-short` skill (`.claude/skills/make-short/SKILL.md`). They run at least 2:00, and up to 3:00 is fine (YouTube's limit for a Short). Each comes with two thumbnails and 10 title suggestions.
- Teaching-Short house style: `docs/style-guide.md`. Change it there, never one Short at a time.
- Teaching reference Short: `shorts/tao-ch2-herd-thinking/` (approved, round 3). Its `short.json` is a complete spec to copy. Every teaching Short must match it on four points, which the pipeline enforces: identical 4K talking-head framing, captions at 66% height, the Tao Te Ching line first with quotation marks in the captions, and imagery keyed directly to the words (any real source). Earlier Shorts (`tao-ch1-*`, `tao-ch4-*`, `tao-ch5-*`) predate these rules.
- Pipeline: `pipeline/` (run from the repo root with `python3 -I pipeline/<script>.py <slug>`). Intermediates and the image cache live in `.work/`, which is git-ignored.
- Teaching-Short audio is the original recording, cut cleanly: joins in pauses with 12 ms fades, de-click only between words, and one static gain to a −1 dBTP peak. Never add denoise, EQ, compression or limiting; that made the first cut sound boxed in. (Reading Shorts keep their approved loudness normalisation; see `docs/reading-style.md`.)
- Source videos: every reading is on the channel's archive.org items (`pipeline/reading.py find` locates a chapter's). Some sources also arrive as release assets on this repo (e.g. tag `tao45`).

## Release schedule

`docs/release-schedule.xlsx` plans all 243 Shorts: three a week, one chapter a week, chapters 1–81 in order, from Fri 23 Oct 2026 (the Chapter 1 reading) to Wed 10 May 2028.

| Day | Short | Made with |
|---|---|---|
| Friday | **Reading**: the chapter read straight through | `reading-short` |
| Monday | **Discussion 1**: the chapter's main teaching from his discussion | `make-short` |
| Wednesday | **Discussion 2**: a second point he emphasizes, or a different presentation of Discussion 1 if there's only one | `make-short` |

The dates are formulas off the Settings tab (first release date, each type's offset, 7 days between chapters), so the whole plan shifts if those change. Never edit dates by hand.

**Every time a Short is made, update the schedule and check we're on track.** This is part of finishing a Short, not optional:

```
python3 -I pipeline/schedule.py mark <chapter> <reading|d1|d2> <status> --title "<title>" [--note "…"]
python3 -I pipeline/schedule.py status
```

- Status moves Planned → In progress → Ready (made and approved) → Scheduled (queued on YouTube) → Released. `mark` fills "Created on" when a Short first reaches Ready. When the user says a Short is approved, scheduled or out, mark it.
- The title is the YouTube title used (or recommended) for the Short. For a teaching Short, `--note` names which discussion it is (main teaching, or the second point).
- Commit `docs/release-schedule.xlsx` with the Short.
- Tell the user the `status` verdict:
  - **ON TRACK:** nothing overdue, and the next Short due is made or more than 2 days away.
  - **AT RISK:** a Short due within 2 days isn't made.
  - **BEHIND:** a release date has passed and that Short isn't marked Released.
- Also tell them the buffer (how many upcoming Shorts in a row are already made) and which Short is due next and when. If the user only made Shorts out of order (e.g. readings ahead), say what's still missing before the next release.
- The workbook's Settings tab shows the same at a glance (Overdue, Made but not yet released, On track?).
