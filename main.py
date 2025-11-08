from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import pickle
import re
import json

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

# Month name to number mapping
MONTH_MAP = {
    'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4',
    'May': '5', 'Jun': '6', 'Jul': '7', 'Aug': '8',
    'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}

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

def is_game_completed(time_text):
    """Check if the time text indicates a completed game (contains score)."""
    # Check for patterns that indicate a score (e.g., "W Blue 67, White 66" or "W 82-74")
    score_patterns = [
        r'\d+[,-]\s*\d+',  # Matches patterns like "82-74" or "67, 66"
        r'[WL]\s+\d+',     # Matches patterns like "W 82" or "L 74"
        r'Blue \d+',       # Matches specific Blue-White game pattern
        r'White \d+'       # Matches specific Blue-White game pattern
    ]
    
    for pattern in score_patterns:
        if re.search(pattern, time_text):
            return True
    return False

def parse_datetime(date_text, time_text):
    """Helper function to parse date and time strings."""
    try:
        # Clean up the date text
        # Remove day of week and any periods
        date_parts = date_text.split()
        month_abbr = date_parts[-3].replace('.', '')  # Get month, remove any periods
        day = date_parts[-2]
        year = date_parts[-1]  # This will be either 2024 or 2025
        
        # Convert month abbreviation to number
        month = MONTH_MAP.get(month_abbr)
        if not month:
            raise ValueError(f"Invalid month abbreviation: {month_abbr}")
            
        # Clean up time text
        time_text = time_text.upper().strip()
        
        # Combine into standard format
        datetime_str = f"{month}/{day}/{year} {time_text}"
        
        # Parse the datetime
        return datetime.strptime(datetime_str, "%m/%d/%Y %I:%M %p")
        
    except Exception as e:
        print(f"Error parsing datetime components:")
        print(f"Date text: {date_text}")
        print(f"Time text: {time_text}")
        print(f"Error details: {str(e)}")
        raise

def parse_schedule(html_content, max_games=None, dry_run=False):
    """
    Parses the schedule HTML and returns list of games.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    games = []
    games_processed = 0

    # Define date range for games to include
    start_date = datetime(2025, 11, 8)
    end_date = datetime(2025, 12, 30, 23, 59, 59)  # Include all of Dec 30

    # Find all schedule items
    schedule_items = soup.find_all('div', class_='schedule-item')
    
    for item in schedule_items:
        try:
            # Skip if we've hit our max games limit
            if max_games and games_processed >= max_games:
                break
                
            # Get date
            date_elem = item.find('time')
            date_spans = date_elem.find_all('span')

            # HTML structure: span[0] = day of week (e.g. "Tue."), span[1] = "Nov 4"
            date_parts = date_spans[1].text.strip().split()
            month = date_parts[0]  # e.g. "Nov"
            day = date_parts[1]    # e.g. "4"

            # Determine year based on month (assuming season spans Oct 2025 - Apr 2026)
            # Basketball season starts in October, so Oct/Nov/Dec are in the first year
            year = "2025" if month in ['Oct', 'Nov', 'Dec'] else "2026"

            date_text = f"{month} {day} {year}"
            
            # Get team names
            team_info = item.find('div', class_='schedule-item__team')
            opponent = team_info.h3.text.strip()
            
            # Get location
            location = team_info.p.text.strip()
            
            # Get time
            time_elem = item.find('span', class_='schedule-item__result')
            time_text = time_elem.text.strip() if time_elem else "TBA"
            
            if dry_run:
                print(f"\nParsing game:")
                print(f"Date text: {date_text}")
                print(f"Time text: {time_text}")
            
            # Skip completed games
            if is_game_completed(time_text):
                if dry_run:
                    print(f"Skipping completed game: {opponent} (Score: {time_text})")
                continue
            
            # Parse the date and time
            if time_text != "TBA":
                game_datetime = parse_datetime(date_text, time_text)
            else:
                # Default to noon for TBA games
                game_datetime = parse_datetime(date_text, "12:00 PM")

            # Skip if game is outside the date range
            if game_datetime < start_date or game_datetime > end_date:
                if dry_run:
                    print(f"Skipping game outside date range: {opponent} on {game_datetime}")
                continue
                
            games.append({
                'datetime': game_datetime,
                'opponent': opponent,
                'location': location
            })
            
            if dry_run:
                print(f"Successfully parsed game:")
                print(f"Opponent: {opponent}")
                print(f"Date/Time: {game_datetime}")
                print(f"Location: {location}")
                print("-" * 50)
            
            games_processed += 1
            
        except Exception as e:
            print(f"Error parsing game for {opponent if 'opponent' in locals() else 'unknown opponent'}: {str(e)}")
            continue
    
    return games

# [Rest of the code remains the same]

def get_event_duration(start_time):
    """Calculate end time handling overnight games."""
    end_time = start_time + timedelta(hours=2)
    return end_time

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
            q=event_summary,  # Search for events with matching summary
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        for event in events:
            # If we find an event with matching summary and start time, consider it a duplicate
            if event['summary'] == event_summary:
                return True
        
        return False
        
    except Exception as e:
        print(f"Error checking for existing event: {str(e)}")
        return False

def create_calendar_events(games, dry_run=False, start_from=None):
    """
    Creates Google Calendar events for each game.

    Args:
        games: List of game dictionaries
        dry_run: If True, just print what would be created
        start_from: Optional opponent name to start from (skips games until this opponent)
    """
    config = load_config()
    attendee_emails = config.get('attendees', [])

    if dry_run:
        print("\nDRY RUN - Would create the following events:")
        for game in games:
            print(f"\nEvent: Kentucky Basketball vs {game['opponent']}")
            print(f"Date/Time: {game['datetime']}")
            print(f"Location: {game['location']}")
            print(f"Attendees: {', '.join(attendee_emails)}")
        return

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    # Flag to track if we've reached the start_from game
    processing = start_from is None
    
    for game in games:
        try:
            # If we're looking for a specific game to start from
            if not processing:
                if game['opponent'].strip() == start_from.strip():
                    processing = True
                else:
                    continue
            
            event_summary = f"Kentucky Basketball vs {game['opponent']}"
            
            # Check if event already exists
            if does_event_exist(service, event_summary, game['datetime']):
                print(f"Skipping existing event: {event_summary}")
                continue
            
            # Calculate end time
            end_time = get_event_duration(game['datetime'])

            # Build event object
            event = {
                'summary': event_summary,
                'location': game['location'],
                'description': f"Kentucky Wildcats basketball game against {game['opponent']}",
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
            print(f'Created calendar event for game vs {game["opponent"]}')
            
        except Exception as e:
            print(f'Error creating event for {game["opponent"]}: {str(e)}')
            print(f'Last error occurred with opponent: {game["opponent"]}')
            raise  # Re-raise the exception to stop processing

def main():
    # Read HTML content from file
    with open('schedule.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse schedule and create events
    games = parse_schedule(html_content, dry_run=False)

    print(f"\nFound {len(games)} games to add")

    if games:
        # You can specify which game to start from by uncommenting and modifying the line below
        create_calendar_events(games, dry_run=False)
        #create_calendar_events(games, dry_run=False, start_from="Brown")
    else:
        print("No upcoming games found to process")

if __name__ == '__main__':
    main()
