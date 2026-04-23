from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter


def merge(pdf_paths: Iterable[Path], output_path: Path) -> Path:
    writer = PdfWriter()
    appended_any = False
    for path in pdf_paths:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
        appended_any = True
    if not appended_any:
        raise ValueError("merge() called with no input PDFs")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        writer.write(fh)
    return output_path
