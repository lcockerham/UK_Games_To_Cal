# Kentucky Basketball Calendar Integration

This Python script automatically imports Kentucky Basketball game schedules into Google Calendar. It parses HTML schedule data from https://ukathletics.com/sports/mbball/schedule/ and creates Google calendar events for upcoming games while skipping past games and avoiding duplicate entries.

This was mostly generated using Claude - I haven't closely code reviewed it, and only cleaned up things as I saw them. It works, but it is janky. I may come back next year and make some tweaks, but it got the job done for now. 

## Features

- Parses Kentucky Basketball schedule from HTML
- Creates Google Calendar events for upcoming games
- Skips previously completed games
- Avoids creating duplicate calendar events
- Handles TBA game times (defaults to noon)
- Supports dry-run mode for testing
- Allows starting from a specific opponent in the schedule

## Prerequisites

- Python 3.x
- Google Calendar API credentials
- Beautiful Soup 4
- Google OAuth2 client libraries

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4
```

3. Set up Google Calendar API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the client configuration file and rename it to `client_secret_[YOUR_CLIENT_ID].json`

## Configuration

1. Place your Google Calendar API credentials file in the same directory as the script
2. Create a `schedule.html` file containing the Kentucky Basketball schedule HTML
3. Ensure the `SCOPES` variable matches your Google Calendar API permissions

## Usage

### Basic Usage

```bash
python main.py
```

### Optional Parameters

You can modify these parameters in the `main()` function:

- `dry_run=True`: Test the parsing without creating calendar events
- `start_from="Opponent Name"`: Start creating events from a specific opponent
- `max_games=N`: Limit the number of games to process

## Function Documentation

### Main Functions

- `parse_schedule(html_content, max_games=None, dry_run=False)`: 
  Parses HTML schedule and returns list of upcoming games

- `create_calendar_events(games, dry_run=False, start_from=None)`: 
  Creates Google Calendar events for parsed games

- `get_credentials()`: 
  Handles OAuth2 authentication flow

### Helper Functions

- `is_game_completed(time_text)`: 
  Checks if a game has already been played

- `parse_datetime(date_text, time_text)`: 
  Converts schedule date/time strings to datetime objects

- `does_event_exist(service, event_summary, event_start)`: 
  Checks for duplicate calendar events

## Error Handling

The script includes comprehensive error handling for:
- Invalid date/time formats
- API authentication failures
- Duplicate events
- Network issues
- HTML parsing errors

## Notes

- Events are created with a default duration of 2 hours
- All times are set to Eastern Time Zone
- TBA game times default to 12:00 PM
- The script assumes the season spans 2024-2025

## Contributing

Feel free to submit issues and pull requests for any improvements or bug fixes.

## License

[Add your chosen license here]
