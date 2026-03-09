# Payslip Distribution Automation — Claude Code Spec

## Executive Summary

A Windows desktop application that automates the monthly distribution of employee payslips. The user uploads a multi-page PDF (one page per employee payslip), selects the month and year, reviews an auto-assigned preview grid, confirms or corrects assignments, and sends encrypted payslip PDFs to each employee via Gmail. Each PDF is password-protected using the employee's Israeli ID number. The app is packaged as a single `.exe` requiring no Python installation.

---

## Conversation Context

### How the Idea Evolved
- Started as a simple split-and-send script
- Evolved to include an interactive preview grid for manual review before sending
- Auto ID extraction retained as a pre-fill assistant, not a blind automation
- Manual month/year selection chosen over extraction to eliminate an entire failure mode
- Tkinter rejected in favor of PyQt6 when the preview grid requirement was introduced

### Key Decisions Made
- **PyQt6** over Tkinter — required for thumbnail grid, card UI, modal dialogs
- **Auto-assign + confirmation** — app pre-fills employee from extracted ID, user confirms or overrides
- **Manual month/year** — dropdown selection, not extracted from PDF
- **Filename format:** `[Employee Name]_[Month in Hebrew]_[Year].pdf`
- **Edge case handling:** Unknown ID → pause + popup to add employee or skip
- **Email:** Gmail API via OAuth2, not SMTP
- **Employee DB:** local CSV editable in Excel

### Explicitly Out of Scope
- WhatsApp / SMS sending (noted for later)
- Automatic month detection from PDF
- Cloud sync of employee list
- Audit log / history (can be added later)

---

## Project Goals & Objectives

### Primary Goals (Must-Have)
- Upload a multi-page PDF and split it into individual pages
- Select month (Hebrew word) and year for the batch
- Display a preview grid of all split pages with auto-assigned employee (from ID extraction)
- Allow user to confirm, correct, or manually assign each page to an employee
- Rename files according to: `[שם עובד]_[חודש]_[שנה].pdf`
- Encrypt each PDF with the employee's ID number as the password
- Send each encrypted PDF via Gmail with a configurable subject + body template
- Send All and Send Selected modes
- Manage a local employee database (add, edit, delete) within the app

### Secondary Goals (Nice-to-Have)
- Status log showing send success/failure per employee
- Re-send individual failed emails without restarting the whole batch
- Remember last used template between sessions

### Non-Goals
- iOS / Android / macOS support
- Cloud storage or backup
- SMS / WhatsApp integration (explicitly deferred)
- Multi-user / multi-company support

### Success Criteria
- Entire monthly workflow completable in under 5 minutes
- Zero payslips sent to the wrong employee
- App runs on any Windows 10/11 machine without Python installed

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│                   PyQt6 Desktop App                  │
│                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │  Upload  │ → │ Preview Grid │ → │  Send Panel │ │
│  │  Screen  │   │  + Assign    │   │  + Template │ │
│  └──────────┘   └──────────────┘   └─────────────┘ │
│        │               │                   │        │
│        ▼               ▼                   ▼        │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │  pymupdf │   │  Employee    │   │  Gmail API  │ │
│  │  splitter│   │  CSV DB      │   │  sender     │ │
│  └──────────┘   └──────────────┘   └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Application Flow

```
1. Launch app
      ↓
2. Upload PDF → select month (dropdown) + year (spinner)
      ↓
3. Split PDF into N pages (pymupdf)
      ↓
4. For each page: extract text → regex for 9-digit ID → lookup CSV
      ↓
5. Preview Grid renders:
   [Thumbnail | Auto-assigned employee | Confirm / Reassign dropdown]
      ↓
   Unknown ID on page → ⚠️ flag card as unassigned
   ID found, not in CSV → popup: "Add employee or skip?"
      ↓
6. User confirms all assignments → "Confirm & Prepare" button
      ↓
7. Files renamed: [שם]_[חודש]_[שנה].pdf
   Files encrypted: password = employee ID number
      ↓
8. Template Editor opens (or is already configured):
   Subject: configurable with {name}, {month}, {year} variables
   Body: configurable with same variables
      ↓
9. Send All / Send Selected
      ↓
10. Status log: ✓ Sent / ✗ Failed per row
```

