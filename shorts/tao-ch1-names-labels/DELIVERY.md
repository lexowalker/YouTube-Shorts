# Names can be given, but not permanent labels: Tao Te Ching, Chapter 1 (bonus)

**File:** `tao-ch1-names-labels.mp4`, 1080×1920 (9:16), 30 fps, H.264 High at about 8 Mbps, AAC 48 kHz. Runs 71.2 s: 67.2 s of speech and a 4 s end card. Loudness −21.5 LUFS, true peak −1.3 dBTP.
**Source:** *Tao Te Ching Chap. 1: "The Gateway of Marvels" 3/27/2024* (archive.org `arredondo-03-27-24-tao-te-ching-chap-1-the-gateway-of-marvels-3-27-2024`). Head shots are cut from the item's 4K WebM (one window, 178–2290 s, because the lines come from minutes 3–8 and 35–38).
**Release slot:** none yet. Chapter 1's three slots are the reading, Discussion 1 and Discussion 2 (candidate A); this is one of two extra Chapter 1 Shorts the user asked for.

## 1. Hook title
Pluto Didn't Change. Only Its Name Did.

## 2. The teaching
Names can be given, but not permanent labels: Pluto, a country's borders and a hundred-dollar bill change with the names we keep in mind, while the thing itself stays as it is (Tao Te Ching, Chapter 1, Thomas Cleary translation).

## 3. Source timestamps used, in order
| # | Source | Short | Line |
|---|---|---|---|
| 1 | 8:18.84 – 8:25.20 | 0:00.00 – 0:06.36 | "Pluto was once named a planet. It's no longer named a planet. It has nothing to do with Pluto." (hook) |
| 2 | 3:05.25 – 3:08.50 | 0:06.36 – 0:09.61 | "Names can be given, but not permanent labels." (Cleary text, read aloud) |
| 3 | 7:58.24 – 8:13.40 | 0:09.61 – 0:24.77 | "We can give names and labels to things, but those names and labels can be switched around without changing the actual object of observation, or study, or inquiry." |
| 4 | 37:37.70 – 37:48.00 | 0:24.77 – 0:35.07 | "The country of Mexico used to include California, Colorado, you know, New Mexico, Arizona, and go all the way up to Wyoming. That was the country. Well, that's not the country anymore." |
| 5 | 37:55.80 – 38:01.00 | 0:35.07 – 0:40.27 | "But what changed in that western part of the United States? Nothing changed but the label." |
| 6 | 35:10.90 – 35:21.92 | 0:40.27 – 0:51.29 | "In order for a hundred dollar bill to, to exist and be observed… we'd have a beautiful piece of green paper," |
| 7 | 35:26.40 – 35:31.82 and 35:33.62 – 35:34.45 | 0:51.29 – 0:57.54 | "So, individually and collectively, we sustain certain things with our intention and our thoughts." ("our, our, uh…" and a 1 s pause before "our thoughts" are cut) |
| 8 | 36:47.22 – 36:52.30 | 0:57.54 – 1:02.62 | "You can have a reality without having the name, and you can have the name without the reality, right?" |
| 9 | 36:38.85 – 36:43.40 | 1:02.62 – 1:07.17 | "But no matter what the name is, the reality is still there." |
| — | — | 1:07.17 – 1:11.17 | End card (4 s, silent) |

This is the transcript the user approved (candidate B), with their change: the Mexico line starts at "the country of Mexico used to include California". All cuts fall in pauses, with 12 ms fades. "you know" (after Colorado) and the repeated "to" in "to, to exist" stay in the audio and are left off the captions.

## 4. Images
Keyed to the words under them. Pluto and the banknote are not museum works: the user asked for the real things, so they come from public-domain sources via `pipeline/ext_image.py` (commands below).

