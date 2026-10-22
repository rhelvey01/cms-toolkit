# CMS toolkit: file guide

Technical = what it is. ELI5 = the plain version. Paths are relative to `cms-toolkit/`. Defaults and examples are here; real site folders live in `content-jobs/` next to the skills (gitignored, so they stay out of the repo).

| File | Technical | ELI5 |
|---|---|---|
| `README.md` | Overview: four skills, pipeline, layout, what stays out of the repo. | The front page. |
| `FILES.md` | This guide. | The map of the map. |
| `.gitignore` | Blocks site folders, CSV logs and `auth.json` from being committed. | A bouncer for private files. |
| `.claude-plugin/plugin.json` | Plugin manifest (name, version 0.3.0, description). | The name tag that lets Claude load the folder as a plugin. |
| **skills/cendyn-discovery/** | | |
| `SKILL.md` | Read-only recipe: read the defaults, read the site's sections, record differences, dry-run. | How to study a site by checking only what is different from normal. |
| `references/page-type-profile.schema.json` | JSON Schema for a page-type profile. | The blank form a profile follows. |
| `references/probes.js` | Browser probes: modules, page fields, template sections, import, image pool. | Little tools pasted into the browser to look at admin screens. |
| `references/probe-sections.js` | One call that lists every ACM section definition. | Reads the whole building-block catalog at once. |
| `references/defaults/README.md` | How the defaults are used and how far to trust them. | The "start here" note. |
| `references/defaults/modules.json` | Default admin modules, endpoints, page-level fields. | Normal map of every admin area. |
| `references/defaults/widgets.json` | The 20 widgets with settings and parameters. | Normal list of drop-in widgets. |
| `references/defaults/settings.json` | Page Manager, layout and site settings structure. | Normal settings map. |
| `references/defaults/page-types/rooms.json`, `venues.json` | Default room and venue page-level fields, tabs, gallery pattern. | How a room or venue page is normally built. |
| `references/templates/page-type.json` | Blank page-type profile. | Empty form for a new kind of page. |
| `references/examples/example-site/mapping.json`, `page-types/rooms.json` | Anonymised sample profile. | A fake finished profile to copy from. |
| **skills/cendyn-copy/** | | |
| `SKILL.md` | Scrape any source site into `content.json`, tagging each field verbatim / derived / authored. | Gather the old site's words and note where each came from. |
| `references/content.schema.json` | JSON Schema for `content.json`. | The blank form for the copied words. |
| `references/example-rooms.content.json` | Synthetic `content.json` showing provenance tags. | A fake sample of copied words. |
| **skills/cendyn-page-builder/** | | |
| `SKILL.md` | Create, import sections, fill, save, verify from a profile + `content.json`; also the rules for widgets and galleries (body widget or section); last step is the log. The only skill that writes. | Builds the new pages and handles photo galleries, then writes down what it did. |
| `references/build.js` | Helpers for create page, fill sections, save. | The hands that fill the form and press save. |
| **skills/migration-log/** | | |
| `SKILL.md` | Rules for the site folder and its one running CSV log: columns, one row per page per job, mandatory problems. | The rules for the notebook. |
| `templates/site-folder/instructions.md` | Blank site rules. | A blank "read me first" sheet for a site. |
| `templates/site-folder/mapping.json` | Blank site mapping: differences, source mapping, section library. | A blank cheat sheet of what is odd about this site and its building blocks. |
| `templates/site-folder/migration-log.csv` | Header-only blank log. | An empty notebook page. |
| **.git/** | Git metadata (hooks, objects, logs, refs; branch `main`, remote `origin`). | The history book. Do not edit. |

Not committed, in `content-jobs/`: one folder per site (`<site>/` with instructions.md, mapping.json, migration-log.csv, optional page-types/, source-files/), plus `_template/` and `_superseded/`. Every skill reads the site folder first.
