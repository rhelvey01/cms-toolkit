#!/usr/bin/env python3
"""Resize/compress images so each is <= MAX_PX on both sides and < MAX_MB.

Usage:
  python prep_images.py INPUT [INPUT ...] -o OUTPUT_DIR [--max-px 5500] [--max-mb 20]
                        [--previews] [--previews-only] [--preview-px 1200]

--previews       also write small JPEG previews + per-folder contact sheets to
                 OUTPUT_DIR/_previews/ (safe for Claude to view).
--previews-only  only write previews/contact sheets (no upload-ready copies).

INPUT can be files or folders (folders are walked recursively, structure kept).
Originals are never modified. Files already within limits are copied unchanged.
A report (prep_report.csv) is written to OUTPUT_DIR.
"""
import argparse, csv, io, os, shutil, sys
from PIL import Image, ImageDraw, ImageFile, ImageOps

Image.MAX_IMAGE_PIXELS = None  # allow very large source photos
ImageFile.MAXBLOCK = 2**28  # avoid "Suspension not allowed" on big progressive JPEGs
ImageFile.LOAD_TRUNCATED_IMAGES = True
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif", ".svg"}
WEB_FMTS = ("JPEG", "PNG", "WEBP", "GIF")  # formats allowed by the Cendyn photo guidelines
SAFETY = 0.97  # aim a little under the byte limit


def encode(img, fmt, quality, icc, exif):
    buf = io.BytesIO()
    kw = {}
    if icc: kw["icc_profile"] = icc
    if fmt == "JPEG":
        if img.mode not in ("RGB", "L", "CMYK"):
            img = img.convert("RGB")
        kw.update(quality=quality, optimize=True, progressive=True, subsampling="4:2:0" if quality < 90 else 0)
        if exif: kw["exif"] = exif
    elif fmt == "PNG":
        kw.update(optimize=True, compress_level=9)
    elif fmt == "WEBP":
        kw.update(quality=quality, method=6)
        if exif: kw["exif"] = exif
    elif fmt == "TIFF":
        kw.update(compression="tiff_lzw")
    img.save(buf, fmt, **kw)
    return buf.getvalue()


def process(src, dst, max_px, max_bytes):
    size0 = os.path.getsize(src)
    if src.lower().endswith(".svg"):  # vector: no pixels to fix, pass through
        shutil.copy2(src, dst)
        return "ok-copied", (0, 0), (0, 0), size0, size0, "SVG passed through (not resized)"
    with Image.open(src) as im:
        fmt = (im.format or "JPEG").upper()
        if getattr(im, "n_frames", 1) > 1 and fmt == "GIF":
            if size0 <= max_bytes and max(im.size) <= max_px:
                shutil.copy2(src, dst); return "ok-copied", im.size, im.size, size0, size0, ""
            return "skipped", im.size, im.size, size0, size0, "animated GIF over limits - fix manually"
        w0, h0 = im.size
        if size0 <= max_bytes * SAFETY and w0 <= max_px and h0 <= max_px and fmt in WEB_FMTS:
            shutil.copy2(src, dst)
            return "ok-copied", (w0, h0), (w0, h0), size0, size0, ""
        icc = im.info.get("icc_profile")
        exif = im.getexif()
        img = ImageOps.exif_transpose(im)  # bake rotation so it doesn't flip after resize
        if exif and 0x0112 in exif:
            exif[0x0112] = 1
        exif_b = exif.tobytes() if exif else None
        img.load()

    out_fmt = fmt if fmt in ("JPEG", "PNG", "WEBP") else "JPEG"  # TIFF/BMP/etc. -> JPEG
    note = ""
    if out_fmt != fmt:
        note = f"converted {fmt} to JPEG"
        dst = os.path.splitext(dst)[0] + ".jpg"

    # 1) dimension cap
    scale = min(1.0, max_px / max(img.size))
    target = img if scale == 1.0 else img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)

    # 2) size cap
    lossy = out_fmt in ("JPEG", "WEBP")
    data = None
    for _ in range(12):
        if lossy:
            for q in (92, 88, 84, 80, 76, 72):
                data = encode(target, out_fmt, q, icc, exif_b)
                if len(data) <= max_bytes * SAFETY: break
        else:
            data = encode(target, out_fmt, None, icc, exif_b)
        if len(data) <= max_bytes * SAFETY: break
        # still too big: shrink dimensions ~10% and retry
        target = target.resize((int(target.width * 0.9), int(target.height * 0.9)), Image.LANCZOS)
    if len(data) > max_bytes:
        return "failed", (w0, h0), target.size, size0, len(data), "could not get under size limit"
    with open(dst, "wb") as f:
        f.write(data)
    return "fixed", (w0, h0), target.size, size0, len(data), note


