<<<<<<< HEAD
# CMS Toolkit

Four Claude skills for discovering, moving and recording content in a Cendyn CMS, for any page type (rooms, offers, venues, events, blog, galleries, sections…).

| Skill | Does | Touches the CMS? |
|---|---|---|
| `cendyn-discovery` | Maps one template page into a reusable page-type profile | read-only |
| `cendyn-copy` | Extracts source copy into `content.json`, every field tagged verbatim / derived / authored | no |
| `cendyn-page-builder` | Creates pages from a profile + `content.json`: create → import sections → fill → save → verify. Also places and updates photo galleries (see "Widgets and galleries" in its SKILL.md) | yes (writes) |
| `migration-log` | Appends rows to the site's single living CSV record after every job | no |

```
source pages ──► cendyn-copy ──► content.json
CMS template ──► cendyn-discovery ──► content-jobs/<site>/page-types/<type>.json
                                              │
content.json + profile ──► cendyn-page-builder ──► pages in the CMS ──► content-jobs/<site>/migration-log.csv
```

## Layout

- `skills/*/SKILL.md`: the skills; schemas, JS helpers and examples sit in each `references/`
- `skills/cendyn-discovery/references/defaults/`: what is the same on every Cendyn CMS site (modules, widgets, settings, rooms/venues page fields)
- `skills/cendyn-discovery/references/templates/`: blank page-type profile
- `skills/cendyn-discovery/references/examples/`: anonymised worked example (rooms page type)
- `skills/cendyn-copy/references/example-rooms.content.json`: synthetic content showing the provenance tags
- `skills/migration-log/templates/site-folder/`: blank site folder (instructions.md, mapping.json, migration-log.csv)

## Defaults here, differences outside

Per-site work holds only what differs from the defaults, and lives outside this repo next to it:

```
content-jobs/
  _template/                  blank site folder
  <site>/
    instructions.md           special rules for this site (read first)
    mapping.json              differences from the base Cendyn profile, source-to-Cendyn mapping, section library
    migration-log.csv         the one running log
    page-types/, source-files/   optional
```

Every skill opens `content-jobs/<site>/` first, then falls back to the base Cendyn profile in `skills/cendyn-discovery/references/defaults/`.

`.gitignore` blocks logs, CSVs and `auth.json`. Task writing and Playwright checks are a separate plugin: `task-builder`.
=======
# cms-toolkit
CMS skills and workflows to discover, migration and build pages
>>>>>>> 087b51780422ad1a7a85bc64afa70bb55b5ad97d
