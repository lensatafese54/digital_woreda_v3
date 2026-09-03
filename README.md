# 🏛️ Digital Woreda — Birth Registration Portal

<div align="center">

**የፌደራል ሲቪል ምዝገባ እና የነዋሪነት አገልግሎት ኤጀንሲ**  
*Civil Registration & Resident Service Agency (CRRSA)*

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Jazzmin](https://img.shields.io/badge/Admin-Jazzmin-1a56db?style=flat)](https://django-jazzmin.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

A modern, bilingual (🇪🇹 Amharic / English) digital birth registration system for Addis Ababa Woreda offices. Citizens can submit birth registration applications online, track approval status, and download official QR-verified certificates — all without visiting a government office.

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [User Roles](#-user-roles)
- [URL Routes](#-url-routes)
- [Data Model](#-data-model)
- [Admin Panel](#-admin-panel)
- [Screenshots](#-screenshots)
- [Configuration](#-configuration)
- [Management Commands](#-management-commands)

---

## 🌍 Overview

**Digital Woreda** replaces the traditional paper-based birth registration process with a fully digital workflow:

```
Citizen registers online  →  Woreda registrar reviews  →  Certificate issued with QR code
```

The system supports both **Amharic** and **English** throughout — all forms, labels, certificates, and error messages appear in both languages simultaneously. A dark/light theme toggle is available on every page.

---

## ✨ Features

### For Citizens (Regular Users)
| Feature | Description |
|---|---|
| 🔐 **Secure Registration** | Sign up with email, phone, first/last name and password |
| 📝 **Birth Registration Form** | 4-section form: Child Info · Parents · Location · Applicant |
| 📸 **Document Upload** | Upload child photo, hospital document, parent photos |
| 📋 **Status Tracking** | Real-time dashboard showing Pending / Approved / Rejected |
| 📄 **Certificate Download** | Download QR-verified official birth certificate when approved |
| 🌐 **Bilingual UI** | Every screen in Amharic + English with toggle |
| 🌙 **Dark / Light Mode** | Persistent theme preference across sessions |

### For Registrar (Admin)
| Feature | Description |
|---|---|
| 🏛️ **Rich Admin Panel** | Jazzmin-powered Django admin with custom branding |
| ✅ **Bulk Approve/Reject** | Select multiple records and approve or reject at once |
| 🔍 **Advanced Search** | Search by child name, parent name, phone, registration ID |
| 📊 **Date Hierarchy** | Browse records by year → month → day |
| 🖨️ **Print Certificate** | Generate printable PDF-style certificate from admin |
| 📤 **CSV Export** | Export filtered records to CSV |
| 👤 **User Management** | View all users with role badges (ADMIN / USER) |

### Security
- Admin pages are completely invisible to regular users (return HTTP 404)
- Role-based access: `UserProfile.role` checked on every protected route
- Session is fully flushed on logout — browser remembers nothing
- Passwords hashed with Django's default PBKDF2 algorithm
- CSRF protection on all forms
- `is_staff` and `is_superuser` explicitly set to `False` on every self-registered user

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 6.1 (Python 3.14) |
| **Database** | SQLite (development) |
| **Admin Theme** | django-jazzmin 3.0.1 |
| **Image Processing** | Pillow 12.3.0 |
| **QR Code Generation** | qrcode 8.2 |
| **SMS Notifications** | Twilio 9.11.0 (optional) |
| **Production Server** | Gunicorn 26.2.0 |
| **Frontend** | Bootstrap 5.3, Bootstrap Icons, Noto Sans Ethiopic |

---

## 📁 Project Structure

```
digital-woreda-v2/
│
├── core/                          # Main application
│   ├── migrations/                # Database migration files
│   ├── templates/                 # HTML templates
│   │   ├── home.html              # Landing page (bilingual, animated)
│   │   ├── login.html             # Login page
│   │   ├── register.html          # Registration page
│   │   ├── index.html             # Birth registration form
│   │   ├── my_registrations.html  # User status dashboard
│   │   ├── print_certificate.html # Printable birth certificate
│   │   ├── registrar_dashboard.html
│   │   └── verify.html            # QR code verification page
│   ├── admin.py                   # Custom admin configuration
│   ├── apps.py
│   ├── management/
│   │   └── commands/
│   │       └── create_admin.py    # Management command to create admin
│   ├── models.py                  # UserProfile + BirthRegistration models
│   ├── signals.py                 # Auto-create UserProfile on User creation
│   ├── urls.py                    # URL routing
│   ├── utils.py                   # SMS helper (Twilio)
│   └── views.py                   # All view functions
│
├── myproject/
│   ├── settings.py                # Django settings + Jazzmin config
│   ├── urls.py                    # Root URL config + SecureAdminSite
│   ├── wsgi.py
│   └── asgi.py
│
├── media/                         # Uploaded files (photos, documents)
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ installed
- `pip` available

### 1. Clone the repository

```bash
git clone <repository-url>
cd digital-woreda-v2
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create the admin user

```bash
python manage.py create_admin
```

This creates the pre-registered admin with default credentials:

| Field | Value |
|---|---|
| Username | `admin` |
| Email | `admin@woreda.gov.et` |
| Password | `Admin@12345` |

> ⚠️ **Change the default password immediately in any non-development environment.**

Custom credentials:
```bash
python manage.py create_admin --username admin --email admin@woreda.gov.et --password YourSecurePassword
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000**

---

## 👥 User Roles

The system has exactly two roles, enforced at the database level via `UserProfile`:

| Role | How Created | Access |
|---|---|---|
| **ADMIN** | `python manage.py create_admin` only | `/admin/` panel — full registration management |
| **USER** | Public `/register/` page | Birth registration form, status tracking, certificate download |

### Role enforcement layers

1. **Registration view** — `is_staff=False`, `is_superuser=False` hardcoded on every self-registered user
2. **Signal** — `UserProfile.role = USER` set automatically when a new User is created
3. **SecureAdminSite** — custom `has_permission()` requires both `is_staff=True` AND `profile.role == 'ADMIN'`
4. **View decorators** — `_require_admin` raises HTTP 404 (not 403) for non-admins on registrar routes

> Regular users who somehow obtain `is_staff=True` (e.g. via direct DB edit) are **still blocked** by layer 3.

---

## 🔗 URL Routes

| URL | View | Access | Description |
|---|---|---|---|
| `/` | `home` | Public | Landing page |
| `/register/` | `register_view` | Public | User self-registration |
| `/login/` | `login_view` | Public | Email + password login |
| `/logout/` | `logout_view` | Authenticated | Logout + full session flush |
| `/register-birth/` | `index` | Login required (USER) | Birth registration form |
| `/my-registrations/` | `my_registrations` | Login required (USER) | Status tracking dashboard |
| `/verify/<pk>/` | `verify_certificate` | Public | QR code verification |
| `/registrar/print/<pk>/` | `print_certificate` | Public | Printable certificate |
| `/registrar/` | `registrar_dashboard` | ADMIN only → 404 | Registration management |
| `/admin/` | Django admin | ADMIN only | Full admin panel |

---

## 🗃 Data Model

### `UserProfile`

Extends Django's built-in `User` model:

```
UserProfile
  ├── user         (OneToOne → User)
  ├── role         (ADMIN | USER)
  └── phone        (CharField, optional)
```

### `BirthRegistration`

```
BirthRegistration
  ├── Child Information
  │     ├── child_full_name_amharic / child_full_name_english
  │     ├── sex  (MALE | FEMALE)
  │     ├── birth_day / birth_month / birth_year_ec / birth_year_gc
  │     └── child_photo
  │
  ├── Parents Information
  │     ├── father_name_amharic / father_name_english / father_photo
  │     └── mother_name_amharic / mother_name_english / mother_photo
  │
  ├── Location
  │     ├── subcity / woreda / hospital_org_name
  │     └── hospital_document
  │
  ├── Applicant / Declarant
  │     ├── applicant_name_amharic / applicant_name_english
  │     ├── applicant_relation / applicant_age / applicant_phone
  │
  └── Status
        ├── status          (PENDING | APPROVED | REJECTED)
        ├── rejection_reason
        ├── created_at
        └── updated_at
```

Registration IDs are formatted as `CRRSA-00001`, `CRRSA-00002`, etc.

Ethiopian Calendar validation is built into the model — month 13 (Pagumē) cannot exceed 6 days.

---

## 🎛 Admin Panel

Access at **http://127.0.0.1:8000/admin/** using admin credentials.

The panel uses **Jazzmin** (Flatly theme) with:
- Dark navy sidebar matching the Digital Woreda brand
- Circular child photo thumbnails in the list view
- Coloured status badges (✓ green / ⏳ amber / ✗ red)
- Inline photo previews on the detail page
- Bulk actions: Approve / Reject / Reset to Pending
- Date hierarchy browser and full-text search

---

## ⚙️ Configuration

Key settings in `myproject/settings.py`:

```python
# Media files (uploaded photos and documents)
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Auth redirects
LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/'

# Optional: SMS via Twilio
TWILIO_ACCOUNT_SID  = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN   = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
```

For production, set the following environment variables:

```bash
DJANGO_SECRET_KEY=your-secret-key
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 🔧 Management Commands

### Create / update admin user

```bash
python manage.py create_admin
python manage.py create_admin --username admin --email admin@crrsa.gov.et --password NewPassword
```

### Database operations

```bash
python manage.py makemigrations   # create new migration after model changes
python manage.py migrate          # apply migrations
python manage.py createsuperuser  # alternative Django built-in (sets role=ADMIN via signal)
```

### Collect static files (production)

```bash
python manage.py collectstatic
```

---

## 📸 Screenshots

| Page | Description |
|---|---|
| **Home** | Animated hero section with floating certificate mockup, bilingual feature cards, step-by-step guide, and live form demo |
| **Register** | Clean card-style form with password strength meter and bilingual labels |
| **Login** | Email + password with show/hide toggle, autofill blocked |
| **Birth Form** | 4-section form with file upload previews and EC→GC year auto-conversion |
| **My Status** | Summary strip (total/approved/pending/rejected) + per-registration cards with colour-coded borders |
| **Certificate** | Official printable certificate with CRRSA branding, QR code, and bilingual fields |
| **Admin** | Jazzmin-themed panel with photo thumbnails, status badges, and bulk actions |

---

## 📄 License

This project was developed for the **Federal Civil Registration & Resident Service Agency (CRRSA)** of Ethiopia.

---

<div align="center">

Made with ❤️ for Ethiopia 🇪🇹

**Digital Woreda** — ዲጂታሉ የልደት ምዝገባ ፖርታል

</div>
