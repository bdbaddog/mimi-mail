import time
from dataclasses import dataclass
from email.utils import parsedate_tz, mktime_tz
from datetime import datetime, timedelta

@dataclass
class Message:
    sender: str
    sent_date: str
    subject: str
    body: dict

    def __post_init__(self):
        self.sent_date = time.localtime(mktime_tz(parsedate_tz(self.sent_date)))

    def get_sender_name(self):
        """Extract just the sender's name from the full sender string."""
        if '<' in self.sender:
            return self.sender.split('<')[0].strip(' "')
        return self.sender

    def get_date_for_display(self):
        """Get a short date string for display in message list (e.g., 'Today', 'Mon', 'Jan 15')."""
        now = datetime.now()
        message_date = datetime.fromtimestamp(time.mktime(self.sent_date))

        if message_date.date() == now.date():
            return "Today"
        elif now.year == message_date.year:
            if now.isocalendar()[1] == message_date.isocalendar()[1] and now.weekday() >= message_date.weekday():
                return time.strftime("%a", self.sent_date)
            else:
                return time.strftime("%b %d", self.sent_date)
        else:
            return time.strftime("%b %d, %Y", self.sent_date)

    def get_date_for_speech(self):
        """Get a full date string suitable for text-to-speech (e.g., 'Today', 'Monday', 'January 15')."""
        now = datetime.now()
        message_date = datetime.fromtimestamp(time.mktime(self.sent_date))

        if message_date.date() == now.date():
            return "Today"
        elif now.year == message_date.year:
            if now.isocalendar()[1] == message_date.isocalendar()[1] and now.weekday() >= message_date.weekday():
                return time.strftime("%A", self.sent_date)  # Full weekday name
            else:
                return time.strftime("%B %d", self.sent_date)  # Full month name
        else:
            return time.strftime("%B %d, %Y", self.sent_date)

    def get_date_full(self):
        """Get full date and time for message detail view."""
        return time.strftime('%B %d, %Y %I:%M %p', self.sent_date)

    def get_speech_summary(self):
        """Get the text to speak when this message is selected in the list."""
        date_spoken = self.get_date_for_speech()
        if date_spoken == "Today":
            date_phrase = "received today"
        else:
            date_phrase = f"received on {date_spoken}"
        return f"From: {self.get_sender_name()}, Subject: {self.subject}. Message {date_phrase}"

    def get_body_text(self):
        """Get the body text of the message."""
        return self.body.get('data', '')

    def __repr__(self):
        return f'{self.get_date_for_display():<10} From:{self.sender:<25} Subject:{self.subject}'
