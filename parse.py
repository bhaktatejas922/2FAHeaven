#!/usr/bin/env python3
"""
Gmail 2FA Code Extractor

This script checks Gmail for new messages containing verification codes (6-8 digits)
and automatically copies them to the clipboard on macOS.

Requirements:
- pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 pyperclip
"""

import os
import re
import time
import base64
import pyperclip
from datetime import datetime, timedelta
import json

# Import OAuth libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# The Gmail API scope needed for read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
# Path to the OAuth client credentials file
def find_client_secret_file():
    """Find the first client_secret JSON file in the current directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(current_dir):
        if file.startswith('client_secret') and file.endswith('.json'):
            return os.path.join(current_dir, file)
    raise FileNotFoundError("No client_secret JSON file found in the directory")

CLIENT_SECRET_FILE = find_client_secret_file()
# Path to store the token after authentication
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
# The email address of the user whose mailbox we want to access
USER_EMAIL = 'me'  # This will be the authenticated user's email
CHECK_INTERVAL = 20  # seconds

def authenticate():
    """Authenticate with the Gmail API using OAuth."""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            # This will open a browser window for authentication
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def extract_verification_code(text):
    """Extract 6-8 digit verification code from text."""
    
    # Look for specific wording around codes
    code_contexts = [
        r"code(?:\s+is)?\s*:?\s*([0-9]{6,8})",
        r"verification(?:\s+code)?\s*:?\s*([0-9]{6,8})",
        r"([0-9]{6,8})(?:\s+is\s+your\s+(?:code|verification))",
        r"([0-9]{6,8})(?=\D|$)",  # Any 6-8 digit number followed by non-digit or end of string
        r"security code\s*:?\s*([0-9]{6,8})",
        r"one-time(?:\s+code)?\s*:?\s*([0-9]{6,8})"
    ]
    
    # Check if "code" or "share" is in the text
    if "code" in text.lower() or "share" in text.lower():
        for pattern in code_contexts:
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                return matches.group(1)
    
    return None

def decode_message(message):
    """Decode the message payload."""
    if 'parts' in message['payload']:
        # Multipart message
        text = ""
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        # Single part message
        if 'data' in message['payload']['body']:
            text = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        else:
            text = ""
    
    return text

def check_for_verification_codes(service):
    """Check recent emails for verification codes and return the latest one if found."""
    # Get emails from the last 5 minutes
    time_frame = (datetime.utcnow() - timedelta(minutes=5)).strftime('%Y/%m/%d')
    
    try:
        # Query for recent messages
        results = service.users().messages().list(
            userId=USER_EMAIL,
            q=f'after:{time_frame}'
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return None
        
        # Process messages in reverse order (newest first)
        for message in messages:
            msg = service.users().messages().get(userId=USER_EMAIL, id=message['id']).execute()
            text = decode_message(msg)
            
            # Try to extract verification code
            code = extract_verification_code(text)
            if code:
                return code
        
        return None
    
    except Exception as e:
        print(f"Error checking for verification codes: {e}")
        return None

def main():
    """Main function to check Gmail and extract codes."""
    print("Starting Gmail 2FA Code Extractor...")
    print("This script will check your Gmail every minute for verification codes.")
    print("When a code is found, it will be automatically copied to your clipboard.")
    print("Press Ctrl+C to stop the script.")
    
    # Authenticate with the Gmail API using OAuth
    credentials = authenticate()
    service = build('gmail', 'v1', credentials=credentials)
    
    last_code = None
    
    try:
        while True:
            # Check for verification codes
            code = check_for_verification_codes(service)
            
            # If code is found and it's different from the last one, copy to clipboard
            if code and code != last_code:
                pyperclip.copy(code)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found code: {code} (copied to clipboard)")
                last_code = code
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No new verification codes found.")
            
            # Wait for the next check
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == '__main__':
    main()
