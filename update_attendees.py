from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def get_credentials():
    """Gets valid user credentials from storage or initiates OAuth2 flow."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_94829445065-jj6fc83as2g12lijs73dtnuetvmsmipb.apps.googleusercontent.com.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def update_all_kentucky_events():
    """Find and update all Kentucky Basketball events with correct attendee."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    # Search for all Kentucky Basketball events
    # Start from Oct 2025 to cover the entire season
    time_min = datetime(2025, 10, 1).isoformat() + 'Z'
    time_max = datetime(2026, 4, 1).isoformat() + 'Z'

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            q='Kentucky Basketball',
            singleEvents=True,
            orderBy='startTime',
            maxResults=100
        ).execute()

        events = events_result.get('items', [])

        print(f"Found {len(events)} Kentucky Basketball events")

        for event in events:
            event_id = event['id']
            summary = event.get('summary', 'Unknown')
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'Unknown'))

            # Update the attendees list
            event['attendees'] = [
                {'email': 'jacinda.bertie@eku.edu'}
            ]

            # Update the event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            print(f"Updated: {summary} - {start}")

        print(f"\nSuccessfully updated {len(events)} events!")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    update_all_kentucky_events()
