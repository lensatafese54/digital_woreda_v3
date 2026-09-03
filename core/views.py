import base64
import csv
import io
import re

from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from .models import BirthRegistration, UserProfile

try:
    import qrcode
    HAS_QRCODE_PKG = True
except ImportError:
    HAS_QRCODE_PKG = False


# ─────────────────────────────────────────────
#  ROLE HELPERS
# ─────────────────────────────────────────────

def _is_admin(user):
    """True only if the user has an ADMIN profile (is_staff)."""
    return (
        user.is_authenticated
        and user.is_staff
        and hasattr(user, 'profile')
        and user.profile.role == UserProfile.Role.ADMIN
    )


def _require_admin(view_fn):
    """Decorator: 404 for anyone who isn't an admin. Admin pages must never surface to users."""
    def wrapper(request, *args, **kwargs):
        if not _is_admin(request.user):
            raise Http404          # ← silent 404, not a redirect to login
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ─────────────────────────────────────────────
#  PUBLIC — HOME
# ─────────────────────────────────────────────

def home(request):
    return render(request, 'home.html')


# ─────────────────────────────────────────────
#  AUTH — REGISTER  (role = USER always)
# ─────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        if _is_admin(request.user):
            return redirect('/admin/')
        return redirect('index')   # already logged in → go to form

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name',  '').strip()
        email      = request.POST.get('email',      '').strip().lower()
        phone      = request.POST.get('phone',      '').strip()
        password1  = request.POST.get('password1',  '')
        password2  = request.POST.get('password2',  '')

        errors = []

        if not first_name:
            errors.append('First name is required. / የመጀመሪያ ስም ያስፈልጋል።')
        if not last_name:
            errors.append('Last name is required. / የአባት ስም ያስፈልጋል።')
        if not email:
            errors.append('Email is required. / ኢሜይል ያስፈልጋል።')
        elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            errors.append('Enter a valid email address. / ትክክለኛ ኢሜይል ያስፈልጋል።')
        elif User.objects.filter(email=email).exists():
            errors.append('This email is already registered. / ይህ ኢሜይል አስቀድሞ ምዝገባ አለው።')
        if not phone:
            errors.append('Phone number is required. / ስልክ ቁጥር ያስፈልጋል።')
        if not password1:
            errors.append('Password is required. / የይለፍ ቃል ያስፈልጋል።')
        elif len(password1) < 8:
            errors.append('Password must be at least 8 characters. / ቢያንስ 8 ቁምፊዎች ይጠቀሙ።')
        elif password1 != password2:
            errors.append('Passwords do not match. / የይለፍ ቃሎቹ አይዛመዱም።')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'register.html', {'fd': request.POST})

        # Use email as the username (unique, no extra field needed)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,        # ← explicit: users can NEVER access /admin/
            is_superuser=False,    # ← explicit: no superuser privileges
        )
        # Profile is auto-created by signal; set phone and enforce USER role
        profile = user.profile
        profile.phone = phone
        profile.role  = UserProfile.Role.USER   # absolute guarantee
        profile.save()

        login(request, user)
        messages.success(request, f'Welcome, {first_name}! Your account was created successfully.')
        return redirect('home')   # go home after registration, user decides when to start the form

    return render(request, 'register.html')


# ─────────────────────────────────────────────
#  AUTH — LOGIN  (email + password)
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if _is_admin(request.user):
            return redirect('/admin/')
        return redirect('index')   # already logged in → go to form

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # Users are stored with username=email
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if _is_admin(user):
                # Admin: log in then send to Django admin — never show dashboard to anyone
                login(request, user)
                return redirect('/admin/')
            else:
                login(request, user)
                next_url = request.GET.get('next', '')
                # If there's a specific ?next= target honour it, otherwise go home
                return redirect(next_url if next_url else 'home')
        else:
            messages.error(request, 'Invalid email or password. / ኢሜይል ወይም የይለፍ ቃሉ ትክክል አይደለም።')

    return render(request, 'login.html')


# ─────────────────────────────────────────────
#  AUTH — LOGOUT
# ─────────────────────────────────────────────

def logout_view(request):
    """
    Log out and completely clear the session so the browser
    doesn't remember who was logged in. The user starts fresh.
    """
    logout(request)                          # clears Django auth session
    request.session.flush()                  # destroys the session record entirely
    response = redirect('home')
    # Delete the session cookie from the browser
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    return response


# ─────────────────────────────────────────────
#  BIRTH REGISTRATION FORM  (login required, USER only)
# ─────────────────────────────────────────────

