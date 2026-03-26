"""
file_parser.py – Extract clean text from PDF, DOCX, and TXT files.

Libraries used:
  • PyMuPDF  (fitz) → PDF
  • python-docx     → DOCX
  • Built-in I/O    → TXT
"""

from pathlib import Path
from app.utils.helpers import setup_logging

logger = setup_logging("drcode.file_parser")


class UnsupportedFileTypeError(Exception):
    """Raised when a file type is not supported."""


def extract_text(filepath: str | Path) -> str:
    """
    Route to the correct extractor based on file extension.

    Args:
        filepath: Path to the uploaded file.

    Returns:
        Extracted plain-text content.

    Raises:
        UnsupportedFileTypeError: If the file extension is not PDF/DOCX/TXT.
        FileNotFoundError:        If the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(path)
    elif ext == ".docx":
        return _extract_docx(path)
    elif ext == ".txt":
        return _extract_txt(path)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: '{ext}'. Accepted: .pdf, .docx, .txt"
        )


# ── PDF extraction ───────────────────────────
def _extract_pdf(path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    import fitz  # PyMuPDF

    text_parts: list[str] = []
    try:
        with fitz.open(str(path)) as doc:
            for page in doc:
                text_parts.append(page.get_text())
    except Exception as exc:
        logger.error("PDF extraction failed for %s: %s", path, exc)
        raise

    return "\n".join(text_parts).strip()


# ── DOCX extraction ─────────────────────────
def _extract_docx(path: Path) -> str:
    """Extract all paragraph text from a DOCX file."""
    from docx import Document

    try:
        doc = Document(str(path))
        return "\n".join(para.text for para in doc.paragraphs).strip()
    except Exception as exc:
        logger.error("DOCX extraction failed for %s: %s", path, exc)
        raise


# ── TXT extraction ──────────────────────────
def _extract_txt(path: Path) -> str:
    """Read a plain-text file."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        logger.error("TXT read failed for %s: %s", path, exc)
        raise
