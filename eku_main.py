from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import pickle
import json
import re

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config.json', 'r') as f:
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

def parse_eku_schedule(html_content):
    """Parse EKU schedule from JSON-LD data and return only HOME games."""
    soup = BeautifulSoup(html_content, 'html.parser')
    games = []

    # Find the JSON-LD script tag with the schedule data
    json_ld_scripts = soup.find_all('script', type='application/ld+json')

    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for event in data:
                    if event.get('@type') == 'SportsEvent':
                        # Check if it's a home game (Baptist Health Arena in Richmond, Ky.)
                        location = event.get('location', {})
                        location_name = location.get('name', '')
                        address = location.get('address', {})
                        location_city = address.get('streetAddress', '')

                        # Only include home games
                        if 'Baptist Health Arena' in location_name and 'Richmond' in location_city:
                            # Parse the datetime
                            start_date_str = event.get('startDate', '')
                            if start_date_str:
                                # Format: "2025-11-10T19:00:00"
                                game_datetime = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S")

                                # Extract opponent from name
                                name = event.get('name', '')
                                # Format is "Eastern Kentucky University Vs Opponent"
                                opponent = name.replace('Eastern Kentucky University Vs ', '')
                                opponent = opponent.replace('Eastern Kentucky University vs ', '')

                                games.append({
                                    'datetime': game_datetime,
                                    'opponent': opponent,
                                    'location': f"{location_name} | {location_city}"
                                })

                                print(f"Found home game: {opponent} on {game_datetime}")
        except Exception as e:
            print(f"Error parsing JSON-LD: {str(e)}")
            continue

    # Sort games by date
    games.sort(key=lambda x: x['datetime'])

    return games

def does_event_exist(service, event_summary, event_start):
    """Check if an event already exists in the calendar."""
    # Convert datetime to RFC3339 format
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

def create_calendar_events(games):
    """Creates Google Calendar events for each home game."""
    config = load_config()
    attendee_emails = config.get('attendees', [])

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    for game in games:
        try:
            event_summary = f"EKU Basketball vs {game['opponent']}"

            # Check if event already exists
            if does_event_exist(service, event_summary, game['datetime']):
                print(f"Skipping existing event: {event_summary}")
                continue

            # Calculate end time (2 hours later)
            end_time = game['datetime'] + timedelta(hours=2)

            # Build event object
            event = {
                'summary': event_summary,
                'location': game['location'],
                'description': f"Eastern Kentucky Colonels basketball home game against {game['opponent']}",
                'start': {
                    'dateTime': game['datetime'].isoformat(),
                    'timeZone': 'America/New_York',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/New_York',
                },
                'reminders': {
                    'useDefault': True
                },
            }

            # Add attendees if any are configured
            if attendee_emails:
                event['attendees'] = [{'email': email} for email in attendee_emails]

            event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
            print(f'Created calendar event for home game vs {game["opponent"]}')

        except Exception as e:
            print(f'Error creating event for {game["opponent"]}: {str(e)}')
            raise

def main():
    # Read HTML content from file
    with open('eku_sched.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse schedule and create events for HOME games only
    games = parse_eku_schedule(html_content)

    print(f"\nFound {len(games)} home games to add")

    if games:
        create_calendar_events(games)
    else:
        print("No home games found to process")

if __name__ == '__main__':
    main()
