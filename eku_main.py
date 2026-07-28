"""EKU Basketball schedule parser for HOME games only."""
import json
from datetime import datetime, time, timedelta

import requests
from bs4 import BeautifulSoup

from calendar_common import REQUEST_HEADERS, does_event_exist, get_calendar_service, load_config

SCHEDULE_URL = 'https://ekusports.com/sports/mens-basketball/schedule/'


def parse_eku_schedule(html_content):
    """Parse EKU schedule from JSON-LD data and return only HOME games."""
    soup = BeautifulSoup(html_content, 'html.parser')
    games = []

    json_ld_scripts = soup.find_all('script', type='application/ld+json')

    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for event in data:
                    if event.get('@type') == 'SportsEvent':
                        location = event.get('location', {})
                        location_name = location.get('name', '')
                        address = location.get('address', {})
                        location_city = address.get('streetAddress', '')

                        # Only include home games
                        if 'Baptist Health Arena' in location_name and 'Richmond' in location_city:
                            start_date_str = event.get('startDate', '')
                            if start_date_str:
                                # Format: "2026-11-10T19:00:00"; "T00:00:00" means no time announced yet
                                game_datetime = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S")
                                is_tba = game_datetime.time() == time(0, 0)

                                name = event.get('name', '')
                                opponent = name.replace('Eastern Kentucky University Vs ', '')
                                opponent = opponent.replace('Eastern Kentucky University vs ', '')

                                games.append({
                                    'date': game_datetime.date(),
                                    'datetime': None if is_tba else game_datetime,
                                    'opponent': opponent,
                                    'location': f"{location_name} | {location_city}"
                                })

                                print(f"Found home game: {opponent} on {game_datetime.date()}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing JSON-LD: {str(e)}")
            continue

    games.sort(key=lambda g: g['date'])

    return games


def build_event_body(game, attendee_emails):
    """Build the Google Calendar event body for a home game (timed or all-day)."""
    event_summary = f"EKU Basketball vs {game['opponent']}"
    description = f"Eastern Kentucky Colonels basketball home game against {game['opponent']}"

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


def create_calendar_events(games):
    """Creates Google Calendar events for each home game."""
    config = load_config()
    attendee_emails = config.get('attendees', [])

    service = get_calendar_service()

    for game in games:
        try:
            event, event_summary = build_event_body(game, attendee_emails)
            check_time = game['datetime'] or datetime.combine(game['date'], datetime.min.time())

            if does_event_exist(service, event_summary, check_time):
                print(f"Skipping existing event: {event_summary}")
                continue

            service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
            print(f'Created calendar event for home game vs {game["opponent"]}')

        except Exception as e:
            print(f'Error creating event for {game["opponent"]}: {str(e)}')
            raise

def main():
    """Main function to fetch the live EKU schedule and create calendar events for HOME games."""
    response = requests.get(SCHEDULE_URL, headers=REQUEST_HEADERS, timeout=30)
    response.raise_for_status()

    games = parse_eku_schedule(response.text)

    print(f"\nFound {len(games)} home games to add")

    if games:
        create_calendar_events(games)
    else:
        print("No home games found to process")

if __name__ == '__main__':
    main()
