# YouTube Shorts: Tao Te Ching readings (style trial)

This branch is a **clean-slate trial of a new visual style**. If the trial wins, it replaces the house style on `main`.

## The rule for this branch: no old style

The user is writing a new set of style rules from scratch. The old house style must not influence this work in any way.

- Don't read, copy or borrow from the old style docs, skills, reference Shorts, fonts or render pipeline. That means `main`, other branches and git history (`docs/style-guide.md`, `docs/reading-style.md`, `.claude/skills/`, `shorts/`, `pipeline/render.py` and so on). They were removed from this branch on purpose.
- Don't fill gaps with old defaults: fonts, colours, caption treatment, imagery sources, end cards, thumbnails, audio treatment, length, title format. If the new rules don't cover something, ask the user. Don't guess from memory of the old look.
- Carried over on purpose:
  - The user chose to keep the **subtitles** and the **end card** of the teaching Shorts on `main`. They are in `pipeline/render.py` (`Captions`, `build_endcard`) with the EB Garamond fonts in `assets/fonts/`.
  - Neutral plumbing: fetching the source and the 4K window, transcription, word timing, audio cutting, face-centred crop and encode.
  - Facts about the material (below) and the release-schedule tooling.
- Nothing else from the old style carries over, for example the warm paper grade on images, museum-only sourcing or the old image rules.

## Where the new style lives

- `docs/style.md`: the new rules, written down as the user gives them. It is the single source of truth. Update it whenever the user adds or changes a rule, never one Short at a time.
- `moodboard/`: the new moodboard (references, images, notes). Only use what the user puts here.
- New pipeline code goes in `pipeline/`. Build it only for what `docs/style.md` asks for.

## The material (facts, not style)

- Long-form readings of the Tao Te Ching (Thomas Cleary translation) by David E. Arredondo, with his commentary.
- Every reading is on the channel's archive.org items. Some sources are also release assets on this repo (e.g. tag `tao45`).
- Intermediates go in `.work/`, which is git-ignored.

## Release schedule

`docs/release-schedule.xlsx` plans the channel's 243 Shorts (`python3 -I pipeline/schedule.py status`). Trial Shorts are experiments, so don't mark them in the schedule unless the user says a trial Short is approved for release.
