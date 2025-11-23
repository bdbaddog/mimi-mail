import curses
import textwrap
from gmail_interface import replace_urls

class UI:
    def __init__(self, stdscr, speaker):
        self.stdscr = stdscr
        self.speaker = speaker
        self.cursor_y = 0
        self.list_scroll = 0
        self.speech_rate = 130
        self.show_urls = False
        self.speak_on_scroll = True
        
        # We still need a flag to toggle speech for the 's' key in the message view
        self._is_speaking_body = False

        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def draw_menu(self, messages):
        k = 0
        self.stdscr.clear()
        self.stdscr.refresh()

        # Speak the first message before starting the loop
        if self.speak_on_scroll and messages:
            self.speaker.say(messages[self.cursor_y].get_speech_summary(), interrupt=True)

        while (k != ord('q')):
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()
            
            max_messages = height - 4

            title = "MimiMail - Mutt Edition"[:width-1]
            statusbarstr = f"Press 'q' to exit | 't' to toggle speak on scroll ({'On' if self.speak_on_scroll else 'Off'})"
            start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)

            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(height-1, 0, statusbarstr)
            self.stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            self.stdscr.attroff(curses.color_pair(3))

            self.stdscr.attron(curses.color_pair(1))
            self.stdscr.attron(curses.A_BOLD)
            self.stdscr.addstr(0, start_x_title, title)
            self.stdscr.attroff(curses.color_pair(1))
            self.stdscr.attroff(curses.A_BOLD)

            for i in range(self.list_scroll, self.list_scroll + max_messages):
                if i < len(messages):
                    message = messages[i]
                    display_string = str(message)[:width-1]
                    if i == self.cursor_y:
                        self.stdscr.attron(curses.color_pair(3))
                    self.stdscr.addstr(i - self.list_scroll + 2, 0, display_string)
                    if i == self.cursor_y:
                        self.stdscr.attroff(curses.color_pair(3))

            self.stdscr.refresh()
            k = self.stdscr.getch()

            if not messages:
                continue

            if k == curses.KEY_DOWN:
                self.cursor_y = min(len(messages) - 1, self.cursor_y + 1)
                if self.speak_on_scroll:
                    self.speaker.say(messages[self.cursor_y].get_speech_summary(), interrupt=True)
            elif k == curses.KEY_UP:
                self.cursor_y = max(0, self.cursor_y - 1)
                if self.speak_on_scroll:
                    self.speaker.say(messages[self.cursor_y].get_speech_summary(), interrupt=True)

            if self.cursor_y < self.list_scroll:
                self.list_scroll = self.cursor_y
            if self.cursor_y >= self.list_scroll + max_messages:
                self.list_scroll = self.cursor_y - max_messages + 1
            
            if k == 10 or k == curses.KEY_ENTER:
                self.speaker.stop()
                self.draw_message(messages[self.cursor_y])
                self.stdscr.clear()
                if self.speak_on_scroll:
                     self.speaker.say(messages[self.cursor_y].get_speech_summary(), interrupt=True)

            elif k == ord('t'):
                self.speak_on_scroll = not self.speak_on_scroll
        
        self.speaker.stop()

    def draw_message(self, message):
        k = 0
        scroll_y = 0
        self.stdscr.clear()
        self.stdscr.refresh()
        self.stdscr.timeout(100)
        self._is_speaking_body = False

        while (k != ord('q')):
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            title = f"Subject: {message.subject}"[:width-1]
            sender = f"From: {message.sender}"[:width-1]
            sent_date = f"Date: {message.get_date_full()}"[:width-1]

            statusbarstr = f"Press 'q' to return | 's' to speak/stop | 'u' to toggle URLs | +/- to change speed (current: {self.speech_rate})"[:width-1]

            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(height-1, 0, statusbarstr)
            self.stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            self.stdscr.attroff(curses.color_pair(3))

            self.stdscr.attron(curses.color_pair(1))
            self.stdscr.attron(curses.A_BOLD)
            self.stdscr.addstr(0, 0, title)
            self.stdscr.addstr(1, 0, sender)
            self.stdscr.addstr(2, 0, sent_date)
            self.stdscr.attroff(curses.color_pair(1))
            self.stdscr.attroff(curses.A_BOLD)
            
            body_text = message.get_body_text()
            if not self.show_urls:
                body_text = replace_urls(body_text, "[URL]")
            
            lines = body_text.split('\n')
            wrapped_lines = []
            for line in lines:
                wrapped_lines.extend(textwrap.wrap(line, width))

            for i, line in enumerate(wrapped_lines):
                if i >= scroll_y:
                    if i + 4 - scroll_y < height -1:
                        self.stdscr.addstr(i + 4 - scroll_y, 0, line)

            self.stdscr.refresh()
            k = self.stdscr.getch()

            if k == curses.KEY_DOWN:
                scroll_y += 1
            elif k == curses.KEY_UP:
                scroll_y -= 1
            elif k == ord('s'):
                if not self._is_speaking_body:
                    text_to_speak = message.get_body_text()
                    if not self.show_urls:
                        text_to_speak = replace_urls(text_to_speak, "")
                    self.speaker.say(text_to_speak, interrupt=True)
                    self._is_speaking_body = True
                else:
                    self.speaker.stop()
                    self._is_speaking_body = False

            elif k == ord('+'):
                self.speech_rate = min(300, self.speech_rate + 10)
                self.speaker.set_rate(self.speech_rate)
            elif k == ord('-'):
                self.speech_rate = max(50, self.speech_rate - 10)
                self.speaker.set_rate(self.speech_rate)
            elif k == ord('u'):
                self.show_urls = not self.show_urls
            
            scroll_y = max(0, scroll_y)

        self.stdscr.timeout(-1)
        self.speaker.stop()