@login_required(login_url='/login/')
@transaction.atomic
def index(request):
    # If an admin hits the public form, log them out and redirect to login
    # so they can sign in as a regular user instead
    if _is_admin(request.user):
        logout(request)
        messages.error(
            request,
            'Admin accounts cannot submit registrations. '
            'Please log in with a regular user account. / '
            'Admin መለያ ምዝገባ ማስገባት አይችልም። እንደ ተጠቃሚ ይግቡ።'
        )
        return redirect('login')

    if request.method == 'POST' and 'submit_registration' in request.POST:

        def safe_int(v):
            try:
                return int(v) if v else None
            except (ValueError, TypeError):
                return None

        required_text = {
            'child_full_name_amharic': 'Child Full Name (Amharic)',
            'child_full_name_english': 'Child Full Name (English)',
            'sex':           'Sex',
            'birth_day':     'Birth Day',
            'birth_month':   'Birth Month',
            'birth_year_ec': 'Birth Year (E.C.)',
            'subcity':       'Subcity',
            'woreda':        'Woreda',
            'father_name_amharic': 'Father Name (Amharic)',
            'father_name_english': 'Father Name (English)',
            'mother_name_amharic': 'Mother Name (Amharic)',
            'mother_name_english': 'Mother Name (English)',
        }
        required_files = {
            'child_photo':  'Child Photo',
            'father_photo': 'Father Photo',
            'mother_photo': 'Mother Photo',
        }

        missing = [lbl for fld, lbl in required_text.items()
                   if not request.POST.get(fld, '').strip()]
        missing += [lbl for fld, lbl in required_files.items()
                    if not request.FILES.get(fld)]

        if missing:
            messages.error(request, f'Please fill all required fields: {", ".join(missing)}')
            return render(request, 'index.html', {'form_data': request.POST})

        BirthRegistration.objects.create(
            submitted_by    = request.user,
            child_full_name_amharic = request.POST.get('child_full_name_amharic', '').strip(),
            child_full_name_english = request.POST.get('child_full_name_english', '').strip(),
            sex             = request.POST.get('sex'),
            birth_day       = safe_int(request.POST.get('birth_day')),
            birth_month     = safe_int(request.POST.get('birth_month')),
            birth_year_ec   = safe_int(request.POST.get('birth_year_ec')),
            birth_year_gc   = safe_int(request.POST.get('birth_year_gc')),
            subcity         = request.POST.get('subcity', '').strip(),
            woreda          = request.POST.get('woreda', '').strip(),
            hospital_org_name = request.POST.get('hospital_org_name', '').strip(),
            father_name_amharic = request.POST.get('father_name_amharic', '').strip(),
            father_name_english = request.POST.get('father_name_english', '').strip(),
            mother_name_amharic = request.POST.get('mother_name_amharic', '').strip(),
            mother_name_english = request.POST.get('mother_name_english', '').strip(),
            applicant_name_amharic = request.POST.get('applicant_name_amharic', '').strip() or None,
            applicant_name_english = request.POST.get('applicant_name_english', '').strip() or None,
            applicant_relation = request.POST.get('applicant_relation', '').strip() or None,
            applicant_age   = safe_int(request.POST.get('applicant_age')),
            applicant_phone = request.POST.get('applicant_phone', '').strip() or None,
            child_photo     = request.FILES.get('child_photo'),
            father_photo    = request.FILES.get('father_photo'),
            mother_photo    = request.FILES.get('mother_photo'),
            hospital_document = request.FILES.get('hospital_document'),
        )

        messages.success(request, 'Registration submitted successfully! / ምዝገባው በጥሩ ሁኔታ ተጠናቋል!')
        return redirect('index')

    return render(request, 'index.html')


# ─────────────────────────────────────────────
#  CERTIFICATE PRINT & VERIFY  (public)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  MY REGISTRATIONS — user's own submissions
# ─────────────────────────────────────────────

@login_required(login_url='/login/')
def my_registrations(request):
    """Shows all birth registrations submitted by the logged-in user."""
    if _is_admin(request.user):
        logout(request)
        messages.error(request, 'Please log in with a regular user account.')
        return redirect('login')

    # Always query by the FK — 100% accurate, no phone matching guesswork
    registrations = BirthRegistration.objects.filter(
        submitted_by=request.user
    ).order_by('-created_at')

    # Compute counts in Python
    reg_list       = list(registrations)
    total_count    = len(reg_list)
    approved_count = sum(1 for r in reg_list if r.status == 'APPROVED')
    pending_count  = sum(1 for r in reg_list if r.status == 'PENDING')
    rejected_count = sum(1 for r in reg_list if r.status == 'REJECTED')

    return render(request, 'my_registrations.html', {
        'registrations':   reg_list,
        'user_phone':      getattr(getattr(request.user, 'profile', None), 'phone', None),
        'total_count':     total_count,
        'approved_count':  approved_count,
        'pending_count':   pending_count,
        'rejected_count':  rejected_count,
    })


