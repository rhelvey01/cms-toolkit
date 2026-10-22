---
name: cendyn-copy
description: Extract copy from any source website (any CMS or platform) verbatim into a provenance-tagged content.json for a Cendyn page type, ready for cendyn-page-builder. Firecrawl first. Use for the content side of a migration into Cendyn.
---

# Cendyn copy

Pulls copy from source pages into `content.json`. The source can be any site on any
platform (WordPress, Squarespace, a custom build, a Cendyn site); only the destination is
Cendyn. Every field records **where its text came from**, so a person can review anything
Claude wrote before it reaches a client site.

## Site folder first

Before anything else, open `content-jobs/<site>/` (the user's folder, outside the plugin and the repo). Read, in order: `instructions.md` (rules, never-touch list), `mapping.json` (differences from the base profile, source mapping, section library), `migration-log.csv` (what was already done). Site rules beat the skill defaults. No folder yet: copy `content-jobs/_template/` (or `skills/migration-log/templates/site-folder/`) to `content-jobs/<site>/` and fill in `instructions.md`.

The base Cendyn profile is `skills/cendyn-discovery/references/defaults/`. Use it only after the site folder.

## Inputs

| Input | Example |
|---|---|
| `source_urls[]`, a site root to map, or a Screaming Frog CSV | the client's existing pages |
| `page_type` profile | `content-jobs/<site>/page-types/<type>.json` from `cendyn-discovery` |

The profile's `content_key` values decide which keys `content.json` must contain. Read
it first; extract only what the page type uses.

## Provenance — the core rule

Every field carries `src`:

| `src` | Meaning | Needs review? |
|---|---|---|
| `verbatim` | copied character-for-character from the source | no |
| `derived` | computed from source facts with no new wording ("3 Beds" from "3 bedrooms") | spot-check |
| `authored` | Claude wrote the wording from source facts | **yes, always** |

Never invent facts. Authored text may only rephrase or combine facts that appear in the
source. If the page type needs a field the source can't support, leave it `null` with
`src: "missing"`. Don't fill it with plausible copy.

## Extraction: most faithful first

1. **Screaming Frog CSV** (if the user provides one). Custom extraction columns map
   straight to content keys. No model in the loop; best fidelity.
2. **Firecrawl (default for web sources).** Use the Firecrawl MCP, CLI or API,
   whichever the session has. If none is available, tell the user and ask for a key
   rather than silently dropping to a lower method.
   - Unknown page list: `map` the site root, then pick the pages with the user.
   - Scrape each page with `formats: ["markdown"]` and `onlyMainContent: true`. Markdown
     output is the page's own text, so it counts as **verbatim**. Add `rawHtml` when
     you need exact markup for `<p>` / `<ul>` values.
   - Many pages: `crawl` with an include-path filter, or batch scrape.
   - **Do not use Firecrawl's LLM / JSON `extract` mode for copy.** A model rewrites the
     text there. If you use it for structure only (e.g. spotting which block is the
     intro), take the wording from the markdown.
   - JS-heavy page that comes back thin: retry with a `waitFor`, or fall back to 3.
3. **Rendered page text from the browser.** Navigate to the source page and read
   `innerText` of the content container via `javascript_tool`. Verbatim.
4. **Tavily extract** (only if a Tavily tool or skill is available this session) for batches of up to 20 URLs. Returns raw
   markdown. Verbatim.
5. **WebFetch, last resort.** It runs a small model over the page and **paraphrases**.
   Ask it to quote, but tag everything from it `authored` unless the step below
   confirms it.

Don't fetch with curl or Python. Stick to the tools above. Record the method used on
each page (`method` in `content.json`).

## Verbatim check

For every `verbatim` field, confirm its text appears as a substring of the raw source
text (normalize whitespace and curly quotes first). Failures get downgraded to
`authored` and listed in the report.

## Mapping to the page type

- **Long copy → sections.** Split source paragraphs across the profile's `copy` elements
  in source order. Don't rewrite a paragraph to fit; if there are more paragraphs than
  slots, join them in the last slot.
- **Lists → repeaters / `<ul>` elements.** If the source has more items than the
  template has rows, put the overflow in a `<ul>` element or flag it. Discovery records
  row counts; adding rows isn't verified to work.
- **Spec badges.** Use the template's pattern ("4 Beds", "8 People") with source
  numbers → `derived`.
- **Keep facts that differ between pages.** If one property lacks something the others
  have (no WiFi, no pool), keep that difference and flag it. Don't normalize it away.
- **Names.** Use the source's spelling. If the CMS needs a different form (e.g. "AcmeSuite" vs
  "Acme Suite"), keep the source spelling in `aliases`, and flag it.

## Output

`content.json`, following `references/content.schema.json`. Shape per field:

```json
"intro": { "value": "<p>…</p>", "src": "verbatim", "from": "https://…#intro" }
```

## Report

- pages extracted, and which method each one used
- count of fields by `src`
- **every `authored` and `missing` field, by page** — this is the review list
- differences between pages that you kept on purpose
- overflow (source items that didn't fit the template)