---

## Technology Stack

**Language:** Python 3.11+

**GUI:** PyQt6 6.6+
- QMainWindow, QStackedWidget for screen navigation
- QScrollArea + QGridLayout for preview grid
- QDialog for modals (add employee, template editor)
- QPainter for thumbnail rendering

**PDF Processing:**
- `pymupdf` (fitz) 1.23+ — splitting, text extraction, thumbnail rendering
- `pypdf` 3.x — PDF encryption (user password = employee ID)

**Email:**
- `google-api-python-client` — Gmail API
- `google-auth-oauthlib` — OAuth2 flow
- `google-auth-httplib2` — HTTP transport

**Employee DB:**
- CSV file (`employees.csv`) in app data directory
- Read/written via Python's built-in `csv` module
- Editable in-app via employee management screen

**Packaging:**
- `PyInstaller` 6.x → single `--onefile` `.exe`
- UPX compression optional

**Config persistence:**
- `config.json` in `%APPDATA%\PayslipApp\` — stores Gmail token, last template, window state

---

## Detailed Component Breakdown

---

### Component 1: PDF Splitter

**Purpose:** Split uploaded PDF into individual single-page PDFs held in memory

**Technology:** `pymupdf` (fitz)

**Inputs:** Path to uploaded PDF file

**Outputs:** List of `bytes` objects (one per page), list of `fitz.Page` objects for thumbnail rendering

**Key Functions:**
```python
def split_pdf(pdf_path: str) -> list[bytes]:
    """Returns list of single-page PDF bytes, one per page."""

def render_thumbnail(page: fitz.Page, width: int = 200) -> QPixmap:
    """Renders page as QPixmap for grid preview."""
```

**Notes:**
- Pages are kept in memory as `bytes` — no temp files written to disk until user confirms assignments
- Thumbnail rendered at low DPI (72) for speed; full page rendered at 150 DPI on click-to-zoom

---

### Component 2: ID Extractor

**Purpose:** Extract Israeli ID number from each payslip page

**Technology:** `pymupdf` text extraction + Python `re`

**Inputs:** Single page `fitz.Page` object

**Outputs:** 9-digit string or `None`

**Key Functions:**
```python
def extract_id(page: fitz.Page) -> str | None:
    """
    Extracts text from page, searches for 9-digit sequence.
    Handles RTL encoding artifacts by normalizing text before regex.
    Returns first 9-digit match, or None.
    """
```

**Implementation Notes:**
- Use `page.get_text("text")` — plain text mode, pymupdf handles RTL normalization better than alternatives
- Primary regex: `r'\b\d{9}\b'`
- If multiple 9-digit numbers found, prefer the one adjacent to Hebrew labels: `תז|ת"ז|תעודת זהות|ת\.ז`
- Log all extracted IDs for debugging during first real-world test

**Critical Risk:** Hebrew RTL text may extract scrambled. Mitigation: test on a real payslip sample before building anything else. If extraction fails, fall back to full manual assignment (grid still renders, all cards show as unassigned).

---

### Component 3: Employee Database

**Purpose:** Local CSV-backed employee registry

**File location:** `%APPDATA%\PayslipApp\employees.csv`

**Schema:**
```csv
id,name,email,phone
123456789,ישראל ישראלי,israel@company.com,050-1234567
987654321,שרה כהן,sara@company.com,052-9876543
```

**Key Functions:**
```python
def load_employees() -> dict[str, Employee]:
    """Returns dict keyed by ID string."""

def save_employees(employees: dict[str, Employee]) -> None:
    """Writes full CSV on every change."""

def add_employee(emp: Employee) -> None:
def update_employee(emp: Employee) -> None:
def delete_employee(id: str) -> None:
```

**Data Class:**
```python
@dataclass
class Employee:
    id: str          # 9-digit string
    name: str        # Full name in Hebrew
    email: str
    phone: str       # Optional, stored for reference
```

