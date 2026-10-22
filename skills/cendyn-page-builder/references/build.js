// Paste-ready build helpers for javascript_tool. Re-define after every navigation.

const S = s => (s || '').toString().replace(/[^A-Za-z0-9 \-_.:]/g, ' ').replace(/\s+/g, ' ').trim();
const pickForm = d => {
  const fs = [...d.querySelectorAll('form')];
  return fs.find(f => f.querySelector('[name="name"]')) ||
         fs.sort((a, b) => b.querySelectorAll('input,select,textarea').length -
                           a.querySelectorAll('input,select,textarea').length)[0];
};

// Step 1: create. pageFields = {name:'…', slug:'…', descr_short:'…'}; categories = ['13']
async function createPage(createPath, pageFields, categories) {
  const d = new DOMParser().parseFromString(
    await fetch(createPath, { credentials: 'include' }).then(r => r.text()), 'text/html');
  const fd = new FormData(pickForm(d));
  if (categories) { fd.delete('categories[]'); categories.forEach(c => fd.append('categories[]', c)); }
  Object.entries(pageFields).forEach(([k, v]) => fd.set(k, v));
  const r = await fetch(createPath, { method: 'POST', credentials: 'include', body: fd, redirect: 'follow' });
  return { status: r.status, landed: r.url.replace(/^https?:\/\/[^/]+/, '') };
}

// Step 2: open Import and fill textarea (then coordinate-click the Import button)
async function openImport(selector, json) {
  document.querySelector(selector).click();
  await new Promise(r => setTimeout(r, 2000));
  const dlg = [...document.querySelectorAll('.ui-dialog')].find(e => e.offsetParent !== null);
  const ta = dlg.querySelector('textarea');
  ta.value = typeof json === 'string' ? json : JSON.stringify(json);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  return { ready: !!dlg, len: ta.value.length };
}
const sectionCount = () => new Set([...document.querySelectorAll('[name^="channel["]')]
  .map(e => e.name.match(/^channel\[([^\]]+)\]/)[1])).size;

// Step 3: fill from LIVE page and save.
// copy = {'[elements][155]': '<p>…</p>', '[row_0][elements][161]': '3 Beds'}
// images = {'thumbnail[image_id]': 1062, '[row_0][elements][79][image_id]': 1063}
async function saveLive(editPath, copy, images) {
  const fd = new FormData(pickForm(document));
  const names = [...fd.keys()];
  const applied = [], missed = [];
  const set = (suf, val, isImg) => {
    const hits = names.filter(n => n === suf || n.endsWith(suf));
    if (!hits.length) { missed.push(suf); return; }
    hits.forEach(n => {
      fd.set(n, String(val));
      if (isImg) { const b = n.replace(/\[image_id\]$/, '');
        ['[cropping]', '[focal_point]'].forEach(x => { if (names.includes(b + x)) fd.set(b + x, ''); }); }
    });
    applied.push(suf);
  };
  Object.entries(copy || {}).forEach(([k, v]) => set(k, v, false));
  Object.entries(images || {}).forEach(([k, v]) => set(k, v, true));
  if (missed.length) return { aborted: true, missed, note: 'profile mismatch: nothing posted' };
  const r = await fetch(editPath, { method: 'POST', credentials: 'include', body: fd, redirect: 'follow' });
  return { status: r.status, landed: r.url.replace(/^https?:\/\/[^/]+/, ''), fields: names.length,
           applied: applied.length, missed };
}

// Step 4: verify a saved page by suffix
async function verify(editPath, suffixes) {
  const d = new DOMParser().parseFromString(
    await fetch(editPath, { credentials: 'include' }).then(r => r.text()), 'text/html');
  const out = {};
  suffixes.forEach(s => { const e = [...d.querySelectorAll('[name]')].find(x => x.name === s || x.name.endsWith(s));
    out[s] = e ? S(e.tagName === 'TEXTAREA' ? e.textContent : e.value).slice(0, 40) : 'MISSING'; });
  out._sections = new Set([...d.querySelectorAll('[name^="channel["]')].map(e => e.name.match(/^channel\[([^\]]+)\]/)[1])).size;
  return out;
}
