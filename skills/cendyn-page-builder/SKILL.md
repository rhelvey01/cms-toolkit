---
name: cendyn-page-builder
description: Create pages in any Cendyn CMS module from a cendyn-discovery page-type profile and a cendyn-copy content.json — create, import sections, fill, save, verify. Also places and updates photo galleries.
---

# Cendyn page builder

Builds pages in a Cendyn CMS module from two inputs:

- `content-jobs/<site>/page-types/<type>.json`, from `cendyn-discovery`
- `content.json`, from `cendyn-copy`

If either is missing, run that skill first. Don't rediscover inline.

## Site folder first

Before anything else, open `content-jobs/<site>/` (the user's folder, outside the plugin and the repo). Read, in order: `instructions.md` (rules, never-touch list), `mapping.json` (differences from the base profile, source mapping, section library), `migration-log.csv` (what was already done). Site rules beat the skill defaults. No folder yet: copy `content-jobs/_template/` (or `skills/migration-log/templates/site-folder/`) to `content-jobs/<site>/` and fill in `instructions.md`.

The base Cendyn profile is `skills/cendyn-discovery/references/defaults/`. Use it only after the site folder.

## Before the first page

1. **Collect every image id up front.** You can't leave the page once sections are
   imported (see Step 3), so look up all the ids from `images.folders` first.
2. **Check content fits.** Every `copy` element in the profile needs a content key or an
   explicit skip. Report any repeater overflow before you build.
3. **Pick models.** Do the first page on the strongest model and verify it on the front
   end. Pages 2–N are the same steps with different values, so a cheaper model is fine.

## Per page

Helpers are at the end of this file. Pick the form by content (`[name="name"]`), never by
position or `action`.

### Step 1 — Create

`GET` the create page → `FormData` from its form → set page-level fields from content
(match the template for anything unclear; e.g. leave `h1`/`roomcode` blank if the
template does) → `POST` to the create endpoint. Then re-read the list page to get the
new id. The create response is a redirect and doesn't reliably contain it.

### Step 2 — Import sections

Skip this step if `import.supported` is false, and stop and ask the user. Otherwise:

1. Navigate to the new page's edit URL.
2. In JS: click `import.button_selector`, wait ~2s, put `import.json` in the visible
   `.ui-dialog` textarea and dispatch `input`.
3. Screenshot, then **coordinate-click** the dialog's Import button. JS `.click()` does
   nothing on it; it needs a trusted event.
4. Confirm the number of section hashes now equals `import.json.length`.

### Step 3 — Fill and save from the live page

> **Imported sections live only in the page DOM until you save.** Navigating away, even
> to fetch image ids, silently discards them, and the next save writes a page with no
> sections. Fill and POST from the same page you imported on.

From the live form:

- `copy` → set from content (`ul` format wraps items as `<ul><li>`)
- `image` → set the id, and blank sibling `[cropping]` and `[focal_point]`
- `icon`, `keep`, `link`, `empty` → leave as they are
- Match fields by **suffix**; for `[row_{n}]` elements, iterate rows up to the template's
  row count

POST to the edit endpoint. **Success = redirect to `endpoints.success_redirect`.**
Landing back on the edit page means the POST was rejected.

Log every suffix as `applied` or `missed`. Any miss means the page differs from the
profile: stop and re-run discovery for this page type.

### Step 4 — Verify

Re-fetch the edit page and check: category/type, section count, every `copy` field
non-empty, image ids as assigned, icons unchanged. Fetch the public URL and check for
HTTP 200 and the page name. Screenshot the first page built; a 200 can still have a
broken hero.

## Images

The default strategy (no contact sheet) is the lowest ids first from the page's folder.
That's **structurally correct and aesthetically arbitrary**. Say so in the report and
don't present the choices as curated. If a contact sheet or classifier output is
provided, use its assignments instead.

## Widgets and galleries

Widgets (gallery, faq, rooms, categories) sit in two places: as a **shortcode span in `content[body]`**, or as a **widget element inside a section** (an ACM). A gallery can be either. Decide in this order: the user's request, then the site's `instructions.md`, then what the site's reference page uses (the section library in `mapping.json` shows which gallery sections exist). Default to the body widget; use a section only when one of those says so, and say which you used in the report. Never mix both on one page.

### Body widget (the default)

`content[body]` holds a CKEditor span:

```html
<p><span class="hebs-widget-shortcode"
  data-widget-shortcode="{widget name=&quot;gallery&quot; action=&quot;index&quot; template=&quot;photo-gallery-page&quot; id=&quot;173,162,469&quot;}"
  contenteditable="false">Gallery@Index · Template: photo-gallery-page · Id: …<span class="hebs-widget-shortcode-edit" contenteditable="false" title="Edit Widget">&#9998;</span></span></p>
```

- `template="photo-gallery-page"` gives the filterable "Show all / category" grid. Legacy pages use `template="index"` or none.
- `id` is a comma list of gallery ids (galleries are per property). **No `id` means all galleries.**
- The label text after `Gallery@Index` is cosmetic; the attribute renders. Keep it accurate anyway.
- Build the span with DOM calls (`setAttribute`), never string concatenation, so quotes serialise as `&quot;`.

Rule (confirm once per site): set `template="photo-gallery-page"` and `id` to **every gallery the property has**. Keep intro text above the widget and replace the old widget in place. Get a property's gallery list from `GET /admin/channel/frontsection/cp/{cp}?id=62` (JSON `{data: html}`): the options of the select ending `[357][id][]` are the gallery ids and names. Keep the old widget's ids first, in their original order, then append the rest.

### Gallery section (when asked for)

Add the site's gallery section (for example `image-gallery`, id 62 on one site) through Step 2, fill its title, body and link, and set its widget element to the same gallery ids. Pages that already use a section stay as sections unless the user asks to convert them. A section holds no `content[body]` widget, so remove the body widget when you convert, and the reverse.

### Bulk update (one write per page, in the logged-in admin tab)

1. `GET /admin/content/edit/cp/{cp}/id/{page}`; use the form that owns `content[body]`.
2. Parse the body, remove existing `.hebs-widget-shortcode` spans (and their empty `<p>`), then append the new widget paragraph.
3. `new FormData(form)`, set `content[body]`, `POST` to the edit URL with `redirect: 'follow'`.
4. **Success = landed on `/admin/content/menu/...`.** Landing back on the edit URL means rejected.
5. Skip pages with anything other than a gallery widget, and flag them.

### Checks per page (machine checks first, screenshots last)

- Re-fetch the edit page: exactly one gallery (widget or section, not both), `template="photo-gallery-page"` for widgets, `id` equals the intended list, no stray `channel[` section fields on a widget page.
- Fetch the live page with a cache-buster (`?nocache=<ts>`, `cache: 'no-store'`): it has a `.gallery-page` element and images, and no leftover widget markup or `.acm-image-gallery`.
- Leave `(OUTDATED)` modules untouched.

### Gotchas

- **Run writes one at a time.** Parallel POSTs for several properties: two of five silently did not persist.
- **The live page is cached.** A stale page right after a save is normal; always cache-bust.
- **The dev front end goes down.** If every public page times out (including untouched ones), it is an outage, not your change. Verify through the edit page and retry the live checks later.
- **Screenshots:** gallery images fade in only after the page scrolls, and large galleries take several seconds. Zoom out (`document.body.style.zoom = 0.55`), scroll the gallery into view, nudge the scroll, wait, then capture.
- The Versions tab keeps every save with Show Changes: the free before snapshot and the rollback.
- If a section was added by mistake, posting the form without its `channel[…]` fields removes it.

Gallery report: one CSV row per page (property, page id, admin and live URLs, action, old ids, new ids, template or section, intro kept, live check, notes). Pages not touched go in too, with the reason.

## Safety

- Never post a `FormData` built from another page's form. `channel[<hash>][id]` values
  belong to that page and can overwrite it.
- Build pages unpublished unless the user says otherwise.

## Report

Pages built (id, URL, sections, images); costs by phase; issues with severity and
status; decisions; and the review list: every `authored`/`missing` field from
content.json, plus image slots filled by the default strategy.

## Helpers (also in references/build.js)

```js
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
```

## Last step: log it

Before reporting done, append rows to `content-jobs/<site>/migration-log.csv` with the `migration-log` skill (a CSV row per page: date, prompt, backend and live URLs, sections touched, result, problems).
