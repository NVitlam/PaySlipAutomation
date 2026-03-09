# PayslipApp

A Windows desktop application that automates monthly payslip distribution. Upload a multi-page PDF, auto-assign pages to employees by Israeli ID extraction, encrypt each payslip with the employee's ID as password, and send via Gmail.

## Features

- **PDF splitting** — Upload a multi-page PDF, splits into individual payslips
- **Auto-assignment** — Extracts 9-digit Israeli ID numbers from each page and matches to employees
- **Preview grid** — Visual review of all payslips with thumbnails, confirm or reassign before sending
- **PDF encryption** — Each payslip encrypted with AES-128, password = employee's ID number
- **Gmail sending** — OAuth2 Gmail API integration with progress tracking and retry
- **Employee management** — In-app CRUD for employee database (CSV-backed)
- **Email templates** — Configurable subject/body with `{name}`, `{month}`, `{year}`, `{id}` variables
- **Hebrew RTL** — Full right-to-left UI, Hebrew month names in filenames
- **Packagable** — PyInstaller spec for single `.exe` distribution

## Screenshots

*Coming soon*

## Setup

### Prerequisites

- Python 3.11+
- A Google Cloud project with Gmail API enabled

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/PaySlipAutomation.git
cd PaySlipAutomation
pip install -r requirements.txt
```

### Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the **Gmail API** (APIs & Services > Library > search "Gmail API")
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth 2.0 Client ID**
6. Choose application type: **Desktop app**
7. Copy the **Client ID** and **Client Secret**

### Running

```bash
python main.py
```

On first launch:
1. Click **Gmail Settings** in the top bar
2. Paste your **Client ID** and **Client Secret**
3. Click **Save Credentials**, then **Test Connection**
4. A browser window will open for Google OAuth consent — sign in and allow access

## Usage

1. **Upload** — Drag a PDF or click to browse, select month and year
2. **Preview** — Review the auto-assigned grid, fix any unassigned or incorrect matches
3. **Send** — Confirm assignments, review the send table, click Send All or Send Selected

## Project Structure

```
PaySlipAutomation/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── payslip_app.spec        # PyInstaller build spec
├── src/
│   ├── splitter.py         # PDF split + thumbnail rendering
│   ├── extractor.py        # Israeli ID extraction
│   ├── employee_db.py      # CSV employee database
│   ├── encryptor.py        # PDF encryption + filename builder
│   ├── gmail_sender.py     # Gmail OAuth2 + send
│   ├── config.py           # JSON config persistence
│   ├── upload_screen.py    # Screen 1: Upload
│   ├── preview_grid.py     # Screen 2: Preview grid
│   ├── send_panel.py       # Screen 3: Send panel
│   ├── dialogs.py          # Template editor, employee manager, Gmail settings
│   └── main_window.py      # Main window + navigation
└── tests/
```

## Building the Executable

```bash
pip install pyinstaller
pyinstaller payslip_app.spec
```

Output: `dist/PayslipApp.exe` — a standalone Windows executable (no Python needed on target machine).

## Data Storage

All user data is stored in `%APPDATA%\PayslipApp\`:

| File | Contents |
|------|----------|
| `employees.csv` | Employee database |
| `config.json` | Email templates, window size |
| `credentials.json` | OAuth2 client config (Client ID/Secret) |
| `token.json` | OAuth2 user token (auto-refreshes) |

## License

MIT
