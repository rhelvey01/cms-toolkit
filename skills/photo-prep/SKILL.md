---
name: photo-prep
description: >
  One pass for hotel/property photos: fixes oversized images (under 20 MB, max 5500 x 5500 px)
  so CMS uploads don't error, makes small previews so Claude can look at photos without
  crashing, then QA's the delivery against Cendyn's web photo guidelines — spec check, hero
  picks, IA folder sorting, SafeSpace crop-margin check — and writes a QA report. Use whenever
  Randy or an associate receives, uploads, or mentions a client photo delivery or a batch of
  property, RFP or marketing photos, or says "prep these images", "shrink these photos", "make
  these upload-ready", "fix image sizes", "organize these photos", "check these images against
  spec", "sort photos into folders", "find the hero images", "check crop safety / SafeSpace",
  "build a photo IA / folder structure", or when an upload or image read fails on size. Run it
  before any CMS image upload and before looking at any original photo. Replaces image-prep and
  photo-delivery-qa.
---

# Photo Prep & Delivery QA

Hotels send batches of property photography that need fixing, checking against Cendyn's web
photo guidelines, sorting into folders, and reporting on before a designer, developer, or the
CMS touches them. This skill runs that whole pass, so a human only reviews the exceptions.

Two modes:

- **Quick prep** ("make these upload-ready", "shrink these"): Steps 0-2 only, then a one-line
  summary. No IA, heroes, or report unless asked.
- **Full delivery QA** (a client delivery, or any of the organize / hero / SafeSpace asks): all
  steps.

## Golden rule: never open original images

Claude errors when it opens an image that's too big. **Never Read or view an original photo.**
Check sizes, resize, and compress in the shell (the scripts read the file data without sending
the picture to the model). To *see* a photo, view only files in `_previews/` or the
`_contact-sheet-*.jpg` files. The plugin's hook blocks large image reads as a backstop; if it
fires, follow its message and don't retry the Read.

Photos dragged straight into the chat are sent to the model on upload. For big batches, ask for
the folder to be connected or the path instead.

## Why the guidelines matter (read before judging)

These images get reused across a responsive site: a desktop hero banner becomes a square mobile
thumbnail, the same shot runs at 16:9 in a gallery and 4:3 in a mid-page push. A photo that looks
perfect at its native crop can fail once reframed. That's why "room around the subject" and hero
status matter — they decide whether the image is usable in production. When in doubt, flag for
human review rather than guess.

## Limits

| Check | Limit | If it fails |
|---|---|---|
| File size | ≤ 20 MB | **Auto-fixed** (compress, then shrink) |
| Max dimensions | 5500 × 5500 | **Auto-fixed** (downscale, aspect kept) |
| Format | jpg, jpeg, png, gif, svg, webp | TIFF/BMP etc. **auto-converted** to JPEG |
| Min dimensions | 200 × 100 | Can't fix — goes to `_Failed_Spec`, back to client |
| Unreadable / corrupt | — | Can't fix — `_Failed_Spec` |

Override upload limits with `--max-px` / `--max-mb` only if the site or Randy gives different ones.

## Workflow

### 0. Find the files

Use uploads or a connected folder (`request_cowork_directory` if none). Unzip zips into their own
new folder. Never write into or over the original delivery.

### 1. Original spec check (records what the client sent)

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_specs.py <delivery> --output <out>/specs_original.json --csv <out>/specs_original.csv
```

SVGs without width/height or viewBox are "unverified" — note them, don't guess.

### 2. Fix + previews

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/prep_images.py <delivery> -o <out>/upload-ready --previews
```

- Within limits → copied unchanged. Too big → downscaled to 5500 px longest side; still over
  20 MB → JPEG/WebP quality 92→72, then shrink 10% at a time until it fits. TIFF/BMP → JPEG.
  SVGs pass through. EXIF rotation baked in; ICC profile and EXIF kept. Animated GIFs over
  limit are skipped and flagged.
- Subfolders are kept. Previews (1200 px) mirror them under `upload-ready/_previews/`, with
  numbered `_contact-sheet-NN.jpg` files (20 photos each) per folder.
