import base64
import csv
import io

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import BirthRegistration

# Fallback check for qrcode library
try:
    import qrcode
    HAS_QRCODE_PKG = True
except ImportError:
    HAS_QRCODE_PKG = False


# Helper rule: Checks if the user is logged in AND is a staff member
def is_registrar(user):
    return user.is_authenticated and user.is_staff


# -------------------------------------------------------------------
# PUBLIC VIEWS (Accessible by anyone)
# -------------------------------------------------------------------

@transaction.atomic
def index(request):
    """
    Homepage view handling both search queries and new birth registration submissions.
    """
    search_query = request.GET.get('search_name', '').strip()
    search_results = None

    if search_query:
        search_results = BirthRegistration.objects.filter(
            child_full_name_amharic__icontains=search_query
        ) | BirthRegistration.objects.filter(
            child_full_name_english__icontains=search_query
        )

    if request.method == 'POST' and 'submit_registration' in request.POST:
        def safe_int(val):
            try:
                return int(val) if val else None
            except (ValueError, TypeError):
                return None

        # 1. Map required fields to human-readable labels for explicit error reporting
        required_text_fields = {
            'child_full_name_amharic': 'Child Full Name (Amharic)',
            'child_full_name_english': 'Child Full Name (English)',
            'sex': 'Sex',
            'birth_day': 'Birth Day',
            'birth_month': 'Birth Month',
            'birth_year_ec': 'Birth Year (E.C.)',
            'subcity': 'Subcity',
            'woreda': 'Woreda',
            'father_name_amharic': 'Father Name (Amharic)',
            'father_name_english': 'Father Name (English)',
            'mother_name_amharic': 'Mother Name (Amharic)',
            'mother_name_english': 'Mother Name (English)',
        }

        required_file_fields = {
            'child_photo': 'Child Photo',
            'father_photo': 'Father Photo',
            'mother_photo': 'Mother Photo',
        }

        missing_fields = []

        # 2. Check missing text fields
        for field, label in required_text_fields.items():
            if not request.POST.get(field, '').strip():
                missing_fields.append(label)

        # 3. Check missing file uploads
        for field, label in required_file_fields.items():
            if not request.FILES.get(field):
                missing_fields.append(label)

        # Re-render form with field-specific warning if any inputs are missing
        if missing_fields:
            missing_str = ", ".join(missing_fields)
            messages.error(
                request, 
                f"⚠️ Please fill in all required fields! Missing: {missing_str}"
            )
            return render(request, 'index.html', {
                'search_query': search_query,
                'search_results': search_results,
                'form_data': request.POST
            })

        # 4. Create record once validation passes
        BirthRegistration.objects.create(
            # Child Details
            child_full_name_amharic=request.POST.get('child_full_name_amharic', '').strip(),
            child_full_name_english=request.POST.get('child_full_name_english', '').strip(),
            sex=request.POST.get('sex'),
            birth_day=safe_int(request.POST.get('birth_day')),
            birth_month=safe_int(request.POST.get('birth_month')),
            birth_year_ec=safe_int(request.POST.get('birth_year_ec')),
            birth_year_gc=safe_int(request.POST.get('birth_year_gc')),
            subcity=request.POST.get('subcity', '').strip(),
            woreda=request.POST.get('woreda', '').strip(),
            hospital_org_name=request.POST.get('hospital_org_name', '').strip(),

            # Parents Details
            father_name_amharic=request.POST.get('father_name_amharic', '').strip(),
            father_name_english=request.POST.get('father_name_english', '').strip(),
            mother_name_amharic=request.POST.get('mother_name_amharic', '').strip(),
            mother_name_english=request.POST.get('mother_name_english', '').strip(),
            
            # Applicant Details (Optional)
            applicant_name_amharic=request.POST.get('applicant_name_amharic', '').strip() or None,
            applicant_name_english=request.POST.get('applicant_name_english', '').strip() or None,
            applicant_relation=request.POST.get('applicant_relation', '').strip() or None,
            applicant_age=safe_int(request.POST.get('applicant_age')),
            applicant_phone=request.POST.get('applicant_phone', '').strip() or None,

            # Uploaded Files
            child_photo=request.FILES.get('child_photo'),
            father_photo=request.FILES.get('father_photo'),
            mother_photo=request.FILES.get('mother_photo'),
            hospital_document=request.FILES.get('hospital_document'),
        )

        messages.success(request, "ምዝገባው በጥሩ ሁኔታ ተጠናቋል! / Registration submitted successfully!")
        return redirect('index')

    context = {
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'index.html', context)


