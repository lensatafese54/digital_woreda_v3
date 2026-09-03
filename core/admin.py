from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.contrib import messages
from .models import BirthRegistration, UserProfile


# ─────────────────────────────────────────────────────────────
#  UserProfile inline — shown inside User change page
# ─────────────────────────────────────────────────────────────
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = "Profile"
    extra = 0
    fields = ('role', 'phone')


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display  = ('username', 'email', 'first_name', 'last_name',
                     'role_badge', 'is_staff', 'date_joined')
    list_filter   = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    def role_badge(self, obj):
        try:
            role = obj.profile.role
        except Exception:
            role = 'USER'
        color = '#1a56db' if role == 'ADMIN' else '#059669'
        return mark_safe(
            f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:50px;font-size:11px;font-weight:700">{role}</span>'
        )
    role_badge.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ─────────────────────────────────────────────────────────────
#  BirthRegistration admin
# ─────────────────────────────────────────────────────────────
@admin.register(BirthRegistration)
class BirthRegistrationAdmin(admin.ModelAdmin):

    # ── List columns ──
    list_display = (
        'reg_id_col',
        'photo_col',
        'child_full_name_amharic',
        'child_full_name_english',
        'sex',
        'dob_col',
        'subcity',
        'woreda',
        'status_col',
        'created_at',
        'actions_col',
    )
    list_display_links = ('reg_id_col', 'child_full_name_amharic')
    list_filter        = ('status', 'sex', 'subcity', 'created_at')
    search_fields      = (
        'child_full_name_amharic', 'child_full_name_english',
        'father_name_english', 'mother_name_english',
        'applicant_phone', 'subcity', 'woreda',
    )
    date_hierarchy  = 'created_at'
    ordering        = ('-created_at',)
    list_per_page   = 20
    readonly_fields = (
        'created_at', 'updated_at',
        'reg_id_readonly',
        'child_photo_preview',
        'father_photo_preview',
        'mother_photo_preview',
        'hospital_doc_preview',
    )

    # ── Detail fieldsets ──
    fieldsets = (
        ('Registration Status', {
            'fields': ('reg_id_readonly', 'status', 'rejection_reason',
                       'created_at', 'updated_at'),
        }),
        ('Child Information', {
            'fields': (
                ('child_full_name_amharic', 'child_full_name_english'),
                ('sex', 'birth_day', 'birth_month', 'birth_year_ec', 'birth_year_gc'),
                'child_photo', 'child_photo_preview',
            ),
        }),
        ('Parents Information', {
            'fields': (
                ('father_name_amharic', 'father_name_english'),
                'father_photo', 'father_photo_preview',
                ('mother_name_amharic', 'mother_name_english'),
                'mother_photo', 'mother_photo_preview',
            ),
        }),
        ('Applicant Details', {
            'fields': (
                ('applicant_name_amharic', 'applicant_name_english'),
                ('applicant_relation', 'applicant_age', 'applicant_phone'),
            ),
        }),
        ('Location and Documents', {
            'fields': (
                ('subcity', 'woreda', 'hospital_org_name'),
                'hospital_document', 'hospital_doc_preview',
            ),
        }),
    )

    # ── Bulk actions ──
    actions = ['approve_selected', 'reject_selected', 'reset_pending']

    @admin.action(description='Approve selected registrations')
    def approve_selected(self, request, queryset):
        n = queryset.update(status='APPROVED')
        self.message_user(request, f'{n} registration(s) approved.', messages.SUCCESS)

    @admin.action(description='Reject selected registrations')
    def reject_selected(self, request, queryset):
        n = queryset.update(status='REJECTED')
        self.message_user(request, f'{n} registration(s) rejected.', messages.WARNING)

    @admin.action(description='Reset selected to PENDING')
    def reset_pending(self, request, queryset):
        n = queryset.update(status='PENDING', rejection_reason='')
        self.message_user(request, f'{n} registration(s) reset to pending.', messages.INFO)

    # ── Custom columns ──
    def reg_id_col(self, obj):
        pk_str = f'{obj.pk:05d}'
        return mark_safe(
            f'<span style="font-weight:700;color:#1a56db;font-family:monospace">'
            f'CRRSA-{pk_str}</span>'
        )
    reg_id_col.short_description = 'Reg ID'
    reg_id_col.admin_order_field = 'id'

    def photo_col(self, obj):
        if obj.child_photo:
            url = obj.child_photo.url
            return mark_safe(
                f'<img src="{url}" style="width:36px;height:36px;object-fit:cover;'
                f'border-radius:50%;border:2px solid #e2e8f0;" />'
            )
        return mark_safe(
            '<span style="display:inline-block;width:36px;height:36px;border-radius:50%;'
            'background:#e2e8f0;text-align:center;line-height:36px;font-size:16px;">👶</span>'
        )
    photo_col.short_description = ''

    def dob_col(self, obj):
        return f"{obj.birth_day}/{obj.birth_month}/{obj.birth_year_ec}"
    dob_col.short_description = 'DOB (E.C.)'

    def status_col(self, obj):
        cfg = {
            'APPROVED': ('#059669', '#ecfdf5', 'Approved'),
            'PENDING':  ('#d97706', '#fef3c7', 'Pending'),
            'REJECTED': ('#dc2626', '#fef2f2', 'Rejected'),
        }
        color, bg, label = cfg.get(obj.status, ('#6b7280', '#f9fafb', obj.status))
        return mark_safe(
            f'<span style="background:{bg};color:{color};padding:3px 10px;'
            f'border-radius:50px;font-weight:700;font-size:11px;'
            f'border:1px solid {color};">{label}</span>'
        )
    status_col.short_description = 'Status'
    status_col.admin_order_field = 'status'

    def actions_col(self, obj):
        if not obj.pk:
            return '—'
        print_url  = reverse('print_certificate',  args=[obj.pk])
        verify_url = reverse('verify_certificate', args=[obj.pk])
        return mark_safe(
            f'<a href="{print_url}" target="_blank" style="background:#1a365d;color:#fff;'
            f'padding:3px 8px;border-radius:4px;text-decoration:none;'
            f'font-size:11px;font-weight:600;margin-right:3px">Print</a>'
            f'<a href="{verify_url}" target="_blank" style="background:#0d9488;color:#fff;'
            f'padding:3px 8px;border-radius:4px;text-decoration:none;'
            f'font-size:11px;font-weight:600">Verify</a>'
        )
    actions_col.short_description = 'Actions'

    def reg_id_readonly(self, obj):
        if obj.pk:
            pk_str = f'{obj.pk:05d}'
            return mark_safe(
                f'<strong style="font-size:1.2rem;color:#1a365d;font-family:monospace">'
                f'CRRSA-{pk_str}</strong>'
            )
        return '— new record'
    reg_id_readonly.short_description = 'Registration ID'

    def _file_preview(self, field, label):
        if not field:
            return mark_safe('<em style="color:#9ca3af">No file uploaded</em>')
        url = field.url
        if url.lower().endswith('.pdf'):
            safe_label = label.replace('&', '&amp;')
            return mark_safe(
                f'<a href="{url}" target="_blank" '
                f'style="color:#1a56db;font-weight:600">View {safe_label}</a>'
            )
        return mark_safe(
            f'<a href="{url}" target="_blank">'
            f'<img src="{url}" style="max-height:120px;max-width:220px;'
            f'border-radius:8px;border:1px solid #e2e8f0;object-fit:cover"/></a>'
        )

    def child_photo_preview(self, obj):
        return self._file_preview(obj.child_photo, 'Child Photo')
    child_photo_preview.short_description = 'Preview'

    def father_photo_preview(self, obj):
        return self._file_preview(obj.father_photo, 'Father Photo')
    father_photo_preview.short_description = 'Preview'

    def mother_photo_preview(self, obj):
        return self._file_preview(obj.mother_photo, 'Mother Photo')
    mother_photo_preview.short_description = 'Preview'

    def hospital_doc_preview(self, obj):
        return self._file_preview(obj.hospital_document, 'Hospital Document')
    hospital_doc_preview.short_description = 'Preview'


# ─────────────────────────────────────────────────────────────
#  Site branding
# ─────────────────────────────────────────────────────────────
admin.site.site_header  = "Digital Woreda — Registrar Panel"
admin.site.site_title   = "Digital Woreda Admin"
admin.site.index_title  = "Birth Registration Management"
