// One-call inventory of every ACM section definition on a Cendyn site (read-only).
// Run with javascript_tool in the logged-in admin tab. Returns compact lines; nothing is saved.
// Output uses '.' and '|' only (no brackets/quotes) so the tool's sanitizer does not block it.
// Set CP to any property id that exists on the site (definitions are site-wide).
const CP = 1;
const S = s => (s || '').toString().replace(/[^A-Za-z0-9 \-_.:|]/g, ' ').replace(/\s+/g, ' ').trim();
const get = async p => new DOMParser().parseFromString(await fetch(p, { credentials: 'include' }).then(r => r.text()), 'text/html');
const idx = await get('/admin/channel');
const ids = [...new Set([...idx.querySelectorAll('a[href*="/admin/channel/edit/id/"]')].map(a => +a.getAttribute('href').match(/id\/(\d+)/)[1]))];
const defs = {};
for (const id of ids) {
  const d = await get(`/admin/channel/edit/cp/${CP}/id/${id}`);
  const f = [...d.querySelectorAll('form')].sort((a, b) => b.querySelectorAll('input,select,textarea').length - a.querySelectorAll('input,select,textarea').length)[0];
  const el = {}, order = [];
  f.querySelectorAll('[name^="elements["]').forEach(e => {
    const parts = [...e.name.matchAll(/\[([^\]]*)\]/g)].map(m => m[1]);
    const i = parts.findIndex(p => ['id', 'type', 'slug', 'title', 'settings'].includes(p));
    if (i < 0) return;
    const key = parts.slice(0, i).join('/'), prop = parts.slice(i).join('.');
    if (!el[key]) { el[key] = {}; order.push(key); }
    const o = el[key];
    if (['id', 'type', 'slug'].includes(prop)) o[prop] = e.value;
    else if (prop === 'settings.attributes.required' && e.checked) o.req = 1;
    else if (prop === 'settings.size.width') o.w = e.value;
    else if (prop === 'settings.size.height') o.h = e.value;
  });
  // 'Related Modules' table = every page using this section (title + property)
  const used = [...d.querySelectorAll('table')].filter(t => /Property/.test(t.innerText)).flatMap(t => [...t.querySelectorAll('tbody tr')]).length;
  defs[id] = { slug: f.querySelector('[name="slug"]')?.value, used,
    tree: order.map(k => ({ d: (k.match(/children/g) || []).length, ...el[k] })) };
}
window.__defs = defs;
// element id -> slug map is needed to read page-form suffixes like [elements][166]
Object.entries(defs).map(([id, v]) => `${id} ${v.slug} used ${v.used} :: ` +
  v.tree.map(t => '>'.repeat(t.d) + t.type + '.' + t.slug + (t.req ? '.REQ' : '') + (t.w ? `.sz${t.w}by${t.h}` : '') + `.eid${t.id}`).join(' | '));
