# Style guide: Tao Te Ching Shorts

This is the house style for vertical Shorts cut from David E. Arredondo's readings of, and commentary on, Thomas Cleary's translation of the Tao Te Ching. It merges the original hand-off brief with the decisions made on the first Short (`shorts/tao-ch4-unimpeded-harmony`) and the user's notes on the Chapter 1 Discussion 1 Short (`shorts/tao-ch1-passionless-subtle`), which is now the reference for how a finished Short looks and sounds. Change this file when the house style changes, never one Short at a time.

## Aim
Capture one main teaching from the video and convey it simply and naturally in 60–120 s. The Taoism here is simple, natural, unadorned and beautiful, so the Short should feel like a breath of fresh air. Nothing is contrived or embellished. Every choice serves the teaching. When in doubt, take something away.

## Format
- 9:16, 1080×1920, 30 fps, H.264 High (2-pass, about 8 Mbps), AAC 256k at 48 kHz, faststart.
- Talking head: a full-height 9:16 crop of the landscape source. The crop follows his face with a heavily smoothed track (1.5 s Gaussian), so it drifts gently and never snaps. His face sits in the upper-middle third. The upscale is Lanczos with no sharpening.
- Cut the head shots from the sharpest copy there is. The archive.org items carry the original 4K upload (a VP9 WebM) next to the 480p MP4, and a full-height 9:16 crop of 480p is only 270 px wide. `pipeline/fetch_hires.py` fetches just the window the Short uses and lines it up with the source audio. Everything else (word timing, face tracking) still runs on the 480p MP4.
- Only David's real voice, never re-worded. No AI voice.

## Structure
1. Choose the one teaching that best carries the spirit of the video. Read the full transcript first.
2. Build 60–120 s, aiming for 70–90 s, from the moments that best express it. They can come from anywhere in the video, but the result must read as one clear thought (a hook, a middle and a clean, settled ending) and stay true to what David meant.
3. Hook in the first 1–2 s with the most striking, quotable line. A Cleary line read aloud works well as a second beat, opener or closer.
4. Cut only at natural pauses, never mid-word. Remove ums, false starts and asides ("I hope that wasn't too fast", "I might add", "probably too esoteric").
5. Pacing should be calm but alive. Alternate talking head and images about every 4–10 s, with roughly a 50–60% head share, and vary shot length. Never hold one mode longer than about 12 s. Leave a beat of silence on a strong image where a line needs to land.
6. Hide every jump cut between source segments, either under an image or by putting the image cut exactly on the join so the dissolve covers it. An image that starts on a join dissolves in over the end of the outgoing shot while he is still moving, and is fully up on the join (`build_edl.py` starts that dissolve 8 frames early). Never dissolve over the next segment's head, which flashes a stray shot of him, and never freeze his frame under the dissolve, which looks like the video stalls.
7. No blips and no dead air. Every shot lasts at least about 1.2 s: a half-second flash of him, or of a painting, between two other shots breaks the flow, so merge it into a neighbour. Across a join, keep the silence under about 0.8 s; a longer gap reads as a stray shot of him saying nothing. Either he is speaking, or an image is up. `draft.py` flags both (BLIP, DEAD).
8. End card.

