"""
Management command to create or update the pre-registered admin user.

Usage:
    python manage.py create_admin
    python manage.py create_admin --username admin --email admin@woreda.gov.et --password secret123

The created user gets:
  - is_staff = True  (gives Django admin access)
  - is_superuser = True
  - UserProfile.role = ADMIN
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Create or update the pre-registered Woreda admin user'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin',    help='Admin username')
        parser.add_argument('--email',    default='admin@woreda.gov.et', help='Admin email')
        parser.add_argument('--password', default='Admin@12345', help='Admin password')
        parser.add_argument('--firstname', default='Woreda',  help='First name')
        parser.add_argument('--lastname',  default='Admin',   help='Last name')

    def handle(self, *args, **options):
        username  = options['username']
        email     = options['email']
        password  = options['password']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email':      email,
                'first_name': options['firstname'],
                'last_name':  options['lastname'],
                'is_staff':   True,
                'is_superuser': True,
            }
        )

        if not created:
            user.email      = email
            user.is_staff   = True
            user.is_superuser = True

        user.set_password(password)
        user.save()

        # Ensure profile exists with ADMIN role
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = UserProfile.Role.ADMIN
        profile.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f"{action} admin user: username='{username}' email='{email}' password='{password}'"
        ))
        self.stdout.write(self.style.WARNING(
            "⚠  Change the default password immediately in production!"
        ))
