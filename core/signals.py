from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import BirthRegistration, UserProfile
from .utils import send_status_sms


# -------------------------------------------------------------------
# Auto-create UserProfile for every new User
# New users always get role=USER and is_staff=False
# (Admin is created only via `python manage.py create_admin`)
# -------------------------------------------------------------------
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if not created:
        return
    # Determine role based on is_staff (admin command sets is_staff=True first)
    role = UserProfile.Role.ADMIN if instance.is_staff else UserProfile.Role.USER
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    if profile.role != role:
        profile.role = role
        profile.save(update_fields=['role'])

    # Safety net: if this is NOT a staff user, make absolutely sure is_staff stays False
    if not instance.is_staff:
        # No need to re-save — create_user already sets is_staff=False
        pass


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