import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings


def send_email(to_email: str, subject: str, html_content: str):
    msg = MIMEMultipart("alternative")

    
    msg["From"] = settings.ADMIN_EMAIL  
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, int(settings.SMTP_PORT), timeout=30) as server:
            server.set_debuglevel(1)  # shows logs in Render
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logging.info(f"Email sent to {to_email}")
        return True

    except Exception as e:
        logging.exception(f"Failed to send email to {to_email}")
        return False
