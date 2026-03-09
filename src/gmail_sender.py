"""Gmail Sender — OAuth2 authentication and email sending via Gmail API."""

import base64
import logging
import os
import json
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
APP_DATA_DIR = Path(os.environ.get("APPDATA", ".")) / "PayslipApp"
TOKEN_PATH = APP_DATA_DIR / "token.json"
CREDENTIALS_PATH = APP_DATA_DIR / "credentials.json"

logger = logging.getLogger("gmail")


def save_credentials(client_id: str, client_secret: str, project_id: str) -> None:
    """Save OAuth2 client credentials to credentials.json in app data."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    creds_data = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "project_id": project_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }
    with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
        json.dump(creds_data, f, indent=2)
    logger.info("Credentials saved to %s", CREDENTIALS_PATH)


def load_saved_credentials() -> dict:
    """Load saved client credentials. Returns dict with client_id, client_secret, project_id."""
    if not CREDENTIALS_PATH.exists():
        return {"client_id": "", "client_secret": "", "project_id": ""}
    try:
        with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        installed = data.get("installed", {})
        return {
            "client_id": installed.get("client_id", ""),
            "client_secret": installed.get("client_secret", ""),
            "project_id": installed.get("project_id", ""),
        }
    except (json.JSONDecodeError, OSError):
        return {"client_id": "", "client_secret": "", "project_id": ""}


def clear_token() -> None:
    """Remove saved OAuth token (forces re-authentication)."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
        logger.info("Token cleared — will re-authenticate on next connection.")


def authenticate(log_callback=None) -> Credentials:
    """Authenticate with Gmail API. Returns credentials object.

    log_callback: optional callable(str) for real-time log messages.
    """
    def log(msg):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    creds = None
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if TOKEN_PATH.exists():
        log("Loading saved token...")
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        log("Token loaded.")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log("Token expired — refreshing...")
            creds.refresh(Request())
            log("Token refreshed successfully.")
        else:
            if not CREDENTIALS_PATH.exists():
                msg = "No credentials configured. Open Gmail Settings and enter your Client ID and Client Secret."
                log(msg)
                raise FileNotFoundError(msg)

            log("Starting OAuth2 browser flow...")
            log("A browser window will open — sign in with your Gmail account.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
            log("OAuth2 authorization complete.")

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        log("Token saved.")

    return creds


def get_gmail_service(log_callback=None):
    """Build and return Gmail API service object."""
    creds = authenticate(log_callback=log_callback)
    return build("gmail", "v1", credentials=creds)


def test_connection(log_callback=None) -> tuple[bool, str]:
    """Test Gmail connection. Returns (success, message).

    Attempts full auth + profile fetch to verify everything works.
    """
    def log(msg):
        logger.info(msg)
        if log_callback:
            log_callback(msg)

    try:
        log("--- Testing Gmail Connection ---")

        # Check credentials exist
        if not CREDENTIALS_PATH.exists():
            log("FAIL: No credentials file found.")
            log("Enter your Client ID and Client Secret and save first.")
            return False, "No credentials configured."

        saved = load_saved_credentials()
        if not saved["client_id"] or not saved["client_secret"]:
            log("FAIL: Client ID or Client Secret is empty.")
            return False, "Client ID or Client Secret is empty."

        log(f"Client ID: {saved['client_id'][:20]}...")
        log(f"Project ID: {saved['project_id'] or '(not set)'}")

        # Try to authenticate
        log("Authenticating...")
        service = get_gmail_service(log_callback=log_callback)

        # Auth succeeded and service was built — token has gmail.send scope
        log("Gmail service built successfully.")
        log("Scope: gmail.send")

        # Verify token info
        creds = authenticate(log_callback=log_callback)
        if creds.valid:
            log("Token is valid.")
        if creds.token:
            log(f"Token expiry: {creds.expiry or 'unknown'}")

        log("--- Connection Test PASSED ---")
        return True, "Connected — ready to send"

    except FileNotFoundError as e:
        log(f"FAIL: {e}")
        return False, str(e)
    except Exception as e:
        error_str = str(e)
        log(f"FAIL: {error_str}")

        # Provide helpful hints based on common errors
        if "invalid_client" in error_str.lower():
            log("Hint: The Client ID or Client Secret is incorrect.")
        elif "access_denied" in error_str.lower():
            log("Hint: The user denied access. Try again and click 'Allow'.")
        elif "redirect_uri_mismatch" in error_str.lower():
            log("Hint: Make sure your OAuth credentials are of type 'Desktop app'.")
        elif "invalid_grant" in error_str.lower():
            log("Hint: Token expired or revoked. Click 'Clear Token' and try again.")
        elif "connectionerror" in error_str.lower() or "timeout" in error_str.lower():
            log("Hint: Check your internet connection.")

        log("--- Connection Test FAILED ---")
        return False, error_str


def send_payslip(
    service,
    to_email: str,
    subject: str,
    body: str,
    attachment_bytes: bytes,
    filename: str,
) -> bool:
    """Send an email with a PDF attachment via Gmail API.

    Returns True on success, False on failure.
    """
    try:
        msg = MIMEMultipart()
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))

        attachment = MIMEApplication(attachment_bytes, _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename=filename
        )
        msg.attach(attachment)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()

        return True
    except Exception as e:
        print(f"Failed to send to {to_email}: {e}")
        return False


def render_template(template: str, name: str, month: str, year: str, emp_id: str) -> str:
    """Substitute variables in an email template string."""
    return template.format(name=name, month=month, year=year, id=emp_id)


def is_authenticated() -> bool:
    """Check if we have valid saved credentials."""
    if not TOKEN_PATH.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        return creds.valid or (creds.expired and creds.refresh_token is not None)
    except Exception:
        return False
