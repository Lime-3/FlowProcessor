#!/usr/bin/env python3
"""extract_group_labels.py

CLI + library for extracting **unique** experimental group labels from
images (JPG/PNG/TIFF, etc.) *or* from slides in a PowerPoint (.pptx)
file by calling OpenAI’s multimodal GPT models.

Label schema expected per group:
    <Test article> - <condition (optional)> - <dose>

Uniqueness policy (2025‑07‑18):
--------------------------------
* The *full* triplet (`test_article`, `condition`, `dose`) **must be
  globally unique** across all images/slides.  If the same `test_article`
  and `dose` appear more than once, the vision model *must* have provided
  a distinguishing `condition`; otherwise the script raises
  `DuplicateLabelError` and exits non‑zero (or raises in library mode).
* **No automatic “_1”, “_2” suffixes** are appended.  The source material
  (image or slide) must contain a real differentiator (usually the
  `condition` field).  If the differentiator is missing you’ll get a hard
  error so you can fix the slide or tweak your prompt.

Quick start examples
--------------------
Extract from a folder of PNGs and write a CSV:
    $ python extract_group_labels.py images/*.png -o groups.csv

Extract from an entire PowerPoint deck:
    $ python extract_group_labels.py study.pptx -o groups.csv

Library usage:
    from extract_group_labels import extract_labels_from_file
    groups = extract_labels_from_file("study.pptx")
    ...

Dependencies
------------
* openai>=1.30.0
* python‑pptx>=0.6.23  (only when processing .pptx)
* pillow>=10.0         (image manipulation)

Set `OPENAI_API_KEY` in your environment (not on the CLI).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Iterable, List, Dict, Tuple, Optional

import openai
from PIL import Image

try:
    from pptx import Presentation  # type: ignore
except ImportError:
    Presentation = None  # pptx support optional

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class DuplicateLabelError(RuntimeError):
    """Raised when two groups have the same TA+dose with no unique condition."""

# ---------------------------------------------------------------------------
# GPT Vision prompt helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an expert study assistant. "
    "You look at images or PowerPoint slides that list experimental group "
    "labels.  Each label follows the pattern <Test article> - <condition (optional)> - <dose>. "
    "Return **only** a JSON array where each element is an object with the keys "
    "`test_article`, `condition`, `dose`.  If a field is missing in the image, "
    "return an empty string for that key. Do not invent information."
)

def vision_prompt(image_path: Path) -> List[Dict[str, str]]:
    """Send an image to GPT‑4o and return the parsed label dicts."""
    with image_path.open("rb") as f:
        base64_img = openai.helpers.to_base64(f.read())

    user_prompt = (
        "Extract all group labels in the image using the schema above. "
        "Answer ONLY with the JSON array—no extra keys, no Markdown, no prose."
    )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # change if you have access to gpt‑4o
        temperature=0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_img}",
                        },
                    },
                    {
                        "type": "text",
                        "text": user_prompt,
                    },
                ],
            },
        ],
    )
    json_str = response.choices[0].message.content.strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"GPT returned invalid JSON for {image_path}:\n{json_str}\n{e}"
        ) from e

# ---------------------------------------------------------------------------
# Deduping / uniqueness
# ---------------------------------------------------------------------------

def ensure_global_uniqueness(labels: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    """Verify that TA+dose combos are unique, else raise DuplicateLabelError."""
    seen: Dict[Tuple[str, str], str] = {}
    out: List[Dict[str, str]] = []
    for lbl in labels:
        ta = lbl.get("test_article", "").strip()
        dose = lbl.get("dose", "").strip()
        cond = lbl.get("condition", "").strip()
        key = (ta.lower(), dose.lower())
        if key in seen:
            # We saw this TA+dose before. Were conditions unique?
            if cond and cond.lower() != seen[key].lower():
                # ok, they differ by condition – allow.
                pass
            else:
                raise DuplicateLabelError(
                    f"Non‑unique label detected: {ta} - {dose}. "
                    f"Provide a differentiating condition in the source slide."
                )
        else:
            seen[key] = cond
        out.append({"test_article": ta, "condition": cond, "dose": dose})
    return out

# ---------------------------------------------------------------------------
# File processing utilities
# ---------------------------------------------------------------------------

def images_from_pptx(pptx_path: Path, temp_dir: Path) -> List[Path]:
    """Render each slide to a PNG in *temp_dir* and return the image paths."""
    if Presentation is None:
        raise RuntimeError("python-pptx is required to process .pptx files")
    prs = Presentation(str(pptx_path))
    img_paths: List[Path] = []
    for idx, slide in enumerate(prs.slides, 1):
        # Render slide to PNG via pillow by rasterizing slide shapes to a new image
        # (python‑pptx doesn’t do this natively; we fall back to shapely-ish bbox)
        # For production you might prefer `libreoffice --convert-to` or wand/ghostscript.
        img = Image.new("RGB", (1920, 1080), "white")
        # TODO: smarter rendering. For now we rely on the slide thumbnail property.
        thumbnail = slide.part.blob
        if thumbnail:
            thumb_img = Image.open(BytesIO(thumbnail))
            thumb_img.thumbnail(img.size)
            img.paste(thumb_img, ((img.width - thumb_img.width) // 2, (img.height - thumb_img.height) // 2))
        out_path = temp_dir / f"slide_{idx:03}.png"
        img.save(out_path)
        img_paths.append(out_path)
    return img_paths

# ---------------------------------------------------------------------------
# Main extraction entry points
# ---------------------------------------------------------------------------

def extract_labels_from_file(path: str | Path) -> List[Dict[str, str]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    image_paths: List[Path] = []
    temp_dir: Optional[Path] = None

    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        image_paths = [path]
    elif path.suffix.lower() == ".pptx":
        # create temp dir to hold rendered slides
        temp_dir = Path(os.getenv("TMPDIR", "/tmp")) / f"pptx_{os.getpid()}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        image_paths = images_from_pptx(path, temp_dir)
    else:
        raise ValueError("Unsupported file type: " + path.suffix)

    all_labels: List[Dict[str, str]] = []
    for img in image_paths:
        labels = vision_prompt(img)
        all_labels.extend(labels)

    return ensure_global_uniqueness(all_labels)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(description="Extract unique group labels from images or PPTX using GPT‑4o (Vision).")
    parser.add_argument("files", nargs="+", help="Image or .pptx files to process")
    parser.add_argument("-o", "--output", help="Write results to this CSV (default: stdout)")
    args = parser.parse_args()

    aggregate: List[Dict[str, str]] = []
    for f in args.files:
        aggregate.extend(extract_labels_from_file(f))

    headers = ["test_article", "condition", "dose"]
    if args.output:
        with open(args.output, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(aggregate)
        print(f"Saved {len(aggregate)} labels -> {args.output}")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=headers)
        writer.writeheader()
        writer.writerows(aggregate)

if __name__ == "__main__":
    _cli()
