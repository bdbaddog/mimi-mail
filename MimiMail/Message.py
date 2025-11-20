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

    def __repr__(self):
        now = datetime.now()
        message_date = datetime.fromtimestamp(time.mktime(self.sent_date))

        if message_date.date() == now.date():
            date_str = "Today"
        elif now.year == message_date.year:
            if now.isocalendar()[1] == message_date.isocalendar()[1] and now.weekday() >= message_date.weekday(): # current week
                date_str = time.strftime("%a", self.sent_date)
            else: # current year, but not current week
                date_str = time.strftime("%b %d", self.sent_date)
        else: # not current year
            date_str = time.strftime("%b %d, %Y", self.sent_date)

        return f'{date_str:<10} From:{self.sender:<25} Subject:{self.subject}'
