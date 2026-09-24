import os
from typing import Optional

import pytesseract
from PIL import Image
from pypdf import PdfReader

from app.config import POPPLER_PATH, TESSERACT_CMD

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

MIN_PDF_TEXT_LEN = 20
OCR_LANG = "por"


def _extract_image(path: str) -> str:
    return pytesseract.image_to_string(Image.open(path), lang=OCR_LANG)


def _extract_pdf(path: str) -> str:
    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(text.strip()) >= MIN_PDF_TEXT_LEN:
        return text

    from pdf2image import convert_from_path

    pages = convert_from_path(path, poppler_path=POPPLER_PATH)
    return "\n".join(pytesseract.image_to_string(page, lang=OCR_LANG) for page in pages)


def _extract_docx(path: str) -> str:
    from docx import Document

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_plain_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(path: str, estante: Optional[str]) -> Optional[str]:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(path)
        if estante == "image":
            return _extract_image(path)
        if ext == ".docx":
            return _extract_docx(path)
        if ext in (".txt", ".csv"):
            return _extract_plain_text(path)
    except Exception:
        return None
    return None
