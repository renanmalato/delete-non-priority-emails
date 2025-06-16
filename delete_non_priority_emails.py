#!/usr/bin/env python3

# ------------------------------------------------- #
#                                                   #
#                                                   #
#    Delete Non-Priority Emails Script             #
#                                                   #
#                                                   #
# ------------------------------------------------- #

import imaplib
import email
import json
import os
from dotenv import load_dotenv
from email.header import decode_header

# ------------------------------- #
#  Load Environment Variables     #
# ------------------------------- #

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

if not EMAIL or not PASSWORD:
    print("❌ Error: EMAIL and PASSWORD must be set in .env file")
    exit(1)

# ------------------------------------------------- #
#                                                   #
#                                                   #
#    Helper Functions                               #
#                                                   #
#                                                   #
# ------------------------------------------------- #

# ------------------------------- #
#  Load Non-Priority Senders      #
# ------------------------------- #

def load_non_priority_senders():
    """Load the list of non-priority senders from JSON file"""
    try:
        with open('non_priority_senders.json', 'r') as f:
            data = json.load(f)
            return data['senders']
    except FileNotFoundError:
        print("❌ Error: non_priority_senders.json file not found")
        exit(1)
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in non_priority_senders.json")
        exit(1)

# ------------------------------- #
#  Decode Email Subject           #
# ------------------------------- #

def decode_subject(subject):
    """Decode email subject handling various encodings"""
    if subject is None:
        return "No Subject"
    
    try:
        decoded_parts = decode_header(subject)
        decoded_subject = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_subject += part.decode(encoding)
                else:
                    decoded_subject += part.decode('utf-8', errors='ignore')
            else:
                decoded_subject += str(part)
        
        return decoded_subject
    except Exception as e:
        return str(subject)

# ------------------------------- #
#  Connect to Gmail               #
# ------------------------------- #

def connect_to_gmail():
    """Connect to Gmail using IMAP"""
    try:
        print("🔄 Connecting to Gmail...")
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(EMAIL, PASSWORD)
        imap.select("inbox")
        print("✅ Connected to Gmail successfully")
        return imap
    except imaplib.IMAP4.error as e:
        print(f"❌ Gmail connection error: {e}")
        print("💡 Make sure you're using an App Password, not your regular password")
        print("💡 Enable 2-factor authentication and create an App Password at: https://myaccount.google.com/apppasswords")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)

# ------------------------------------------------- #
#                                                   #
#                                                   #
#    Main Email Processing                          #
#                                                   #
#                                                   #
# ------------------------------------------------- #

# ------------------------------- #
#  Find Emails from Senders       #
# ------------------------------- #

def find_emails_from_senders(imap, senders):
    """Find all emails from the specified senders"""
    emails_to_delete = []
    
    print(f"🔍 Searching for emails from {len(senders)} non-priority senders...")
    
    for sender in senders:
        print(f"   📧 Searching emails from: {sender}")
        
        try:
            # Search for emails from this sender
            search_criteria = f'FROM "{sender}"'
            status, messages = imap.search(None, search_criteria)
            
            if status == 'OK':
                message_ids = messages[0].split()
                
                for msg_id in message_ids:
                    try:
                        # Fetch the email
                        status, msg_data = imap.fetch(msg_id, '(RFC822)')
                        
                        if status == 'OK':
                            email_body = msg_data[0][1]
                            email_message = email.message_from_bytes(email_body)
                            
                            subject = decode_subject(email_message["Subject"])
                            date = email_message["Date"]
                            from_addr = email_message["From"]
                            
                            emails_to_delete.append({
                                'id': msg_id.decode(),
                                'subject': subject,
                                'from': from_addr,
                                'date': date,
                                'sender': sender
                            })
                    
                    except Exception as e:
                        print(f"   ⚠️  Error processing message {msg_id}: {e}")
                        continue
                        
                print(f"   📊 Found {len([e for e in emails_to_delete if e['sender'] == sender])} emails from {sender}")
        
        except Exception as e:
            print(f"   ❌ Error searching for {sender}: {e}")
            continue
    
    return emails_to_delete

# ------------------------------- #
#  Display Email Summary          #
# ------------------------------- #

def display_email_summary(emails):
    """Display summary of emails found"""
    if not emails:
        print("✅ No emails found from non-priority senders!")
        return False
    
    print(f"\n📋 Found {len(emails)} emails from non-priority senders:")
    print("=" * 80)
    
    # Group by sender
    by_sender = {}
    for email_info in emails:
        sender = email_info['sender']
        if sender not in by_sender:
            by_sender[sender] = []
        by_sender[sender].append(email_info)
    
    for sender, sender_emails in by_sender.items():
        print(f"\n📧 {sender} ({len(sender_emails)} emails):")
        print("-" * 60)
        
        for i, email_info in enumerate(sender_emails[:5], 1):  # Show max 5 per sender
            subject = email_info['subject'][:60] + "..." if len(email_info['subject']) > 60 else email_info['subject']
            print(f"   {i}. {subject}")
        
        if len(sender_emails) > 5:
            print(f"   ... and {len(sender_emails) - 5} more emails")
    
    print("=" * 80)
    return True

# ------------------------------- #
#  Delete Emails                  #
# ------------------------------- #

def delete_emails(imap, emails):
    """Delete the specified emails"""
    print(f"\n🗑️  Deleting {len(emails)} emails...")
    
    deleted_count = 0
    failed_count = 0
    
    for email_info in emails:
        try:
            # Mark email as deleted
            imap.store(email_info['id'], '+FLAGS', '\\Deleted')
            deleted_count += 1
            
            if deleted_count % 10 == 0:  # Progress update every 10 deletions
                print(f"   📊 Deleted {deleted_count}/{len(emails)} emails...")
                
        except Exception as e:
            print(f"   ❌ Failed to delete email '{email_info['subject'][:30]}...': {e}")
            failed_count += 1
    
    # Expunge to permanently delete
    try:
        imap.expunge()
        print(f"✅ Successfully deleted {deleted_count} emails")
        if failed_count > 0:
            print(f"⚠️  Failed to delete {failed_count} emails")
    except Exception as e:
        print(f"❌ Error expunging deleted emails: {e}")

# ------------------------------------------------- #
#                                                   #
#                                                   #
#    Main Function                                  #
#                                                   #
#                                                   #
# ------------------------------------------------- #

def main():
    """Main function to orchestrate the email deletion process"""
    print("🚀 Starting Non-Priority Email Deletion Script")
    print("=" * 50)
    
    # Load non-priority senders
    senders = load_non_priority_senders()
    print(f"📝 Loaded {len(senders)} non-priority senders from JSON")
    
    # Connect to Gmail
    imap = connect_to_gmail()
    
    try:
        # Find emails from non-priority senders
        emails_to_delete = find_emails_from_senders(imap, senders)
        
        # Display summary
        if not display_email_summary(emails_to_delete):
            return
        
        # Ask for confirmation
        print(f"\n❓ Do you want to delete these {len(emails_to_delete)} emails? (y/N): ", end="")
        confirmation = input().strip().lower()
        
        if confirmation in ['y', 'yes']:
            delete_emails(imap, emails_to_delete)
            print("\n🎉 Email deletion completed!")
        else:
            print("\n❌ Email deletion cancelled by user")
    
    finally:
        # Close connection
        try:
            imap.close()
            imap.logout()
            print("🔌 Disconnected from Gmail")
        except:
            pass

if __name__ == "__main__":
    main() 