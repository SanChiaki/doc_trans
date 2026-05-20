from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.conversion.pdf_ops import validate_pdf


def image_to_pdf(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, "PDF", resolution=100.0)
    validate_pdf(output_path)