def make_preview(src, dst, preview_px):
    """Small RGB JPEG of the original, longest side <= preview_px."""
    with Image.open(src) as im:
        im.draft("RGB", (preview_px, preview_px))  # fast JPEG downscale on load
        img = ImageOps.exif_transpose(im).convert("RGB")
    img.thumbnail((preview_px, preview_px), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    img.save(dst, "JPEG", quality=80, optimize=True)
    return dst


def contact_sheets(previews, out_dir, cols=5, rows=4, cell=300, label_h=22):
    """previews: list of (label, preview_path). Writes sheets of cols*rows, ~1500px wide."""
    per = cols * rows
    paths = []
    for n in range(0, len(previews), per):
        chunk = previews[n:n + per]
        r = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell, r * (cell + label_h)), "white")
        d = ImageDraw.Draw(sheet)
        for i, (label, pth) in enumerate(chunk):
            x, y = (i % cols) * cell, (i // cols) * (cell + label_h)
            with Image.open(pth) as t:
                t = t.copy()
            t.thumbnail((cell - 8, cell - 8))
            sheet.paste(t, (x + (cell - t.width) // 2, y + (cell - t.height) // 2))
            d.text((x + 4, y + cell + 4), f"{n + i + 1}. {label}"[:44], fill="black")
        p = os.path.join(out_dir, f"_contact-sheet-{n // per + 1:02d}.jpg")
        sheet.save(p, "JPEG", quality=80)
        paths.append(p)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--max-px", type=int, default=5500)
    ap.add_argument("--max-mb", type=float, default=20)
    ap.add_argument("--previews", action="store_true")
    ap.add_argument("--previews-only", action="store_true")
    ap.add_argument("--preview-px", type=int, default=1200)
    a = ap.parse_args()
    if a.previews_only:
        a.previews = True
    max_bytes = int(a.max_mb * 1024 * 1024)
    os.makedirs(a.out, exist_ok=True)

    jobs = []
    for p in a.inputs:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in ("_previews", "upload-ready")]
                for fn in files:
                    if fn.startswith("_contact-sheet"):
                        continue
                    if os.path.splitext(fn)[1].lower() in EXTS:
                        rel = os.path.relpath(os.path.join(root, fn), p)
                        jobs.append((os.path.join(root, fn), os.path.join(a.out, rel)))
        elif os.path.splitext(p)[1].lower() in EXTS:
            jobs.append((p, os.path.join(a.out, os.path.basename(p))))
        else:
            print(f"skip (not a supported image): {p}", file=sys.stderr)

    rows, counts, sheets_in = [], {}, {}
    prev_root = os.path.join(a.out, "_previews")
    for src, dst in jobs:
        if a.previews and not src.lower().endswith(".svg"):
            rel = os.path.relpath(dst, a.out)
            pdst = os.path.splitext(os.path.join(prev_root, rel))[0] + ".jpg"
            try:
                make_preview(src, pdst, a.preview_px)
                sheets_in.setdefault(os.path.dirname(pdst), []).append((os.path.basename(src), pdst))
            except Exception as e:
                print(f"preview failed: {os.path.basename(src)}: {e}", file=sys.stderr)
        if a.previews_only:
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            st, d0, d1, s0, s1, note = process(src, dst, a.max_px, max_bytes)
        except Exception as e:
            st, d0, d1, s0, s1, note = "failed", (0, 0), (0, 0), os.path.getsize(src), 0, str(e)
        counts[st] = counts.get(st, 0) + 1
        rows.append([os.path.basename(src), st, f"{d0[0]}x{d0[1]}", f"{d1[0]}x{d1[1]}",
                     f"{s0/1048576:.2f}", f"{s1/1048576:.2f}", note])
        print(f"{st:10} {os.path.basename(src)}  {d0[0]}x{d0[1]} {s0/1048576:.1f}MB -> {d1[0]}x{d1[1]} {s1/1048576:.1f}MB {note}")

    for folder, items in sheets_in.items():
        for p in contact_sheets(items, folder):
            print(f"contact sheet: {p}")
    if a.previews:
        print(f"previews: {prev_root}")
    if a.previews_only:
        return

    with open(os.path.join(a.out, "prep_report.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "status", "original_px", "final_px", "original_mb", "final_mb", "notes"])
        w.writerows(rows)
    print("\nSummary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())), f"| total={len(jobs)}")


if __name__ == "__main__":
    main()