**In-App Management Screen:**
- Searchable table (QTableWidget) listing all employees
- Add / Edit / Delete buttons
- Input validation: ID must be exactly 9 digits, email must be valid format

---

### Component 4: Preview Grid

**Purpose:** Visual review screen showing all split pages with auto-assigned employee labels

**Technology:** PyQt6 — QScrollArea, QGridLayout, custom `PayslipCard` widget

**Card Layout (per page):**
```
┌────────────────────┐
│   [PDF Thumbnail]  │
│                    │
│  Page 3            │
│  ────────────────  │
│  ישראל ישראלי ✓   │
│  [Change Employee ▼]│
└────────────────────┘
```

**Card States:**
- ✅ **Confirmed** — auto-assigned, green border
- ⚠️ **Unassigned** — ID not found or not in DB, yellow border, dropdown required
- ✏️ **Manual Override** — user changed assignment, blue border

**Interactions:**
- Click thumbnail → opens full-page zoom modal
- Change Employee dropdown → searchable QComboBox populated from employee CSV
- "Confirm & Prepare" button (bottom of screen) — disabled until all cards are assigned

**Grid Layout:**
- Responsive columns based on window width (default: 4 columns)
- Cards are fixed size: 220px wide

---

### Component 5: File Processor

**Purpose:** Rename and encrypt confirmed payslip assignments

**Technology:** `pymupdf` (write), `pypdf` (encrypt)

**Inputs:** List of `(page_bytes, Employee, month_str, year_str)` tuples

**Outputs:** List of `(filename, encrypted_bytes, Employee)` tuples ready for sending

**Hebrew Month Map:**
```python
HEBREW_MONTHS = {
    1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
    5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
    9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
}
```

**Filename format:** `{employee.name}_{month}_{year}.pdf`
Example: `ישראל ישראלי_ינואר_2025.pdf`

**Encryption:**
```python
def encrypt_pdf(pdf_bytes: bytes, password: str) -> bytes:
    """
    Uses pypdf PdfWriter to apply user password = employee ID.
    Owner password = same (no editing restriction needed).
    Returns encrypted bytes.
    """
```

**Note:** Encryption happens in memory — no unencrypted files ever written to disk.

---

### Component 6: Email Template Editor

**Purpose:** In-app editor for Gmail subject and body with variable substitution

**UI:** QDialog with two fields:
- Subject line: QLineEdit
- Body: QTextEdit (plain text, not HTML — payslips are formal)
- Variable reference panel showing: `{name}` `{month}` `{year}` `{id}`
- Preview button: renders a sample with dummy values
- Save button: persists to `config.json`

**Template Example:**
```
Subject: תלוש שכר - {month} {year}

Body:
שלום {name},

מצורף תלוש השכר שלך לחודש {month} {year}.
הקובץ מוגן בסיסמה - מספר תעודת הזהות שלך.

בברכה,
מחלקת שכר
```

**Substitution at send time:**
```python
def render_template(template: str, employee: Employee, month: str, year: str) -> str:
    return template.format(name=employee.name, month=month, year=year, id=employee.id)
```

---

### Component 7: Gmail Sender

**Purpose:** Authenticate with Gmail API and send encrypted PDFs

**Technology:** `google-api-python-client`, `google-auth-oauthlib`

**OAuth2 Setup (one-time, done during first launch):**
1. User clicks "Connect Gmail" in settings
2. Browser opens → Google OAuth consent screen
3. Token saved to `%APPDATA%\PayslipApp\token.json`
4. Subsequent launches use saved token (auto-refresh)

**Required Gmail API Scope:** `https://www.googleapis.com/auth/gmail.send`

**Send Function:**
```python
def send_payslip(
    service,              # Gmail API service object
    to_email: str,
    subject: str,
    body: str,
    attachment_bytes: bytes,
    filename: str
) -> bool:
    """
    Builds MIME message with PDF attachment.
    Sends via Gmail API users.messages.send().
    Returns True on success, False on failure.
    """
```

