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
        raise TextExtractionError("L'extraction de texte DOC n'est pas encore prise en charge. Importez un fichier PDF ou DOCX.")

    raise TextExtractionError("Format de fichier non pris en charge.")


def _extract_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        parts = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise TextExtractionError("Impossible d'extraire le texte du fichier PDF.") from exc

    return _normalize_text("\n".join(parts))


def _extract_docx_text(file_path: Path) -> str:
    try:
        document = Document(str(file_path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
    except Exception as exc:
        raise TextExtractionError("Impossible d'extraire le texte du fichier DOCX.") from exc

    return _normalize_text("\n".join(paragraphs))


def _normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()
