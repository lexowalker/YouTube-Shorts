# YouTube Shorts: Tao Te Ching readings (style trial)

This branch is a **clean-slate trial of a new visual style**. If the trial wins, it replaces the house style on `main`.

## The rule for this branch: no old style

The user is writing a new set of style rules from scratch. The old house style must not influence this work in any way.

- Don't read, copy or borrow from the old style docs, skills, reference Shorts, fonts or render pipeline. That means `main`, other branches and git history (`docs/style-guide.md`, `docs/reading-style.md`, `.claude/skills/`, `shorts/`, `pipeline/render.py` and so on). They were removed from this branch on purpose.
- Don't fill gaps with old defaults: fonts, colours, caption treatment, imagery sources, end cards, thumbnails, audio treatment, length, title format. If the new rules don't cover something, ask the user. Don't guess from memory of the old look.
- The only things carried over are facts about the material (below) and the release-schedule tooling. Neither one is a style rule.

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
