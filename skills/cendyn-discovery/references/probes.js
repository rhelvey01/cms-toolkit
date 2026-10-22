// Paste-ready probes for javascript_tool. Each returns sanitized JSON.
// Run in the logged-in admin tab. Same-origin fetch only.

// --- shared helpers (prepend to any probe) ---
const S = s => (s || '').toString().replace(/[^A-Za-z0-9 \-_.:]/g, ' ').replace(/\s+/g, ' ').trim();
const getDoc = async path => new DOMParser().parseFromString(
  await fetch(path, { credentials: 'include' }).then(r => r.text()), 'text/html');
// Pick the content form: the one with [name=name], else the one with most fields.
const pickForm = d => {
  const fs = [...d.querySelectorAll('form')];
  return fs.find(f => f.querySelector('[name="name"]')) ||
         fs.sort((a, b) => b.querySelectorAll('input,select,textarea').length -
                           a.querySelectorAll('input,select,textarea').length)[0];
};
const suffix = n => n.replace(/^channel\[[^\]]+\]/, '');

// --- 1. module inventory (run on any admin page) ---
// [...document.querySelectorAll('a[href^="/admin/"]')].map(a => ({t: S(a.textContent), h: a.getAttribute('href')}))
//   .filter(x => x.t && /\/admin\/[a-z]+(\/(create|index))?$/.test(x.h))

// --- 2. page-level form ---
async function pageFields(createPath) {
  const f = pickForm(await getDoc(createPath));
  return [...f.querySelectorAll('input,select,textarea')].filter(e => e.name && !e.name.startsWith('channel['))
    .map(e => ({ n: e.name, t: e.tagName === 'SELECT' ? 'select' : e.type,
      v: e.type === 'checkbox' ? e.value : undefined,
      opts: e.tagName === 'SELECT' ? [...e.options].map(o => o.value + '~' + S(o.text)) : undefined }));
}

// --- 3+4. template sections, grouped by hash, with role hints ---
async function templateSections(editPath) {
  const f = pickForm(await getDoc(editPath));
  const groups = {};
  f.querySelectorAll('[name^="channel["]').forEach(e => {
    const h = e.name.match(/^channel\[([^\]]+)\]/)[1];
    if (/\[settings\]|\[id\]$|\[section_id\]$/.test(e.name)) return;
    const val = e.tagName === 'TEXTAREA' ? e.textContent : e.value;
    (groups[h] = groups[h] || []).push({ s: suffix(e.name), t: e.type, len: (val || '').length,
      preview: S(val).slice(0, 30) });
  });
  // icon hint: same image_id value repeated across rows of one element
  Object.values(groups).forEach(els => {
    const byEl = {};
    els.filter(x => /\[image_id\]$/.test(x.s)).forEach(x => {
      const k = x.s.replace(/\[row_\d+\]/, '[row_n]'); (byEl[k] = byEl[k] || []).push(x.preview);
    });
    els.forEach(x => {
      const k = x.s.replace(/\[row_\d+\]/, '[row_n]');
      if (byEl[k] && byEl[k].length > 1 && new Set(byEl[k]).size === 1 && byEl[k][0]) x.hint = 'icon';
      else if (/\[image_id\]$/.test(x.s)) x.hint = x.len ? 'image' : 'empty';
      else if (/\[(name|url|target)\]$/.test(x.s)) x.hint = 'link';
      else x.hint = x.len ? 'copy?' : 'empty';
    });
  });
  return groups;
}

// --- 5. import support ---
// const b = document.querySelector('.js-open-popup-import');
// ({ supported: !!b, dataUrl: b && b.dataset.url, sections: b && S(b.dataset.sections) })

// --- 6. image pool folder (after navigating to /admin/ipool?folder_id=N) ---
async function poolIds() {
  const sel = [...document.querySelectorAll('select')].find(s => [...s.options].some(o => o.value === '60'));
  if (sel) { sel.value = '60'; sel.dispatchEvent(new Event('change', { bubbles: true }));
             await new Promise(r => setTimeout(r, 3500)); }
  const ids = [...new Set([...document.querySelectorAll('a[href*="ipool/view/id/"]')]
    .map(a => +(a.getAttribute('href').match(/id\/(\d+)/) || [])[1]).filter(Boolean))].sort((a, b) => a - b);
  return { count: ids.length, ids, info: S((document.querySelector('.dataTables_info') || {}).innerText) };
}
