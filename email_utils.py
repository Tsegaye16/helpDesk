import smtplib
import logging
from email.mime.text import MIMEText
from config import GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_support_email(user_email: str, user_concern: str, recipient_email: str = "abewatsegaye16@gmail.com") -> dict:
    """
    Sends an email to the support team with the user's concern.

    Args:
        user_email (str): The email address of the user.
        user_concern (str): The specific question or concern of the user.
        recipient_email (str): The support team's email address (default: abewatsegaye16@gmail.com).

    Returns:
        dict: Status of the email sending operation.
    """
    try:
        sender_email = GMAIL_SENDER_EMAIL
        app_password = GMAIL_APP_PASSWORD

        # Create email
        subject = f"Support Request from {user_email}"
        body = f"User Email: {user_email}\n\nConcern:\n{user_concern}"
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
        logger.error(f"Error sending email: {e}")
        return {"status": "error", "message": f"Failed to send email: {str(e)}"}