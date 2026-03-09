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
git clone https://github.com/NVitlam/PaySlipAutomation.git
cd PaySlipAutomation
pip install -r requirements.txt
```

### Google Cloud Setup (Step-by-Step)

#### Step 1 — Create a Google Cloud Project

Go to [console.cloud.google.com](https://console.cloud.google.com/). Sign in with the Google account that will send the payslips. Click the project dropdown at the top left (next to "Google Cloud") and hit **New Project**. Give it a name like `payslip-sender`, leave organization as-is, and click **Create**. Make sure it's selected as the active project.

#### Step 2 — Enable the Gmail API

In the left sidebar go to **APIs & Services → Library** (or just search "Gmail API" in the top search bar). Click on **Gmail API** and hit **Enable**. Wait a few seconds for it to activate.

#### Step 3 — Configure the OAuth Consent Screen

Before you can create credentials, Google forces you to set up the consent screen. Go to **APIs & Services → OAuth consent screen**. Choose **External** as the user type (unless you have a Workspace org, then Internal is fine). Click **Create**.

Fill in the required fields:
- **App name** — e.g. "Payslip Sender"
- **User support email** — your email
- **Developer contact email** — same email at the bottom

Skip the logo/links, just hit **Save and Continue**.

On the **Scopes** page, click **Add or Remove Scopes**, search for `gmail.send`, check it (`https://www.googleapis.com/auth/gmail.send`), and click **Update** then **Save and Continue**.

On the **Test Users** page, click **Add Users** and add the Gmail address that will send payslips. This is critical — while the app is in "Testing" mode, only listed test users can authenticate. Hit **Save and Continue**, then **Back to Dashboard**.

#### Step 4 — Create OAuth2 Desktop Credentials

Go to **APIs & Services → Credentials**. Click **+ Create Credentials** at the top and choose **OAuth client ID**. For Application type, select **Desktop app**. Name it something like `payslip-desktop-client`. Click **Create**.

A dialog pops up with your **Client ID** and **Client Secret** — copy these (you'll paste them into the app).

#### Step 5 — First Run

```bash
python main.py
```

1. Click **Gmail Settings** in the top bar
2. Paste your **Client ID** and **Client Secret**
3. Click **Save Credentials**
4. Click **Test Connection** — a browser window will open asking you to sign in and grant permission
5. You'll see a scary "Google hasn't verified this app" screen — click **Advanced → Go to [app name] (unsafe)**. This is normal for personal/test apps.
6. Click **Allow** — the app receives a token which gets saved locally
7. The connection log should show "Connection Test PASSED"

After that first auth, subsequent runs use the saved token and won't prompt again unless it expires.

> **Tip:** If the token expires or you change scopes, open Gmail Settings, click **Clear Token**, and test again to re-authenticate.

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
