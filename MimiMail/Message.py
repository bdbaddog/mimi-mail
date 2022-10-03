from dataclasses import dataclass
from email.utils import parsedate_tz, mktime_tz
from time import localtime, asctime

@dataclass
class Message:
    sender: str
    sent_date: str
    subject: str
    body: dict

    def __post_init__(self):
        self.sent_date = localtime(mktime_tz(parsedate_tz(self.sent_date)))

    def __repr__(self):
        mytime = asctime(self.sent_date)
        return f'Date:{mytime}  From:{self.sender}  Subject:{self.subject}'
