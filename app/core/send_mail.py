
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from app.core.config import settings
import logging

# Configure API key
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key["api-key"] = settings.BREVO_API_KEY

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)


def send_mail(to_email: str, subject: str, html_content: str):
    try:
        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={
                "email": settings.ADMIN_EMAIL,
                "name": "Wholesale Stationery"
            },
            subject=subject,
            html_content=html_content,
        )

        api_instance.send_transac_email(email)
        logging.info(f"Brevo email sent to {to_email}")
        return True

    except ApiException as e:
        logging.exception("Brevo email failed")
        return False
