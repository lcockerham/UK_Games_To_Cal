# Basketball Calendar Integration

This project contains Python scripts to automatically import basketball game schedules into Google Calendar. It supports both Kentucky Wildcats and Eastern Kentucky Colonels basketball schedules, parsing HTML schedule data and creating Google calendar events with calendar invites.

This was mostly generated using Claude - I haven't closely code reviewed it, and only cleaned up things as I saw them. It works, but it is janky. I may come back next year and make some tweaks, but it got the job done for now.

## Features

- **UK Basketball (main.py)**: Parses Kentucky Basketball schedule from HTML with date range filtering
- **EKU Basketball (eku_main.py)**: Parses EKU Basketball schedule and adds HOME games only
- Creates Google Calendar events with automatic attendee invitations
- Skips previously completed games
- Avoids creating duplicate calendar events
- Handles TBA game times (defaults to noon)
- Date range filtering to add specific game periods
- Supports dry-run mode for testing
- Update existing events to change attendees (update_attendees.py)

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
2. Download schedule HTML files:
   - `schedule.html`: Kentucky Basketball schedule from https://ukathletics.com/sports/mbball/schedule/
   - `eku_sched.html`: EKU Basketball schedule from https://ekusports.com/sports/mens-basketball/schedule/
3. Ensure the `SCOPES` variable matches your Google Calendar API permissions

## Usage

### UK Basketball Schedule

Add UK basketball games within a specific date range:

```bash
python main.py
```

The script is configured to add games between specific dates. Modify `start_date` and `end_date` in the `parse_schedule()` function to change the date range.

### EKU Basketball Schedule (Home Games Only)

Add EKU home games at Baptist Health Arena:

```bash
python eku_main.py
```

This automatically filters for home games only - no configuration needed.

### Update Event Attendees

To update attendees on existing calendar events:

```bash
python update_attendees.py
```

This finds all Kentucky Basketball events and updates the attendee list.

### Optional Parameters

You can modify these parameters in the respective `main()` functions:

- `dry_run=True`: Test the parsing without creating calendar events
- `start_from="Opponent Name"`: Start creating events from a specific opponent (main.py only)
- `max_games=N`: Limit the number of games to process (main.py only)

## Scripts Overview

### main.py
Parses UK Basketball schedule from HTML and creates calendar events. Features:
- Date range filtering (configurable start/end dates)
- Skips completed games based on score patterns
- Adds attendees to calendar invites
- Supports dry-run mode

### eku_main.py
Parses EKU Basketball schedule from JSON-LD data and creates calendar events for HOME games only. Features:
- Automatically filters for games at Baptist Health Arena in Richmond, Ky.
- Adds attendees to calendar invites
- Prevents duplicate events

### update_attendees.py
Updates attendees on existing Kentucky Basketball calendar events. Features:
- Finds all Kentucky Basketball events in a date range
- Updates attendee list on all found events
- Sends calendar invitations to new attendees

## Key Functions

### Main Functions

- `parse_schedule()`: Parses HTML schedule and returns games within date range
- `parse_eku_schedule()`: Parses EKU schedule from JSON-LD and filters home games
- `create_calendar_events()`: Creates Google Calendar events with attendees
- `get_credentials()`: Handles OAuth2 authentication flow
- `update_all_kentucky_events()`: Updates attendees on existing UK events

### Helper Functions

- `is_game_completed()`: Checks if a game has already been played based on score patterns
- `parse_datetime()`: Converts schedule date/time strings to datetime objects
- `does_event_exist()`: Checks for duplicate calendar events

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
- The scripts handle the 2025-2026 basketball season
- Calendar invitations are automatically sent when `sendUpdates='all'` is set
- Token credentials are stored in `token.pickle` (delete to re-authenticate)
- HTML schedule files should be downloaded fresh from the athletic websites for accuracy

## Contributing

Feel free to submit issues and pull requests for any improvements or bug fixes.

## License

[Add your chosen license here]
