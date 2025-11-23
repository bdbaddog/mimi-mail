# GEMINI.md

This file provides context to the Gemini AI model for the mimi-mail project.

## Project Overview

MimiMail is a keyboard-driven, accessible terminal email client for macOS, Linux, and Windows. It connects to the Gmail API to fetch and display unread emails. It features text-to-speech (TTS) integration for accessibility, using `pyttsx3`, and a `curses`-based terminal user interface (TUI).

## Setup and Running

1.  **Install Dependencies:** Install the required dependencies from `requirements.txt`. It is recommended to do this within a Python virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Google API Credentials:** This project requires Google API credentials to access Gmail.
    1.  Create a Google Cloud Project and enable the Gmail API.
    2.  Create OAuth 2.0 desktop application credentials.
    3.  The application will guide you on creating the `credentials.json` file on the first run if it is missing. Follow the printed instructions to download the credentials and paste the content into the created `credentials.json` file.

3.  **Run the Application:** To run the application, execute the `mutt_main.py` script.
    ```bash
    python MimiMail/mutt_main.py
    ```
    The first time you run the application with valid credentials, it will open a browser window for you to authorize access to your Gmail account. A `token.json` file will then be created to store the authorization token for future sessions.

## Architecture

### Key Files

*   `MimiMail/mutt_main.py`: The main entry point of the application. Initializes the UI and orchestrates the application flow.
*   `MimiMail/auth.py`: Handles all aspects of Google API authentication, including the OAuth2 flow and credential/token management (`credentials.json`, `token.json`).
*   `MimiMail/ui.py`: Implements the `curses`-based TUI, including the message list and message view.
*   `MimiMail/gmail_interface.py`: Handles all communication with the Gmail API, including fetching and parsing emails.
*   `MimiMail/Message.py`: Defines the `Message` data class, which represents an email message.
*   `requirements.txt`: Lists the Python dependencies for the project.

### Data Flow

```
mutt_main.py → auth.get_gmail_service() → Gmail API Auth Flow
             ↓
             gmail_interface.getUnreadEmails() → UI.draw_menu()
                                                    ↓
                                               UI.draw_message()
```

## Key Patterns & Conventions

*   **Gmail API Authentication:** Uses an OAuth2 refresh token flow managed by the `google-auth-oauthlib` library.
    *   Reads from `credentials.json` (Google Cloud Console credentials for a Desktop App).
    *   Generates and manages `token.json` (the auto-generated user refresh token).
    *   Uses a `gmail.readonly` scope, so the application can only read emails.

*   **Threading for TTS:** All text-to-speech operations run in daemon threads to prevent UI blocking.
    ```python
    import threading
    thread = threading.Thread(target=self._speak_in_thread, args=(text,))
    thread.daemon = True
    thread.start()
    ```

*   **Email Body Handling:** Supports both plain text and HTML emails.
    *   HTML is parsed with `BeautifulSoup4` to extract clean text.
    *   The email body is Base64 decoded from the Gmail API payload.

*   **Curses Color Pairs:** The UI uses a predefined set of colors.
    *   Pair 1 (Cyan): Titles
    *   Pair 2 (Red): Alternative highlights
    *   Pair 3 (Black on White): Status bar / selected items

## Key Dependencies

*   `windows-curses`: Windows support for the `curses` library.

## Attempted Solutions for Speech Issues (Failed or Partially Successful)

This section documents various attempts to resolve persistent text-to-speech (TTS) issues, primarily related to `pyttsx3`'s behavior in a multi-threaded `curses` environment. The primary goal is to avoid re-trying solutions that proved ineffective.

### 1. Initial Refactoring for TTS Stability

*   **Problem:** `pyttsx3` `RuntimeError: run loop already started` on exit, 's' key not working for message speech, initial message not reading, "received on today" phrasing.
*   **Fixes Implemented:**
    *   Centralized `pyttsx3` engine instance, passing it from `mutt_main.py` to `UI`.
    *   Simplified `ui.py`'s speech methods (`_speak`, `_start_speech`) to use a single background thread per utterance, aiming to prevent `runAndWait()` conflicts.
    *   Added explicit call to `_start_speech` in `UI.draw_menu` for the initial message.
    *   Modified `Message.py`'s `get_speech_summary` for grammatically correct "received today" phrasing.
*   **Outcome:** Date phrasing was fixed. The initial message was still not read. Scrolling messages were still not read. The 's' key for message speech was still not working. Crash on exit was still present.

### 2. Progress Reporting with Threading and Lock

*   **Problem:** Audible progress updates during email loading (requested by user) were not working reliably.
*   **Fixes Implemented:**
    *   Introduced a dedicated `_speak_progress` helper function in `gmail_interface.py` to run speech in a separate thread.
    *   Implemented a `threading.Lock` (`_speech_lock`) to serialize access to the `pyttsx3` engine for progress updates, preventing `runAndWait()` conflicts between progress threads.
*   **Outcome:** Progress reporting still did not work.

### 3. Centralized `Speaker` Class Refactoring

*   **Problem:** General unreliability of speech, `RuntimeError`s, 's' key not working, scrolling not speaking, progress reporting not working consistently. Suspected fundamental issues with `pyttsx3`'s interaction with multiple threads.
*   **Fixes Implemented:**
    *   Created `MimiMail/speaker.py` with a robust `Speaker` class. This class manages a single `pyttsx3` engine instance and uses a dedicated internal worker thread with a `queue.Queue` to process all speech requests sequentially.
    *   Refactored `mutt_main.py`, `gmail_interface.py`, and `ui.py` to all use this `Speaker` instance for speech, removing all direct `pyttsx3.init()` and direct `engine` calls from these modules.
*   **Outcome:** The first message in the message list *now reads* correctly. However, progress reporting *still did not work*, scrolling messages *still did not read*, and the 's' key for message speech *still did not work*. Crash on exit was still present.

### 4. `Speaker.stop()` Modification (Removed `engine.stop()` Call)

*   **Problem:** Despite the `Speaker` class, speech issues persisted. Hypothesis: `self.engine.stop()` was leaving the `pyttsx3` engine in an unusable state after an interruption.
*   **Fixes Implemented:**
    *   Modified the `Speaker.stop()` method to only clear the internal speech queue, explicitly *not* calling `self.engine.stop()`. This allowed the current utterance to finish naturally instead of being interrupted.
*   **Outcome:** This change had no discernible positive effect. Progress reporting *still did not work*, scrolling messages *still did not read*, and the 's' key for message speech *still did not work*. Crash on exit was still present.

## Known Issues

*   Date formatting logic may be duplicated in `ui.py` and `Message.py`.
*   No formal testing framework is configured.
*   No linting configuration is in place.
