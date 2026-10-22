# Cendyn CMS defaults

What is the same on every Cendyn CMS site (v.11.4). Discovery starts here and records only what differs.

## Use

1. Read these defaults instead of re-mapping modules, widgets, settings and page-level fields.
2. Run `../probe-sections.js` in the logged-in admin tab to read the site's section definitions.
3. Write the **differences only** to `content-jobs/<site>/` (outside the repo): `mapping.json` (differences, source mapping and section library in one file) and any `page-types/<type>.json` that differs. Start from `skills/migration-log/templates/site-folder/mapping.json`.
4. Run the discovery dry run (step 7). A field that does not match is a difference: record it for the site, do not edit these defaults.
5. Log the work in `content-jobs/<site>/migration-log.csv`.

## What is default vs per site

| File | Default (here) | Per site (in `content-jobs/<site>/`) |
|---|---|---|
| `modules.json` | Admin modules, endpoints, page-level fields, whether Import exists | Extra modules, `import_sections` ids (blank here), existing pages |
| `widgets.json` | The 20 widgets, settings, parameters, shortcode format | Option lists: template names, category ids, record names |
| `settings.json` | Page Manager, layout and site settings structure | Values, alert-bar content, loaded section ids |
| `page-types/rooms.json`, `venues.json` | Page-level form fields, tabs, gallery pattern | Feature ids, layout section hashes, categories, `type_id` |
| ACM sections | none | Everything: section ids, slugs, elements (15 on a demo site, 58 on a production site, so no default library) |

## How far to trust it

Checked against one production site's live forms: every default module exists in its admin sidebar; every `venues.json` page-level field is on its venue create form; every `rooms.json` page-level field is on its room create form except `type_id` (optional per site).

Not checked on a second site: `widgets.json` settings, `settings.json`, and the field types and select options in `modules.json`. Treat those as a first guess.

Examples of finished site profiles are in `../examples/`. Blank files are in `../templates/`.