- `upload-ready/prep_report.csv` lists original vs final px and MB per file.
- HEIC/RAW aren't supported; flag them and ask for JPEG exports.
- Viewing only, no upload copies needed: add `--previews-only`.

Then re-check the fixed set:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_specs.py <out>/upload-ready --csv <out>/specs_final.csv
```

Anything still failing (too small, unreadable, couldn't fix) is a true spec failure.

**Quick prep stops here**: report fixed / already OK / failed counts and flagged files in one or
two lines; present `prep_report.csv` if anything was fixed or failed.

### 3. Intake signals

Look for a **manifest** (CSV/spreadsheet mapping filenames to category, subtype, hero) and
filenames following `reference/naming-convention.md`. If neither exists, say so up front in the
report — downstream steps lean on visual judgment and get flagged accordingly.

Check for a **client-supplied IA** (folder tree / taxonomy). Use it if given; otherwise use the
default in `reference/ia-categories.md` (General Hotel Shots, Accommodations, Meeting Rooms,
Dining, Weddings/Events, Spa, Activities, Lifestyle, Hospitality Services, Special
Offers/Promotions, Video).

### 4. Hero identification

All visual judgment uses contact sheets first, single previews only when detail matters. Refer to
photos by the filename on the sheet.

1. **Manifest or filename says hero** (`HERO` flag or manifest column) → confirmed.
2. **No signal** → visual judgment. Favor wide/bannerable shots, subject centered with open space
   around it (ties to SafeSpace), high resolution (check `specs_original.csv`, not the preview),
   and the starred "strongly suggested" shot types in `reference/ia-categories.md`.
3. Any visual pick is labeled **"AI-suggested — needs confirmation"**. Never present a guess as
   equal to a confirmed hero.

### 5. IA placement

Manifest/filename first, visual classification second. Ask "which single category's example shot
list in `reference/ia-categories.md` does this most resemble?" A clean non-match goes to
`_Needs_Review` — a short review queue beats a quiet misplacement.

### 6. SafeSpace — crop-margin check

Checks that each image has enough room around its subject to survive cropping to the site's
ratios (not content moderation).

1. Get target ratios from `reference/crop-ratios.md` by placement (masthead/hero, mid-page push,
   carousel/gallery, footer). Placement unknown → check all of them.
2. Judge where the subject sits and whether each crop would cut into it. Centered with generous
   space passes everything; edge-to-edge or off-center subjects tend to fail the extreme ratios
   (masthead ~3.8:1).
3. Record pass/fail per ratio — "fails 1:1 push, passes masthead" beats "safe: no".

### 7. Report

One report per batch, following `reference/report-template.md` (markdown, or an HTML page if
the associate wants something more visual). Always include: summary counts, auto-fixed files,
true spec failures, heroes (confirmed vs AI-suggested), IA placement map with confidence,
SafeSpace findings, needs-review queue, and caveats (default IA used, default crop ratios,
unverified SVGs).

### 8. Organize

Build the output tree from the active IA, plus `_Failed_Spec` and `_Needs_Review` at the top.
**Copy the fixed files from `upload-ready/`** (not the originals, not previews) into place; true
spec failures go to `_Failed_Spec` as the original files so the client sees what they sent. Copy,
don't move, unless told otherwise.

### 9. Hand off

Upload from the organized tree (or `upload-ready/`) with cendyn-page-builder — never from
`_previews/`.

## Reference files

- `reference/naming-convention.md` — recommended filename format; share with clients and
  photographers before a shoot.
- `reference/ia-categories.md` — default IA from Cendyn's property-shot guidelines, with starred
  shot types per category.
- `reference/crop-ratios.md` — target aspect ratios by placement, for SafeSpace.
- `reference/report-template.md` — report structure.
- `reference/photo-guidelines-source.md` — condensed source guidelines, for re-verifying a rule.

## When information is missing

No client IA → use the default and say so; don't present default placements with the same
confidence as client-confirmed ones. Unknown site crop ratios → use the general set and note they
are guideline defaults, not confirmed for this build.
