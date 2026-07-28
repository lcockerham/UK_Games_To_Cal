"""Kentucky Basketball schedule parser and Google Calendar integration."""
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from calendar_common import (REQUEST_HEADERS, does_event_exist, get_calendar_service,
                              load_config, resolve_game_year)

SCHEDULE_URL = 'https://ukathletics.com/sports/mbball/schedule/'

# Month name to number mapping
MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}


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


def parse_game_date(month, day):
    """Parse a schedule month/day into a date object, inferring the year."""
    month_num = MONTH_MAP.get(month)
    if not month_num:
        raise ValueError(f"Invalid month abbreviation: {month}")
    game_date = resolve_game_year(month_num, int(day))
    if game_date is None:
        raise ValueError(f"Could not resolve a plausible year for {month} {day}")
    return game_date


def parse_datetime(game_date, time_text):
    """Combine a date with a "H:MM AM/PM" time string into a datetime."""
    time_text = time_text.upper().strip()
    return datetime.strptime(f"{game_date.isoformat()} {time_text}", "%Y-%m-%d %I:%M %p")


def parse_schedule(html_content, dry_run=False):
    """
    Parses the schedule HTML and returns list of games for the current/upcoming season.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    games = []

    schedule_items = soup.find_all('div', class_='schedule-item')

    for item in schedule_items:
        opponent = None
        try:
            date_elem = item.find('time')
            date_spans = date_elem.find_all('span')

            # HTML structure: span[0] = day of week (e.g. "Tue."), span[1] = "Nov 4"
            date_parts = date_spans[1].text.strip().split()
            month = date_parts[0]  # e.g. "Nov"
            day = date_parts[1]    # e.g. "4"

            game_date = parse_game_date(month, day)

            team_info = item.find('div', class_='schedule-item__team')
            opponent = ' '.join(team_info.h3.text.split())
            location = team_info.p.text.strip()

            time_elem = item.find('span', class_='schedule-item__result')
            time_text = time_elem.text.strip() if time_elem else "TBA"

            if dry_run:
                print("\nParsing game:")
                print(f"Date: {game_date}")
                print(f"Time text: {time_text}")

            if is_game_completed(time_text):
                if dry_run:
                    print(f"Skipping completed game: {opponent} (Score: {time_text})")
                continue

            game_datetime = None if time_text == "TBA" else parse_datetime(game_date, time_text)

            games.append({
                'date': game_date,
                'datetime': game_datetime,
                'opponent': opponent,
                'location': location
            })

            if dry_run:
                print("Successfully parsed game:")
                print(f"Opponent: {opponent}")
                print(f"Date: {game_date}")
                print(f"Time: {time_text if game_datetime else 'TBA'}")
                print(f"Location: {location}")
                print("-" * 50)

        except Exception as e:
            print(f"Error parsing game for {opponent or 'unknown opponent'}: {str(e)}")
            continue

    return games


def build_event_body(game, attendee_emails):
    """Build the Google Calendar event body for a game (timed or all-day)."""
    event_summary = f"Kentucky Basketball vs {game['opponent']}"
    description = f"Kentucky Wildcats basketball game against {game['opponent']}"

    event = {
        'summary': event_summary,
        'location': game['location'],
        'reminders': {'useDefault': True},
    }

    if game['datetime']:
        end_time = game['datetime'] + timedelta(hours=2)
        event['start'] = {'dateTime': game['datetime'].isoformat(), 'timeZone': 'America/New_York'}
        event['end'] = {'dateTime': end_time.isoformat(), 'timeZone': 'America/New_York'}
        event['description'] = description
    else:
        next_day = (game['date'] + timedelta(days=1)).isoformat()
        event['start'] = {'date': game['date'].isoformat()}
        event['end'] = {'date': next_day}
        event['description'] = f"{description} (Time TBA — update once announced)"

    if attendee_emails:
        event['attendees'] = [{'email': email} for email in attendee_emails]

    return event, event_summary


def create_calendar_events(games, dry_run=False):
    """Creates Google Calendar events for each game."""
    config = load_config()
    attendee_emails = config.get('attendees', [])

    if dry_run:
        print("\nDRY RUN - Would create the following events:")
        for game in games:
            print(f"\nEvent: Kentucky Basketball vs {game['opponent']}")
            time_note = game['datetime'].strftime('at %I:%M %p') if game['datetime'] else '(all-day, TBA)'
            print(f"Date: {game['date']} {time_note}")
            print(f"Location: {game['location']}")
            print(f"Attendees: {', '.join(attendee_emails)}")
        return

    service = get_calendar_service()

    for game in games:
        try:
            event, event_summary = build_event_body(game, attendee_emails)
            check_time = game['datetime'] or datetime.combine(game['date'], datetime.min.time())

            if does_event_exist(service, event_summary, check_time):
                print(f"Skipping existing event: {event_summary}")
                continue

            service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
            print(f'Created calendar event for game vs {game["opponent"]}')

        except Exception as e:
            print(f'Error creating event for {game["opponent"]}: {str(e)}')
            print(f'Last error occurred with opponent: {game["opponent"]}')
            raise

def main():
    """Main function to fetch the live schedule and create calendar events."""
    response = requests.get(SCHEDULE_URL, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()

    games = parse_schedule(response.text, dry_run=False)

    print(f"\nFound {len(games)} games to add")

    if games:
        create_calendar_events(games, dry_run=False)
    else:
        print("No upcoming games found to process")

if __name__ == '__main__':
    main()
