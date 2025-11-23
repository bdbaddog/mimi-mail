import curses
from ui import UI
from gmail_interface import getUnreadEmails
from auth import get_gmail_service
from speaker import Speaker

def main(stdscr):
    # Initialize the speaker
    speaker = Speaker()
    speaker.say("Please wait while I load your email")

    service = get_gmail_service()
    
    if not service:
        speaker.shutdown()
        return

    unread_messages = getUnreadEmails(service, speaker)

    ui = UI(stdscr, speaker)
    ui.draw_menu(unread_messages)
    
    # Shutdown the speaker thread before exiting
    speaker.shutdown()

if __name__ == '__main__':
    curses.wrapper(main)