| Short (s) | Words | Work | Artist | Date | License | Source |
|---|---|---|---|---|---|---|
| 6.09–12.73 | "Names can be given, but not permanent labels. We can give names and labels to things" | Pluto in True Color, on black | NASA / Johns Hopkins APL / SwRI (New Horizons) | 2015 | Public domain (NASA) | https://commons.wikimedia.org/wiki/File:Pluto_in_True_Color_-_High-Res.jpg |
| 24.50–31.43 | "the country of Mexico used to include California, Colorado… Wyoming" | Mount Starr King, Yosemite | Albert Bierstadt | 1866 | CC0 | https://clevelandart.org/art/1922.684 |
| 34.80–40.27 | "what changed in that western part of the United States? Nothing changed but the label" | Fir Trees and Storm Clouds | Albert Bierstadt | c. 1870 | CC0 | https://clevelandart.org/art/1982.37 |
| 49.89–57.54 | "a beautiful piece of green paper… we sustain certain things with our intention and our thoughts" (pan from Franklin to the "100") | One Hundred Dollars, Gold Certificate, Series 1934 | Bureau of Engraving and Printing | 1934 | Public domain (U.S. government work); scan from the Endlos Museum on archive.org | https://archive.org/details/one-hundred-dollars-from-1934-by-the-bureau-of-engraving-and-printing-endlos |

```
python3 -I pipeline/ext_image.py ext-pluto <1280px Wikimedia thumbnail> --canvas 1350:2400 --fill 0.92 --cy 0.4 …
python3 -I pipeline/ext_image.py ext-bill-1934 <archive.org PNG> --crop 0,0,1,0.5 --desat 0.3 --gain 0.52 --grain 7 …
```
`images.json` has the image-file URL, exact crop and motion for each shot.

## 5. Notes on choices
- **Approved** by the user on 26 Oct 2026 after round 2 ("great!"). No release slot yet.
- **Round 2 (the user's notes, 26 Oct):** the clip now starts after a soft false start on "P-" before "Pluto". The Moon became Pluto itself (New Horizons, set on black). The Swedish plate money became a slow pan across a 1934 hundred-dollar note, from Franklin to the "100", toned down and grained so it sits with the paintings and keeps the captions off white paper. The Red Fuji is gone: the last two lines are on his face, so there is one cut on his face at 1:02.6, between two takes 8 s apart in the video with nearly the same pose. Fixing that cut also turned up a clipped word: "our thoughts" had been cut, leaving "our, uh", which every pass heard as "our sense". The clip now jumps from "…intention and" to "our thoughts".
- **Imagery:** the hook stays on his face, then Pluto itself on "Names can be given". Bierstadt's California and western mountains carry the Mexico lines, the hundred-dollar note pans under "a beautiful piece of green paper… we sustain certain things with our intention and our thoughts", and the last two lines are his own, on camera.
- **Passed over:** Goryeo bronze seals and a Kushan gold coin (grey museum backdrops under the captions), and Kenyon Cox's *Design for United States Currency* (literal, but from 1912, and the house style takes no 20th-century work).
- **Words:** large-v3 and small.en hear "the name" twice in "You can have a reality without having the name", and the captions follow them; medium.en and the QA pass hear "a name", and QA hears "could". The line "But no matter what the name is, the reality is still there" was misheard by medium.en and is timed from a narrow large-v3 pass and the envelope.
- **Head share:** 60%. One cut on his face at 1:02.6 (see Round 2).
- **Listen once:** I can't hear the audio. Please check 0:51.3–0:57.5 ("So, individually… and | our thoughts", where a stammer is cut) and the cut on his face at 1:02.6.

## 6. Thumbnails
- `thumbnails/thumbnail_face.jpg`: frame 35:16.60, eyes toward the camera, mouth at rest, cut from the 4K.
- `thumbnails/thumbnail_book_cover.jpg`: *The Essential Tao* (Cleary, HarperOne, ISBN 9780062502162). Amazon's scan is only 306×500, so it is soft at full size.

## 7. Titles (recommended first)
1. **Pluto Didn't Change. Only Its Name Did.**
2. Names Can Be Given, but Not Permanent Labels
3. A $100 Bill Is Only Real Because We Agree
4. Nothing Changed but the Label
5. Why Labels Never Hold the Truth
6. The Name Is Not the Thing
7. What Pluto Teaches About Reality
8. We Hold the World Together With Our Thoughts
9. The Reality Is Still There, Whatever We Call It
10. Lao Tzu on Why Names Don't Last
