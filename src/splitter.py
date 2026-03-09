"""PDF Splitter — splits a multi-page PDF into individual single-page PDFs."""

import fitz  # pymupdf
from io import BytesIO


def split_pdf(pdf_path: str) -> list[bytes]:
    """Split a multi-page PDF into a list of single-page PDF bytes."""
    doc = fitz.open(pdf_path)
    pages_bytes = []
    for page_num in range(len(doc)):
        single = fitz.open()
        single.insert_pdf(doc, from_page=page_num, to_page=page_num)
        buf = single.tobytes()
        single.close()
        pages_bytes.append(buf)
    doc.close()
    return pages_bytes


def get_page_objects(pdf_path: str) -> list[fitz.Page]:
    """Return list of fitz.Page objects for thumbnail rendering.

    Caller is responsible for keeping the returned doc reference alive.
    Returns (doc, pages) tuple so caller can close doc when done.
    """
    doc = fitz.open(pdf_path)
    pages = [doc[i] for i in range(len(doc))]
    return doc, pages


def render_thumbnail(page: fitz.Page, width: int = 200) -> bytes:
    """Render a page as PNG bytes at the given width.

    Returns PNG image bytes suitable for creating QPixmap.
    """
    zoom = width / page.rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")


def render_full_page(page: fitz.Page, dpi: int = 150) -> bytes:
    """Render a page as PNG bytes at higher DPI for zoom view."""
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes("png")
