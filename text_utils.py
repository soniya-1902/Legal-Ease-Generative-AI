import html
import re
from typing import Iterable


def sanitize_text(text: str) -> str:
    """Normalize AI/user text into safe, portable plain text."""
    if not text:
        return ""
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ",
        "\u2022": "-", "\u00a9": "(c)", "\u00ae": "(R)",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def pdf_safe_text(text: str) -> str:
    """Make text compatible with FPDF's built-in Helvetica encoding."""
    text = sanitize_text(text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def escape_html(text: str) -> str:
    return html.escape(text, quote=True)


def split_terms(terms: str | Iterable[str]) -> list[str]:
    if isinstance(terms, str):
        items = re.split(r"[;\n]+", terms)
    else:
        items = list(terms)
    return [sanitize_text(item).lstrip("-• ").strip() for item in items if sanitize_text(item)]


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", sanitize_text(value)).strip("-").lower()
    return value or "document"
