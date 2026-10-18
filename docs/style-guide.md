# Style guide: Tao Te Ching Shorts

This is the house style for vertical Shorts cut from David E. Arredondo's readings of, and commentary on, Thomas Cleary's translation of the Tao Te Ching. It merges the original hand-off brief with the decisions made on the first Short (`shorts/tao-ch4-unimpeded-harmony`), which is the reference for how a finished Short looks and sounds. Change this file when the house style changes, never one Short at a time.

## Aim
Capture one main teaching from the video and convey it simply and naturally in 60–120 s. The Taoism here is simple, natural, unadorned and beautiful, so the Short should feel like a breath of fresh air. Nothing is contrived or embellished. Every choice serves the teaching. When in doubt, take something away.

## Format
- 9:16, 1080×1920, 30 fps, H.264 High (2-pass, about 8 Mbps), AAC 256k at 48 kHz, faststart.
- Talking head: a full-height 9:16 crop of the landscape source. The crop follows his face with a heavily smoothed track (1.5 s Gaussian), so it drifts gently and never snaps. His face sits in the upper-middle third. The upscale is Lanczos with no sharpening.
- Only David's real voice, never re-worded. No AI voice.

## Structure
1. Choose the one teaching that best carries the spirit of the video. Read the full transcript first.
2. Build 60–120 s, aiming for 70–90 s, from the moments that best express it. They can come from anywhere in the video, but the result must read as one clear thought (a hook, a middle and a clean, settled ending) and stay true to what David meant.
3. Hook in the first 1–2 s with the most striking, quotable line. A Cleary line read aloud works well as a second beat, opener or closer.
4. Cut only at natural pauses, never mid-word. Remove ums, false starts and asides ("I hope that wasn't too fast", "I might add", "probably too esoteric").
5. Pacing should be calm but alive. Alternate talking head and images about every 4–10 s, with roughly a 50–60% head share, and vary shot length. Never hold one mode longer than about 12 s. Leave a beat of silence on a strong image where a line needs to land.
6. Hide every jump cut between source segments, either under an image or by putting the image cut exactly on the join so the dissolve covers it.
7. End card.

## Images
- Real artworks only, never AI-generated or AI-looking images. Classical Chinese ink and shanshui painting (Song masters Ma Yuan, Xia Gui, Fan Kuan, Guo Xi, Muqi), Zen ink, and Korean Joseon and Japanese Muromachi ink are all in keeping. Check the date: no 20th-century pieces.
- Use the Cleveland Museum of Art Open Access collection (CC0, full-resolution TIFF masters) by default, so every Short has one clean license. Other public-domain or open-access collections (Met, Smithsonian, National Palace Museum, Wikimedia Commons PD) are fine if CMA lacks a subject. Log the source URL and license for every image.
- Each image is a single full-bleed still: one subject with plenty of negative space, matched literally to the line being spoken (a magpie for "birds", a rainstorm for "storm", bamboo under the moon for "very, very simple"). An image appears on the spoken word it illustrates, never earlier.
- Fill 9:16 by cropping into a detail. Never stretch or letterbox. Keep crops off folding-screen panel seams. Choose a tighter crop of a high-resolution master rather than upscaling a small one.
- Motion: a linear zoom-out from 1.08× to 1.00× (1.12× for shots of 8 s or more), with no easing. Handscrolls alone may pan slowly and horizontally. No Ken Burns jumps.
- One gentle warm paper grade on every image (`render.py: warm_grade`). No textures, particles or light leaks.
- Hard cuts between images. An 8-frame soft dissolve into and out of images.

## Captions
- EB Garamond SemiBold (`assets/fonts/EBGaramond-600.ttf`), 70 px, sentence case, warm off-white #F4EFE4.
- Legibility comes from a soft dark halo plus a close shadow, never a stroke. A plain shadow is lost on David's tan sweater.
- Two-line phrase chunks, each line 1–3 words and each phrase 2–5 words, centered with the block's center at 70% of the frame height, inside a 900 px safe width (the renderer asserts this).
- Each word appears on its spoken onset with a 3-frame fade. No pop, bounce or scale.
- One key word per phrase (or none) in pale ochre #D9B26F. This is the only caption accent.
- Captions are clean. Fillers that stay in the audio ("you know", "um") can be left off the screen (`~you ~know` in the spec), but every word that is shown matches the speech exactly and appears on its real onset. `build_edl.py` refuses any mismatch, and `qa.py` re-transcribes the finished audio to check words and onsets.
- Opening title: the teaching in a few words ("Nothing in nature is separate") in EB Garamond Medium at 52 px, dark ink on a thin rice-paper box, centered at 15% of the height, for the first 3.6 s.

## Sound
- David's voice is the whole soundtrack, and it should sound as it does in the original video. No noise reduction, EQ, compression or limiting. Those made the first cut sound boxed in.
- Clean joins only: every cut falls in a pause and gets a 12 ms fade out and fade in.
- Mouth clicks and pops are removed only in the pauses between words, never inside a word.
- One static gain so the true peak sits at −1 dBTP. The loudness follows from that (about −23 LUFS for the first source), and the tone is untouched.
- No music, effects, whooshes or risers. Silence on the end card.

## End card (4 s)
- The last shot settles, then dissolves into the card over 15 frames. The card holds with a 1.03× to 1.00× zoom-out.
- Rice-paper background #F4EFE4 and a small cinnabar seal square (#A8473A, the only red).
- "David E. Arredondo" in EB Garamond SemiBold, with "Readings from the Tao Te Ching · Thomas Cleary translation" beneath it.
- YouTube @DavidEArredondo and X @davidarredondo, each with a small monochrome icon.
- Kept in the upper-middle, clear of YouTube's lower-third subscribe prompt.

## Thumbnails (two per Short)
1. **Face:** a frame where David looks into the camera with eyes open and mouth at rest (`thumbs.py faces` scores candidates). It's cropped 9:16 around his face, with a rice-paper band across the middle reading "Readings from the" / "Tao Te Ching" in EB Garamond, dark ink, and the small seal. The band stays in the middle so it survives YouTube's crops.
2. **Book cover:** the cover of the edition David reads (*The Essential Tao*, Thomas Cleary, HarperOne, ISBN 9780062502162), scaled to fill 1080×1920 with nothing added. Use the largest scan available. Amazon's is only 306×500, so a photo of David's own copy would be sharper.

## Titles
Offer 10 calm, specific titles drawn from David's own words or the Cleary line, under about 60 characters. No clickbait, emoji or ALL CAPS. Optionally add "· Tao Te Ching, Ch. N" for search. Recommend one.

## Restraint
No flashy effects, emoji, stickers, shakes, glitches, zoom punches, animated text pops or busy transitions. One font family. One caption accent color. Nothing on screen that doesn't serve the line, and no images that contradict the teaching (violence, machines, glossy stock).
