# Recommended Naming Convention

Giving photographers/clients this convention up front removes most of the guesswork later —
every downstream step (spec check, hero ID, IA placement, SafeSpace) works off filename +
manifest signals first, and only falls back to visual judgment when those are missing.

## Format

```
{Property}_{Category}_{Subtype}_{Descriptor}_{Seq}[_{Flags}].ext
```

| Segment | Required? | Description |
|---|---|---|
| `Property` | Yes | Short property/client code, consistent across the whole delivery (e.g. `VICEROY-SL`). |
| `Category` | Yes | One of the fixed category codes below, matching the IA in `ia-categories.md`. |
| `Subtype` | Yes | What within the category — a room type, restaurant name, meeting room name, activity, etc. CamelCase or hyphenated, no spaces (`KingSuite`, `Marea`, `Ballroom-A`). |
| `Descriptor` | Yes | What's depicted — ties back to the specific guideline bullet (`Exterior`, `View`, `Bed`, `SignatureDish`, `Decor`). |
| `Seq` | Yes | 2-digit sequence number, scoped to that Subtype+Descriptor combo (`01`, `02`...). |
| `Flags` | No | Optional tags, joined with `+`: `HERO` (confirmed hero shot), `REQ` (fulfills a starred/required shot type). |

## Category codes

| Code | Category |
|---|---|
| `GEN` | General Hotel Shots |
| `ACC` | Accommodations |
| `MTG` | Meeting Rooms |
| `DIN` | Dining & Signature Restaurants |
| `WED` | Weddings / Events |
| `SPA` | Spa |
| `ACT` | Activities |
| `LIFE` | Lifestyle |
| `HOSP` | Hospitality Services |
| `PROMO` | Special Offers / Promotions |
| `VID` | Video |

## Examples

```
VICEROY-SL_ACC_KingSuite_View_01_HERO.jpg
VICEROY-SL_DIN_Marea_SignatureDish_02_REQ.jpg
VICEROY-SL_GEN_Exterior_Entrance_01_HERO+REQ.jpg
VICEROY-SL_SPA_Facial_ServiceRoom_01.jpg
```

## When renaming isn't practical

If the client or photographer can't rename files before delivery, ask for a manifest instead —
a spreadsheet/CSV with columns: `filename, category, subtype, descriptor, hero (yes/no)`. Either
signal (filename or manifest) is enough to skip the visual-judgment fallback for that file.
