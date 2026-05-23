/* ----------------------------------------------------------------------
   Тиха Молитва — the listening experience
   Loads data/chant.json, paints the lines, and lets the audio's own
   clock decide which word is glowing in this exact moment.
   ---------------------------------------------------------------------- */

const audio       = document.getElementById('audio');
const sceneImage  = document.getElementById('sceneImage');
const veil        = document.getElementById('veil');
const enterBtn    = document.getElementById('enterBtn');
const chantEl     = document.getElementById('chant');

let chant = null;          // the loaded data
let flatWords = [];        // [{ start, lineIndex, el }] sorted by start time
let currentLine = -1;
let currentWord = -1;
const EMERGE_END = 6;      // background fully emerged just as the first word arrives (~5.68s)
const BG_MAX = 0.25;       // end state: 75% dimmed (peaks at 25% opacity)
let textRevealEnd = 6.68;  // verse text fully bloomed 1s before the first word (set in buildLines)

/* ---- load the chant data ---- */
async function loadChant() {
  try {
    const res = await fetch('data/chant.json', { cache: 'no-store' });
    if (!res.ok) throw new Error(res.status);
    chant = await res.json();
  } catch (e) {
    chant = SAMPLE; // graceful fallback so the site is never blank
  }
  buildLines();
}

/* ---- render lines + words ---- */
let lineData = [];   // per line: { enSpans:[...], cyCount } for proportional EN highlight

function buildLines() {
  chantEl.innerHTML = '';
  flatWords = [];
  lineData = [];

  chant.lines.forEach((line, li) => {
    const lineEl = document.createElement('div');
    lineEl.className = 'line';
    lineEl.dataset.line = li;

    const cy = document.createElement('div');
    cy.className = 'line__cy';

    const cyWords = line.words || [];
    cyWords.forEach((w, wi) => {
      const span = document.createElement('span');
      span.className = 'w';
      span.textContent = w.cy;
      cy.appendChild(span);
      cy.appendChild(document.createTextNode(' '));
      flatWords.push({ start: w.t, lineIndex: li, wiInLine: wi, el: span });
    });

    lineEl.appendChild(cy);

    // English, split into words so it can fill in alongside the chant
    const enSpans = [];
    if (line.en) {
      const en = document.createElement('div');
      en.className = 'line__en';
      line.en.split(' ').forEach((word) => {
        const s = document.createElement('span');
        s.className = 'ew';
        s.textContent = word;
        en.appendChild(s);
        en.appendChild(document.createTextNode(' '));
        enSpans.push(s);
      });
      lineEl.appendChild(en);
    }
    // chunk boundaries: which English words belong to each Serbian word
    const chunks = line.chunks || [];
    const chunkStart = [];
    let acc = 0;
    for (const c of chunks) { chunkStart.push(acc); acc += c; }
    lineData[li] = { enSpans, cyCount: cyWords.length, chunks, chunkStart };
    chantEl.appendChild(lineEl);
  });

  flatWords.sort((a, b) => a.start - b.start);
  // the verse text slowly blooms in during the intro,
  // reaching full visibility 1 second before the first sung word
  if (flatWords.length) textRevealEnd = Math.max(0.5, flatWords[0].start - 1.0);
  if (document.title === 'document') document.title = chant.title || 'A Serbian Chant';
}

/* ---- render the text/glow for whatever time the audio is at ----
   Called both by the playback loop and on every seek, so the text always
   tracks the audio — scrub, rewind, jump, paused or playing. */
function renderAt(t) {
  // find the last word whose start time has passed
  let idx = -1;
  for (let i = 0; i < flatWords.length; i++) {
    if (flatWords[i].start <= t + 0.02) idx = i;
    else break;
  }

  if (idx !== currentWord) {
    flatWords.forEach((w, i) => {
      w.el.classList.toggle('now', i === idx);
      w.el.classList.toggle('sung', i < idx);
    });
    currentWord = idx;

    const li = idx >= 0 ? flatWords[idx].lineIndex : -1;
    if (li !== currentLine) {
      if (currentLine >= 0) highlightEnglish(currentLine, 0);  // reset the line we left
      setActiveLine(li);
      currentLine = li;
    }
    // fill the English in step with how far the verse has been chanted
    if (li >= 0) highlightEnglish(li, flatWords[idx].wiInLine + 1);
  }

  // background very slowly appears, fully emerged (to 25% opacity) by EMERGE_END
  if (sceneImage) {
    sceneImage.style.opacity = Math.max(0, Math.min(1, t / EMERGE_END)) * BG_MAX;
  }

  // verse text blooms in across the intro, fully present 1s before the first word
  if (chantEl) {
    chantEl.style.opacity = Math.max(0, Math.min(1, t / textRevealEnd));
  }
}