**Credentials Setup (developer one-time task):**
- Create project in Google Cloud Console
- Enable Gmail API
- Create OAuth2 credentials (Desktop app type)
- Download `credentials.json` → bundle into app via PyInstaller

**Send Panel UI:**
- Table view: Employee | Email | Status (Pending / Sending... / ✓ Sent / ✗ Failed)
- Checkbox per row for selective sending
- "Send All" button — sends all
- "Send Selected" button — sends checked rows only
- Progress bar during batch send
- "Retry Failed" button appears after batch if any failures

---

## Screen Flow

```
┌─────────────┐
│   SCREEN 1  │  Upload Screen
│             │  - Drag & drop or file picker for PDF
│             │  - Month dropdown (Hebrew month names)
│             │  - Year spinner (default: current year)
│             │  - [Process →] button
└──────┬──────┘
       ↓
┌─────────────┐
│   SCREEN 2  │  Preview Grid
│             │  - Grid of PayslipCards (thumbnail + assignment)
│             │  - Employee management button (top bar)
│             │  - [← Back] [Confirm & Prepare →]
└──────┬──────┘
       ↓
┌─────────────┐
│   SCREEN 3  │  Send Panel
│             │  - Email template editor (collapsible)
│             │  - Send table with status column
│             │  - [Send All] [Send Selected] [← Back]
└─────────────┘
```

**Persistent top bar across all screens:**
- App name/logo
- Employee DB button (opens management modal)
- Gmail settings / reconnect button

---

## Development Phases

### Phase 1: Core Pipeline (No GUI)
**Estimated Duration:** 3–4 days

**Deliverables:**
- `splitter.py` — PDF split + thumbnail render
- `extractor.py` — ID extraction with RTL handling
- `employee_db.py` — CSV read/write
- `encryptor.py` — PDF password encryption
- `gmail_sender.py` — OAuth2 + send with attachment
- CLI test harness: feed a real PDF, print extracted IDs, send one test email

**Why first:** Validates the only real technical risk (Hebrew ID extraction) before building any UI.

**Risk gate:** If ID extraction on real payslip fails badly → decide on fallback strategy before proceeding.

---

### Phase 2: Basic GUI Shell
**Estimated Duration:** 3–4 days

**Deliverables:**
- PyQt6 app skeleton with QStackedWidget navigation
- Screen 1: file picker + month/year selection → triggers pipeline
- Screen 3: basic send table (no template editor yet) + send buttons
- End-to-end flow working (no preview grid yet)

---

### Phase 3: Preview Grid
**Estimated Duration:** 4–5 days

**Deliverables:**
- `PayslipCard` custom widget
- Grid layout with scroll
- Auto-assignment display
- Reassign dropdown (searchable)
- Click-to-zoom modal
- Card state colors (confirmed / unassigned / manual)
- "Confirm & Prepare" gate

**This is the hardest UI phase.** Thumbnail rendering performance needs testing — 30 cards at 200px should be fine, but test with real payslip page count.

---

### Phase 4: Polish & Edge Cases
**Estimated Duration:** 2–3 days

**Deliverables:**
- Template editor UI + variable preview
- Add Employee popup (triggered by unknown ID)
- Employee management screen (full CRUD table)
- Retry failed sends
- Error handling throughout (corrupted PDF, network failure, OAuth expiry)
- Config persistence (`config.json`)

---

### Phase 5: Packaging
**Estimated Duration:** 1–2 days

**Deliverables:**
- PyInstaller spec file
- Bundle `credentials.json` (OAuth client config) into exe
- Test cold install on clean Windows 10/11 VM
- Test Hebrew filenames on Windows (UTF-8 path handling)
- Final `.exe`

---

## Critical Challenges & Solutions

### Challenge 1: Hebrew RTL Text Extraction

**Why It's Hard:** PDFs store text as a byte stream. RTL languages like Hebrew are sometimes stored in visual order (right to left in the raw bytes), causing extracted text to appear reversed or scrambled depending on the PDF generator.

