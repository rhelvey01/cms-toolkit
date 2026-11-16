#!/usr/bin/env python3
"""
validate_specs.py

Deterministic spec check for a hotel/property photo delivery, per Cendyn's photo guidelines:
  - Max file size: 20MB
  - Min dimensions: 200x100
  - Max dimensions: 5500x5500
  - Allowed extensions: jpg, jpeg, png, gif, svg, webp

Usage:
    python3 validate_specs.py <delivery_folder> [--output results.json] [--csv results.csv]

Walks the folder recursively, checks every file against the limits above, and writes a
structured result per file. SVGs that don't expose explicit width/height (or a viewBox) are
marked "unverified" for the dimension check rather than guessed at — flag these for a human
rather than passing or failing them silently.
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB
MIN_DIMENSIONS = (200, 100)   # width, height
MAX_DIMENSIONS = (5500, 5500)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "svg", "webp"}


def get_extension(path: Path) -> str:
    return path.suffix.lower().lstrip(".")


def get_raster_dimensions(path: Path):
    """Return (width, height) for a raster image using Pillow, or None if unreadable."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size
    except Exception:
        return None


def get_svg_dimensions(path: Path):
    """
    Best-effort SVG dimension extraction from width/height or viewBox attributes.
    Returns (width, height, unit_note) or None if it can't be determined.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    svg_tag_match = re.search(r"<svg\b[^>]*>", content, re.IGNORECASE | re.DOTALL)
    if not svg_tag_match:
        return None
    svg_tag = svg_tag_match.group(0)

    width_match = re.search(r'width\s*=\s*"([\d.]+)', svg_tag)
    height_match = re.search(r'height\s*=\s*"([\d.]+)', svg_tag)
    if width_match and height_match:
        return (float(width_match.group(1)), float(height_match.group(1)))

    viewbox_match = re.search(r'viewBox\s*=\s*"([-\d.\s]+)"', svg_tag)
    if viewbox_match:
        parts = viewbox_match.group(1).split()
        if len(parts) == 4:
            return (float(parts[2]), float(parts[3]))

    return None


def check_file(path: Path):
    result = {
        "file": str(path),
        "extension": get_extension(path),
        "size_bytes": None,
        "dimensions": None,
        "dimension_status": None,  # "ok" | "fail" | "unverified"
        "pass": True,
        "reasons": [],
    }

    # Extension check
    ext = result["extension"]
    if ext not in ALLOWED_EXTENSIONS:
        result["pass"] = False
        result["reasons"].append(f"extension '.{ext}' not in allowed set {sorted(ALLOWED_EXTENSIONS)}")

    # Size check
    try:
        size_bytes = path.stat().st_size
        result["size_bytes"] = size_bytes
        if size_bytes > MAX_FILE_SIZE_BYTES:
            result["pass"] = False
            result["reasons"].append(
                f"file size {size_bytes / (1024 * 1024):.1f}MB exceeds {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB limit"
            )
    except OSError as e:
        result["pass"] = False
        result["reasons"].append(f"could not read file size: {e}")

    # Dimension check
    if ext == "svg":
        dims = get_svg_dimensions(path)
        if dims is None:
            result["dimension_status"] = "unverified"
            result["reasons"].append("SVG dimensions could not be determined automatically — verify manually")
        else:
            result["dimensions"] = dims
            w, h = dims
            if w < MIN_DIMENSIONS[0] or h < MIN_DIMENSIONS[1]:
                result["dimension_status"] = "fail"
                result["pass"] = False
                result["reasons"].append(f"dimensions {w:.0f}x{h:.0f} below minimum {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}")
            elif w > MAX_DIMENSIONS[0] or h > MAX_DIMENSIONS[1]:
                result["dimension_status"] = "fail"
                result["pass"] = False
                result["reasons"].append(f"dimensions {w:.0f}x{h:.0f} exceed maximum {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}")
            else:
                result["dimension_status"] = "ok"
    elif ext in ALLOWED_EXTENSIONS:
        dims = get_raster_dimensions(path)
        if dims is None:
            result["dimension_status"] = "unverified"
            result["reasons"].append("could not read image dimensions (corrupt or unsupported file)")
        else:
            result["dimensions"] = dims
            w, h = dims
            if w < MIN_DIMENSIONS[0] or h < MIN_DIMENSIONS[1]:
                result["dimension_status"] = "fail"
                result["pass"] = False
                result["reasons"].append(f"dimensions {w}x{h} below minimum {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}")
            elif w > MAX_DIMENSIONS[0] or h > MAX_DIMENSIONS[1]:
                result["dimension_status"] = "fail"
                result["pass"] = False
                result["reasons"].append(f"dimensions {w}x{h} exceed maximum {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}")
            else:
                result["dimension_status"] = "ok"
    else:
        # Unknown extension - dimension check not meaningful
        result["dimension_status"] = "unverified"

    return result


def walk_delivery(folder: Path):
    files = []
    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "_previews"]  # previews are for viewing, not delivery
        for name in filenames:
            if name.startswith(".") or name.startswith("_contact-sheet") or name == "prep_report.csv":
                continue
            files.append(Path(root) / name)
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description="Validate a photo delivery against Cendyn spec limits.")
    parser.add_argument("folder", help="Path to the delivery folder to scan (recursive)")
    parser.add_argument("--output", help="Write JSON results to this path")
    parser.add_argument("--csv", help="Write CSV results to this path")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory", file=sys.stderr)
        sys.exit(1)

    files = walk_delivery(folder)
    results = [check_file(f) for f in files]

    passed = sum(1 for r in results if r["pass"])
    failed = len(results) - passed
    unverified = sum(1 for r in results if r["dimension_status"] == "unverified")

    summary = {
        "total_files": len(results),
        "passed": passed,
        "failed": failed,
        "dimension_unverified": unverified,
    }

    output = {"summary": summary, "results": results}

    print(json.dumps(summary, indent=2))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"\nFull results written to {args.output}")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "extension", "size_bytes", "dimensions", "dimension_status", "pass", "reasons"])
            for r in results:
                writer.writerow([
                    r["file"], r["extension"], r["size_bytes"], r["dimensions"],
                    r["dimension_status"], r["pass"], "; ".join(r["reasons"]),
                ])
        print(f"CSV results written to {args.csv}")


if __name__ == "__main__":
    main()
