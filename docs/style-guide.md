# Style guide: Tao Te Ching Shorts

This is the house style for vertical Shorts cut from David E. Arredondo's readings of, and commentary on, Thomas Cleary's translation of the Tao Te Ching. It merges the original hand-off brief with the decisions made on the first Short (`shorts/tao-ch4-unimpeded-harmony`) and the user's notes on the Chapter 1 Discussion 1 Short (`shorts/tao-ch1-passionless-subtle`), and the user's round-3 process changes (Nov 2026). The reference Short is now `shorts/tao-ch2-herd-thinking` (Ch. 2, Discussion 1), the first made fully under the round-3 rules. Change this file when the house style changes, never one Short at a time.

## Aim
Capture one main teaching from the video and convey it simply and naturally in about 90 s. The Taoism here is simple, natural, unadorned and beautiful, so the Short should feel like a breath of fresh air. Nothing is contrived or embellished. Every choice serves the teaching. When in doubt, take something away.

## Format
- 9:16, 1080×1920, 30 fps, H.264 High (2-pass, about 8 Mbps), AAC 256k at 48 kHz, faststart.
- **Talking-head framing is identical in every Short; consistency is key.** Always the full-height 9:16 crop of the 4K source (the archive.org item's VP9 WebM, fetched for just the window used by `pipeline/fetch_hires.py`), Lanczos-upscaled to 1080×1920 with no sharpening. The crop follows his face with a heavily smoothed track (1.5 s Gaussian), so it drifts gently and never snaps, and his face sits in the upper-middle third. No per-Short zoom, no tighter or looser crop, never the 480p: he appears the same size and position from Short to Short. `render.py` refuses to render without the 4K window. Word timing and face tracking still run on the 480p MP4.
- Some uploads are HDR (HLG/BT.2020, e.g. 3/28/24). Every head-shot decode tone-maps them to SDR BT.709 (`common.sdr_filter`), otherwise his face comes out washed out and blanched.
- Only David's real voice, never re-worded. No AI voice.

## Structure
1. Choose the one teaching that best carries the spirit of the video. Read the full transcript first.
2. **Open with the line from the Tao Te Ching.** The Short starts with him reading the line from the book proper (Cleary's translation) that the teaching is about, captioned in quotation marks: “ on the first word, ” on the last, so the viewer knows what is being discussed. Never open on a commentary line. `build_edl.py` checks this (a spec sets `"quote": false` only in the rare Short that quotes no text). Then build about 90 s (85–95 s; 60–120 s is the hard limit) from the moments that best express it. They can come from anywhere in the video, but the result must read as one clear thought (a hook, a middle and a clean, settled ending) and stay true to what David meant.
3. After the quote, the most striking line of his commentary comes next as the hook.
4. Cut only at natural pauses, never mid-word. Remove ums, false starts and asides ("I hope that wasn't too fast", "I might add", "probably too esoteric").
5. Pacing should be calm but alive. Alternate talking head and images about every 4–10 s, with roughly a 50–60% head share, and vary shot length. Never hold one mode longer than about 12 s. Leave a beat of silence on a strong image where a line needs to land.
6. Hide every jump cut between source segments, either under an image or by putting the image cut exactly on the join so the dissolve covers it. An image that starts on a join dissolves in over the end of the outgoing shot while he is still moving, and is fully up on the join (`build_edl.py` starts that dissolve 8 frames early). Never dissolve over the next segment's head, which flashes a stray shot of him, and never freeze his frame under the dissolve, which looks like the video stalls.
7. No blips and no dead air. Every shot lasts at least about 1.2 s: a half-second flash of him, or of a painting, between two other shots breaks the flow, so merge it into a neighbour. Across a join, keep the silence under about 0.8 s; a longer gap reads as a stray shot of him saying nothing. Either he is speaking, or an image is up. `draft.py` flags both (BLIP, DEAD).
8. End card.

## Images
- **The guiding principle: engaging imagery keyed directly to the words.** Every image is chosen because it directly shows what he is saying at that moment, so the image supports the teaching. That outranks everything else in this section, including source and style. Before searching, write the plan line by line: the words, the thing or idea they name, and the most direct, engaging picture of it. "Thalidomide" is a pack of thalidomide; "a herd" is a herd; "Miss America" is a beauty pageant line-up of near-identical contestants; "the tulips in Holland" is Dutch tulip fields; "everyone deciding this is beautiful" is a crowd all photographing the Mona Lisa. If no honest match exists, stay on his face.
- **Not restricted to any source or style.** Photographs (modern or historical), newsreel and film frames, documents, advertisements, scientific imagery, illustrations, artworks, and pictures the user supplies are all fair game. Art is welcome when it is the most direct match, never as a default. Never AI-generated imagery.
- **Simplicity and naturalness for the Way.** When the words describe the Tao, or living in accord with it (stillness, the natural, effortless action, the nameless), the picture reflects that: simple, natural, uncluttered (water, mist, mountains, a quiet figure, nature at work). Worldly states and mistakes (craving, obsession, herd thinking, arrogance) can be shown as vividly and as modern as they are.
- **Clean licensing.** Public domain, CC0, or a licence that allows reuse (CC BY / CC BY-SA need a credit line in the YouTube description), or the user's own picture; log the source URL, licence and author per image in `images.json` and DELIVERY.md, and list the credit lines. What works from here: Wikimedia Commons through `pipeline/commons.py` (search, licence and author from the file page, 1280 px thumbnails), public-domain films on archive.org (Prelinger Archives, Universal Newsreels: grab a frame with ffmpeg, then `ext_image.py`), and the Met and Cleveland open-access APIs. Openverse, Flickr, the Library of Congress, Unsplash and Pexels are blocked by the environment's network policy. When a slot has no strong match, show the user a numbered sheet of options rather than settle.
- **Pacing (unchanged, it is good):** alternate talking head and images about every 4–10 s, roughly a 50–60% head share; an image comes in on the word that names it and holds while the line stays on that idea; no shot under about 1.2 s.
- **Don't zoom in too far.** Show the subject whole with `"fit": [x0, y0, x1, y1]` (the region to show, as fractions of the image): it fills the frame's width or height, the rest of the 9:16 frame is a soft, darkened, blurred copy of the same picture, and it zooms out gently from 1.04× to 1.00×. For a wide picture, choose a region of about 4:5 around the subject so it still fills most of a phone screen. Never crop off part of the thing the words name. Real objects on a plain background (a coin) can be placed whole on a 9:16 field of their own background (`ext-coin-obverse` is the example).
- Photographs, documents and film frames skip the warm grade (`"grade": false`); artworks keep the light warm grade.
- Hide every jump cut between source segments under an image or on an image cut, unless the user asks to stay on his face.

## Captions
- EB Garamond SemiBold (`assets/fonts/EBGaramond-600.ttf`), 70 px, sentence case, warm off-white #F4EFE4.
- Legibility comes from a soft dark halo plus a close shadow, never a stroke. At 66% the captions sit on his white beard, so the halo is strong (85%, widened 13 px, 16 px blur). When a caption lands on a bright image, change the image's region; the captions never move.
- Two-line phrase chunks, each line 1–3 words and each phrase 2–5 words, centered with the block's center at 66% of the frame height in every Short, inside a 900 px safe width (the renderer asserts this). The height is a house constant (`common.CAPTION_Y`), not a per-Short setting: lower captions get covered by YouTube's title and channel overlay, and `build_edl.py` refuses a spec that sets another height.
- Each word appears on its spoken onset with a 3-frame fade. No pop, bounce or scale.
- One key word per phrase (or none) in pale ochre #D9B26F. This is the only caption accent.
- Captions are clean. Fillers that stay in the audio ("you know", "um") can be left off the screen (`~you ~know` in the spec), but every word that is shown matches the speech exactly and appears on its real onset. `build_edl.py` refuses any mismatch, and `qa.py` re-transcribes the finished audio to check words and onsets.
- The Tao Te Ching line opens the Short, in quotation marks (see Structure). No opening title by default (the user had the title removed from `tao-ch1-passionless-subtle`). Add one only if the user asks for it, in this style: the teaching in a few words ("Nothing in nature is separate") in EB Garamond Medium at 52 px, dark ink on a thin rice-paper box, centered at 15% of the height, for the first 3.6 s.

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
No flashy effects, emoji, stickers, shakes, glitches, zoom punches, animated text pops or busy transitions. One font family. One caption accent color. Nothing on screen that doesn't serve the line. No gratuitous or graphic images (the thalidomide harm stays on his face).
