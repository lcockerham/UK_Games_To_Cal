# Basketball Calendar Integration

This project contains Python scripts to automatically import basketball game schedules into Google Calendar. It supports both Kentucky Wildcats and Eastern Kentucky Colonels basketball schedules, fetching the schedule live from the team's athletics site and creating Google Calendar events with calendar invites.

This was mostly generated using Claude - I haven't closely code reviewed it, and only cleaned up things as I saw them. It works, but it is janky. I may come back next year and make some tweaks, but it got the job done for now.

## Features

- **UK Basketball (main.py)**: Fetches the Kentucky Basketball schedule live from ukathletics.com
- **EKU Basketball (eku_main.py)**: Fetches the EKU Basketball schedule live from ekusports.com and adds HOME games only
- Automatically figures out the current/upcoming season - no yearly date edits needed
- Creates Google Calendar events with automatic attendee invitations
- Skips previously completed games
- Avoids creating duplicate calendar events
- Games without a published time yet are added as all-day events (so it's obvious a real time still needs to be set), and get a real timed event once one is announced and the script is re-run
- Supports dry-run mode for testing

## Prerequisites

- Python 3.x
- Google Calendar API credentials
- Beautiful Soup 4
- Google OAuth2 client libraries

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/lcockerham/UK_Games_To_Cal.git
   cd UK_Games_To_Cal
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

   Or manually:
   ```bash
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4 requests
   ```

3. Set up Google Calendar API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the client configuration file

## Configuration

### Step 1: Google Calendar API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the client configuration file and save it in the project directory

### Step 2: Create Configuration File

1. Copy `config.json.example` to `config.json`:
   ```bash
   cp config.json.example config.json
   ```

2. Edit `config.json` and update:
   - `attendees`: List of email addresses to invite to calendar events
   - `google_client_secret_file`: Name of your Google API credentials file

   Example:
   ```json
   {
       "attendees": [
           "person1@example.com",
           "person2@example.com"
       ],
       "google_client_secret_file": "client_secret_YOURCLIENTID.apps.googleusercontent.com.json"
   }
   ```

**Note:** `config.json` is excluded from git to protect your email addresses and configuration. Never commit this file.

## Usage

### UK Basketball Schedule

Fetches the current schedule from ukathletics.com and adds games for the current/upcoming season:

```bash
python main.py
```

### EKU Basketball Schedule (Home Games Only)

Fetches the current schedule from ekusports.com and adds EKU home games at Baptist Health Arena:

```bash
python eku_main.py
```

This automatically filters for home games only - no configuration needed.

### Optional Parameters

`dry_run=True` in `create_calendar_events()`/`parse_schedule()` runs the parsing/matching logic without creating calendar events - useful for sanity-checking a fresh season's data before sending real invites.

## Scripts Overview

### calendar_common.py
Shared helpers used by both scripts:
- `load_config()` / `get_credentials()` / `get_calendar_service()`: config and OAuth2 handling
- `does_event_exist()`: duplicate-event check
- `get_season_years()`: figures out which season (start year/end year) "now" belongs to, so nothing needs to be hardcoded and manually bumped every year

### main.py
Fetches the live UK Basketball schedule and creates calendar events. Features:
- Automatically scoped to the current/upcoming season
- Skips completed games based on score patterns
- Adds attendees to calendar invites
- TBA games become all-day events; timed games become normal 2-hour events

### eku_main.py
Fetches the live EKU Basketball schedule (JSON-LD) and creates calendar events for HOME games only. Features:
- Automatically filters for games at Baptist Health Arena in Richmond, Ky.
- Adds attendees to calendar invites
- Prevents duplicate events
- TBA games (JSON-LD games with no time component) become all-day events

## Notes

- Timed events are created with a default duration of 2 hours; TBA games are added as all-day events on the game date instead of guessing a time
- All times are set to Eastern Time Zone
- The season window is computed from today's date, not hardcoded - re-running the scripts in a later year picks up the next season automatically
- Calendar invitations are automatically sent when `sendUpdates='all'` is set
- Token credentials are stored in `token.pickle` (delete to re-authenticate)

## Development

### Code Quality

This project uses pylint for code quality checks. To run linting:

```bash
# Run pylint on all Python files
make lint

# Or manually:
python -m pylint main.py eku_main.py calendar_common.py
```

### Auto-fix Common Issues

```bash
# Fix import ordering and some formatting issues
make lint-fix
```

### Project Structure

```
UK_Games_To_Cal/
├── main.py                 # UK Basketball schedule fetcher/parser
├── eku_main.py             # EKU Basketball schedule fetcher/parser (home games)
├── calendar_common.py      # Shared config/auth/season helpers
├── config.json.example     # Configuration template
├── config.json              # Your config (not in git)
├── requirements.txt        # Python dependencies
├── .pylintrc                # Pylint configuration
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Contributing

Feel free to submit issues and pull requests for any improvements or bug fixes.

When contributing:
1. Run `make lint` to check code quality
2. Ensure all scripts work with the config.json system
3. Update README if adding new features

## License

MIT License - See LICENSE file for details
