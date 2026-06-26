/* ── Shared helpers and panel switching ── */

const fmtPct = v => (v >= 0 ? '+' : '') + v + '%';
const fmtHz  = v => (v >= 0 ? '+' : '') + v + ' Hz';
const fmtT   = s => {
  if (!isFinite(s)) return '0:00';
  return Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');
};

function switchPanel(name, tab) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  tab.classList.add('active');
}

function copyText(text, el) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = el.textContent;
    el.textContent = '✓';
    setTimeout(() => { el.textContent = orig; }, 1800);
  });
}