**Proposed Solution:**
1. Use `pymupdf`'s `get_text("text")` — it applies Unicode BiDi algorithm, best RTL handling available in Python PDF libs
2. Normalize extracted text with `unicodedata.normalize("NFKC", text)`
3. Search for `r'\b\d{9}\b'` (9-digit sequences) as primary signal — ID numbers are not affected by RTL ordering
4. Use Hebrew label proximity only as a tiebreaker if multiple 9-digit numbers appear

**Fallback:** If extraction works 0% of the time on real payslips (rare but possible with some PDF generators), all cards render as unassigned and the user assigns everything manually. Grid still fully functional.

**Validation step:** Before writing any UI, run `extractor.py` against a real payslip sample. This is the first thing to build.

---

### Challenge 2: Hebrew Filenames on Windows

**Why It's Hard:** Windows handles UTF-8 filenames inconsistently across older versions and some apps render Hebrew filenames RTL in Explorer.

**Proposed Solution:**
- Python 3's `pathlib.Path` handles Unicode filenames correctly on Windows 10+
- Use `Path.write_bytes()` — no encoding issues with binary PDF data
- Test on target machine explicitly; if Hebrew filenames cause issues, offer an option to use transliterated names or ID-based names as fallback

---

### Challenge 3: PyInstaller + Google Auth Bundles

**Why It's Hard:** `google-auth-oauthlib` has hidden imports PyInstaller won't detect automatically. The OAuth browser flow also requires `credentials.json` to be accessible at runtime.

