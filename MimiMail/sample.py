"""
From:
https://developers.google.com/gmail/api/quickstart/python

"""
import os.path
import base64
import codecs
import re

import pyttsx3

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from Message import Message

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

engine = pyttsx3.init()
# This is the speaking rate defaults to 200 words per minute
engine.setProperty('rate', 130)

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


def getUnreadEmails(service):
    messages = []
    results = service.users().messages().list(userId='me', labelIds=['UNREAD', 'INBOX']).execute()
    for r in results.get('messages'):
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
        body = payload.get('body')

        mess = Message(sender, sent_date, subject, body)


        messages.append(mess)

    for m in messages:
        print(f"From:{m.sender} Date:{m.sent_date} Subject:{m.subject}")

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
                engine.say(body_text)
                engine.runAndWait()
        break


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        # results = service.users().labels().list(userId='me').execute()
        # labels = results.get('labels', [])
        #
        # if not labels:
        #     print('No labels found.')
        #     return
        # print('Labels:')
        # for label in labels:
        #     print(label['name'])
        #     engine.say(label['name'])
        # engine.runAndWait()

        # getEmail(service)
        unread_messages = getUnreadEmails(service)
        for m in unread_messages:
            print(m)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
