# GEMINI.md

This file provides context to the Gemini AI model for the mimi-mail project.

## Project Overview

MimiMail is a keyboard-driven, accessible terminal email client designed exclusively for **Windows**. It connects to the Gmail API to fetch and display unread emails. It. It features text-to-speech (TTS) integration for accessibility, using the native Windows SAPI5 interface, and a `curses`-based terminal user interface (TUI).

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
*   `MimiMail/ui.py`: Implements the `curses`-based TUI, including the message list and message view. Handles user input, screen rendering, and debounced speech for navigation.
*   `MimiMail/gmail_interface.py`: Handles all communication with the Gmail API, including fetching and parsing emails. Also provides visual and audible progress updates during loading.
*   `MimiMail/Message.py`: Defines the `Message` data class, which represents an email message.
*   `MimiMail/speaker.py`: Manages all text-to-speech operations using the native Windows SAPI5 interface. Implements a thread-safe, action-based queueing system with text chunking and state tracking (`is_speaking()`).
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

*   **Platform Specificity:** The application is designed to run exclusively on **Windows**.
*   **Gmail API Authentication:** Uses an OAuth2 refresh token flow managed by the `google-auth-oauthlib` library.
    *   Reads from `credentials.json` (Google Cloud Console credentials for a Desktop App).
    *   Generates and manages `token.json` (the auto-generated user refresh token).
    *   Uses a `gmail.readonly` scope, so the application can only read emails.
*   **Text-to-Speech (TTS):** All text-to-speech operations are handled by the `MimiMail/speaker.py` module, utilizing the native Windows SAPI5 interface for stability and responsiveness.
    *   A single dedicated worker thread manages the SAPI `SpVoice` COM object, ensuring proper COM threading.
    *   An action-based queue (`say`, `stop`, `set_rate`) allows for precise control.
    *   Long texts are chunked to enable responsive interruptions.
    *   The `is_speaking()` method provides real-time status.
*   **Debounced UI Speech:** When navigating the message list, speech is debounced to avoid reading every message during rapid scrolling.
*   **Email Body Handling:** Supports both plain text and HTML emails.
    *   HTML is parsed with `BeautifulSoup4` to extract clean text.
    *   The email body is Base64 decoded from the Gmail API payload.
*   **Curses Color Pairs:** The UI uses a predefined set of colors:
    *   Pair 1 (Cyan): Titles
    *   Pair 2 (Red): Alternative highlights
    *   Pair 3 (Black on White): Status bar / selected items

## Key Dependencies

*   `google-api-python-client`: Google API Client Library.
*   `google-auth-httplib2`: HTTP transport for Google auth.
*   `google-auth-oauthlib`: OAuth 2.0 flow support.
*   `beautifulsoup4`: HTML parsing.
*   `windows-curses`: Provides `curses` functionality on Windows.
*   `pywin32`: Required for direct interaction with Windows COM APIs (e.g., SAPI5).

## Attempted Solutions for Speech Issues (Failed or Partially Successful)

This section documents various attempts to resolve persistent text-to-speech (TTS) issues. The primary goal is to keep a record of debugging efforts and prevent retrying ineffective strategies.

### 1. Initial `pyttsx3` Refactoring

*   **Problem:** `pyttsx3` `RuntimeError: run loop already started` on exit, 's' key not working for message speech, initial message not reading, "received on today" phrasing.
*   **Fixes Implemented:** Centralized `pyttsx3` engine, simplified `ui.py` speech methods, explicit `_start_speech` call, grammatically correct date phrasing.
*   **Outcome:** Date phrasing was fixed. Other issues (initial message, scrolling, 's' key, exit crash) persisted.

### 2. Progress Reporting with `pyttsx3` Threading and Lock

*   **Problem:** Audible progress updates during email loading (requested by user) were not working reliably.
*   **Fixes Implemented:** Dedicated `_speak_progress` helper in `gmail_interface.py`, `threading.Lock` for `pyttsx3` access.
*   **Outcome:** Progress reporting still did not work.

### 3. Centralized `Speaker` Class with `pyttsx3` (initial)

*   **Problem:** General unreliability of speech, `RuntimeError`s, 's' key not working, scrolling not speaking, progress reporting not working consistently.
*   **Fixes Implemented:** Created `MimiMail/speaker.py` with a robust `Speaker` class using `pyttsx3` in a dedicated worker thread with a `queue.Queue`. Refactored other modules to use this `Speaker`.
*   **Outcome:** First message in message list *now read* correctly. However, progress reporting *still did not work*, scrolling messages *still did not read*, 's' key *still did not work*, and crash on exit *still present*.

