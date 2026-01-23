from email.message import EmailMessage
import aiosmtplib
import logging
from app.core.config import settings


async def send_email_async(to_email: str, subject: str, html_content: str):
    msg = EmailMessage()
    msg["From"] = settings.ADMIN_EMAIL  # VERIFIED BREVO SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(html_content, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=int(settings.SMTP_PORT),
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            timeout=30,
        )
        logging.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logging.exception(f"Email failed for {to_email}")
        return False
