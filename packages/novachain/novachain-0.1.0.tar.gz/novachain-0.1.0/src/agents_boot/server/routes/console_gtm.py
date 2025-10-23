# src/agents_boot/server/routes/console_gtm.py
from __future__ import annotations
from fastapi import APIRouter, Response

router = APIRouter()

_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>GTM Panel</title>
  <style>
    :root { --c1:#111; --c2:#222; --c3:#2d2d2d; --cA:#09f; --fg:#eaeaea; --ok:#1db954; --err:#ff4d4f; }
    body { background:#0b0b0b; color:var(--fg); font:14px/1.4 system-ui,Segoe UI,Roboto,Helvetica,Arial; margin:0; }
    header { background:var(--c2); padding:16px 20px; border-bottom:1px solid #333; }
    header h1 { margin:0; font-size:18px; letter-spacing:.3px; }
    main { display:grid; grid-template-columns: 340px 1fr; gap:16px; padding:16px; }
    section { background:var(--c3); border:1px solid #333; border-radius:8px; padding:14px; }
    h2 { font-size:14px; margin:0 0 10px 0; color:#aaa; letter-spacing:.4px; }
    label { display:block; margin:8px 0 4px; color:#bbb; }
    input[type=text], select, textarea { width:100%; background:#121212; color:var(--fg); border:1px solid #444; border-radius:6px; padding:8px; }
    textarea { min-height:160px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Courier New", monospace;}
    button { background:var(--cA); border:0; border-radius:6px; color:#fff; padding:10px 12px; margin-right:8px; cursor:pointer; }
    button.secondary { background:#444; }
    .row { display:flex; gap:8px; flex-wrap:wrap; margin:6px 0 10px; }
    .tag { background:#111; border:1px solid #444; border-radius:999px; padding:4px 8px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .status { margin-top:8px; }
    .pill { display:inline-flex; align-items:center; gap:6px; padding:2px 8px; border-radius:999px; border:1px solid #444; }
    .pill.ok { border-color: #2c5; }
    .pill.err { border-color: #e33; }
    small.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Courier New", monospace; color:#aaa; }
    .muted { color:#aaa; }
    .list { max-height: 220px; overflow:auto; border:1px solid #333; border-radius:6px; }
    .list table { width:100%; border-collapse: collapse; }
    .list th, .list td { border-bottom:1px solid #333; padding:6px 8px; font-size:12px; }
    .list th { position: sticky; top:0; background:#1a1a1a; }
  </style>
</head>
<body>
<header><h1>GTM Panel — Multi‑Channel Release</h1></header>
<main>
  <section>
    <h2>Controls</h2>
    <label>Product</label>
    <select id="product"></select>
    <div class="row" id="channels"></div>
    <div class="row">
      <button id="btn-release">Release</button>
      <button id="btn-post" class="secondary">Post‑release only</button>
      <button id="btn-full">Release + Post</button>
    </div>
    <div class="grid-2">
      <div>
        <h2>Latest Release (selected product)</h2>
        <div id="latest" class="list"></div>
      </div>
      <div>
        <h2>Recent History</h2>
        <div id="history" class="list"></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Run Output</h2>
    <div id="status" class="status"></div>
    <label>Raw JSON</label>
    <textarea id="raw" readonly></textarea>
    <p class="muted"><small class="mono">Endpoints used: /gtm/channels, /gtm/catalog, /gtm/release, /gtm/post, /gtm/release_full, /gtm/history</small></p>
  </section>
</main>

<script>
const $ = (s) => document.querySelector(s);

async function loadChannels() {
  const r = await fetch('/gtm/channels'); const j = await r.json();
  const box = $('#channels'); box.innerHTML = '';
  (j.channels || []).forEach(ch => {
    const id = 'ch-' + ch;
    const span = document.createElement('span'); span.className='tag';
    span.innerHTML = '<input type="checkbox" id="'+id+'" data-name="'+ch+'" checked> '+ch;
    box.appendChild(span);
  });
}

async function loadCatalog() {
  const r = await fetch('/gtm/catalog'); const j = await r.json();
  const sel = $('#product'); sel.innerHTML = '';
  (j.products || []).forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id; opt.textContent = p.name + ' ('+p.version+')';
    sel.appendChild(opt);
  });
  await refreshHistory();
}

function selectedChannels() {
  return Array.from(document.querySelectorAll('#channels input[type=checkbox]:checked')).map(x => x.dataset.name);
}

function pills(results=[]) {
  return results.map(r => `<span class="pill ${r.status==='error'?'err':'ok'}">${r.channel}<small class="mono">${r.status}</small></span>`).join(' ');
}

function renderLatest(latest) {
  if (!latest) { $('#latest').innerHTML = '<p class="muted">No releases yet.</p>'; return; }
  const h = `
    <table>
      <thead><tr><th>When</th><th>Version</th><th>Channels</th></tr></thead>
      <tbody>
        <tr>
          <td>${new Date(latest.ts*1000).toLocaleString()}</td>
          <td>${latest.version}</td>
          <td>${pills(latest.results)}</td>
        </tr>
      </tbody>
    </table>`;
  $('#latest').innerHTML = h;
}

function renderHistory(items=[]) {
  if (!items.length) { $('#history').innerHTML = '<p class="muted">—</p>'; return; }
  const rows = items.slice(-10).reverse().map(e => `
    <tr>
      <td>${new Date(e.ts*1000).toLocaleString()}</td>
      <td>${e.version}</td>
      <td>${pills(e.results)}</td>
    </tr>`).join('');
  $('#history').innerHTML = `<table>
    <thead><tr><th>When</th><th>Version</th><th>Channels</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

async function refreshHistory() {
  const pid = $('#product').value;
  const r = await fetch('/gtm/history?product_id=' + encodeURIComponent(pid));
  const j = await r.json();
  renderLatest(j.latest); renderHistory(j.items||[]);
}

async function doPost(url, body) {
  $('#status').innerHTML = 'Running…';
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const j = await r.json();
  $('#raw').value = JSON.stringify(j, null, 2);
  const rel = j.release || j; // release_full nests it
  if (rel.latest || j.latest) await refreshHistory();
  $('#status').innerHTML = (j.ok===true||rel.ok===true) ? '<span class="pill ok">ok</span>' : '<span class="pill err">error</span>';
}

document.addEventListener('DOMContentLoaded', async () => {
  await loadChannels(); await loadCatalog();
  $('#product').addEventListener('change', refreshHistory);
  $('#btn-release').addEventListener('click', () => doPost('/gtm/release', {product_id: $('#product').value, channels: selectedChannels()}));
  $('#btn-post').addEventListener('click', () => doPost('/gtm/post', {product_id: $('#product').value}));
  $('#btn-full').addEventListener('click', () => doPost('/gtm/release_full', {product_id: $('#product').value, channels: selectedChannels()}));
});
</script>
</body></html>
"""

@router.get("/console/gtm")
def console_gtm():
    return Response(content=_HTML, media_type="text/html")