### 4. `Speaker.stop()` Modification (Removed `engine.stop()` Call)

*   **Problem:** Hypothesis: `self.engine.stop()` was leaving `pyttsx3` in an unusable state.
*   **Fixes Implemented:** Modified `Speaker.stop()` to only clear the internal speech queue, explicitly *not* calling `self.engine.stop()`.
*   **Outcome:** No discernible positive effect. All speech issues persisted.

### 5. Transition to Windows-only `win32com.client` (SAPI5) with Incorrect COM Initialization

*   **Problem:** Persistent speech issues on Windows, suspected `pyttsx3` and COM threading conflicts.
*   **Fixes Implemented:** Switched `Speaker` to use `win32com.client` directly for Windows SAPI5. Added `pywin32` dependency. Implemented `pythoncom.CoInitialize()` in `_windows_worker` and (erroneously) in `say_and_wait` on the main thread.
*   **Outcome:** Regression: initial message *no longer read*. All other speech issues persisted. `say_and_wait`'s COM handling was identified as interfering with the main thread's COM state.

### 6. `win32com.client` with Corrected COM Initialization

*   **Problem:** `say_and_wait`'s COM handling was interfering.
*   **Fixes Implemented:** Removed `pythoncom.CoInitialize()` and `CoUninitialize()` from `say_and_wait`, ensuring COM is only initialized once per thread (in `_windows_worker`).
*   **Outcome:** Initial message *still not read*. Scrolling messages *still not read*. 's' key *still not working*. Progress reporting *still not working*. This indicated that even with correct COM initialization, `voice.Speak` might be blocking.

### 7. `win32com.client` with `is_speaking()` State Tracking & Debounced Scrolling

*   **Problem:** 's' key toggle not working, inconsistent speech state feedback, rapid-fire speech on scrolling.
*   **Fixes Implemented:** Introduced `threading.Event` (`_is_speaking_flag`) in `Speaker` and polled SAPI `RunningState` to update it. `UI` refactored to use `speaker.is_speaking()`. Implemented debounced speech for message list scrolling using `stdscr.nodelay(True)` and time-based checks. Added visual speech status to `draw_message` status bar.
*   **Outcome:** Initial message *now reads*. Debounced scrolling implemented (not yet confirmed if effective). Visual speech status implemented. However, start/stop with 's' *still did not work* and the visual indicator *remained "Speaking"*, suggesting `voice.Speak` might be blocking the worker thread or `_ACTION_STOP_SILENT` was ineffective.

### 8. `win32com.client` with Text Chunking (Current Approach)

*   **Problem:** `voice.Speak()` potentially blocking the worker thread for long texts, preventing interruption commands from being processed, despite `SVSFPurgeBeforeSpeak` flag.
*   **Fixes Implemented:** Modified `Speaker` to chunk large texts (approx. 200 chars) before queuing them. `say` method ensures `_ACTION_STOP_SILENT` is sent before new chunks.
*   **Outcome:** (Not yet tested by user, this is the current state after latest changes.) Aiming to resolve all remaining interruption and responsiveness issues.

## Current State and Lingering Issues

The application is now **Windows-only**. Text-to-speech relies on the native SAPI5 interface (`win32com.client`) via a robust `Speaker` class with:
*   A single dedicated worker thread for COM threading safety.
*   An action-based queueing system.
*   Text chunking for improved responsiveness.
*   `is_speaking()` state tracking based on SAPI's `RunningState`.

**Lingering Speech Interruption Issues (as per latest user feedback):**
*   **Start/stop (`s` key) in message view is not working reliably:** Initial press of 's' starts reading, but subsequent presses do not stop. The visual indicator stays "Speaking".
*   **Scrolling in the message list does not stop reading the previous message's details.**
*   **Opening a message from the list does not stop reading the previous message's details.**
*   **Progress reporting during email loading is not working** (i.e., audible progress updates are not heard).

**Debugging Hypothesis:** The primary suspect for the above lingering issues is that the `voice.Speak()` method might still be blocking the worker thread for some duration, despite text chunking and the `SVSFPurgeBeforeSpeak` flag. This would prevent the worker from quickly processing subsequent `_ACTION_STOP_SILENT` commands from the queue.

## Known Architectural/Code Issues

*   Date formatting logic may be duplicated in `ui.py` and `Message.py`.
*   No formal testing framework is configured.
*   No linting configuration is in place.
