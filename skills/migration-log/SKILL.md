---
name: migration-log
description: Keep one living migration record per site as a CSV. After any write to a Cendyn CMS (page edit, section change, category or setting change), append rows with the date, prompt, backend and live URLs, sections touched, result and problems. Use at the end of every discovery-to-build job, or when asked to log, record or summarise what was changed on a site.
---

# Migration log

Each site has a folder: `content-jobs/<site>/`, outside this plugin and outside the repo. It holds `instructions.md`, `mapping.json` and `migration-log.csv`. The log is one file per site; never create a second one, and never write client data into the plugin.

Read the folder's `instructions.md` before logging; it may add site-specific rules (extra columns are not allowed, extra notes go in `problems`).

Start a new site by copying `templates/site-folder/` (or `content-jobs/_template/`) to `content-jobs/<site>/`.

## When to write

After every job that changed the CMS, before reporting done. Read-only discovery gets rows too, marked "read-only", so the next session knows what was mapped.

## Columns

`date, prompt, job, cp, property, backend_url, live_url, sections_updated, result, problems`

## Rules

- **One row per page changed per job.** A job that changes 27 pages adds 27 rows with the same date, prompt and job. A change with no page (a category, a setting) uses its backend list URL in `backend_url`.
- Append rows to the end of the file; the file is sorted by date when viewed. Edit older rows only to correct a fact.
- `date` is the day the work ran (YYYY-MM-DD). If unknown, write "Date not recorded". Never guess one.
- `prompt` is the user's request as given, the same text on every row of a job. If not saved, write "not recorded".
- `cp` is the property id, blank for brand level. `backend_url` is the admin edit link with property and page ids. `live_url` is the public page, blank if none.
- `sections_updated` lists section ids and slugs with added, edited, reordered or removed (for example `59 neighborhood added`), or "none".
- `result` is only what a re-read confirmed. Mark anything unchecked as "not verified".
- `problems` is mandatory per job: anything that failed, was skipped, hit a wrong scope, or needs a person (leftovers automation cannot delete). Write it on the rows it affects; leave it blank only if there was none.
- Quote any field containing a comma or newline. Save as UTF-8 with BOM so Excel opens it cleanly.
- Do not paste raw JSON. Link to files in `content-jobs/<site>/` by name instead.