## Images
- Real artworks only, never AI-generated or AI-looking images. Classical Chinese ink and shanshui painting (Song masters Ma Yuan, Xia Gui, Fan Kuan, Guo Xi, Muqi), Zen ink, and Korean Joseon and Japanese Muromachi ink are the home ground, but not a limit: use whatever artwork best serves the line being spoken, from any culture. That includes tomb figures and other objects, Hudson River School and European landscapes, vanitas still lifes, and Indian painting (the third Short, `tao-ch5-straw-dogs`, mixes them). Check the date: no 20th-century pieces.
- Use the Cleveland Museum of Art Open Access collection (CC0, full-resolution TIFF masters) by default, so every Short has one clean license. Other public-domain or open-access collections (Met, Smithsonian, National Palace Museum, Wikimedia Commons PD) are fine if CMA lacks a subject. Log the source URL and license for every image.
- Each image is a single full-bleed still: one subject with plenty of negative space, matched literally to the line being spoken (a magpie for "birds", a rainstorm for "storm", bamboo under the moon for "very, very simple"). An image appears on the spoken word it illustrates, never earlier.
- **Key every image to the words under it.** Before searching, write the image plan line by line: the words, the thing they name, and the picture of that thing. The viewer should see what he is saying at that moment, not something merely in the mood of it. Concrete nouns get the literal picture: "that bell" is a bell, "study this book" is a scholar reading, "lust" is lovers, "run over by a bus" is a stampede of horses. If no honest match exists for a line, stay on his face rather than show a vague landscape.
- **Don't change images too often.** When the next line continues the same thought ("pay attention… what's in front of you… hear that bell"), let the image already up carry it rather than cut to a new picture for every noun. A new image should mark a new idea. As a rough guide, an image run holds 4–10 s.
- **Scrolls first, but simplicity over medium.** Chinese, Korean and Japanese ink scrolls are the default because they are Taoist in spirit, simple and natural. When no scroll shows the thing he names, depart from them for another simple, natural image (an object, a bronze bell, a figure study, a landscape from another tradition) rather than force a scroll that doesn't fit.
- **States against the Way get contrasting imagery.** Anger, passion, lust, anxiety, craving and striving are not simple or natural, so don't illustrate them with calm shanshui. Show them as the turbulent, grasping or worldly thing they are (a storm dragon for anger and confusion, a leaping tiger for "vim and vigor and drive", lovers for lust), so they read as the opposite of the stillness the teaching points to, and return to quiet imagery (mist, water, a still figure) when he comes back to the Way.
- Modern things (a car, a bus, a phone) get a classical stand-in that keeps the meaning, or stay on his face. When he names a specific real thing that only a photograph or document can show (Pluto, Earth from space, a hundred-dollar bill), use the real thing from a public-domain source: NASA imagery, a historic banknote scan. Tone it to sit with the paintings (grain, muted paper; `pipeline/ext_image.py`), and never put captions on white paper.
- **Show the action, not a pose.** "The artistic, scientific, or creative spirit" is someone painting, playing or writing, not a figure reclining. Talk of many different people gets a crowd of visibly different individuals. A contrast in the words gets a contrast in the picture: rich and poor for "different resources" (two crops of one painting cut on the word if they sit far apart), and a rigid oak torn down by the storm for "too fixed, too rigid", set against the bending bamboo of "the way is like wind".
- **One clear image, held.** Two images cut in quick succession (1–2 s each) feel choppy; hold one that says it (a single pauper for "different resources", 4–5 s) rather than illustrate both halves of a contrast. And the image must read at a glance: a storm-tossed oak did not read as "a stiff tree that broke"; a bolt-upright official in formal robes reads as rigid instantly.
- **On the word, not a line late.** An image belongs to the phrase that names its subject. If the picture of "many different people" only appears on the next line ("different resources"), move it, and give the next line its own picture.
- **Scale needs real scale.** "The universe" and "a little pathway by a major road" call for things grander than a planet and smaller than a path: the Hubble Deep Field, and the Pale Blue Dot with a white arrow labelled "Earth".
- Prefer paintings on warm silk or toned paper. Near-white paper makes the off-white captions vanish (the first draft of the second Short had to swap Dong Qichang's *Mt. Qingbian* for this reason). If a pale image is the only literal match, crop to its darkest passage.
- **Centre the subject.** The crop is centred on what the line is about (the couple, the bird), with its focal point (an eye, the faces) well inside the frame, at least about 10% from every edge, because the 1.08× start of the zoom trims another 4% from each side. Never let the subject run off an edge or sit pushed to one side. On a wide subject, take a larger crop or soften the zoom (`"zoom": [1.04, 1.0]`).
- Fill 9:16 by cropping into a detail. Never stretch or letterbox. Keep crops off folding-screen panel seams. Choose a tighter crop of a high-resolution master rather than upscaling a small one.
- Motion: a linear zoom-out from 1.08× to 1.00× (1.12× for shots of 8 s or more), with no easing. Handscrolls may pan slowly and horizontally; so may a wide subject that can't fit a 9:16 crop and is read left to right (a banknote from the portrait to the "100", a bookshelf screen). No Ken Burns jumps.
- One gentle warm paper grade on every image (`render.py: warm_grade`). No textures, particles or light leaks.
- Hard cuts between images. An 8-frame soft dissolve into and out of images.

## Captions
- EB Garamond SemiBold (`assets/fonts/EBGaramond-600.ttf`), 70 px, sentence case, warm off-white #F4EFE4.
- Legibility comes from a soft dark halo plus a close shadow, never a stroke. A plain shadow is lost on David's tan sweater.
- Two-line phrase chunks, each line 1–3 words and each phrase 2–5 words, centered with the block's center at 70% of the frame height, inside a 900 px safe width (the renderer asserts this). The 4K full-height crop frames him closer, so 70% falls on his white beard. There, set `"caption_y": 0.83` in the spec to put the captions on his sweater (`tao-ch1-passionless-subtle` is the example).
- Each word appears on its spoken onset with a 3-frame fade. No pop, bounce or scale.
- One key word per phrase (or none) in pale ochre #D9B26F. This is the only caption accent.
- Captions are clean. Fillers that stay in the audio ("you know", "um") can be left off the screen (`~you ~know` in the spec), but every word that is shown matches the speech exactly and appears on its real onset. `build_edl.py` refuses any mismatch, and `qa.py` re-transcribes the finished audio to check words and onsets.
- No opening title by default: the hook line opens the Short on its own (the user had the title removed from `tao-ch1-passionless-subtle`). Add one only if the user asks for it, in this style: the teaching in a few words ("Nothing in nature is separate") in EB Garamond Medium at 52 px, dark ink on a thin rice-paper box, centered at 15% of the height, for the first 3.6 s.

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
Offer 10 titles that would grip a general YouTube audience, most of whom have never read the Tao Te Ching. Open with a tension, a paradox or a problem people recognise from their own lives ("Why Trying Harder Makes You Miss What Matters"), built from what David actually says. Keep them honest and under about 60 characters, with no clickbait ("secret", "shocking"), emoji or ALL CAPS. "· Tao Te Ching Ch. N" helps search but usually pushes past 60 characters, so it can go in the description instead. Recommend one and say why.

## Restraint
No flashy effects, emoji, stickers, shakes, glitches, zoom punches, animated text pops or busy transitions. One font family. One caption accent color. Nothing on screen that doesn't serve the line, and no images that contradict the teaching (violence, machines, glossy stock).
