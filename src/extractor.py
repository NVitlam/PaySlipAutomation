"""ID Extractor — extracts Israeli ID numbers from payslip PDF pages."""

import re
import unicodedata
import fitz  # pymupdf

# Hebrew labels that typically appear near ID numbers
HEBREW_ID_LABELS = re.compile(r'תז|ת"ז|תעודת זהות|ת\.ז')

# Primary pattern: exactly 9 digits as a standalone token
NINE_DIGIT_PATTERN = re.compile(r'\b\d{9}\b')


def extract_text(page: fitz.Page) -> str:
    """Extract and normalize text from a PDF page."""
    raw = page.get_text("text")
    normalized = unicodedata.normalize("NFKC", raw)
    return normalized


def extract_id(page: fitz.Page) -> str | None:
    """Extract a 9-digit Israeli ID number from a PDF page.

    Strategy:
    1. Extract and normalize text
    2. Find all 9-digit sequences
    3. If multiple found, prefer the one closest to a Hebrew ID label
    4. Return first match or None
    """
    text = extract_text(page)
    matches = NINE_DIGIT_PATTERN.findall(text)

    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    # Multiple 9-digit numbers — find one closest to Hebrew ID label
    best_match = None
    best_distance = float('inf')

    for label_match in HEBREW_ID_LABELS.finditer(text):
        label_pos = label_match.start()
        for digit_match in NINE_DIGIT_PATTERN.finditer(text):
            distance = abs(digit_match.start() - label_pos)
            if distance < best_distance:
                best_distance = distance
                best_match = digit_match.group()

    # If we found one near a label, use it; otherwise use the first match
    return best_match if best_match else matches[0]


def extract_ids_from_pdf(pdf_path: str) -> list[str | None]:
    """Extract IDs from all pages of a PDF. Returns list parallel to pages."""
    doc = fitz.open(pdf_path)
    ids = []
    for i in range(len(doc)):
        page = doc[i]
        found_id = extract_id(page)
        ids.append(found_id)
    doc.close()
    return ids
