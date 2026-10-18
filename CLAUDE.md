# YouTube Shorts: Tao Te Ching readings

This repo turns David E. Arredondo's long-form readings of the Tao Te Ching (Thomas Cleary translation) into vertical Shorts, all in one consistent house style.

- When the user points to a video and asks for a Short, follow the `make-short` skill (`.claude/skills/make-short/SKILL.md`). Each Short comes with two thumbnails and 10 title suggestions.
- House style: `docs/style-guide.md`. Change it there, never one Short at a time.
- Reference Short: `shorts/tao-ch4-unimpeded-harmony/`. Its `short.json` is a complete spec to copy.
- Pipeline: `pipeline/` (run from the repo root with `python3 -I pipeline/<script>.py <slug>`). Intermediates and the museum image cache live in `.work/`, which is git-ignored.
- Audio is the original recording, cut cleanly: joins in pauses with 12 ms fades, de-click only between words, and one static gain to a −1 dBTP peak. Never add denoise, EQ, compression or limiting; that made the first cut sound boxed in.
- Source videos usually arrive as release assets on this repo (e.g. tag `tao45`).
