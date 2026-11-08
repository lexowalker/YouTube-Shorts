# Style (trial): teaching Shorts with East Asian imagery and animated collage

These are the user's rules for the trial style. Change them here, never one Short at a time. Points marked
*(implementation)* are how the pipeline meets a rule. They can change if the user wants something different.

## Workflow

1. The user watches one of the long-form videos and picks a few teachings, in the order they appear.
2. The user gives the essence of each teaching, in order.
3. Claude suggests transcript excerpts from the video that embody each teaching, without unnecessary material
   (ums, ahs, gaps, false starts). If an excerpt quotes the chapter's Tao Te Ching text (e.g. a couplet) or
   Cleary's note, **the Short begins with that excerpt**. Target length: **2:00–3:00**.
4. The user finalises the transcript. Sometimes the user gives a finished, timestamped transcript instead. Then
   go straight to step 5.
5. Video creation (below).

## Elements of every Short

1. Talking-head sections (Dr. Arredondo speaking, as in the original video).
2. Still images with **very slight** zoom or pan.
3. Animated collages.
4. Subtitles keyed to the audio.
5. The end card.

### Pacing

Every scene lasts a few seconds or more. No quick, disorienting cuts.
*(implementation)* A scene is at least 3 s, and an image or collage usually runs 4–15 s. Changes between scenes are
soft dissolves of 0.4 s. Keep the bottom fifth of the frame clear in collages: that is where the subtitles sit.

### Talking head

- Every talking-head section is cropped, framed and centred the same way, so all head shots match.
  *(implementation)* Cut from the item's 4K file. One fixed full-height 9:16 crop for every head shot in the Short,
  centred on his median face position (`pipeline/crop_track.py`, fixed mode).
- The archive.org uploads look washed out. **Restore natural colour** in every head shot.
  *(implementation)* The washed-out look has a cause: the 4K files are **HDR** (10-bit HLG, BT.2020, from the
  phone). `common.HDR_TO_SDR` converts every head frame properly to SDR BT.709: linearise, BT.709 primaries, Mobius
  tone map at 260 nits reference white, no desaturation. It is applied automatically to any HLG or PQ source.
  Chosen by eye against the raw decode and Hable; awaiting the user's approval.

### Images

- Follow the moodboard (`moodboard/`): ancient East Asian iconography, statuary, woodblock prints, scrolls, ink
  landscapes, bird-and-flower painting, mandalas, palace and garden scenes. The moodboard sets the aesthetic.
  Images can come from anywhere, but they must be high quality.
- **Most important: every image is keyed to its words.** Birds' simplicity and naturalness → woodblock birds.
  Disarray in a populace → a crowded city in disarray. Inflamed passions → an angry dragon or yokai. Abiding by
  the Way like the wind → leaves or branches in the wind. Picture and audio must make sense together.
- Any pan or zoom is very light, slow and tasteful. Too much, or too fast, disorients the viewer.
- *(implementation)* Sources: `pipeline/images.py` searches The Met, the Cleveland Museum of Art and the Art
  Institute of Chicago (all CC0, high resolution). Wikimedia rate-limits this environment, so it is a last resort.
  Each image fills the frame as a 9:16 crop in its own colour, with no grade.
  *(implementation)* At most about 4% zoom across a whole shot, or a pan of a few percent of the frame, eased in and out.

### Collages

- Animated collage in the style of the reference video ("Motion Graphic | Collage", youtu.be/CMqw9usH8-8),
  simplified for a 9:16 Short. Each collage runs **5–15 s**.
- What the user likes in the reference:
  - A balance of black-and-white and colour.
  - Simple animated movements of the pieces.
  - The collage builds up: a background and a couple of pieces first, then a couple more, then a couple more.
- Collages follow the same keyed-to-the-words rule as images. They may use imagery more freely and need not
  follow the moodboard tightly.
- *(implementation)* `pipeline/collage.py`, specs under "collages" in short.json; a piece can arrive on a spoken
  word. From the reference's stills: a dark ground, cut-out pieces with rough white paper edges and
  soft shadows, black-and-white engravings and photos with a few colour accents (red paper, a sun disc, flowers),
  newsprint and paper scraps. Pieces arrive in groups of two or three by sliding a short way, rising or settling
  into place. Once placed, they drift or bob slightly.

### Subtitles

Same as the teaching Shorts on `main` (not the reading Shorts): EB Garamond SemiBold, 70 px, off-white
`#F4EFE4` with a soft dark halo. One ochre `#D9B26F` key word per phrase. Each word appears as it is spoken,
in phrases of one or two lines, centred, with the block centre at 0.83 of the height for 4K head shots.
*(implementation)* `pipeline/render.py: Captions`, unchanged from `main`.

### End card

Same end card as the Shorts on `main`. *(implementation)* `pipeline/render.py: build_endcard`, unchanged.

### Audio

*(implementation, not yet confirmed by the user)* The original recording, cut cleanly in pauses with 12 ms fades,
and one static gain to a −1 dBTP peak, as on `main` (`pipeline/audio.py`).