def print_certificate(request, pk):
    """
    Renders the official printable birth certificate with QR verification link.
    """
    registration = get_object_or_404(BirthRegistration, pk=pk)
    
    relative_url = reverse('verify_certificate', args=[registration.pk])
    verify_url = request.build_absolute_uri(relative_url)
    
    qr_code_base64 = None
    if HAS_QRCODE_PKG:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,
            border=2,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a365d", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'registration': registration,
        'verify_url': verify_url,
        'qr_code': qr_code_base64,
    }
    return render(request, 'print_certificate.html', context)


def verify_certificate(request, pk):
    """
    Public verification endpoint opened when scanning the certificate's QR code.
    """
    registration = get_object_or_404(BirthRegistration, pk=pk)
    return render(request, 'verify.html', {'registration': registration})


# -------------------------------------------------------------------
# PROTECTED REGISTRAR VIEWS (Requires Admin / Staff Login)
# -------------------------------------------------------------------

@user_passes_test(is_registrar, login_url='/admin/login/')
def registrar_dashboard(request):
    """
    Protected dashboard for registrars to review, search, and manage birth registrations.
    """
    current_status = request.GET.get('status', 'PENDING').upper()
    filter_q = request.GET.get('q', '').strip()

    # Base Queryset
    registrations = BirthRegistration.objects.all().order_by('-id')

    # Apply Search Filter across multiple fields
    if filter_q:
        clean_q = filter_q.upper().replace('CRRSA-', '').zfill(5) if filter_q.upper().startswith('CRRSA-') else filter_q
        registrations = registrations.filter(
            Q(child_full_name_amharic__icontains=filter_q) |
            Q(child_full_name_english__icontains=filter_q) |
            Q(father_name_english__icontains=filter_q) |
            Q(id__icontains=clean_q)
        )

    # Calculate status counts across searched query
    total_count = registrations.count()
    pending_count = registrations.filter(status='PENDING').count()
    approved_count = registrations.filter(status='APPROVED').count()
    rejected_count = registrations.filter(status='REJECTED').count()

    # Apply Status Tab Filter
    if current_status and current_status != 'ALL':
        registrations = registrations.filter(status=current_status)

    context = {
        'registrations': registrations,
        'current_status': current_status,
        'filter_q': filter_q,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'registrar_dashboard.html', context)


@user_passes_test(is_registrar, login_url='/admin/login/')
@require_POST
def update_status(request, pk, new_status):
    """
    Updates the approval status and captures rejection reasons when applicable.
    """
    registration = get_object_or_404(BirthRegistration, pk=pk)
    target_status = new_status.upper()
    
    if target_status in ['APPROVED', 'REJECTED', 'PENDING']:
        registration.status = target_status
        
        # Save rejection reason if provided from modal form
        if target_status == 'REJECTED':
            reason = request.POST.get('rejection_reason', '').strip()
            registration.rejection_reason = reason if reason else "No specific reason provided."
        
        registration.save()
        messages.success(request, f"Status updated to {target_status} for CRRSA-{registration.pk:05d}.")
    else:
        messages.error(request, "Invalid status update requested.")
        
    return redirect(request.META.get('HTTP_REFERER', 'registrar_dashboard'))


@user_passes_test(is_registrar, login_url='/admin/login/')
def export_registrations_csv(request):
    """
    Exports filtered registration data as a downloadable CSV file.
    """
    current_status = request.GET.get('status', 'ALL').upper()
    filter_q = request.GET.get('q', '').strip()

    registrations = BirthRegistration.objects.all().order_by('-id')

    if filter_q:
        clean_q = filter_q.upper().replace('CRRSA-', '').zfill(5) if filter_q.upper().startswith('CRRSA-') else filter_q
        registrations = registrations.filter(
            Q(child_full_name_amharic__icontains=filter_q) |
            Q(child_full_name_english__icontains=filter_q) |
            Q(father_name_english__icontains=filter_q) |
            Q(id__icontains=clean_q)
        )

    if current_status and current_status != 'ALL':
        registrations = registrations.filter(status=current_status)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="birth_registrations_{current_status.lower()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Reg ID', 'Child Name (Amharic)', 'Child Name (English)', 'Sex', 
        'DOB (E.C)', 'Father Name', 'Mother Name', 'Subcity', 'Woreda', 
        'Hospital', 'Status', 'Rejection Reason'
    ])

    for reg in registrations:
        writer.writerow([
            f"CRRSA-{reg.pk:05d}",
            reg.child_full_name_amharic,
            reg.child_full_name_english,
            reg.get_sex_display() if hasattr(reg, 'get_sex_display') else reg.sex,
            f"{reg.birth_day}/{reg.birth_month}/{reg.birth_year_ec}",
            reg.father_name_english,
            reg.mother_name_english,
            reg.subcity,
            reg.woreda,
            reg.hospital_org_name,
            reg.status,
            getattr(reg, 'rejection_reason', '')
        ])

    return response