/* Light the English by CHUNK: each Serbian word owns a contiguous span of
   English words (chunks abut, covering the whole line — no gaps). When the
   Serbian word at position cyPos (1-based; 0 resets) is current, its English
   chunk glows; everything before it stays lit. */
function highlightEnglish(li, cyPos) {
  const data = lineData[li];
  if (!data || !data.enSpans.length) return;
  if (cyPos <= 0) {
    data.enSpans.forEach((s) => s.classList.remove('ew-now', 'ew-sung'));
    return;
  }
  const wi = cyPos - 1;
  const start = data.chunkStart[wi] ?? data.enSpans.length;
  const end = start + (data.chunks[wi] || 0);
  data.enSpans.forEach((s, i) => {
    s.classList.toggle('ew-sung', i < start);
    s.classList.toggle('ew-now', i >= start && i < end);
  });
}

/* the playback heartbeat */
function tick() {
  if (!audio.paused) requestAnimationFrame(tick);
  renderAt(audio.currentTime);
}

/* jump the audio to a time and snap the text to it immediately */
function seek(t) {
  if (!audio.duration) return;
  audio.currentTime = Math.max(0, Math.min(audio.duration, t));
  renderAt(audio.currentTime);   // snap text now, don't wait for the next frame
}

function setActiveLine(li) {
  // before the first word is sung, hold on the opening verse
  const show = li < 0 ? 0 : li;
  document.querySelectorAll('.line').forEach((el, i) => {
    el.classList.toggle('is-active', i === show);
  });
  fitLine(show);
}

// shrink the Cyrillic so the whole verse sits on one unbroken line
const BASE_CY_PX = 64;            // matches .line__cy base font-size (4rem)
function fitLine(i) {
  const line = document.querySelectorAll('.line')[i];
  if (!line) return;
  const cy = line.querySelector('.line__cy');
  if (!cy) return;
  const avail = window.innerWidth * 0.92;
  cy.style.fontSize = BASE_CY_PX + 'px';
  const natural = cy.scrollWidth;
  if (natural > avail) {
    cy.style.fontSize = Math.max(20, BASE_CY_PX * (avail / natural)) + 'px';
  }
}

// re-fit the active verse if the window resizes
window.addEventListener('resize', () => {
  const active = document.querySelector('.line.is-active');
  if (active) fitLine([...document.querySelectorAll('.line')].indexOf(active));
});

/* ---- enter the experience ---- */
let canToggle = false;          // gates click-to-pause until the veil has lifted
let entered = false;

/* ---- background ambient (starts on the pre-veil click) ---- */
const bgSfx = document.getElementById('bgSfx');
if (bgSfx) bgSfx.volume = 0.6;

/* ---- pre-veil: the click that wakes the audio, then 135 fades in ---- */
const preveil = document.getElementById('preveil');
if (preveil) {
  preveil.addEventListener('click', () => {
    if (bgSfx) bgSfx.play().catch(() => {});  // user gesture — now allowed
    preveil.classList.add('is-gone');
    // let the pre-veil fade, then bring 135 in with the rise it had before
    setTimeout(() => {
      veil.classList.add('is-shown');
      enterBtn.classList.add('is-rising');
    }, 600);
  }, { once: true });
}
function fadeOutBg(dur) {
  if (!bgSfx) return;
  const start = bgSfx.volume; const steps = 24;
  let i = 0;
  const iv = setInterval(() => {
    i++;
    bgSfx.volume = Math.max(0, start * (1 - i / steps));
    if (i >= steps) {
      clearInterval(iv);
      try { bgSfx.pause(); bgSfx.currentTime = 0; } catch (e) {}
    }
  }, (dur * 1000) / steps);
}

/* ---- the seal-opening sound on the 135 click ---- */
function playUnlock() {
  // play the seal/book-opening file Tim picked
  const sfx = document.getElementById('sealSfx');
  if (!sfx) return;
  try { sfx.currentTime = 0; sfx.play(); } catch (e) {}
}

/* Looping hover hum on 135 — fades in while pointing, fades out on leave.
   The file is already slowed + reverbed, so each loop sustains as bzzzzzhhh. */
