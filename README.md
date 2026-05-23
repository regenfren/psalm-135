# Тиха Молитва — Psalm 135, as a listening experience

A web piece for a Serbian Orthodox chant of **Psalm 135 (LXX / 136 KJV)** —
the Polyeleos. The verses are illuminated word by word in step with the
chanter's voice, the King James English fills in chunk by chunk beneath, and
a background image emerges from black over the first five seconds.

```
click 135 → seal-opening sound → fade to black → 1s breath → the chant
```

## How it's put together

- **One clock.** Everything (word glow, English chunks, line cross-fade,
  background opacity) derives from `audio.currentTime`, with `seeked` /
  `timeupdate` events keeping the text in sync when you scrub.
- **Sample-accurate audio.** The chant plays back as WAV so seeking is
  frame-exact — MP3 frame/encoder delay caused visible drift otherwise.
- **Automated word-level alignment.** Per-word start times were produced by
  CTC forced alignment with Meta's MMS model via `torchaudio` — accurate even
  for a slow, melismatic chant with a refrain repeated 26 times.
- **Hand-mapped English chunks.** Each Serbian word owns a contiguous span of
  the KJV English; chunks abut to fill the line with no gaps.

## Files

| Path | Purpose |
|---|---|
| `index.html` · `styles.css` · `chant.js` | The experience |
| `studio.html` · `server.py` | Manual timing studio (superseded by MMS alignment) |
| `data/chant.json` | The live data — text, timings, English chunks |
| `data/chant.aligned.json` | MMS-aligned timings (deployed source) |
| `data/chant.manual.json` | Original hand-tapped timings (kept for reference) |
| `assets/chant.wav` | Trimmed, sample-accurate chant audio |
| `assets/chant-original.mp3` | Original recording before the 5.41s head-trim |
| `assets/seal.mp3` | Book-opening sound on the 135 click (+6dB) |
| `assets/hands.png` | Background image (emerges to 25% opacity) |
| `assets/fonts/miroslav.ttf` | Cyrillic display font (Miroslav Gospel) |
| `align/align_mms.py` | The forced-alignment pipeline (re-runnable) |
| `build_lyrics.py` | One-off lyric/placeholder builder (historical) |

## Running locally

```bash
python3 server.py    # threaded · HTTP Range · POST /save → data/chant.json
# then open http://localhost:8080
```

The server is only needed locally (Range requests + the Studio's save endpoint).
For static hosting, any web server / GitHub Pages serves it fine — the experience
is fully static.

## Re-running the alignment

```bash
cd align
uv venv --python 3.11 .venv
uv pip install --python .venv --no-build-isolation "numpy<2" "setuptools==59.8.0" wheel
uv pip install --python .venv torch torchaudio soundfile uroman
.venv/bin/python align_mms.py
```

Writes `data/chant.aligned.json`. Copy over `data/chant.json` to deploy.

## Credits

- **Audio**: *Serbian Orthodox Church Music — Psalm 135.*
- **Background image**: generated with Nano Banana Pro (Gemini 3 Pro Image).
- **Seal sound**: book-opening sample (freesound.org #345808), volume boosted.
- **Font**: Miroslav (after the medieval Miroslav Gospel) via fonts2u.com.
- **Alignment**: Meta's MMS forced aligner via `torchaudio`.
