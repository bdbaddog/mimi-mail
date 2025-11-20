import curses
import pyttsx3
import textwrap
import threading
from gmail_interface import replace_urls

class UI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.cursor_x = 0
        self.cursor_y = 0
        self.list_scroll = 0
        self.engine = pyttsx3.init()
        self.speech_rate = 130
        self.engine.setProperty('rate', self.speech_rate)
        self.speaking = False
        self.show_urls = False
        self.speak_on_scroll = True

        # Simple stop flag
        self._stop_flag = False

        # For pause/resume in message body
        self._message_words = []
        self._message_word_index = 0
        self._message_speaking = False  # Separate flag for message speech

        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def _stop_speech(self):
        """Request speech to stop."""
        self._stop_flag = True
        self.speaking = False
        try:
            self.engine.stop()
        except:
            pass

    def _start_speech_simple(self, text):
        """Start speech in a new thread with simple stop mechanism."""
        self._stop_flag = False
        self.speaking = True

        thread = threading.Thread(target=self._speak_simple, args=(text,))
        thread.daemon = True
        thread.start()

    def _speak_simple(self, text):
        """Simple speech function - speaks entire text (for list speech only)."""
        if self._stop_flag:
            return

        self.engine.say(text)
        self.engine.runAndWait()
        # Don't set self.speaking = False here - let the caller handle it

    def _start_message_speech(self, text):
        """Start message body speech with pause/resume support."""
        self._stop_flag = False
        self._message_speaking = True

        # Check if resuming same text
        words = text.split()
        if words == self._message_words and self._message_word_index > 0:
            # Resume from where we left off
            start_index = self._message_word_index
        else:
            # Start fresh
            self._message_words = words
            self._message_word_index = 0
            start_index = 0

        thread = threading.Thread(target=self._speak_message, args=(start_index,))
        thread.daemon = True
        thread.start()

    def _speak_message(self, start_index):
        """Speak message body with chunking for pause/resume."""
        chunk_size = 20

        self._message_word_index = start_index

        while self._message_word_index < len(self._message_words):
            if self._stop_flag:
                break

            end_index = min(self._message_word_index + chunk_size, len(self._message_words))
            chunk = ' '.join(self._message_words[self._message_word_index:end_index])

            self.engine.say(chunk)
            self.engine.runAndWait()

            if self._stop_flag:
                break

            self._message_word_index = end_index

        # Reset if finished completely
        if not self._stop_flag:
            self._message_word_index = 0
            self._message_words = []

        self._message_speaking = False

    def draw_menu(self, messages):
        k = 0
        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()

        # Loop where k is the last character pressed
        while (k != ord('q')):

            # Initialization
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            max_messages = height - 4

            if k == 0 and self.speak_on_scroll and len(messages) > 0:
                self._start_speech_simple(messages[self.cursor_y].get_speech_summary())

            # Declaration of strings
            title = "MimiMail - Mutt Edition"[:width-1]
            statusbarstr = f"Press 'q' to exit | 't' to toggle speak on scroll ({'On' if self.speak_on_scroll else 'Off'})"

            # Centering calculations
            start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)

            # Render status bar
            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(height-1, 0, statusbarstr)
            self.stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            self.stdscr.attroff(curses.color_pair(3))

            # Turning on attributes for title
            self.stdscr.attron(curses.color_pair(1))
            self.stdscr.attron(curses.A_BOLD)

            # Rendering title
            self.stdscr.addstr(0, start_x_title, title)

            # Turning off attributes for title
            self.stdscr.attroff(curses.color_pair(1))
            self.stdscr.attroff(curses.A_BOLD)

            # Display messages
            for i in range(self.list_scroll, self.list_scroll + max_messages):
                if i < len(messages):
                    message = messages[i]
                    display_string = str(message)[:width-1]
                    if i == self.cursor_y:
                        self.stdscr.attron(curses.color_pair(3))
                    self.stdscr.addstr(i - self.list_scroll + 2, 0, display_string)
                    if i == self.cursor_y:
                        self.stdscr.attroff(curses.color_pair(3))

            # Refresh the screen
            self.stdscr.refresh()

            # Wait for next input
            k = self.stdscr.getch()

            if k == curses.KEY_DOWN:
                self.cursor_y = self.cursor_y + 1
                if self.speak_on_scroll:
                    self._stop_speech()
                    self._start_speech_simple(messages[self.cursor_y].get_speech_summary())
            elif k == curses.KEY_UP:
                self.cursor_y = self.cursor_y - 1
                if self.speak_on_scroll:
                    self._stop_speech()
                    self._start_speech_simple(messages[self.cursor_y].get_speech_summary())

            self.cursor_y = max(0, self.cursor_y)
            self.cursor_y = min(len(messages) -1, self.cursor_y)

            if self.cursor_y < self.list_scroll:
                self.list_scroll = self.cursor_y
            if self.cursor_y >= self.list_scroll + max_messages:
                self.list_scroll = self.cursor_y - max_messages + 1
            
            if k == 10 or k == curses.KEY_ENTER:
                if len(messages) > 0:
                    self._stop_speech()
                    self.draw_message(messages[self.cursor_y])
            elif k == ord('t'):
                self.speak_on_scroll = not self.speak_on_scroll

    def draw_message(self, message):
        k = 0
        scroll_y = 0
        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        self.stdscr.timeout(100)

        # Reset message speech state for new message
        self._message_words = []
        self._message_word_index = 0


        # Loop where k is the last character pressed
        while (k != ord('q')):
            # Initialization
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            # Declaration of strings
            title = f"Subject: {message.subject}"[:width-1]
            sender = f"From: {message.sender}"[:width-1]
            sent_date = f"Date: {message.get_date_full()}"[:width-1]

            statusbarstr = f"Press 'q' to return | 's' to speak/stop | 'u' to toggle URLs | +/- to change speed (current: {self.speech_rate})"[:width-1]

            # Render status bar
            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(height-1, 0, statusbarstr)
            self.stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            self.stdscr.attroff(curses.color_pair(3))

            # Turning on attributes for title
            self.stdscr.attron(curses.color_pair(1))
            self.stdscr.attron(curses.A_BOLD)

            # Rendering title
            self.stdscr.addstr(0, 0, title)
            self.stdscr.addstr(1, 0, sender)
            self.stdscr.addstr(2, 0, sent_date)


            # Turning off attributes for title
            self.stdscr.attroff(curses.color_pair(1))
            self.stdscr.attroff(curses.A_BOLD)
            
            # TODO: handle mimetypes other than text/plain
            body_text = message.get_body_text()
            if not self.show_urls:
                body_text = replace_urls(body_text, "[URL]")

            
            # Display message body
            lines = body_text.split('\n')
            wrapped_lines = []
            for line in lines:
                wrapped_lines.extend(textwrap.wrap(line, width))

            for i, line in enumerate(wrapped_lines):
                if i >= scroll_y:
                    if i + 4 - scroll_y < height -1:
                        self.stdscr.addstr(i + 4 - scroll_y, 0, line)


            # Refresh the screen
            self.stdscr.refresh()

            k = self.stdscr.getch()

            if k == curses.KEY_DOWN:
                scroll_y += 1
            elif k == curses.KEY_UP:
                scroll_y -= 1
            elif k == ord('s'):
                if not self._message_speaking:
                    text_to_speak = message.get_body_text()
                    if not self.show_urls:
                        text_to_speak = replace_urls(text_to_speak, "")

                    self._start_message_speech(text_to_speak)
                else:
                    self._stop_speech()
                    self._message_speaking = False

            elif k == ord('+'):
                self.speech_rate += 10
                self.engine.setProperty('rate', self.speech_rate)
            elif k == ord('-'):
                self.speech_rate -= 10
                self.engine.setProperty('rate', self.speech_rate)
            elif k == ord('u'):
                self.show_urls = not self.show_urls

            
            scroll_y = max(0, scroll_y)

        self.stdscr.timeout(-1)
        if self._message_speaking:
            self._stop_speech()
            self._message_speaking = False
