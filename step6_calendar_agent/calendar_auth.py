from datetime import datetime, timezone
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Narrowest scope that covers list/create/delete of events
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

BASE_DIR = Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def _login():
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    return flow.run_local_server(port=0)


def get_calendar_service():
    """Return an authorized Google Calendar API client."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None  # refresh token expired/revoked: log in again
        else:
            creds = None

    if not creds:
        creds = _login()
        TOKEN_FILE.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)


if __name__ == "__main__":
    service = get_calendar_service()
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=5,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = result.get("items", [])
    if not events:
        print("Connected. No upcoming events.")
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        print(start, "-", e.get("summary", "(no title)"))
