"""Draw the B.I.R.D.S icons from the logo, for every platform.

Two icons, each in the formats the platforms want:

* ``birds_app``      -- the application: the emblem on a rounded square;
* ``birds_document`` -- a saved ``.birds`` session: a page with a folded
  corner, the emblem small on it and "BIRDS" beneath.

Written to ``packaging/icons/`` as ``.png`` (1024 px, and 256 px for
Linux), ``.ico`` (Windows, 16-256 px) and ``.icns`` (macOS, 16-1024 px;
needs ``iconutil``, so only on a Mac).  Run it again after changing the
logo:  ``python3 packaging/make_icons.py``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
LOGO = HERE.parent / "birds" / "resources" / "LOGO-BIRDS.png"
OUT = HERE / "icons"
S = 1024

INK = (46, 52, 64, 255)
PAGE = (251, 250, 245, 255)
EDGE = (176, 170, 156, 255)
FLAP = (229, 225, 214, 255)

_ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
              (128, 128), (256, 256)]
_ICNS_SIZES = (16, 32, 128, 256, 512)


def emblem() -> Image.Image:
    """The logo's emblem with its paper made transparent.

    The paper colour is read from the corners; alpha rises from 0 to 1
    as a pixel departs from it, so the pale fills keep their softness
    instead of being cut out hard.
    """
    rgb = np.asarray(Image.open(LOGO).convert("RGB")).astype(float)
    corners = np.concatenate([rgb[:40, :40].reshape(-1, 3),
                              rgb[:40, -40:].reshape(-1, 3),
                              rgb[-40:, :40].reshape(-1, 3),
                              rgb[-40:, -40:].reshape(-1, 3)])
    paper = np.median(corners, axis=0)
    dist = np.sqrt(((rgb - paper) ** 2).sum(axis=2))
    ys, xs = np.where(dist > 40)
    alpha = np.clip((dist - 12.0) / 33.0, 0.0, 1.0) * 255.0
    rgba = np.dstack([rgb, alpha]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA").crop(
        (xs.min() - 8, ys.min() - 8, xs.max() + 8, ys.max() + 8))


def _fit(image: Image.Image, width: int) -> Image.Image:
    return image.resize((width, round(image.height * width / image.width)),
                        Image.LANCZOS)


def _shadow(shape, offset=(6, 14), blur=18, alpha=110) -> Image.Image:
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    shifted = [(x + offset[0], y + offset[1]) for x, y in shape]
    draw.polygon(shifted, fill=(20, 24, 34, alpha))
    return layer.filter(ImageFilter.GaussianBlur(blur))


def _font(size: int):
    for path in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                 "C:/Windows/Fonts/arialbd.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def document_icon(mark: Image.Image) -> Image.Image:
    """A page, folded at the top right, the emblem small, BIRDS below."""
    left, right, top, bottom = 196, 828, 84, 940
    fold = 170
    page = [(left + 24, top), (right - fold, top), (right, top + fold),
            (right, bottom - 24), (right - 24, bottom), (left + 24, bottom),
            (left, bottom - 24), (left, top + 24)]
    img = Image.alpha_composite(Image.new("RGBA", (S, S), (0, 0, 0, 0)),
                                _shadow(page))
    draw = ImageDraw.Draw(img)
    draw.polygon(page, fill=PAGE)
    draw.line(page + [page[0]], fill=EDGE, width=5, joint="curve")
    flap = [(right - fold, top), (right - fold, top + fold - 18),
            (right - fold + 18, top + fold), (right, top + fold)]
    draw.polygon(flap, fill=FLAP)
    draw.line(flap + [flap[0]], fill=EDGE, width=5, joint="curve")
    small = _fit(mark, int((right - left) * 0.50))
    centre = (left + right) // 2
    img.alpha_composite(small, (centre - small.width // 2,
                                top + int((bottom - top) * 0.30)))
    font = _font(92)
    width = draw.textlength("BIRDS", font=font)
    draw.text((centre - width / 2, bottom - 200), "BIRDS", font=font,
              fill=INK)
    return img


def app_icon(mark: Image.Image) -> Image.Image:
    """The emblem on a rounded square of the logo's paper colour, in the
    proportions macOS draws application icons at (824 px of 1024)."""
    inset, radius = 100, 185
    box = (inset, inset, S - inset, S - inset)
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (box[0] + 4, box[1] + 16, box[2] + 4, box[3] + 16), radius,
        fill=(20, 24, 34, 120))
    img = Image.alpha_composite(Image.new("RGBA", (S, S), (0, 0, 0, 0)),
                                shadow.filter(ImageFilter.GaussianBlur(20)))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(box, radius, fill=(240, 239, 233, 255),
                           outline=EDGE, width=4)
    big = _fit(mark, int((box[2] - box[0]) * 0.80))
    img.alpha_composite(big, ((S - big.width) // 2,
                              (S - big.height) // 2 + 10))
    return img


def write_formats(image: Image.Image, name: str) -> list:
    """``name``.png (1024), ``name``_256.png, ``name``.ico, ``name``.icns."""
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    png = OUT / f"{name}.png"
    image.save(png)
    small = OUT / f"{name}_256.png"
    image.resize((256, 256), Image.LANCZOS).save(small)
    ico = OUT / f"{name}.ico"
    image.save(ico, sizes=_ICO_SIZES)
    written += [png, small, ico]
    if shutil.which("iconutil"):
        with tempfile.TemporaryDirectory() as tmp:
            iconset = Path(tmp) / f"{name}.iconset"
            iconset.mkdir()
            for size in _ICNS_SIZES:
                image.resize((size, size), Image.LANCZOS).save(
                    iconset / f"icon_{size}x{size}.png")
                image.resize((2 * size, 2 * size), Image.LANCZOS).save(
                    iconset / f"icon_{size}x{size}@2x.png")
            icns = OUT / f"{name}.icns"
            subprocess.run(["iconutil", "-c", "icns", str(iconset),
                            "-o", str(icns)], check=True)
            written.append(icns)
    else:
        print("iconutil not found: .icns skipped (it needs a Mac)",
              file=sys.stderr)
    return written


def main() -> None:
    mark = emblem()
    for name, image in (("birds_app", app_icon(mark)),
                        ("birds_document", document_icon(mark))):
        for path in write_formats(image, name):
            print(path.relative_to(HERE.parent))


if __name__ == "__main__":
    main()
