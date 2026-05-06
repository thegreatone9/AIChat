"""
Document text extraction — supports PDF, TXT, Markdown, DOCX, CSV, and web URLs.
"""

from pathlib import Path
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".csv"}


def load_file(file_path: str) -> str:
    """
    Extract text from a file based on its extension.

    Args:
        file_path: Absolute path to the file.

    Returns:
        Extracted text content.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file type is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    if ext == ".pdf":
        return _load_pdf(path)
    elif ext in (".txt", ".md", ".csv"):
        return _load_text(path)
    elif ext == ".docx":
        return _load_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def load_url(url: str) -> str:
    """
    Fetch and extract text from a web page.

    Args:
        url: The URL to scrape.

    Returns:
        Extracted text content.
    """
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(url, timeout=30, headers={
        "User-Agent": "AIChat Knowledge Bot/1.0",
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script, style, nav, footer, header elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Extract text from the main content
    text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive blank lines
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    return text


# --- Private loaders ---

def _load_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(str(path))
    pages_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return "\n\n".join(pages_text)


def _load_text(path: Path) -> str:
    """Read a plain text, markdown, or CSV file."""
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_docx(path: Path) -> str:
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


# Keep backward compatibility
def load_pdf(file_path: str) -> str:
    """Legacy wrapper — use load_file() instead."""
    return _load_pdf(Path(file_path))
