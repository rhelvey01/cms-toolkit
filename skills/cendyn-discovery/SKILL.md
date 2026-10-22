---
name: cendyn-discovery
description: Map any Cendyn CMS module (rooms, offers, venues, events, blog, ACM pages) from one template page into a reusable page-type profile. Read-only. Run before migrating content into a new site or page type.
---

# Cendyn discovery

Turns one existing template page in a Cendyn CMS module into a **page-type profile**:
everything `cendyn-page-builder` needs to create more pages like it. Writes nothing to
the CMS.

## Site folder first

Before anything else, open `content-jobs/<site>/` (the user's folder, outside the plugin and the repo). Read, in order: `instructions.md` (rules, never-touch list), `mapping.json` (differences from the base profile, source mapping, section library), `migration-log.csv` (what was already done). Site rules beat the skill defaults. No folder yet: copy `content-jobs/_template/` (or `skills/migration-log/templates/site-folder/`) to `content-jobs/<site>/` and fill in `instructions.md`.

The base Cendyn profile is `skills/cendyn-discovery/references/defaults/`. Use it only after the site folder.

## Inputs

| Input | Required | Example |
|---|---|---|
| `admin_base` | yes | `https://<site>/admin` |
| `template_url` | yes | `/admin/rooms/edit/id/91` — a finished page of the type to clone |
| `page_type` | yes | `rooms`, `offers`, `venues`… (your label) |
| `section_import_json` | if the module has Import | the JSON pasted into the Import dialog |
| `image_folder_id` | if pages need photos | image-pool folder |

**Then check `content-jobs/<site>/page-types/<page_type>.json`** (real site data never lives in this repo). If it exists and the
template hasn't changed, stop — discovery is done.
No site profile? Read `references/defaults/` (modules, widgets, settings and rooms/venues page-level fields are already mapped), run `references/probe-sections.js` once to read every section definition, and write only the **differences** to `content-jobs/<site>/` (`mapping.json`, `page-types/`). The blank mapping is `skills/migration-log/templates/site-folder/mapping.json`, the blank profile is in `references/templates/`, a finished example in `references/examples/`. Then run the step 7 dry run instead of full discovery.

## Tooling

Use `javascript_tool` (built-in browser or Claude in Chrome) in the user's logged-in admin tab, with
same-origin `fetch` + `DOMParser`. Helpers are at the end of this file.

- **Return sanitized values only.** Raw HTML, `<option>` text or anything URL-shaped
  trips `[BLOCKED: Cookie/query string data]`. Strip with
  `s.replace(/[^A-Za-z0-9 \-_.]/g,' ')`.
- If `browser_batch` / `get_page_text` error, use `javascript_tool` + screenshots.
- If the browser bridge times out twice, stop and tell the user. Don't keep retrying.

## Steps

### 1. Module inventory

Read the admin sidebar: every module and its list/create links. Record them in
`mapping.json → modules` the first time you touch a site. Derive the endpoints from
the links rather than assuming `/admin/<module>/create`.

### 2. Page-level form (create page)

`GET` the module's create page. **Pick the form by content, not position or `action`:**
the form that contains `[name="name"]`, or failing that the one with the most fields.
Its `action` is often empty.

Record each page-level field: name, type, select options, checkbox values. Match
checkbox values to labels by DOM order against a screenshot — `<label for>` is often
missing.

### 3. Template sections

`GET` the template's edit page. Group `[name^="channel["]` fields by hash
(`channel[<hash>]…`). Hashes differ per section **and per page**, so describe every
element by **name suffix** (`[elements][155]`, `[row_0][elements][161]`), never full
name.

For each section, record its `section_id` (from the import JSON, in order), title,
elements, and repeater row counts (`row_0…row_N`).

### 4. Classify each element's role

| Role | Heuristic |
|---|---|
| `icon` | `[image_id]` whose value repeats across sibling rows, or wrapper has `data-override-imagesize` ≤ 50px |
| `image` | other `[image_id]` with a value |
| `empty` | blank in the template |
| `link` | `[name]` + `[url]` pair |
| `keep` | value identical on two or more existing pages of the site, or is a class name (`background-primary`) |
| `copy` | everything else with text |

Spot-check `keep` vs `copy` by fetching a second existing page of the same module and
comparing values: identical → `keep`, different → `copy`.

### 5. Import support

Look for `.js-open-popup-import` and record its `data-url` and `data-sections`
(the section ids the module allows). If absent, set `import.supported: false`. The
builder will then stop and ask — don't improvise section creation.

### 6. Image pool (if needed)

Navigate to `/admin/ipool?folder_id=<id>`, wait for the DataTable, set per-page to 60,
read `a[href*="ipool/view/id/"]`. The grid is JS-rendered; a plain `fetch` returns no
ids. Check `.dataTables_info` to confirm the folder filter held. Record organization
(per-page subfolders? descriptive filenames?) and folder ids.

### 7. Dry run

Build `FormData` from the template's live form and confirm every suffix in your profile
matches at least one field. Any miss means the map is wrong; fix it before saving.
**Do not POST.**

### 8. Write outputs

- `content-jobs/<site>/page-types/<page_type>.json` — schema in
  `references/page-type-profile.schema.json`; worked example in
  `references/examples/example-site/page-types/rooms.json`
- `content-jobs/<site>/mapping.json` — one file: add the differences from the defaults, how a non-Cendyn source maps to Cendyn,
  and any newly mapped section ids (under `sections`) so the next page type reuses them

## Report

List: module endpoints, section count, element counts by role, image slots filled vs
empty in the template, import support, and every assumption (especially role guesses
you couldn't confirm with a second page).

## Helpers (also in references/probes.js)

```js
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
```

## Also probe: body widgets and version history

Discovery should not stop at the Sections tab.

- Scan `content[body]` for `.hebs-widget-shortcode` spans and record each widget's name, action and attributes. A widget with no `id` means "all". A `template` attribute means a custom layout.
- Read the Versions tab: "Show Changes" is a free before/after diff and the rollback path. Use it to learn a mapping instead of asking the user to walk through it.
- For a site-wide change, scan every property in one pass and return one compact line per page (property, page id, widget attributes, whether the new section already exists).
- Gallery convert-in-place is described in the "Widgets and galleries" section of `skills/cendyn-page-builder/SKILL.md`.
