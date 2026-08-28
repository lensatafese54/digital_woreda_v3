import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_status_sms(phone_number, message_body):
    """Sends an SMS to the applicant's phone number."""
    if not phone_number:
        return False

    # Format phone number to international format (e.g., +251...)
    clean_phone = phone_number.strip().replace(" ", "")
    if clean_phone.startswith("0"):
        clean_phone = "+251" + clean_phone[1:]
    elif not clean_phone.startswith("+"):
        clean_phone = "+" + clean_phone

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=clean_phone
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False