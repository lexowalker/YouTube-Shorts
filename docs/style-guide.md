# Style guide: Tao Te Ching Shorts

This is the house style for vertical Shorts cut from David E. Arredondo's readings of, and commentary on, Thomas Cleary's translation of the Tao Te Ching. It merges the original hand-off brief with the decisions made on the first Short (`shorts/tao-ch4-unimpeded-harmony`) and the user's notes on the Chapter 1 Discussion 1 Short (`shorts/tao-ch1-passionless-subtle`), which is now the reference for how a finished Short looks and sounds. Change this file when the house style changes, never one Short at a time.

## Aim
Capture one main teaching from the video and convey it simply and naturally in about 90 s. The Taoism here is simple, natural, unadorned and beautiful, so the Short should feel like a breath of fresh air. Nothing is contrived or embellished. Every choice serves the teaching. When in doubt, take something away.

## Format
- 9:16, 1080×1920, 30 fps, H.264 High (2-pass, about 8 Mbps), AAC 256k at 48 kHz, faststart.
- Talking head: a full-height 9:16 crop of the landscape source. The crop follows his face with a heavily smoothed track (1.5 s Gaussian), so it drifts gently and never snaps. His face sits in the upper-middle third. The upscale is Lanczos with no sharpening. **The talking-head framing is identical in every Short:** always the full-height 9:16 crop of the 4K source (never a tighter zoom, never the 480p), so he appears the same size and position from Short to Short.
- Cut the head shots from the sharpest copy there is. The archive.org items carry the original 4K upload (a VP9 WebM) next to the 480p MP4, and a full-height 9:16 crop of 480p is only 270 px wide. `pipeline/fetch_hires.py` fetches just the window the Short uses and lines it up with the source audio. Everything else (word timing, face tracking) still runs on the 480p MP4. Some uploads are HDR (HLG/BT.2020, e.g. 3/28/24): every head-shot decode tone-maps them to SDR BT.709 (`common.sdr_filter`), otherwise his face comes out washed out and blanched.
- Only David's real voice, never re-worded. No AI voice.

## Structure
1. Choose the one teaching that best carries the spirit of the video. Read the full transcript first.
2. **Open with the quoted text.** When the Short uses a line of the Tao Te Ching (or Cleary's notes), it starts with him reading that quote, captioned in quotation marks (“ on the first word, ” on the last), so the viewer knows what is being discussed. Never open on a random line. Then build about 90 s (85–95 s; 60–120 s is the hard limit) from the moments that best express it. They can come from anywhere in the video, but the result must read as one clear thought (a hook, a middle and a clean, settled ending) and stay true to what David meant.
3. After the quote, the most striking line of his commentary comes next as the hook.
4. Cut only at natural pauses, never mid-word. Remove ums, false starts and asides ("I hope that wasn't too fast", "I might add", "probably too esoteric").
5. Pacing should be calm but alive. Alternate talking head and images about every 4–10 s, with roughly a 50–60% head share, and vary shot length. Never hold one mode longer than about 12 s. Leave a beat of silence on a strong image where a line needs to land.
6. Hide every jump cut between source segments, either under an image or by putting the image cut exactly on the join so the dissolve covers it. An image that starts on a join dissolves in over the end of the outgoing shot while he is still moving, and is fully up on the join (`build_edl.py` starts that dissolve 8 frames early). Never dissolve over the next segment's head, which flashes a stray shot of him, and never freeze his frame under the dissolve, which looks like the video stalls.
7. No blips and no dead air. Every shot lasts at least about 1.2 s: a half-second flash of him, or of a painting, between two other shots breaks the flow, so merge it into a neighbour. Across a join, keep the silence under about 0.8 s; a longer gap reads as a stray shot of him saying nothing. Either he is speaking, or an image is up. `draft.py` flags both (BLIP, DEAD).
8. End card.

## Images (rewritten in round 3; the old art-first rules are retired)
- **The words choose the picture.** Every image is keyed to the exact words under it, so the viewer sees what he is saying at that moment and the image supports the teaching. Before searching, write the plan line by line: the words, the thing or idea they name, and the most direct picture of it. "Thalidomide" is thalidomide (the drug, its packaging, the pills), "smoking was thought to be good for you" is a period cigarette advertisement, "Miss America" is a Miss America pageant photo, "the Big Bang" is the cosmos. If no honest match exists, stay on his face.
- **Draw from anything real.** Photographs, historical photos and documents, advertisements, scientific and NASA imagery, illustrations, prints and artworks are all fair game. Art is welcome when it is the most direct match, not as a default. Never AI-generated imagery.
- **Clean licensing.** Public domain, CC0 or another licence that allows reuse, logged per image (source URL, licence) in `images.json` and DELIVERY.md. Sources reachable from here: the Cleveland Museum of Art and the Met open-access APIs, archive.org, NASA mirrors on archive.org, and Wikimedia files by exact name. Openverse, Wikimedia search, the Library of Congress, Unsplash and Pexels need the environment's network policy to allow them.
- **Pacing is unchanged** (it is good): alternate talking head and images about every 4–10 s, roughly a 50–60% head share; an image comes in on the word that names it and holds while the line stays on that idea; no shot under about 1.2 s.
- **Don't zoom in too far.** Show the subject whole. By default an image is shown with `"fit": [x0, y0, x1, y1]` (the region to show, as fractions of the image): it fills the frame's width or height and the rest of the 9:16 frame is a soft, darkened, blurred copy of the same picture, with a gentle 1.04× to 1.00× zoom-out. For a wide picture, choose a region of about 4:5 around the subject so it still fills most of the screen; a full landscape becomes a thin strip on a phone. Crop into a detail (`x0, y0, h`) only when the detail alone is the subject and it still reads whole; never crop off part of the thing the words name (the whole coin, the whole face).
- Real objects photographed on a plain background (a coin, a jar) can be placed whole on a 9:16 field of their own background (`ext-coin-obverse` is the example).
- A light warm grade applies to artworks; photographs and documents can skip it (`"grade": false`).
- Hide every jump cut between source segments under an image or on an image cut, unless the user asks to stay on his face.

## Captions
- EB Garamond SemiBold (`assets/fonts/EBGaramond-600.ttf`), 70 px, sentence case, warm off-white #F4EFE4.
- Legibility comes from a soft dark halo plus a close shadow, never a stroke. At 66% the captions sit on his white beard, so the halo is strong (85%, widened 13 px, 16 px blur).
- Two-line phrase chunks, each line 1–3 words and each phrase 2–5 words, centered with the block's center at 66% of the frame height (`"caption_y": 0.66` in every spec), inside a 900 px safe width (the renderer asserts this). Lower captions get covered by YouTube's title and channel overlay on the bottom quarter of the screen; never go below 0.66.
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
