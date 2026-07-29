"""Generate CT-only tri-planar thumbnails for the React scan library.

The label volume is used only to choose a useful anatomical center. No label,
prediction, or source-of-truth pixels are drawn into the exported previews.
"""

from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image, ImageDraw, ImageFont


CASES_DIR = Path(__file__).resolve().parents[1] / "ui" / "public" / "cases"
CANVAS_SIZE = (900, 300)
PANEL_SIZE = 280
PANEL_GAP = 10
PANEL_LABELS = ("Axial", "Coronal", "Sagittal")


def normalize_ct(image: np.ndarray) -> np.ndarray:
    """Normalize a prepared CT slice to display-ready uint8 grayscale."""
    finite = image[np.isfinite(image)]
    if finite.size == 0:
        return np.zeros(image.shape, dtype=np.uint8)

    nonzero = finite[finite != 0]
    sample = nonzero if nonzero.size else finite
    low, high = np.percentile(sample, (1, 99))
    if high <= low:
        high = low + 1.0
    normalized = np.clip((image - low) / (high - low), 0, 1)
    return np.round(normalized * 255).astype(np.uint8)


def fit_panel(image: np.ndarray) -> Image.Image:
    panel = Image.fromarray(normalize_ct(np.rot90(image)), mode="L")
    panel = panel.resize((PANEL_SIZE, PANEL_SIZE), Image.Resampling.LANCZOS)
    return panel.convert("RGB")


def render_case(case_dir: Path) -> None:
    ct = nib.as_closest_canonical(nib.load(case_dir / "ct.nii.gz")).get_fdata(
        dtype=np.float32
    )
    label = nib.as_closest_canonical(
        nib.load(case_dir / "gt.nii.gz")
    ).get_fdata(dtype=np.float32)

    points = np.argwhere(label > 0)
    center = (
        np.rint(points.mean(axis=0)).astype(int)
        if points.size
        else np.asarray(ct.shape, dtype=int) // 2
    )
    center = np.clip(center, 0, np.asarray(ct.shape) - 1)

    slices = (
        ct[:, :, center[2]],
        ct[:, center[1], :],
        ct[center[0], :, :],
    )

    canvas = Image.new("RGB", CANVAS_SIZE, "#071019")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    for index, (label_text, image) in enumerate(zip(PANEL_LABELS, slices)):
        x = 10 + index * (PANEL_SIZE + PANEL_GAP)
        panel = fit_panel(image)
        canvas.paste(panel, (x, 10))
        draw.rectangle((x, 10, x + PANEL_SIZE - 1, 289), outline="#315064", width=1)
        draw.rounded_rectangle(
            (x + 8, 18, x + 69, 38),
            radius=5,
            fill="#071019",
            outline="#315064",
        )
        draw.text((x + 16, 23), label_text, fill="#bfd0d6", font=font)

    canvas.save(case_dir / "thumbnail.webp", "WEBP", quality=88, method=6)


def main() -> None:
    case_dirs = sorted(path.parent for path in CASES_DIR.glob("*/ct.nii.gz"))
    for case_dir in case_dirs:
        render_case(case_dir)
        print(f"wrote {case_dir / 'thumbnail.webp'}")


if __name__ == "__main__":
    main()
