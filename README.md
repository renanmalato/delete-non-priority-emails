# Delete Non-Priority Emails

A Python script to automatically find and delete emails from non-priority senders in your Gmail inbox.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Environment File
Create a `.env` file in the project root with your Gmail credentials:

```
EMAIL=your-email@gmail.com
PASSWORD=your-app-password
```

**Important**: You must use an App Password, not your regular Gmail password:
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate an App Password for this script
4. Use the App Password in the .env file

### 3. Configure Non-Priority Senders
Edit `non_priority_senders.json` to add/remove email addresses you want to automatically delete:

```json
{
  "senders": [
    "jobalerts-noreply@linkedin.com",
    "noreply@medium.com",
    "newsletter@example.com"
  ]
}
```

## Usage

Run the script:
```bash
python3 delete_non_priority_emails.py
```

The script will:
1. Connect to your Gmail inbox
2. Search for emails from the specified senders
3. Display a summary of found emails (grouped by sender)
4. Ask for confirmation before deletion
5. Delete the emails if confirmed

## Cost Information

This script is **completely free** to use with Gmail:
- Uses Gmail's IMAP protocol (no API costs)
- No quotas or limits for personal use
- Processing 100 emails per day is well within normal usage

## Features

- ✅ Secure connection using IMAP over SSL
- ✅ Displays email subjects before deletion
- ✅ Groups emails by sender for easy review
- ✅ Confirmation prompt before deletion
- ✅ Progress updates during deletion
- ✅ Error handling and recovery
- ✅ Proper email encoding support

## Security

- Credentials stored in `.env` file (git-ignored)
- Uses App Passwords (more secure than regular passwords)
- No data sent to external services
- Connects directly to Gmail IMAP servers 