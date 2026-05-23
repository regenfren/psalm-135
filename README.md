# psalm 135 — a practice in soundscape

A small soundscape piece built around a Serbian Orthodox chant of
**Psalm 135 (LXX / 136 KJV)** — the Polyeleos. A practice project: a quiet,
layered listening environment where the chant's text illuminates word by
word in step with the voice, an English KJV translation fills in beneath
phrase by phrase, and a background image emerges from black over the first
eight seconds.

Live: **https://regenfren.github.io/psalm-135/**

## The shape of the piece

```
click anywhere to begin                  ← user gesture wakes audio (browsers require it)
   ↓  pre-veil fades
135                                       ← rises, breathing slight gold; hover = bzzzz hum
   ↓  click: dissolve + seal-opening sound
black, held for a breath                  ← 1s
   ↓
chant + image emerge together             ← image to 25% opacity over 8s, word-glow tracks audio
```

## How it's put together

- **One clock.** Word glow, English chunks, line cross-fade, and background
  opacity all derive from `audio.currentTime`, with `seeked` / `timeupdate`
  events keeping the text in sync when you scrub.
- **Sample-accurate audio.** Chant plays back as WAV so seeking is
  frame-exact — MP3 frame/encoder delay caused visible drift otherwise.
- **Automated word-level alignment.** Per-word start times produced by
  CTC forced alignment with Meta's MMS model via `torchaudio` — robust
  to the chant's 26 repeating refrains where DTW aligners collapse.
- **Hand-mapped English chunks.** Each Serbian word owns a contiguous span
  of the KJV English; chunks abut so the translation fills with no gaps.

## Files

| Path | Purpose |
|---|---|
| `index.html` · `styles.css` · `chant.js` | The experience |
| `data/chant.json` | Live data — Cyrillic, KJV, word timings, EN chunks |
| `data/chant.aligned.json` | MMS-aligned timings (deployed source) |
| `data/chant.manual.json` | Hand-tapped timings (kept for comparison) |
| `assets/chant.wav` | Trimmed sample-accurate chant audio |
| `assets/chant-original.mp3` | Untrimmed source recording |
| `assets/background.mp3` | Looping hum on the start screen (slowed + pitched down) |
| `assets/seal.mp3` | Book-opening sound on the 135 click (+6dB) |
| `assets/hover.mp3` | Looping bzzz under the cursor on 135 (slowed + reverb) |
| `assets/hands.png` | Background image — emerges to 25% opacity |
| `assets/favicon.svg` | Eight-pointed Orthodox cross favicon |
| `assets/fonts/miroslav.ttf` | Cyrillic display face (Miroslav Gospel) |
| `align/align_mms.py` | The forced-alignment pipeline (re-runnable) |
| `studio.html` · `server.py` | Manual timing studio (superseded by MMS alignment) |
| `build_lyrics.py` | Lyric/placeholder generator (historical) |

## Running locally

```bash
python3 server.py    # threaded · HTTP Range · POST /save → data/chant.json
# then open http://localhost:8080
```

The dev server is only needed locally (Range requests + the Studio's save
endpoint). For static hosting any web server / GitHub Pages serves it — the
experience is fully static.

## Re-running the alignment

```bash
cd align
uv venv --python 3.11 .venv
uv pip install --python .venv "numpy<2" "setuptools==59.8.0" wheel
uv pip install --python .venv --no-build-isolation torch torchaudio soundfile uroman
.venv/bin/python align_mms.py
# writes data/chant.aligned.json — copy over data/chant.json to deploy
```

## Credits

- **Audio**: *Serbian Orthodox Church Music — Psalm 135.*
- **Background image**: generated with Nano Banana Pro (Gemini 3 Pro Image).
- **Sounds**: book-opening sample (freesound.org #345808), low engine hum
  (#72529), UI hover (#519788) — all reprocessed.
- **Font**: Miroslav (after the medieval Miroslav Gospel), fonts2u.com.
- **Alignment**: Meta MMS forced aligner via `torchaudio`.
