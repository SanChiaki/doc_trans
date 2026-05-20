from __future__ import annotations

from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from app.conversion.image_converter import image_to_pdf


def test_image_to_pdf_creates_readable_pdf(tmp_path: Path) -> None:
    image_path = tmp_path / "photo.png"
    output_path = tmp_path / "photo.pdf"
    Image.new("RGB", (120, 80), color="white").save(image_path)

    image_to_pdf(image_path, output_path)

    assert output_path.exists()
    assert len(PdfReader(str(output_path)).pages) == 1
