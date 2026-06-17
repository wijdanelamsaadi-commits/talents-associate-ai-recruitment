from pathlib import Path

from docx import Document
from pypdf import PdfReader


class TextExtractionError(ValueError):
    pass


def extract_text_from_file(file_path: Path, extension: str) -> str:
    normalized_extension = extension.lower()

    if normalized_extension == ".pdf":
        return _extract_pdf_text(file_path)
    if normalized_extension == ".docx":
        return _extract_docx_text(file_path)
    if normalized_extension == ".doc":
        raise TextExtractionError("DOC text extraction is not supported yet. Please upload a PDF or DOCX file.")

    raise TextExtractionError("Unsupported file format.")


def _extract_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        parts = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise TextExtractionError("Could not extract text from the PDF file.") from exc

    return _normalize_text("\n".join(parts))


def _extract_docx_text(file_path: Path) -> str:
    try:
        document = Document(str(file_path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
    except Exception as exc:
        raise TextExtractionError("Could not extract text from the DOCX file.") from exc

    return _normalize_text("\n".join(paragraphs))


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
