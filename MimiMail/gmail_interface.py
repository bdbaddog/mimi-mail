"""
From:
https://developers.google.com/gmail/api/quickstart/python

"""
import base64
import codecs
import re
import time
import threading
import curses # New import

from bs4 import BeautifulSoup

from Message import Message


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

URL_PATTERN = r'[A-Za-z0-9]+://[A-Za-z0-9%-_]+(/[A-Za-z0-9%-_])*(#|\\?)[A-Za-z0-9%-_&=]*'

headers = ['Subject', 'From', 'Date', 'body',
           'parts']


# from: https://github.com/jmgomezsoriano/mysmallutils
def replace_urls(text: str, replace: str, end_with: str = '') -> str:
    """ Replace all the URLs with path by a text.
    :param text: The text to replace.
    :param replace: The text to replace with.
    :param end_with: A regular expression which the URL has to finish with.
         By default, replace all the URLs.
    :return: The replaced text.
    """
    matches = list(re.finditer(URL_PATTERN + end_with, text))
    matches.reverse()
    for match in matches:
        start, end = match.span()[0], match.span()[1]
        text = text[:start] + replace + text[end:]
    return text


def _find_body_parts(payload):
    """Recursively search for text/plain and text/html body parts in the email payload."""
    plain_text_body = None
    html_body = None

    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')

            if mime_type == 'text/plain':
                plain_text_body = part['body']
            elif mime_type == 'text/html':
                html_body = part['body']
            elif mime_type.startswith('multipart/'):
                # Recursively search nested multipart structures
                nested_plain, nested_html = _find_body_parts(part)
                if nested_plain and not plain_text_body:
                    plain_text_body = nested_plain
                if nested_html and not html_body:
                    html_body = nested_html
    else:
        # No parts, check the payload directly
        mime_type = payload.get('mimeType', '')
        if mime_type == 'text/plain':
            plain_text_body = payload.get('body')
        elif mime_type == 'text/html':
            html_body = payload.get('body')

    return plain_text_body, html_body

def getUnreadEmails(service, speaker, stdscr): # stdscr added to signature
    messages = []
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    api_messages = results.get('messages')
    
    # Display initial loading message
    if stdscr:
        stdscr.clear()
        stdscr.addstr(0, 0, "Fetching emails, please wait...")
        stdscr.refresh()

    if not api_messages:
        return messages

    total_messages = len(api_messages)
    start_time = time.time()
    last_update_time = start_time

    for i, r in enumerate(api_messages):
        message = service.users().messages().get(userId='me', id=r['id']).execute()
        payload = message.get('payload')
        headers = payload.get('headers')

        sender = None
        sent_date = None
        subject = None
        body = None
        for x in headers:
            name = x['name']
            value = x['value']
            if name == 'From':
                sender = value
            if name == 'Date':
                sent_date = value
            if name == 'Subject':
                subject = value

        plain_text_body, html_body = _find_body_parts(payload)

        body_data = None
        if plain_text_body and 'data' in plain_text_body:
            body_data = plain_text_body['data']
        elif html_body and 'data' in html_body:
            body_data = html_body['data']

        if body_data:
            data = body_data.replace('-', '+').replace('_', '/')
            decoded_data = base64.b64decode(data)
            if html_body and not plain_text_body:
                soup = BeautifulSoup(decoded_data, 'html.parser')
                body = {'data': soup.get_text()}
            else:
                body = {'data': decoded_data.decode('utf-8')}


        mess = Message(sender, sent_date, subject, body if body else {})
        messages.append(mess)
        
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        if elapsed_time > 3 and (current_time - last_update_time > 4):
            progress_text = f"Loaded {i + 1} of {total_messages} emails."
            if stdscr:
                stdscr.addstr(1, 0, progress_text + " " * (stdscr.getmaxyx()[1] - len(progress_text) -1)) # Clear rest of line
                stdscr.refresh()
            speaker.say(progress_text, interrupt=False)
            last_update_time = current_time

    return messages


def getEmail(service):
    results = service.users().messages().list(userId='me').execute()
    for r in results.get('messages'):
        leer = service.users().messages().get(userId='me', id=r['id']).execute()
        payload = leer.get("payload")
        header = payload.get("headers")
        for x in header:
            if x['name'] in headers:
                sub = x['value']
                print("%-20s :%s" % (x['name'], x['value']))
            else:
                # print("Header:%-10s : %s"%(x['name'],x['value']))
                pass
        # print(leer['snippet'])  #body

        parts = payload.get('parts')
        for p in parts:
            body = p['body']
            data = body['data']
            # print(data)
            # data = data.replace('-', '+')
            b64str = codecs.encode(data)
            body_text = base64.urlsafe_b64decode(b64str).decode('utf-8')
            print("%-4s [%-12s]: %s " % (p['partId'], p['mimeType'], body_text))
            if p['mimeType'] == 'text/plain':
                body_text = replace_urls(body_text, "LINK")
                # This will fail now as there is no global engine
                # engine.say(body_text)
                # engine.runAndWait()
        break
