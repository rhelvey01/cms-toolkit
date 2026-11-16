# Photo Delivery QA Report — Template

Fill in every section below for each delivery batch. Omit a table's rows (not the section) if
there's nothing to report — e.g. "No spec failures" rather than deleting the heading.

```markdown
# Photo Delivery QA Report — {Property Name} — {Date}

## Summary
- Total files received: {n}
- Passed as delivered: {n} | Auto-fixed: {n} | True spec failures: {n}
- Heroes found: {n} confirmed, {n} AI-suggested
- Sent to Needs Review: {n}
- IA used: {default guideline IA / client-supplied IA, name it}

## Auto-Fixed Files
| File | Original (px / MB / format) | Final (px / MB / format) |
|---|---|---|
| ... | ... | ... |

## Spec Failures (could not fix, back to client)
| File | Size | Dimensions | Extension | Reason |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

## Hero Images
### Confirmed (manifest/filename)
- {file} — {category/subtype}

### AI-Suggested — Needs Confirmation
- {file} — {category/subtype} — {why it was flagged as a hero candidate}

## IA Placement Map
| File | Destination Folder | Signal | Confidence |
|---|---|---|---|
| ... | ... | manifest / filename / visual | high / medium / low |

## SafeSpace Findings
| File | Failing Ratio(s) | Why |
|---|---|---|
| ... | ... | subject too close to frame edge on the left, will be cut by 1:1 crop |

## Needs Review Queue
| File | Reason |
|---|---|
| ... | no manifest/filename signal, ambiguous category |

## Notes
- {Any caveats — e.g. "no client IA supplied, used default"; "3 SVGs could not be dimension-checked"}
```
