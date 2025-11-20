import curses
import pyttsx3
import textwrap
import threading
import time
from sample import replace_urls

class UI:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.cursor_x = 0
        self.cursor_y = 0
        self.list_scroll = 0
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 130)
        self.speaking = False
        self.show_urls = False
        self.speak_on_scroll = True

        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

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
                sender_text = messages[self.cursor_y].sender
                if '<' in sender_text:
                    sender_name = sender_text.split('<')[0].strip(' "')
                else:
                    sender_name = sender_text
                thread = threading.Thread(target=self._speak_in_thread, args=(f"From: {sender_name}, Subject: {messages[self.cursor_y].subject}",))
                thread.daemon = True
                thread.start()

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
                    self.engine.stop()
                    sender_text = messages[self.cursor_y].sender
                    if '<' in sender_text:
                        sender_name = sender_text.split('<')[0].strip(' "')
                    else:
                        sender_name = sender_text
                    thread = threading.Thread(target=self._speak_in_thread, args=(f"From: {sender_name}, Subject: {messages[self.cursor_y].subject}",))
                    thread.daemon = True
                    thread.start()
            elif k == curses.KEY_UP:
                self.cursor_y = self.cursor_y - 1
                if self.speak_on_scroll:
                    self.engine.stop()
                    sender_text = messages[self.cursor_y].sender
                    if '<' in sender_text:
                        sender_name = sender_text.split('<')[0].strip(' "')
                    else:
                        sender_name = sender_text
                    thread = threading.Thread(target=self._speak_in_thread, args=(f"From: {sender_name}, Subject: {messages[self.cursor_y].subject}",))
                    thread.daemon = True
                    thread.start()

            self.cursor_y = max(0, self.cursor_y)
            self.cursor_y = min(len(messages) -1, self.cursor_y)

            if self.cursor_y < self.list_scroll:
                self.list_scroll = self.cursor_y
            if self.cursor_y >= self.list_scroll + max_messages:
                self.list_scroll = self.cursor_y - max_messages + 1
            
            if k == 10 or k == curses.KEY_ENTER:
                if len(messages) > 0:
                    self.draw_message(messages[self.cursor_y])
            elif k == ord('t'):
                self.speak_on_scroll = not self.speak_on_scroll


    def _speak_in_thread(self, text):
        self.engine.say(text)
        self.engine.runAndWait()
        self.speaking = False
            
    def draw_message(self, message):
        k = 0
        scroll_y = 0
        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        self.stdscr.timeout(100)


        # Loop where k is the last character pressed
        while (k != ord('q')):
            # Initialization
            self.stdscr.clear()
            height, width = self.stdscr.getmaxyx()

            # Declaration of strings
            title = f"Subject: {message.subject}"[:width-1]
            sender = f"From: {message.sender}"[:width-1]
            sent_date = f"Date: {time.strftime('%B %d, %Y %I:%M %p', message.sent_date)}"[:width-1]
            rate = self.engine.getProperty('rate')

            statusbarstr = f"Press 'q' to return | 's' to speak/stop | 'u' to toggle URLs | +/- to change speed (current: {rate})"

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
            body_text = message.body.get('data', '')
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
                if not self.speaking:
                    self.speaking = True
                    text_to_speak = message.body.get('data', '')
                    if not self.show_urls:
                        text_to_speak = replace_urls(text_to_speak, "")
                    thread = threading.Thread(target=self._speak_in_thread, args=(text_to_speak,))
                    thread.daemon = True
                    thread.start()
                else:
                    self.speaking = False
                    self.engine.stop()

            elif k == ord('+'):
                rate = self.engine.getProperty('rate')
                self.engine.setProperty('rate', rate + 10)
            elif k == ord('-'):
                rate = self.engine.getProperty('rate')
                self.engine.setProperty('rate', rate - 10)
            elif k == ord('u'):
                self.show_urls = not self.show_urls

            
            scroll_y = max(0, scroll_y)

        self.stdscr.timeout(-1)
        self.speaking = False
        self.engine.stop()
