import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    _TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    _TWILIO_AVAILABLE = False


def send_status_sms(phone_number, message_body):
    """Sends an SMS to the applicant's phone number via Twilio (if installed)."""
    if not phone_number or not _TWILIO_AVAILABLE:
        return False

    clean_phone = phone_number.strip().replace(" ", "")
    if clean_phone.startswith("0"):
        clean_phone = "+251" + clean_phone[1:]
    elif not clean_phone.startswith("+"):
        clean_phone = "+" + clean_phone

    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=clean_phone
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False
