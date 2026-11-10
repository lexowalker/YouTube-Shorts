# YouTube Shorts: Tao Te Ching readings

This repo turns David E. Arredondo's long-form readings of the Tao Te Ching (Thomas Cleary translation) into vertical Shorts, all in one consistent house style.

## Start here: every Short is one of the three kinds below

When the user asks for "a short" in any wording, it is **always** a Reading Short, an image-and-collage teaching Short, or (only when asked for by name) an older 90-second painting Short, made with that kind's skill, pipeline and style doc. Never design a new look, write a one-off build script, or start from scratch. If something the style can't handle comes up (e.g. a new source format), fix it in `pipeline/` and the style doc so every later Short gets it too.

- Pick the kind:
  - "reading of ch N", "chapter N read through" → **Reading Short** (`reading-short` skill).
  - A teaching, a discussion, a point he makes, a video or time range to cut from, "Discussion 1/2", anything about images, collages or the moodboard → **image-and-collage teaching Short** (`collage-short` skill). This is the current style for teaching Shorts (approved 10 Nov 2026).
  - "The 90-second style", "the painting style", "like the Chapter 1 or 2 Discussion Shorts" → the older **painting Short** (`make-short` skill).
  - Just "make a short" or "the next short" → run `python3 -I pipeline/schedule.py status`, take the next Short due that isn't made, tell the user which one (chapter, Reading / D1 / D2, date) and make it with that kind's skill.
  - Still ambiguous → ask one question: "Reading of chapter N, or a teaching Short?"
- Load the skill first (Skill tool, or read its `SKILL.md`), then its style doc, then copy the reference Short's spec. Don't skip this even for a "quick" Short.
- Check `shorts/` before making a Short: if that chapter's Reading / D1 / D2 already exists, say so and ask before making another.
- Keep `main` the source of truth. New sessions start from `main`, so a Short or a style change that stays on a side branch is invisible to them. Once the user approves a Short or a style change, merge it into `main`.

- The kinds of Short:
  - **Reading Shorts:** "make a short of the reading of ch N". One chapter read straight through, captioned line by line, in the fixed look of `shorts/tao-ch1-gateway-of-marvels/`. Follow the `reading-short` skill (`.claude/skills/reading-short/SKILL.md`). The style is in `docs/reading-style.md` and the pipeline is `pipeline/reading.py`.
  - **Painting Shorts (the older teaching style):** one teaching cut from his commentary, with paintings. Follow the `make-short` skill (`.claude/skills/make-short/SKILL.md`). They run about 90 s. Each comes with two thumbnails and 10 title suggestions.
- **Image-and-collage teaching Shorts** (2:00–3:00): talking head, museum images keyed to his words, built-up paper collages, house subtitles and end card. Follow the `collage-short` skill (`.claude/skills/collage-short/SKILL.md`) and `docs/collage-style.md`. Reference: `shorts/tao-ch3-sage-government/`, approved 10 Nov 2026. Two stages: the transcript for the user's approval, then the build. Two things never to skip: prove the head shots were converted to natural colour (`pipeline/hdr.py check <slug>`), and keep the subtitles centred at 73% of the height so YouTube's overlay doesn't cover them.
- Teaching-Short house style: `docs/style-guide.md`. Change it there, never one Short at a time.
- Teaching reference Short: `shorts/tao-ch1-passionless-subtle/` (approved after three rounds of the user's notes: 4K head shots, no opening title, every image keyed to its words). Its `short.json` is a complete spec to copy. The first Short, `shorts/tao-ch4-unimpeded-harmony/`, predates those notes.
- Pipeline: `pipeline/` (run from the repo root with `python3 -I pipeline/<script>.py <slug>`). Intermediates and the museum image cache live in `.work/`, which is git-ignored.
- Teaching-Short audio is the original recording, cut cleanly: joins in pauses with 12 ms fades, de-click only between words, and one static gain to a −1 dBTP peak. Never add denoise, EQ, compression or limiting; that made the first cut sound boxed in. (Reading Shorts keep their approved loudness normalisation; see `docs/reading-style.md`.)
- Source videos: every reading is on the channel's archive.org items (`pipeline/reading.py find` locates a chapter's). Some sources also arrive as release assets on this repo (e.g. tag `tao45`).

## Release schedule

`docs/release-schedule.xlsx` plans all 243 Shorts: three a week, one chapter a week, chapters 1–81 in order, from Fri 23 Oct 2026 (the Chapter 1 reading) to Wed 10 May 2028.

| Day | Short | Made with |
|---|---|---|
| Friday | **Reading**: the chapter read straight through | `reading-short` |
| Monday | **Discussion 1**: the chapter's main teaching from his discussion | `collage-short` |
| Wednesday | **Discussion 2**: a second point he emphasizes, or a different presentation of Discussion 1 if there's only one | `collage-short` |

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
