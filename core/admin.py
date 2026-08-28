from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from .models import BirthRegistration


@admin.register(BirthRegistration)
class BirthRegistrationAdmin(admin.ModelAdmin):
    # ------------------------------------------------------------------
    # 1. LIST VIEW CONFIGURATION
    # ------------------------------------------------------------------
    list_display = (
        'registration_id',
        'child_full_name_amharic',
        'child_full_name_english',
        'applicant_name_amharic',
        'applicant_relation',
        'status_badge',
        'created_at',
        'certificate_actions',
    )
    list_filter = ('status', 'subcity', 'created_at')
    search_fields = (
        'id',
        'child_full_name_amharic',
        'child_full_name_english',
        'applicant_name_amharic',
        'applicant_phone',
        'father_name_english',
        'mother_name_english',
    )
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')

    # ------------------------------------------------------------------
    # 2. DETAIL/EDIT VIEW FIELDSETS (ORGANIZED SECTIONS)
    # ------------------------------------------------------------------
    fieldsets = (
        ('📋 Application Overview', {
            'fields': ('status', 'rejection_reason', 'created_at', 'updated_at')
        }),
        ('👶 Child Information', {
            'fields': (
                ('child_full_name_amharic', 'child_full_name_english'),
                ('sex', 'birth_day', 'birth_month', 'birth_year_ec', 'birth_year_gc'),
                'child_photo',
            )
        }),
        ('👪 Parents Information', {
            'fields': (
                ('father_name_amharic', 'father_name_english'),
                'father_photo',
                ('mother_name_amharic', 'mother_name_english'),
                'mother_photo',
            )
        }),
        ('👤 Applicant Details', {
            'fields': (
                ('applicant_name_amharic', 'applicant_relation'),
                ('applicant_age', 'applicant_phone'),
            )
        }),
        ('🏛️ Location & Supporting Documents', {
            'fields': (
                ('subcity', 'woreda', 'hospital_org_name'),
                'hospital_document',
            )
        }),
    )

    # ------------------------------------------------------------------
    # 3. BULK ADMIN ACTIONS
    # ------------------------------------------------------------------
    actions = ['approve_registrations', 'reject_registrations']

    @admin.action(description='✅ Mark selected registrations as APPROVED')
    def approve_registrations(self, request, queryset):
        updated_count = queryset.update(status='APPROVED', rejection_reason='')
        self.message_user(
            request, 
            f'Successfully approved {updated_count} birth registration(s).', 
            messages.SUCCESS
        )

    @admin.action(description='❌ Mark selected registrations as REJECTED')
    def reject_registrations(self, request, queryset):
        updated_count = queryset.update(status='REJECTED')
        self.message_user(
            request, 
            f'{updated_count} registration(s) marked as REJECTED. Ensure reasons are updated.', 
            messages.WARNING
        )

    # ------------------------------------------------------------------
    # 4. CUSTOM DISPLAY COLUMNS
    # ------------------------------------------------------------------
    @admin.display(description='Registration ID', ordering='id')
    def registration_id(self, obj):
        return f"CRRSA-{obj.pk:05d}"

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'APPROVED': '#16a34a',  # Green
            'PENDING': '#d97706',   # Amber
            'REJECTED': '#dc2626',  # Red
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: #ffffff; padding: 3px 8px; '
            'border-radius: 12px; font-weight: 600; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
        )

    @admin.display(description='Actions')
    def certificate_actions(self, obj):
        if not obj or not obj.pk:
            return "-"

        print_url = reverse('print_certificate', args=[obj.pk])
        verify_url = reverse('verify_certificate', args=[obj.pk])

        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer" '
            'style="background-color: #1a365d; color: #ffffff; padding: 4px 8px; '
            'border-radius: 4px; text-decoration: none; font-weight: 600; font-size: 11px; margin-right: 4px;">'
            '🖨️ Print</a>'
            '<a href="{}" target="_blank" rel="noopener noreferrer" '
            'style="background-color: #0d9488; color: #ffffff; padding: 4px 8px; '
            'border-radius: 4px; text-decoration: none; font-weight: 600; font-size: 11px;">'
            '🔍 Verify</a>',
            print_url,
            verify_url
        )