# YouTube Shorts: Tao Te Ching readings

This repo turns David E. Arredondo's long-form readings of the Tao Te Ching (Thomas Cleary translation) into vertical Shorts, all in one consistent house style.

- There are two kinds of Short:
  - **Reading Shorts:** "make a short of the reading of ch N". One chapter read straight through, captioned line by line, in the fixed look of `shorts/tao-ch1-gateway-of-marvels/`. Follow the `reading-short` skill (`.claude/skills/reading-short/SKILL.md`). The style is in `docs/reading-style.md` and the pipeline is `pipeline/reading.py`.
  - **Teaching Shorts:** one teaching cut from his commentary, with paintings. Follow the `make-short` skill (`.claude/skills/make-short/SKILL.md`). Each comes with two thumbnails and 10 title suggestions.
- Teaching-Short house style: `docs/style-guide.md`. Change it there, never one Short at a time.
- Teaching reference Short: `shorts/tao-ch4-unimpeded-harmony/`. Its `short.json` is a complete spec to copy.
- Pipeline: `pipeline/` (run from the repo root with `python3 -I pipeline/<script>.py <slug>`). Intermediates and the museum image cache live in `.work/`, which is git-ignored.
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
