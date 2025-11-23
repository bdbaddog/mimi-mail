import os
import json
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

CREDENTIALS_FILENAME = 'credentials.json'
TOKEN_FILENAME = 'token.json'

PLACEHOLDER_CREDENTIALS = {
    "installed": {
        "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
        "project_id": "YOUR_PROJECT_ID",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uris": [
            "http://localhost"
        ]
    }
}

def _create_placeholder_credentials():
    """Creates a placeholder credentials.json file and exits."""
    print(f"'{CREDENTIALS_FILENAME}' not found.")
    print(f"Creating a placeholder file at '{os.path.abspath(CREDENTIALS_FILENAME)}'.")
    print("Please open this file and replace the placeholder values with your actual Google Cloud credentials.")
    with open(CREDENTIALS_FILENAME, 'w') as f:
        json.dump(PLACEHOLDER_CREDENTIALS, f, indent=4)
    print("\nTo get your credentials, follow these steps:")
    print("1. Go to the Google Cloud Console: https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one.")
    print("3. Enable the Gmail API for your project.")
    print("4. Go to 'Credentials' and click 'Create Credentials' -> 'OAuth client ID'.")
    print("5. Choose 'Desktop app' as the application type.")
    print("6. After creation, download the JSON file.")
    print(f"7. Copy the contents of the downloaded file into '{CREDENTIALS_FILENAME}'.")
    print("\nAfter updating the credentials, please restart the application.")
    sys.exit(1)


def get_gmail_service():
    """
    Authenticates with the Gmail API and returns a service object.
    Handles token creation, refresh, and placeholder credentials file.
    """
    creds = None
    if os.path.exists(TOKEN_FILENAME):
        creds = Credentials.from_authorized_user_file(TOKEN_FILENAME, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                # If refresh fails, could be due to revoked token.
                # We'll proceed to re-authenticate.
                print(f"Could not refresh token: {e}")
                creds = None # Force re-authentication
        
        if not creds: # Either no token or refresh failed
            if not os.path.exists(CREDENTIALS_FILENAME):
                _create_placeholder_credentials()
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILENAME, SCOPES)
                creds = flow.run_local_server(port=0)
            except (ValueError, KeyError) as e:
                # Catches invalid JSON format or if 'installed' key is missing
                if 'invalid' in str(e).lower() or 'installed' in str(e):
                    print(f"Error: The '{CREDENTIALS_FILENAME}' file appears to contain invalid or placeholder values.")
                    print("Please follow the instructions to get your credentials and update the file.")
                    sys.exit(1)
                else:
                    raise e


        with open(TOKEN_FILENAME, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
