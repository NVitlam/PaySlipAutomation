"""PDF Encryptor — encrypts PDFs with employee ID as password."""

from io import BytesIO
from pypdf import PdfReader, PdfWriter

HEBREW_MONTHS = {
    1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
    5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
    9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
}


def encrypt_pdf(pdf_bytes: bytes, password: str) -> bytes:
    """Encrypt a PDF with AES-128 using the given password.

    Both user and owner passwords are set to the same value.
    Returns encrypted PDF bytes.
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.encrypt(
        user_password=password,
        owner_password=password,
        algorithm="AES-128",
    )

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_filename(employee_name: str, month: int, year: int) -> str:
    """Build the Hebrew filename: name_month_year.pdf"""
    month_str = HEBREW_MONTHS[month]
    return f"{employee_name}_{month_str}_{year}.pdf"


def process_payslip(
    page_bytes: bytes,
    employee_name: str,
    employee_id: str,
    month: int,
    year: int,
) -> tuple[str, bytes]:
    """Encrypt a single payslip page and return (filename, encrypted_bytes)."""
    filename = build_filename(employee_name, month, year)
    encrypted = encrypt_pdf(page_bytes, employee_id)
    return filename, encrypted
