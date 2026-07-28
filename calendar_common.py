"""Shared config, auth, and season-date helpers for the basketball calendar scripts."""
import json
import os.path
import pickle
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

# How far in the past a resolved game date is allowed to be, in days. Keeps
# re-runs mid-season working (today can be after some games already happened)
# without letting an Oct/Nov/Dec game snap back to last year's date.
PAST_BUFFER_DAYS = 120

REQUEST_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36')
}


def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found!")
        print("Please copy config.json.example to config.json and fill in your details.")
        raise
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config.json: {e}")
        raise


def get_credentials():
    """Gets valid user credentials from storage or initiates OAuth2 flow."""
    config = load_config()
    client_secret_file = config.get('google_client_secret_file')

    if not client_secret_file:
        raise ValueError("google_client_secret_file not specified in config.json")

    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def get_calendar_service():
    """Builds an authenticated Google Calendar API service."""
    creds = get_credentials()
    return build('calendar', 'v3', credentials=creds)


def does_event_exist(service, event_summary, event_start):
    """Check if an event already exists in the calendar."""
    time_min = (event_start - timedelta(minutes=1)).isoformat() + 'Z'
    time_max = (event_start + timedelta(minutes=1)).isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            q=event_summary,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            if event['summary'] == event_summary:
                return True

        return False

    except Exception as e:
        print(f"Error checking for existing event: {str(e)}")
        return False


def resolve_game_year(month_num, day, today=None):
    """Resolves the year for a schedule entry that only lists month/day.

    Schedule pages only ever show the current/upcoming season, so the right
    year is whichever of last/this/next year produces the earliest date that
    isn't more than PAST_BUFFER_DAYS in the past. This avoids ever having to
    hardcode a season year that goes stale once the season rolls over.
    """
    today = today or date.today()
    best = None
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidate = date(year, month_num, day)
        except ValueError:
            continue  # e.g. Feb 29 in a non-leap year
        if (candidate - today).days >= -PAST_BUFFER_DAYS:
            if best is None or candidate < best:
                best = candidate
    return best