const hoverSfx = document.getElementById('hoverSfx');
const HOVER_PEAK = 0.5;
let hoverFade = null;
function hoverIn() {
  if (!hoverSfx) return;
  clearInterval(hoverFade);
  hoverSfx.volume = Math.min(hoverSfx.volume, HOVER_PEAK);
  hoverSfx.play().catch(() => {});
  let v = hoverSfx.volume; const steps = 14;
  hoverFade = setInterval(() => {
    v += HOVER_PEAK / steps;
    if (v >= HOVER_PEAK) { v = HOVER_PEAK; clearInterval(hoverFade); hoverFade = null; }
    hoverSfx.volume = v;
  }, 24);
}
function hoverOut() {
  if (!hoverSfx) return;
  clearInterval(hoverFade);
  let v = hoverSfx.volume; const steps = 16;
  hoverFade = setInterval(() => {
    v -= HOVER_PEAK / steps;
    if (v <= 0) {
      v = 0; clearInterval(hoverFade); hoverFade = null;
      try { hoverSfx.pause(); hoverSfx.currentTime = 0; } catch (e) {}
    }
    hoverSfx.volume = Math.max(0, v);
  }, 32);
}

function enter() {
  if (entered) return;          // ignore the bubbled/extra clicks
  entered = true;

  enterBtn.classList.add('opening');   // 135 flares + dissolves into the dark
  fadeOutBg(1.2);                       // the ambient hum fades away
  playUnlock();                        // the seal sound rides the dissolve

  // wait for the 135 animation to complete, then lift the veil
  setTimeout(() => {
    veil.classList.add('is-gone');
    document.body.classList.add('is-revealed');
    setActiveLine(0);
    // a held breath of darkness, then the chant and the image emerge together
    setTimeout(() => { play(); canToggle = true; }, 1000);
  }, 1600);
}

function play() {
  audio.play().then(() => {
    document.body.classList.add('is-playing');
    requestAnimationFrame(tick);
  }).catch(() => {/* user gesture needed; ignore */});
}

function pause() {
  audio.pause();
  document.body.classList.remove('is-playing');
}

function togglePlay() { audio.paused ? play() : pause(); }

/* ---- controls (no on-screen panel) ---- */
enterBtn.addEventListener('click', enter);
enterBtn.addEventListener('mouseenter', hoverIn);
enterBtn.addEventListener('mouseleave', hoverOut);
audio.addEventListener('ended', () => pause());
audio.addEventListener('play',  () => requestAnimationFrame(tick));
// whenever the audio's clock moves — including native seeks — re-sync the text
audio.addEventListener('seeked',     () => renderAt(audio.currentTime));
audio.addEventListener('timeupdate', () => { if (audio.paused) renderAt(audio.currentTime); });

// once inside, a click/tap anywhere quietly toggles play/pause
document.addEventListener('click', () => { if (canToggle) togglePlay(); });

// keyboard: space play/pause · ← → seek 10s · T toggles translation
document.addEventListener('keydown', (e) => {
  if (veil.classList.contains('is-gone') === false) {
    if (e.code === 'Space' || e.code === 'Enter') { e.preventDefault(); enter(); }
    return;
  }
  if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
  else if (e.code === 'ArrowRight') { e.preventDefault(); seek(audio.currentTime + 10); }
  else if (e.code === 'ArrowLeft')  { e.preventDefault(); seek(audio.currentTime - 10); }
  else if (e.key.toLowerCase() === 't') { document.body.classList.toggle('hide-translation'); }
});

/* ---- a tiny sample so the page is alive before real data arrives ---- */
const SAMPLE = {
  title: 'Тиха Молитва',
  lines: [
    { en: 'Holy God, Holy Mighty, Holy Immortal,',
      words: [ {cy:'Свети', t:0.0}, {cy:'Боже,', t:1.1}, {cy:'Свети', t:2.4}, {cy:'Крепки,', t:3.5}, {cy:'Свети', t:5.0}, {cy:'Бесмртни,', t:6.1} ] },
    { en: 'have mercy on us.',
      words: [ {cy:'помилуј', t:8.0}, {cy:'нас.', t:9.6} ] },
    { en: 'Glory to the Father, and to the Son, and to the Holy Spirit.',
      words: [ {cy:'Слава', t:11.5}, {cy:'Оцу', t:12.8}, {cy:'и', t:13.6}, {cy:'Сину', t:14.2}, {cy:'и', t:15.4}, {cy:'Светоме', t:16.0}, {cy:'Духу.', t:17.6} ] },
  ]
};

loadChant();
