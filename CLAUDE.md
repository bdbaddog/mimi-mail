# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MimiMail is a keyboard-driven, accessible terminal email client that connects to Gmail via the Google Gmail API. It features text-to-speech integration for accessibility using pyttsx3 and a curses-based TUI.

## Commands

### Running the Application

```bash
cd MimiMail && python3 mutt_main.py
```

### Testing Individual Modules

```bash
# Test Gmail API connection
python3 MimiMail/gmail_interface.py

# Test Gmail OAuth quickstart
python3 MimiMail/QuickStart.py
```

## Architecture

### Core Files

- **`MimiMail/mutt_main.py`** - Entry point. Handles OAuth authentication with Gmail API, initializes SpeechController, and starts the UI.

- **`MimiMail/ui.py`** - Curses-based terminal UI. Contains the `UI` class with:
  - `draw_menu(messages)` - Email list view with navigation and speak-on-scroll
  - `draw_message(message)` - Individual message view with scrolling and speech controls ('s' to speak/stop, '+'/'-' for rate, 'u' to toggle URLs)

- **`MimiMail/speech_controller.py`** - Thread-safe TTS controller using command queue pattern:
  - Single worker thread owns the pyttsx3 engine
  - UI communicates via `speak()`, `stop()`, `set_rate()`, `is_speaking()`
  - Supports resumable speech (pause/resume from same position in message body)

- **`MimiMail/gmail_interface.py`** - Gmail API integration:
  - `getUnreadEmails(service)` - Fetches inbox emails with recursive multipart parsing
  - `replace_urls()` - Regex-based URL replacement for accessibility
  - `_find_body_parts()` - Handles nested multipart email structures

- **`MimiMail/Message.py`** - Message dataclass with:
  - Smart date formatting: `get_date_for_display()`, `get_date_for_speech()`, `get_date_full()`
  - `get_speech_summary()` - Text spoken when message selected in list
  - `get_body_text()` - Extract body from payload

### Data Flow

```
mutt_main.py → OAuth2 auth → gmail_interface.getUnreadEmails() → UI.draw_menu()
     ↓                                                                ↓
SpeechController ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←← UI.draw_message()
```

## Key Patterns

### Command Queue for TTS
SpeechController uses a command queue pattern to handle pyttsx3 thread safety:
- Worker thread processes SPEAK, STOP, SET_RATE, RESET_RESUMABLE, SHUTDOWN commands
- UI thread never directly touches the pyttsx3 engine
- Resumable speech tracks word index for pause/resume within message body

### Gmail API Authentication
Uses OAuth2 refresh token flow:
- Reads from `credentials.json` (Google Cloud Console credentials)
- Manages `token.json` (auto-generated refresh token)
- Scopes: `gmail.readonly`

### Email Body Handling
Supports both plain text and HTML emails:
- Recursively searches nested multipart structures
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
3. Place `credentials.json` in MimiMail directory
4. First run opens browser for OAuth approval
5. `token.json` is auto-generated with refresh token

## Known Issues

- pyttsx3 threading on macOS: `runAndWait()` may not block properly in background threads
- No formal testing framework configured
