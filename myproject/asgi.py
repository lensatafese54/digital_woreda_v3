import base64
import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import BirthRegistration

# Fallback check for qrcode library
try:
    import qrcode
    HAS_QRCODE_PKG = True
except ImportError:
    HAS_QRCODE_PKG = False


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
        # Helper function to safely cast integer inputs
        def safe_int(val):
            try:
                return int(val) if val else None
            except (ValueError, TypeError):
                return None

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
            
            # Applicant / Declarant Details (Typo fixed: applicant_name_amharic)
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
    
    # Dynamic URL resolution instead of hardcoded strings
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


@staff_member_required
def registrar_dashboard(request):
    """
    Protected dashboard for registrars to review pending birth registrations.
    """
    status_filter = request.GET.get('status', 'PENDING')
    
    if status_filter == 'ALL':
        registrations = BirthRegistration.objects.all()
    else:
        registrations = BirthRegistration.objects.filter(status=status_filter)

    context = {
        'registrations': registrations,
        'current_status': status_filter,
        'pending_count': BirthRegistration.objects.filter(status='PENDING').count(),
        'approved_count': BirthRegistration.objects.filter(status='APPROVED').count(),
        'rejected_count': BirthRegistration.objects.filter(status='REJECTED').count(),
    }
    return render(request, 'registrar_dashboard.html', context)


@staff_member_required
@require_POST
def update_status(request, pk, new_status):
    """
    Updates the approval status of a birth record via HTTP POST.
    """
    registration = get_object_or_404(BirthRegistration, pk=pk)
    if new_status in ['APPROVED', 'REJECTED', 'PENDING']:
        registration.status = new_status
        registration.save()
        messages.success(request, f"Status updated to {new_status} for {registration.child_full_name_english}")
    return redirect('registrar_dashboard')