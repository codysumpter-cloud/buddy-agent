#!/usr/bin/env python3
"""Generate Buddy pixel-art mouth/viseme assets from a clean base PNG.

Dependencies:
- ImageMagick `magick`
- Python standard library only

The default coordinates target the canonical Prismtek/Buddy host crop. Operators can
override geometry for a different crop without editing the script.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


DEFAULT_FACE_SAMPLE = "50x30+216+224"
DEFAULT_FACE_TARGET = "+216+246"
DEFAULT_ERASE_RECTS = (
    ("#d2f5eb", "rectangle 222,273 232,278"),
    ("#d1f4ea", "rectangle 252,273 263,278"),
)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def magick(*args: str | Path) -> None:
    run(["magick", *map(str, args)])


def parse_erase_rect(value: str) -> tuple[str, str]:
    """Parse COLOR:DRAW_RECT values for extra mouth cleanup."""
    if ":" not in value:
        raise argparse.ArgumentTypeError("erase rect must use COLOR:DRAW_RECT format")
    color, draw_rect = value.split(":", 1)
    color = color.strip()
    draw_rect = draw_rect.strip()
    if not color or not draw_rect:
        raise argparse.ArgumentTypeError("erase rect must include both color and rectangle")
    return color, draw_rect


def build_states() -> dict[str, list[str]]:
    return {
        "mouth-closed": [
            "-fill",
            "#18205e",
            "-draw",
            "rectangle 229,253 234,258 rectangle 234,258 244,262 rectangle 244,253 250,258",
        ],
        "mouth-small-open": [
            "-fill",
            "#18205e",
            "-draw",
            "rectangle 231,249 249,266 rectangle 234,266 246,270",
            "-fill",
            "#ff6f8f",
            "-draw",
            "rectangle 235,254 245,268",
            "-fill",
            "#ffe2d2",
            "-draw",
            "rectangle 236,252 244,255",
        ],
        "mouth-wide-open": [
            "-fill",
            "#18205e",
            "-draw",
            "rectangle 226,248 254,264 rectangle 230,264 250,270",
            "-fill",
            "#ff6f8f",
            "-draw",
            "rectangle 231,254 249,268",
            "-fill",
            "#ffe2d2",
            "-draw",
            "rectangle 233,252 247,255",
        ],
        "mouth-round-o": [
            "-fill",
            "#18205e",
            "-draw",
            "rectangle 232,249 248,266 rectangle 235,266 245,270",
            "-fill",
            "#ff6f8f",
            "-draw",
            "rectangle 236,253 244,265",
        ],
        "mouth-soft": [
            "-fill",
            "#18205e",
            "-draw",
            "rectangle 229,255 250,261",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Buddy mouth/viseme PNGs from a clean base avatar"
    )
    parser.add_argument("base", type=Path, help="Clean Buddy PNG")
    parser.add_argument("--out-dir", type=Path, help="Output directory")
    parser.add_argument("--prefix", default="buddy-host-main-v12", help="Output filename prefix")
    parser.add_argument("--face-sample", default=DEFAULT_FACE_SAMPLE)
    parser.add_argument("--face-target", default=DEFAULT_FACE_TARGET)
    parser.add_argument(
        "--erase-rect",
        action="append",
        default=[],
        type=parse_erase_rect,
        help="Extra cleanup rectangle as COLOR:DRAW_RECT, for example '#d2f5eb:rectangle 1,2 3,4'",
    )
    args = parser.parse_args()

    if shutil.which("magick") is None:
        raise SystemExit("Missing dependency: ImageMagick `magick`")
    if not args.base.exists():
        raise SystemExit(f"Base image not found: {args.base}")
    if not args.base.is_file():
        raise SystemExit(f"Base path is not a file: {args.base}")

    out_dir = args.out_dir or args.base.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix

    no_mouth = out_dir / f"{prefix}-no-mouth-base.png"

    magick(
        args.base,
        "(",
        args.base,
        "-crop",
        args.face_sample,
        "+repage",
        ")",
        "-geometry",
        args.face_target,
        "-compose",
        "over",
        "-composite",
        no_mouth,
    )

    for color, draw_rect in [*DEFAULT_ERASE_RECTS, *args.erase_rect]:
        magick(no_mouth, "-fill", color, "-draw", draw_rect, no_mouth)

    outputs: list[Path] = []
    for name, draw_args in build_states().items():
        out = out_dir / f"{prefix}-{name}.png"
        magick(no_mouth, *draw_args, out)
        outputs.append(out)

    for out in [*outputs, no_mouth]:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
