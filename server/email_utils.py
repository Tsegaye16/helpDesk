import smtplib
import logging
from email.mime.text import MIMEText
from typing import List, Dict
from config import GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD, EMAIL_RECIPIENT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_support_email(user_email: str, user_concern: str, recipient_email: str = EMAIL_RECIPIENT, chat_history: List[Dict[str, str]] = None) -> dict:
    """
    Sends an email to the support team with the user's concern and the last three conversations.

    Args:
        user_email (str): The email address of the user.
        user_concern (str): The specific question or concern of the user.
        recipient_email (str): The support team's email address (default: EMAIL_RECIPIENT).
        chat_history (List[Dict[str, str]]): List of recent conversation messages (user and assistant).

    Returns:
        dict: Status of the email sending operation.
    """
    try:
        sender_email = GMAIL_SENDER_EMAIL
        app_password = GMAIL_APP_PASSWORD

        # Create email body
        body = f"User Email: {user_email}\n\nConcern:\n{user_concern}\n\nRecent Conversation (Last 3 Exchanges):\n"
        
        if chat_history:
            # Take the last 6 messages (3 user + 3 assistant) if available
            recent_messages = chat_history[-10:-4]  # Last 6 to cover 3 user-assistant pairs
            for msg in recent_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                body += f"{role}: {msg['content']}\n"
        else:
            body += "No recent conversation available.\n"

        # Create email
        subject = f"Support Request from {user_email}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email

        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {recipient_email}")
        return {"status": "success", "message": "Email sent to support team."}

    except Exception as e:
        logger.error(f"Error sending email to {recipient_email}: {e}")
        return {"status": "error", "message": f"Failed to send email: {str(e)}"}