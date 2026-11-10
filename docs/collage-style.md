# Image-and-collage teaching Shorts: style and process

This is how the teaching Shorts with museum images and animated collages are made. The user approved the first one,
`shorts/tao-ch3-sage-government/` ("Government of Sages", Chapter 3 Discussion 1, 10 Nov 2026), after five rounds
of notes. That Short is the reference: its `short.json` is a complete working spec and its `DELIVERY.md` records
what was chosen and why.

The guide has three parts: what the user asked for, what is fixed, and what is yours to decide. Most of a Short is
the third part. The fixed part is short on purpose.

## 1. What the user asked for (their brief)

A vertical Short of Dr. David E. Arredondo teaching from the Tao Te Ching (Thomas Cleary translation), cut from
one of the long-form videos, **2:00–3:00** long including the end card. Each Short has:

1. **Talking-head sections:** him speaking, as in the original video.
2. **Images** with very slight zoom or pan.
3. **Animated collages.**
4. **Subtitles** timed and keyed to the audio.
5. **The end card.**

In the user's words:

- **Talking head.** Crop, frame and centre every talking-head section the same way, so the head scenes are
  consistent. Restore the natural colours (see "Colour" below).
- **Images.** Follow the moodboard (`moodboard/`): ancient East Asian iconography, statuary, woodblock prints,
  scrolls. The moodboard sets the style. Images can come from anywhere, but they must be high quality. Any pan or
  zoom is very light and tasteful; too much, or too fast, is disorienting.
- **The most important thing: the imagery is keyed to the transcript and audio.** Birds' simplicity and
  naturalness → woodblock prints of birds. Disarray in a populace → a bustling city in disarray. Inflaming
  passions → an angry dragon or yokai. Abiding by the Way like the wind → leaves or branches in the wind. Picture
  and audio go hand in hand and make sense together.
- **Collages.** In the style of the reference video (https://youtu.be/CMqw9usH8-8), simpler and smaller, 5–15 s
  each. What the user likes about it: a balance of black-and-white and colour; simple animated movements of the
  pieces; the collage being built up (a background and a couple of images first, then a couple more, then a
  couple more). Collages are keyed to the words like the images, with more freedom in what they use; they
  needn't follow the moodboard tightly.
- **Subtitles.** Same font and colouring as the teaching Shorts on `main`. Anything he reads from the book goes in
  quotation marks.
- **End card.** The same as the other Shorts on `main`.
- **Timing.** Each scene lasts a few seconds or more. No quick, disorienting cuts.
- **Caveats from earlier attempts.** Keep collage pieces and the important parts of images out of the subtitle
  area. Don't let collage pieces cover faces (a statue's or a figure's). A cut-out with holes punched through it
  looks broken: use a torn scrap of the picture, or a solid cut-out. If something isn't covered, ask rather than
  guess.

## 2. The process: transcript first, then the video

### Step 1. The transcript (the user approves it before anything is built)

The user gives a video, a time range and the teaching to focus on (or a finished transcript).

1. Fetch the item's 480p MP4 as `.work/<slug>/source.mp4` and transcribe the range (`medium.en` is accurate enough
   to choose from).
2. Propose a transcript of 2:00–3:00 made from excerpts that embody the teaching, in the order they appear:
   - If an excerpt quotes the chapter's text, the Short starts with it.
   - Leave out ums, ahs, gaps, false starts and asides.
   - Give it as a table: source time, the words as heard, rough seconds. Say what is left out, and offer any
     strong optional lines with their cost in seconds.
   - Leave room for the 4 s end card: Shorts can't exceed 3:00.
3. Stop and wait for the user's edits and approval.

He pauses, restarts and stutters a lot mid-sentence, so the final wording can differ slightly from the proposal
where there is no clean place to cut (a sentence that runs on, a word that trails into the next). Tell the user
each difference when you deliver.

### Step 2. Putting it together

Everything runs from the repo root with `python3 -I pipeline/<script>.py <slug>`.

| Step | Command | What it does |
|---|---|---|
| 4K window | `fetch_hires.py <slug> <webm url> <from> <to>` | Head shots are cut from the item's 4K WebM |
| Cut | write `"segments"` in `shorts/<slug>/short.json` | Source pieces in program order, each cut in a real pause |
| Word timings | `prog.py <slug>` | Cuts the audio as the Short is cut, then transcribes that: word times in program time |
| Spec | `"phrases"`, `"scenes"`, `"collages"` in `short.json` | Copy the reference spec's shape |
| Build | `scenes.py build <slug>` | Checks every caption word against the speech; prints the scene list |
| Head shots | `head.py <slug>` | Same crop for every head scene, HDR converted to natural colour |
| **Colour check** | `hdr.py check <slug>` | **Proves the conversion was applied** (see "Colour") |
| Draft | `scenes.py draft <slug>` | Contact sheets of every scene and every collage piece, composed as the render will |
| Audio | `audio.py <slug>` | Original voice, clean joins, one static gain |
| Render | `scenes.py render <slug>` then `encode.py <slug>` | About 10–15 min; run in the background |

Images come from `museum.py search|get|proxy` (The Met, Art Institute of Chicago, Cleveland; all public domain).

Things learned on the first Short that save time:

