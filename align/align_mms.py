#!/usr/bin/env python3
"""High-precision word-level forced alignment with Meta's MMS model (torchaudio).

CTC forced alignment of the KNOWN transcript: one monotonic Viterbi path through
the whole token sequence, so repeated refrains can't be reordered or collapsed.

Reads ../data/chant.json (for the word order + display text), aligns against
../assets/chant.wav, and writes ../data/chant.aligned.json with new per-word
start times. Does NOT overwrite the manual chant.json — compare first.
"""
import json, re, sys, unicodedata
import torch, torchaudio
from uroman import Uroman

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
AUDIO = f"{HERE}/../assets/chant.wav"
SRC   = f"{HERE}/../data/chant.json"
OUT   = f"{HERE}/../data/chant.aligned.json"

print("loading MMS_FA bundle ...")
bundle = torchaudio.pipelines.MMS_FA
model = bundle.get_model()
tokenizer = bundle.get_tokenizer()
aligner = bundle.get_aligner()
DICT = bundle.get_dict()           # allowed chars -> index
ALLOWED = set(DICT.keys())
SR = bundle.sample_rate
print("allowed chars:", "".join(sorted(c for c in ALLOWED if c.strip())))

# ---- load transcript (word order + display) ----
chant = json.load(open(SRC, encoding="utf-8"))
flat = []   # (lineIndex, wordIndex, display_cy)
for li, ln in enumerate(chant["lines"]):
    for wi, w in enumerate(ln["words"]):
        flat.append((li, wi, w["cy"]))
display = [f[2] for f in flat]
print(f"{len(display)} words to align")

# ---- romanize each word, clean to the model's alphabet ----
uro = Uroman()
def romanize_word(w):
    # strip punctuation, romanize Serbian Cyrillic -> latin, keep only dict chars
    bare = re.sub(r"[^\w]", "", w, flags=re.UNICODE)
    rom = uro.romanize_string(bare, lcode="srp")
    rom = unicodedata.normalize("NFD", rom)
    rom = "".join(c for c in rom.lower() if c in ALLOWED).strip()
    return rom

tokens, empties = [], []
for i, w in enumerate(display):
    r = romanize_word(w)
    if not r:                      # punctuation-only / unromanizable -> placeholder vowel
        r = "a"; empties.append(i)
    tokens.append(r)
if empties:
    print(f"note: {len(empties)} words had no romanization, used placeholder")

# ---- load + prep audio (mono, 16k) via soundfile ----
print("loading audio ...")
import soundfile as sf
data, sr = sf.read(AUDIO, dtype="float32", always_2d=True)   # (samples, channels)
wav = torch.from_numpy(data.T)                                # (channels, samples)
if wav.size(0) > 1:
    wav = wav.mean(0, keepdim=True)
if sr != SR:
    wav = torchaudio.functional.resample(wav, sr, SR)

# ---- emissions + forced alignment ----
print("running acoustic model ...")
with torch.inference_mode():
    emission, _ = model(wav)
num_frames = emission.size(1)
ratio = wav.size(1) / num_frames

print("forced-aligning ...")
token_spans = aligner(emission[0], tokenizer(tokens))

# ---- map spans back to per-word times ----
assert len(token_spans) == len(tokens), (len(token_spans), len(tokens))
times = []
for spans in token_spans:
    start = spans[0].start * ratio / SR
    end   = spans[-1].end   * ratio / SR
    times.append((round(start, 2), round(end, 2)))

# enforce monotonic non-decreasing starts
for i in range(1, len(times)):
    if times[i][0] < times[i-1][0]:
        times[i] = (times[i-1][0], times[i][1])

# ---- write aligned chant.json ----
out = {"title": chant.get("title"), "subtitle": chant.get("subtitle"),
       "aligned_by": "mms_fa", "lines": []}
k = 0
for ln in chant["lines"]:
    words = []
    for w in ln["words"]:
        st, en = times[k]; k += 1
        words.append({"cy": w["cy"], "t": st})
    out["lines"].append({"en": ln.get("en"), "words": words})
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

allt = [t[0] for t in times]
print(f"\nwrote {OUT}")
print(f"first word: {allt[0]}s   last word: {allt[-1]}s   span: {allt[-1]-allt[0]:.1f}s")
print("first 8 words:")
for (li, wi, cy), (st, en) in list(zip(flat, times))[:8]:
    print(f"  {st:6.2f}-{en:6.2f}  {cy}")
