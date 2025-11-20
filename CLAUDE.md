# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MimiMail is a keyboard-driven, accessible terminal email client that connects to Gmail via the Google Gmail API. It features text-to-speech integration for accessibility using pyttsx3 and a curses-based TUI.

## Commands

### Running the Application

```bash
# Activate virtual environment and run
source /Users/bdbaddog/.virtualenvs/mimi/bin/activate
python MimiMail/mutt_main.py

# Or directly with the venv python
/Users/bdbaddog/.virtualenvs/mimi/bin/python MimiMail/mutt_main.py
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Testing Individual Modules

```bash
# Test Gmail API connection
python MimiMail/sample.py

# Test Gmail OAuth quickstart
python MimiMail/QuickStart.py
```

## Architecture

### Core Files

- **`MimiMail/mutt_main.py`** - Entry point. Handles OAuth authentication with Gmail API and initializes the UI with fetched messages.

- **`MimiMail/ui.py`** - Curses-based terminal UI implementation. Contains the `UI` class with:
  - `draw_menu(messages)` - Email list view with navigation and speak-on-scroll
  - `draw_message(message)` - Individual message view with scrolling and speech controls
  - Threading for non-blocking TTS playback

- **`MimiMail/sample.py`** - Gmail API integration and utilities:
  - `getUnreadEmails(service)` - Fetches inbox emails
  - `replace_urls()` - Regex-based URL replacement for accessibility
  - OAuth credential management

- **`MimiMail/Message.py`** - Message dataclass with smart date formatting in `__repr__()`

### Data Flow

```
mutt_main.py → OAuth2 authentication → sample.getUnreadEmails() → UI.draw_menu()
                                                                       ↓
                                                              UI.draw_message()
```

## Key Patterns

### Threading for TTS
All text-to-speech operations run in daemon threads to prevent UI blocking:
```python
thread = threading.Thread(target=self._speak_in_thread, args=(text,))
thread.daemon = True
thread.start()
```

### Gmail API Authentication
Uses OAuth2 refresh token flow:
- Reads from `credentials.json` (Google Cloud Console credentials)
- Manages `token.json` (auto-generated refresh token)
- Scopes: `gmail.readonly`

### Email Body Handling
Supports both plain text and HTML emails:
- HTML parsed with BeautifulSoup to extract text
- Base64 decoding for Gmail API payload

### Curses Color Pairs
- Pair 1 (Cyan) - Titles
- Pair 2 (Red) - Alternative highlights
- Pair 3 (Black on White) - Status bar/selected items

## Dependencies

- `google-api-python-client` - Gmail API client
- `google-auth-httplib2` - HTTP transport for auth
- `google-auth-oauthlib` - OAuth2 flow
- `pyttsx3` - Text-to-speech engine
- `beautifulsoup4` - HTML parsing

## Setup Requirements

1. Create Google Cloud Project and enable Gmail API
2. Create OAuth 2.0 desktop application credentials
3. Place `credentials.json` in project root
4. First run opens browser for OAuth approval
5. `token.json` is auto-generated with refresh token

## Known Issues

- Date formatting logic is duplicated in both `ui.py` and `Message.py` (candidate for refactoring)
- No formal testing framework configured
- No linting configuration
