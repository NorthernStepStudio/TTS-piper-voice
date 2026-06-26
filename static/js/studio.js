/* ── Studio Panel — voice grid, synthesis, player ── */

let selectedVoice = window.APP_CONFIG.voices[0].id;
let currentBlob   = null;
let currentUrl    = null;
let animFrame     = null;
const audioEl     = document.getElementById('audioEl');

/* ── Voice grid ── */
function buildVoiceGrid() {
  const grid = document.getElementById('voiceGrid');
  grid.innerHTML = '';
  window.APP_CONFIG.voices.forEach(v => {
    const c = document.createElement('div');
    c.className = 'voice-card' + (v.id === selectedVoice ? ' selected' : '');
    c.dataset.id = v.id;
    c.innerHTML = `
      <div class="voice-name">${v.name}</div>
      <div class="voice-meta">
        <span class="gdot ${v.gender === 'Female' ? 'f' : 'm'}"></span>
        ${v.gender} · ${v.style}
      </div>`;
    c.addEventListener('click', () => {
      selectedVoice = v.id;
      document.querySelectorAll('.voice-card').forEach(x => x.classList.remove('selected'));
      c.classList.add('selected');
    });
    grid.appendChild(c);
  });
}

/* ── Text helpers ── */
function updateCharCount() {
  const n = document.getElementById('textInput').value.length;
  document.getElementById('charCount').textContent = n + ' / 5000';
}

function setPhrase(text) {
  document.getElementById('textInput').value = text;
  updateCharCount();
}

function resetControls() {
  [
    ['rate',   'rateVal',  fmtPct, 0],
    ['pitch',  'pitchVal', fmtHz,  0],
    ['volume', 'volVal',   fmtPct, 0],
  ].forEach(([id, lid, fmt, def]) => {
    document.getElementById(id).value = def;
    document.getElementById(lid).textContent = fmt(def);
  });
}

/* ── Status bar ── */
function setStatus(msg, type = '') {
  const el = document.getElementById('statusBar');
  el.innerHTML = msg;
  el.className = 'status-bar ' + type;
}

/* ── Synthesize ── */
async function synthesize() {
  const text = document.getElementById('textInput').value.trim();
  if (!text) { setStatus('Please enter some text.', 'error'); return; }

  const sb = document.getElementById('synthBtn');
  const rb = document.getElementById('regenBtn');
  sb.disabled = rb.disabled = true;
  setStatus('<span class="spinner"></span>Generating speech…', 'loading');
  document.getElementById('playerCard').classList.remove('show');

  try {
    const t0 = Date.now();
    const res = await fetch('/api/v1/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        voice:  selectedVoice,
        rate:   +document.getElementById('rate').value,
        pitch:  +document.getElementById('pitch').value,
        volume: +document.getElementById('volume').value,
      }),
    });

    if (!res.ok) {
      const e = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(e.error || res.statusText);
    }

    const blob    = await res.blob();
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

    if (currentUrl) URL.revokeObjectURL(currentUrl);
    currentBlob = blob;
    currentUrl  = URL.createObjectURL(blob);

    audioEl.src = currentUrl;
    await new Promise(r => { audioEl.onloadedmetadata = r; audioEl.load(); });

    setupPlayer(elapsed);
    audioEl.play();
    setStatus('Ready in ' + elapsed + 's', 'ok');
    rb.style.display = '';
  } catch (e) {
    setStatus('Error: ' + e.message, 'error');
  } finally {
    sb.disabled = rb.disabled = false;
  }
}

/* ── Player setup ── */
function setupPlayer(elapsed) {
  document.getElementById('playerCard').classList.add('show');
  const dur = audioEl.duration;
  document.getElementById('timeDuration').textContent = fmtT(dur);
  document.getElementById('seekBar').max = isFinite(dur) ? dur : 100;
  const v = window.APP_CONFIG.voices.find(x => x.id === selectedVoice);
  document.getElementById('playerMeta').textContent =
    `${v ? v.name + ' · ' : ''}${fmtT(dur)} · Generated in ${elapsed}s`;
  drawWaveform();
  startProgress();
}

/* ── Waveform ── */
async function drawWaveform() {
  const canvas = document.getElementById('waveform');
  const ctx = canvas.getContext('2d');
  canvas.width  = canvas.offsetWidth  * devicePixelRatio;
  canvas.height = canvas.offsetHeight * devicePixelRatio;
  try {
    const ab      = await currentBlob.arrayBuffer();
    const ac      = new (window.AudioContext || window.webkitAudioContext)();
    const decoded = await ac.decodeAudioData(ab);
    const data    = decoded.getChannelData(0);
    const w = canvas.width, h = canvas.height;
    const step = Math.ceil(data.length / w), mid = h / 2;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(124,92,252,0.6)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i < w; i++) {
      let mn = 1, mx = -1;
      for (let j = 0; j < step; j++) {
        const v = data[i * step + j] || 0;
        if (v < mn) mn = v;
        if (v > mx) mx = v;
      }
      ctx.moveTo(i, mid + mn * mid * 0.88);
      ctx.lineTo(i, mid + mx * mid * 0.88);
    }
    ctx.stroke();
    ac.close();
  } catch (_) {}
}

/* ── Progress ticker ── */
function startProgress() {
  cancelAnimationFrame(animFrame);
  function tick() {
    if (audioEl.paused || audioEl.ended) {
      if (audioEl.ended) {
        document.getElementById('playBtn').textContent = '▶';
        document.getElementById('waveOverlay').style.width = '0%';
        document.getElementById('seekBar').value = 0;
        document.getElementById('timeCurrent').textContent = '0:00';
      }
      return;
    }
    const pct = (audioEl.currentTime / audioEl.duration) * 100;
    document.getElementById('waveOverlay').style.width = pct + '%';
    document.getElementById('seekBar').value = audioEl.currentTime;
    document.getElementById('timeCurrent').textContent = fmtT(audioEl.currentTime);
    animFrame = requestAnimationFrame(tick);
  }
  animFrame = requestAnimationFrame(tick);
}

/* ── Player controls ── */
function togglePlay() {
  if (!currentUrl) return;
  if (audioEl.paused) {
    audioEl.play();
    document.getElementById('playBtn').textContent = '⏸';
    startProgress();
  } else {
    audioEl.pause();
    document.getElementById('playBtn').textContent = '▶';
  }
}

function seek(delta) {
  if (!currentUrl) return;
  audioEl.currentTime = Math.max(0, Math.min(audioEl.duration, audioEl.currentTime + delta));
}

function onSeek(val) {
  if (currentUrl) audioEl.currentTime = +val;
}

function downloadAudio() {
  if (!currentBlob) return;
  const a = document.createElement('a');
  a.href = currentUrl;
  a.download = 'speech.mp3';
  a.click();
}

audioEl.addEventListener('play',  () => { document.getElementById('playBtn').textContent = '⏸'; startProgress(); });
audioEl.addEventListener('pause', () => { document.getElementById('playBtn').textContent = '▶'; });

/* ── Keyboard shortcut ── */
document.getElementById('textInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && e.ctrlKey) { e.preventDefault(); synthesize(); }
});

/* ── Init ── */
buildVoiceGrid();
updateCharCount();