def print_certificate(request, pk):
    registration = get_object_or_404(BirthRegistration, pk=pk)
    verify_url = request.build_absolute_uri(reverse('verify_certificate', args=[pk]))

    qr_code_base64 = None
    if HAS_QRCODE_PKG:
        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=5, border=2)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1a365d", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_code_base64 = base64.b64encode(buf.getvalue()).decode()

    return render(request, 'print_certificate.html', {
        'registration': registration,
        'verify_url': verify_url,
        'qr_code': qr_code_base64,
    })


def verify_certificate(request, pk):
    registration = get_object_or_404(BirthRegistration, pk=pk)
    return render(request, 'verify.html', {'registration': registration})


# ─────────────────────────────────────────────
#  REGISTRAR DASHBOARD — admin-only, raises 404 for everyone else
# ─────────────────────────────────────────────

@_require_admin
def registrar_dashboard(request):
    current_status = request.GET.get('status', 'PENDING').upper()
    filter_q = request.GET.get('q', '').strip()

    registrations = BirthRegistration.objects.all().order_by('-id')

    if filter_q:
        clean_q = (filter_q.upper().replace('CRRSA-', '').zfill(5)
                   if filter_q.upper().startswith('CRRSA-') else filter_q)
        registrations = registrations.filter(
            Q(child_full_name_amharic__icontains=filter_q) |
            Q(child_full_name_english__icontains=filter_q) |
            Q(father_name_english__icontains=filter_q) |
            Q(id__icontains=clean_q)
        )

    total_count    = registrations.count()
    pending_count  = registrations.filter(status='PENDING').count()
    approved_count = registrations.filter(status='APPROVED').count()
    rejected_count = registrations.filter(status='REJECTED').count()

    if current_status and current_status != 'ALL':
        registrations = registrations.filter(status=current_status)

    return render(request, 'registrar_dashboard.html', {
        'registrations': registrations,
        'current_status': current_status,
        'filter_q': filter_q,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@_require_admin
@require_POST
def update_status(request, pk, new_status):
    registration = get_object_or_404(BirthRegistration, pk=pk)
    target = new_status.upper()
    if target in ['APPROVED', 'REJECTED', 'PENDING']:
        registration.status = target
        if target == 'REJECTED':
            reason = request.POST.get('rejection_reason', '').strip()
            registration.rejection_reason = reason or 'No specific reason provided.'
        registration.save()
        messages.success(request, f'Status updated to {target} for CRRSA-{registration.pk:05d}.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect(request.META.get('HTTP_REFERER', 'registrar_dashboard'))


@_require_admin
def export_registrations_csv(request):
    current_status = request.GET.get('status', 'ALL').upper()
    filter_q = request.GET.get('q', '').strip()
    registrations = BirthRegistration.objects.all().order_by('-id')

    if filter_q:
        clean_q = (filter_q.upper().replace('CRRSA-', '').zfill(5)
                   if filter_q.upper().startswith('CRRSA-') else filter_q)
        registrations = registrations.filter(
            Q(child_full_name_amharic__icontains=filter_q) |
            Q(child_full_name_english__icontains=filter_q) |
            Q(father_name_english__icontains=filter_q) |
            Q(id__icontains=clean_q)
        )

    if current_status != 'ALL':
        registrations = registrations.filter(status=current_status)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="registrations_{current_status.lower()}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Reg ID', 'Child Name (Am)', 'Child Name (En)', 'Sex',
                     'DOB (E.C)', 'Father', 'Mother', 'Subcity', 'Woreda',
                     'Hospital', 'Status', 'Rejection Reason'])
    for r in registrations:
        writer.writerow([
            f'CRRSA-{r.pk:05d}',
            r.child_full_name_amharic, r.child_full_name_english,
            r.sex,
            f'{r.birth_day}/{r.birth_month}/{r.birth_year_ec}',
            r.father_name_english, r.mother_name_english,
            r.subcity, r.woreda, r.hospital_org_name,
            r.status, getattr(r, 'rejection_reason', ''),
        ])
    return response
