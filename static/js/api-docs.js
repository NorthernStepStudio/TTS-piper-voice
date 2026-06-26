/* ── API Panel — sidebar, code tabs, playground ── */

/* ── Sidebar scroll ── */
function apiScrollTo(selector, el) {
  event.preventDefault();
  document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
  el.classList.add('active');
  const target = document.querySelector(selector);
  if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ── Code tabs ── */
function showCode(tab, panelId) {
  const group = tab.closest('.endpoint-body');
  group.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
  group.querySelectorAll('.code-panel').forEach(p => p.classList.remove('active'));
  tab.classList.add('active');
  document.getElementById(panelId).classList.add('active');
}

function copyCode(btn) {
  const raw = btn.closest('.code-block').innerText.replace(/^Copy\n?/, '');
  navigator.clipboard.writeText(raw).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

/* ── Playground ── */
async function runPlayground() {
  const text = document.getElementById('pgText').value.trim();
  if (!text) return;

  const btn    = document.getElementById('pgBtn');
  const result = document.getElementById('pgResult');
  btn.disabled = true;
  btn.textContent = '⏳ Running…';
  result.className = 'pg-result';
  result.textContent = 'Calling API…';
  document.getElementById('pgAudioWrap').style.display = 'none';

  const endpoint = document.getElementById('pgEndpoint').value;
  const payload  = {
    text,
    voice: document.getElementById('pgVoice').value,
    rate:  +document.getElementById('pgRate').value,
    pitch: +document.getElementById('pgPitch').value,
  };

  try {
    const t0  = Date.now();
    const res = await fetch('/api/v1/' + endpoint, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const elapsed = ((Date.now() - t0) / 1000).toFixed(2);

    if (endpoint === 'speak') {
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || res.statusText);
      const display = { ...json, audio: { ...json.audio, base64: json.audio.base64.slice(0, 40) + '… [truncated]' } };
      result.className  = 'pg-result ok';
      result.textContent = `HTTP ${res.status} · ${elapsed}s\n\n` + JSON.stringify(display, null, 2);
      const audio = document.getElementById('pgAudio');
      audio.src   = `data:${json.audio.mime_type};base64,${json.audio.base64}`;
      document.getElementById('pgAudioWrap').style.display = '';
      audio.play().catch(() => {});
    } else {
      if (!res.ok) {
        const e = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(e.error || res.statusText);
      }
      const blob = await res.blob();
      result.className  = 'pg-result ok';
      result.textContent = `HTTP 200 · ${elapsed}s · ${blob.size.toLocaleString()} bytes\nContent-Type: ${res.headers.get('Content-Type')}\n\nAudio ready ↓`;
      const audio = document.getElementById('pgAudio');
      audio.src   = URL.createObjectURL(blob);
      document.getElementById('pgAudioWrap').style.display = '';
      audio.play().catch(() => {});
    }
  } catch (e) {
    result.className  = 'pg-result err';
    result.textContent = 'Error: ' + e.message;
  } finally {
    btn.disabled    = false;
    btn.textContent = '▶ Run Request';
  }
}
