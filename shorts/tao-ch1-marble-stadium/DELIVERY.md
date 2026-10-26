# The marble in the stadium: Tao Te Ching, Chapter 1 (bonus)

**File:** `tao-ch1-marble-stadium.mp4`, 1080×1920 (9:16), 30 fps, H.264 High at about 8 Mbps, AAC 48 kHz. Runs 63.1 s: 59.1 s of speech and a 4 s end card. True peak −1.3 dBTP.
**Source:** *Tao Te Ching Chap. 1: "The Gateway of Marvels" 3/27/2024* (archive.org `arredondo-03-27-24-tao-te-ching-chap-1-the-gateway-of-marvels-3-27-2024`). Head shots are cut from the item's 4K WebM (window 1728–1862 s).
**Release slot:** none yet. This is one of two extra Chapter 1 Shorts the user asked for.

## 1. Hook title
Your Whole Life Is a Marble in a Stadium

## 2. The teaching
Everything a lifetime takes in through the eyes, ears and thoughts is a marble in a stadium, and outside the stadium is the universe: the evident is a little pathway by a major road, while the real is larger than the universe (Tao Te Ching, Chapter 1, with Cleary's note on "the evident").

## 3. Source timestamps used, in order
| # | Source | Short | Line |
|---|---|---|---|
| 1 | 30:01.59 – 30:06.25 | 0:00.00 – 0:04.66 | "We unnecessarily restrict ourselves to such a small, puny, little, meager existence." (hook; starts after "But we,") |
| — | 29:08.20 – 29:08.65 | 0:04.66 – 0:05.11 | (0.45 s of his room tone, for the pause after the hook) |
| 2 | 29:06.74 – 29:07.75 and 29:09.85 – 29:19.00 | 0:05.11 – 0:15.27 | "If we take a human lifetime and what it's observed with its eyes and its ears and its thoughts, it's like a little ping pong ball, max." (a 2.5 s hesitation after "take a" is trimmed) |
| 3 | 29:22.55 – 29:46.84 | 0:15.27 – 0:39.56 | "This is how many books you can read… in a lifetime. It's not even a ping pong ball. It's like a marble. That's the first attention. The second attention would be the size of the largest stadium that you've ever seen. So you have this little ping pong ball, or a little marble, in a huge stadium." (one continuous take) |
| 4 | 29:51.75 – 29:57.50 | 0:39.56 – 0:45.31 | "And then outside the stadium, you have the universe. And now we're talking about the third attention." |
| 5 | 30:37.55 – 30:42.00 | 0:45.31 – 0:49.76 | "The evident is an edge of reality, like a little pathway by a major road." (Cleary's note, read aloud) |
| 6 | 30:44.49 – 30:53.85 | 0:49.76 – 0:59.12 | "So the evident is like a tiny little pathway. But the real is the size of the universe. Larger than the universe," |
| — | — | 0:59.12 – 1:03.12 | End card (4 s, silent) |

This is the transcript the user approved (candidate C), starting on "We unnecessarily" at their request. "you can, you can experience" keeps the repeat in the audio, off the captions.

## 4. Images
Museum works are CC0 from the Cleveland Museum of Art. The space images are NASA's (public domain), added at the user's request via `pipeline/ext_image.py`.

| Short (s) | Words | Work | Artist | Date | License | Source |
|---|---|---|---|---|---|---|
| 4.39–10.57 | "a human lifetime and what it's observed with its eyes and its ears and its thoughts" | The Thinker | Auguste Rodin | 1880–81 | CC0 | https://clevelandart.org/art/1917.42 |
| 15.00–23.80 | "This is how many books you can read, how many courses… in a lifetime" (slow pan) | Books and Scholars' Accoutrements (chaekgeori) | Yi Taek-gyun | late 1800s | CC0 | https://clevelandart.org/art/2011.37 |
| 29.76–39.56 | "The second attention would be the size of the largest stadium… in a huge stadium" | Views of Rome: The Colosseum | Giovanni Battista Piranesi | 1776 | CC0 | https://clevelandart.org/art/1922.225 |
| 41.95–45.31 | "you have the universe… the third attention" | Hubble Ultra Deep Field | NASA, ESA, S. Beckwith (STScI) and the HUDF Team | 2004 | Public domain (NASA) | https://commons.wikimedia.org/wiki/File:Hubble_ultra_deep_field.jpg |
| 45.31–49.76 | "The evident is an edge of reality, like a little pathway by a major road" | Pale Blue Dot, with a white arrow and "Earth" | NASA / JPL, Voyager 1 | 1990 | Public domain (NASA) | https://commons.wikimedia.org/wiki/File:Pale_Blue_Dot.png |
| 54.41–63.12 | "But the real is the size of the universe. Larger than the universe" (slow zoom out; under the end card) | Hubble Ultra Deep Field | NASA, ESA, S. Beckwith (STScI) and the HUDF Team | 2004 | Public domain (NASA) | https://commons.wikimedia.org/wiki/File:Hubble_ultra_deep_field.jpg |

```
python3 -I pipeline/ext_image.py ext-pale-blue-dot <Wikimedia Pale_Blue_Dot.png> --upscale 4 --arrow 0.7594,0.5603 --label "Earth" …
python3 -I pipeline/ext_image.py ext-hudf <Wikimedia Hubble_ultra_deep_field.jpg> …
```
The Pale Blue Dot exists only at 453×614 on reachable hosts, so it is upscaled 4×; its grain is the original's. `images.json` has the exact crops and motion.

## 5. Notes on choices
- **Approved** by the user on 26 Oct 2026 after round 2 ("great!"). No release slot yet.
- **Round 2 (the user's notes, 26 Oct):**
  - **The opening:** it starts on "We unnecessarily", after "But we,".
  - **Clipped words:** "existence", "ball" and "huge stadium" had been clipped. Each is now whole, and so is "max", which turned out to come after a soft, late "ball".
  - **The stadium:** the Colosseum waits for "The second attention". To allow that, the books lines and "That's the first attention" are one continuous take, and the chaekgeori bookshelves cover the list of books, courses and TV shows.
  - **The universe:** the star deities, the scroll path and the scroll pan gave way to the Hubble Ultra Deep Field for "the universe" and the Pale Blue Dot, arrowed "Earth", for "a little pathway by a major road". The Deep Field returns, slowly widening, for "larger than the universe".
- **Imagery:** the Thinker for a lifetime of seeing, hearing and thinking (the "first attention", the intellect at work); bookshelves for "how many books you can read"; Piranesi's Colosseum for "the largest stadium"; then real astronomy, at the user's request, for scale beyond anything painted: the Deep Field's thousands of galaxies for "the universe" and the Pale Blue Dot for how small the evident is.
- **Passed over:** a silk of dragons chasing flaming pearls for "a marble" (the pearls are lost in the pattern); in round 2, the star-deity painting and the scroll path, which the user found too small in scale.
- **Captions on the hook:** he cups his hands to show "small" right behind the captions at 0:02–0:05; they stay readable, and the gesture is worth keeping.
- **Head share:** 37%. No mode runs over 9.8 s.
- **Listen once:** I can't hear the audio. Please check the first join at 0:04.7–0:05.1 (the inserted room tone and "If we take"), and the restored "…ping pong… ball, max." at 0:13–0:15.

## 6. Thumbnails
- `thumbnails/thumbnail_face.jpg`: frame 29:36.20, eyes open to the camera, cut from the 4K.
- `thumbnails/thumbnail_book_cover.jpg`: *The Essential Tao* (Cleary, HarperOne, ISBN 9780062502162). Amazon's scan is only 306×500, so it is soft at full size.

## 7. Titles (recommended first)
1. **Your Whole Life Is a Marble in a Stadium**
2. Everything You Know Is a Marble in a Stadium
3. We Restrict Ourselves to Such a Small Existence
4. The Real Is Larger Than the Universe
5. Why You're Living in Such a Small World
6. A Little Path Beside a Major Road
7. All the Books You'll Ever Read Are a Marble
8. Beyond the Stadium Is the Universe
9. The Evident Is Only the Edge of Reality
10. How Much of Reality Do You Really See?
