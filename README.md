# Gmail 2FA Code Extractor (w/Google Voice)

This tool automatically extracts two-factor authentication (2FA) codes from your Gmail inbox and copies them to your clipboard. It's perfect for streamlining your authentication workflow when logging into various services.
It's designed for people that have Google Voice set up with their Gmail, such that they're getting Google Voice text messages in their email as well. 
It will work for verification codes sent to normal emails as well. 

## Features

- Automatically checks Gmail for new messages every minute
- Extracts 6-8 digit verification codes from emails
- Looks for emails that contain the words "code" or "share"
- Uses various regex patterns to find codes in different formats
- Copies found codes to clipboard automatically
- Only processes new codes to avoid duplicates
- Runs in the background on macOS

## Prerequisites

- Python 3.6+
- A Google account with Gmail
- macOS (for background service setup)

## Installation

1. Clone or download this repository

2. Install the required packages:
   ```
   pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 pyperclip
   ```

3. OAuth Credentials Setup:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project (or select an existing one)
   - Enable the Gmail API:
     - Navigate to "APIs & Services" → "Library"
     - Search for "Gmail API" and enable it
   - Create OAuth credentials:
     - Go to "APIs & Services" → "Credentials"
     - Click "Create Credentials" → "OAuth client ID"
     - If prompted, configure the consent screen (External type is fine)
     - For Application type, select "Desktop application"
     - Name your application (e.g., "Gmail 2FA Extractor")
     - Download the JSON file
   - Rename the downloaded file to `client_secret.json` and place it in the project directory

## Usage

1. Run the script once manually to complete the OAuth flow:
   ```
   python parse.py
   ```
   - A browser window will open asking you to sign in to your Google account
   - Grant the application permission to access your Gmail
   - After authorizing, the script will save a token file for future use

2. The script will start checking your Gmail account every minute
   - When a code is found, it will be copied to your clipboard
   - You'll see a message in the terminal: `Found code: 123456 (copied to clipboard)`

3. Press `Ctrl+C` to stop the script

## Setting Up Background Service on macOS

Create a launch agent to run the script in the background:

```bash
cat > ~/Library/LaunchAgents/com.yourusername.gmail2fa.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.yourusername.gmail2fa</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/your/python</string>
        <string>/full/path/to/parse.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yourusername/Library/Logs/gmail2fa.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/Library/Logs/gmail2fa.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF
```

Replace:
- `/path/to/your/python` with your Python interpreter path
- `/full/path/to/parse.py` with the full path to the script
- `yourusername` with your macOS username

Load the service:

```bash
launchctl load ~/Library/LaunchAgents/com.yourusername.gmail2fa.plist
```

## How It Works

1. The script authenticates with the Gmail API using OAuth 2.0
2. Every minute, it searches for emails from the last 5 minutes
3. It checks each email for the words "code" or "share"
4. If those words are found, it searches for 6-8 digit numbers using various regex patterns
5. When a code is found, it's copied to the clipboard using `pyperclip`

## Troubleshooting

- Check if the service is running:
  ```bash
  launchctl list | grep gmail2fa
  ```

- View logs:
  ```bash
  tail -f ~/Library/Logs/gmail2fa.log
  ```

- Restart the service:
  ```bash
  launchctl unload ~/Library/LaunchAgents/com.yourusername.gmail2fa.plist
  launchctl load ~/Library/LaunchAgents/com.yourusername.gmail2fa.plist
  ```

## Security Notes

- The script uses OAuth 2.0 for secure authentication with Gmail
- Your Gmail credentials are never stored in the script
- The token file contains sensitive information and should be kept secure
- The script only requests read-only access to your Gmail
- If you want to revoke access, visit your Google Account's security settings 