- **Cutting.** Whisper stretches a word across every long pause, so don't trust its times near pauses. Place each
  cut on the audio envelope (`env.py`), in room tone. A quiet "s" or "th" at the end of a word sits near the noise
  floor: the first cut clipped the "s" of "worse". When a word ends in a fricative, leave another 0.3–0.5 s.
- **Check the cut by re-transcribing it** (`prog.py`, and once with `--model large-v3 --no-prompt`). If the cut
  reads as clean sentences, the joins are sound. You can't hear the audio: say so, and list the joins most worth
  a listen.
- **Joins and scenes.** Plan scenes so audio joins fall on a scene change or under an image or collage. A join
  inside a head scene is a visible jump.
- **Reading close-ups.** When he leans in to read from the book his face fills the frame and his beard reaches
  the subtitle area. Put those lines under an image.
- **Picture research** is a good job for a helper agent: give it the lines, the thing each line names, and the
  aesthetic, and have it download and describe 2–4 candidates per line. Then look at the candidates yourself
  before choosing.
- **Look at the draft sheets before rendering**, and at stills of the finished mp4 afterwards. Measure anything
  the user has given a reference for; don't judge it by eye from small stills (see "Colour").
- **Finishing.** Write `DELIVERY.md` and `images.json` (every work's title, maker, date, licence and URL), mark
  the release schedule (see `CLAUDE.md`), commit, push, and send the mp4.

## 3. Fixed: keep these the same in every Short

### Colour: the head shots must be converted to natural colour, and you must prove it

The 4K files are HDR (10-bit HLG, BT.2020). Decoded as ordinary video they look pale, grey and faded.
`pipeline/hdr.py` converts them properly to SDR (no saturation boost), with numbers fitted to the user's own
screenshot of the original video, `docs/reference/head-colour-original.webp`. That picture is the target: bright,
warm skin, a mid-grey sweater, black shelves.

- After `head.py`, always run `python3 -I pipeline/hdr.py check <slug>` and look at
  `.work/<slug>/colour_check.jpg` (reference | raw decode | rendered). It fails if the rendered head shots are as
  pale as the raw decode.
- After the final encode, compare a head frame from the delivered mp4 with the reference once more.
- Why this is a rule: the first three cuts of the reference Short went out with **no conversion at all**. A
  metadata check silently returned "not HDR", the tuning that followed changed nothing, and the stills were
  judged by eye and passed. The user saw "little to no difference" each time. `head.py` now refuses a 10-bit
  source without a conversion, and the check above measures the result.
- If a future video is lit or shot differently and the result doesn't match its original, refit the numbers in
  `hdr.py` to a screenshot of that original. Don't tune by taste.

### Subtitles: same look, same height

- EB Garamond SemiBold 70 px, off-white `#F4EFE4` with a soft dark halo, one ochre `#D9B26F` key word per phrase,
  phrases of one or two lines, each word appearing as it is spoken (`render.py: Captions`, unchanged).
- **Centred at 73% of the frame height** (`"caption_y": 0.73`, the default in `scenes.py`). In the YouTube Shorts
  feed the channel name, title and buttons cover everything below about 80%, so the subtitles must end above
  that. Don't move them lower.
- Lines stay under about 760 px wide, clear of the Like / Comment / Save column on the right.
- Quotation marks around everything he reads from the book. The marks go in the phrase text
  (`“Therefore the | *government of sages`).
- Because the subtitles sit at 73%: collage pieces stay above about 64% of the height, and the subject of an
  image stays in the upper two thirds of its crop.

### The rest of the fixed list

- 1080×1920, 30 fps; 2:00–3:00 including the 4 s end card.
- The end card is the house end card (`render.py: build_endcard`).
- Audio is his original voice: joins in pauses with 12 ms fades, one static gain to about −1 dBTP. No denoise, EQ,
  compression or limiting.
- Every head scene uses the same full-height 9:16 crop centred on his face (`head.py` does this).
- Scenes last a few seconds or more (about 3 s at the least; images and collages usually 4–15 s). Scene changes
  are soft dissolves.
- Image moves are tiny: about 3.5% of zoom across a whole shot, eased in and out.
- Real, public-domain artworks only, with their sources logged. Nothing AI-generated.
- The user's caveats in section 1.

## 4. Yours to decide

These are creative choices. The reference Short shows one way; it is not a template to copy.

- Which excerpts make the transcript, and how to shape the arc of the teaching.
- Which lines stay on his face, which get an image, and which get a collage; how many of each. (The reference has
  about 37% head, 9 images and 3 collages. That balance worked; it isn't a quota.)
- Which artwork shows each line, and how literal or how evocative it is, as long as picture and words make sense
  together and the images keep to the moodboard's world.
- What goes into each collage, how it is laid out, what arrives on which word, and how the pieces move. The
  engine (`collage.py`) has torn scraps, solid cut-outs, paper discs and sheets of colour; add to it if an idea
  needs something else.
- The ground, colours and accents of a collage; the mix of black-and-white and colour.
- Crops, and whether an image zooms in, out or drifts.
- Titles to suggest.

If an idea needs something the pipeline can't do, extend the pipeline (and note it here) rather than drop the
idea. If something isn't covered by this guide or the brief, ask the user.
