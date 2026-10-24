# YouTube Shorts: Tao Te Ching readings

This repo turns David E. Arredondo's long-form readings of the Tao Te Ching (Thomas Cleary translation) into vertical Shorts, all in one consistent house style.

- There are two kinds of Short:
  - **Reading Shorts:** "make a short of the reading of ch N". One chapter read straight through, captioned line by line, in the fixed look of `shorts/tao-ch1-gateway-of-marvels/`. Follow the `reading-short` skill (`.claude/skills/reading-short/SKILL.md`). The style is in `docs/reading-style.md` and the pipeline is `pipeline/reading.py`.
  - **Teaching Shorts:** one teaching cut from his commentary, with paintings. Follow the `make-short` skill (`.claude/skills/make-short/SKILL.md`). Each comes with two thumbnails and 10 title suggestions.
- Teaching-Short house style: `docs/style-guide.md`. Change it there, never one Short at a time.
- Teaching reference Short: `shorts/tao-ch4-unimpeded-harmony/`. Its `short.json` is a complete spec to copy.
- Pipeline: `pipeline/` (run from the repo root with `python3 -I pipeline/<script>.py <slug>`). Intermediates and the museum image cache live in `.work/`, which is git-ignored.
- Teaching-Short audio is the original recording, cut cleanly: joins in pauses with 12 ms fades, de-click only between words, and one static gain to a −1 dBTP peak. Never add denoise, EQ, compression or limiting; that made the first cut sound boxed in. (Reading Shorts keep their approved loudness normalisation; see `docs/reading-style.md`.)
- Source videos usually arrive as release assets on this repo (e.g. tag `tao45`).
