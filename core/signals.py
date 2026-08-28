from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import BirthRegistration
from .utils import send_status_sms


@receiver(pre_save, sender=BirthRegistration)
def track_previous_status(sender, instance, **kwargs):
    """Remembers the status before saving changes."""
    if instance.pk:
        try:
            old_record = BirthRegistration.objects.get(pk=instance.pk)
            instance._previous_status = old_record.status
        except BirthRegistration.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=BirthRegistration)
def notify_applicant_on_status_change(sender, instance, created, **kwargs):
    """Triggers SMS whenever the status changes."""
    # Do not send SMS on initial creation or if status hasn't changed
    if created or getattr(instance, '_previous_status', None) == instance.status:
        return

    phone = instance.applicant_phone
    if not phone:
        return

    # Message for APPROVED status
    if instance.status == BirthRegistration.Status.APPROVED:
        msg = (
            f"CRRSA Alert: The birth registration for {instance.child_full_name_english} "
            f"({instance.formatted_id}) has been APPROVED.\n"
            f"የ{instance.child_full_name_amharic} የልደት መዝገብ (ID: {instance.formatted_id}) ፅድቋል::"
        )
        send_status_sms(phone, msg)

    # Message for REJECTED status
    elif instance.status == BirthRegistration.Status.REJECTED:
        reason = instance.rejection_reason or "Document discrepancy."
        msg = (
            f"CRRSA Alert: Birth registration ({instance.formatted_id}) was REJECTED.\n"
            f"Reason: {reason}\n"
            f"የልደት መዝገብ ማመልከቻዎ አልጸደቀም:: ምክንያት: {reason}"
        )
        send_status_sms(phone, msg)