**Proposed Solution:**
- Use `--collect-all google_auth_oauthlib` and `--collect-all googleapiclient` in PyInstaller spec
- Add `credentials.json` via `--add-data "credentials.json;."` 
- At runtime, locate `credentials.json` via `sys._MEIPASS` (PyInstaller's temp extraction path)
- Token stored in `%APPDATA%` — persists across app updates

---

### Challenge 4: PDF Encryption Compatibility

**Why It's Hard:** `pypdf`'s encryption uses AES-128 or AES-256. Some older PDF readers (especially on mobile) don't support AES-256.

**Proposed Solution:** Use AES-128 (RC4 is deprecated, AES-256 has compatibility issues on mobile). Israeli ID numbers as passwords are always 9 digits — short but sufficient for payslip protection, and matches what employees already know.

---

## Resource Requirements

### Technical Setup

- Python 3.11+ (dev machine only)
- Google Cloud Console account (free)
- Gmail API enabled on a project
- OAuth2 Desktop credentials (`credentials.json`)
- PyInstaller 6.x
- Windows 10/11 for final packaging test (can develop on Linux with Wine for packaging only)

### Python Dependencies

```
pymupdf>=1.23.0
pypdf>=3.0.0
PyQt6>=6.6.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
pyinstaller>=6.0.0
```

### Knowledge Requirements

| Skill | Status |
|---|---|
| Python | ✅ Have |
| PyQt6 | 🟡 Learn — docs are excellent, Qt concepts transfer from any GUI experience |
| pymupdf API | 🟡 Learn — well documented, straightforward |
| Gmail API + OAuth2 | 🟡 Learn — Google's Python quickstart covers 90% of what's needed |
| PyInstaller packaging | 🟡 Learn — standard flow, 1-2 hours |

### Cost

| Item | Cost |
|---|---|
| Gmail API | Free (well within free tier for 15–30 emails/month) |
| Google Cloud project | Free |
| All libraries | Free / open source |
| **Total** | **₪0** |

---

## Risk Analysis

### High Risk

**Gmail OAuth credentials in `.exe`**
The bundled `credentials.json` is the OAuth *client config* (app identity), not the user token. It's semi-public by nature (Google accepts this for desktop apps). The actual authorization (user token) lives in `%APPDATA%` and never leaves the machine. Risk is low but worth understanding.

**Mitigation:** Use OAuth2 Desktop App type (not Web), which Google treats differently and doesn't penalize for embedded client ID.

---

**ID extraction failure on first real payslip**
If the payslip PDF generator scrambles Hebrew text beyond recovery, auto-assignment breaks entirely.

**Mitigation:** Manual assignment fallback is built in from day one. The grid still works, just starts with all cards unassigned.

---

### Medium Risk

**Windows path issues with Hebrew characters**
Hebrew employee names in filenames may cause issues on some Windows configurations.

**Mitigation:** Test explicitly. Add a settings toggle for Latin-only filenames (ID-based) as fallback.

---

**Gmail token expiry during batch send**
OAuth tokens expire and need refresh mid-send.

**Mitigation:** `google-auth` handles token refresh automatically if refresh token is stored. Test explicitly.

---

### Potential Deal-Breakers

None identified. Every component uses mature, stable libraries with no exotic dependencies. Worst case on extraction failure → fully manual workflow, which is still faster than the current presumably-manual process.

---

## Testing Strategy

### Phase 1 Validation (Critical)
Before building any UI:
```
python test_extraction.py real_payslip.pdf
```
Output: page number, raw extracted text, found ID (or None). Validate against known IDs.

### Manual QA Checklist (before each send)
- [ ] Page count matches expected employee count
- [ ] All cards assigned before "Confirm & Prepare" enables
- [ ] Filenames correct after confirmation
- [ ] Test email sends to personal address with correct attachment
- [ ] PDF opens with correct ID as password
- [ ] Wrong password correctly rejected

### Edge Case Tests
- PDF with 1 page
- PDF with 30+ pages
- Page where ID extraction fails (confirm manual assignment works)
- Employee not in CSV (confirm add-employee popup works)
- Network failure mid-batch (confirm retry works)
- Gmail token expired (confirm re-auth flow triggers)

---

## Deployment & Distribution

### Initial Deployment
1. Developer runs `pyinstaller payslip_app.spec` on Windows machine
2. Output: `dist/PayslipApp.exe` (~80–150MB with all dependencies)
3. Copy `.exe` to wife's machine — no installation, just run
4. First launch: Gmail OAuth browser window opens → she logs in → token saved
5. Done

### Updates
- Replace `.exe` file — OAuth token in `%APPDATA%` persists across updates
- Employee CSV in `%APPDATA%` also persists

### No Auto-Update Mechanism Needed
Manual `.exe` replacement is sufficient for this usage pattern.

---

## Next Steps (Ordered)

1. **Set up Google Cloud project** — Enable Gmail API, create OAuth2 Desktop credentials, download `credentials.json`
2. **Build and test `extractor.py`** — Feed a real payslip PDF, validate 9-digit ID extraction works. This is the go/no-go gate.
3. **Build `splitter.py` + `encryptor.py` + `gmail_sender.py`** — Full pipeline as CLI, send one real encrypted test payslip to yourself
4. **Build PyQt6 app skeleton** — Navigation, Screen 1 (upload), Screen 3 (send table), wire to pipeline
5. **Build Preview Grid (Screen 2)** — PayslipCard widget, auto-assignment, manual override
6. **Add Employee management + Add Employee popup**
7. **Add Template Editor**
8. **Package with PyInstaller + test on clean Windows machine**
9. **Real-world pilot: one month's payslips, supervised**

---

## Appendices

### Key Documentation Links
- pymupdf: https://pymupdf.readthedocs.io/en/latest/
- pypdf encryption: https://pypdf.readthedocs.io/en/stable/user/encryption-decryption.html
- Gmail API Python quickstart: https://developers.google.com/gmail/api/quickstart/python
- PyQt6 docs: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- PyInstaller: https://pyinstaller.org/en/stable/

### Open Questions
- What happens if two employees share a page (edge case — probably impossible for payslips, but worth confirming)
- Should sent emails be saved to Gmail Sent folder? (Gmail API sends do appear in Sent by default — confirm this is desired)
- Does the company want a CC or BCC on all outgoing payslips?

### Employee CSV Initial Setup
Before first use, create `employees.csv` in `%APPDATA%\PayslipApp\` or use the in-app employee management screen to populate it. The app creates an empty CSV with headers on first launch if none exists.
