from django.urls import path
from . import views

urlpatterns = [
    # -------------------------------------------------------------------
    # HOME / LANDING PAGE
    # -------------------------------------------------------------------
    path('', views.home, name='home'),

    # -------------------------------------------------------------------
    # AUTHENTICATION
    # -------------------------------------------------------------------
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # -------------------------------------------------------------------
    # BIRTH REGISTRATION FORM (login required)
    # -------------------------------------------------------------------
    path('register-birth/', views.index, name='index'),

    # -------------------------------------------------------------------
    # MY REGISTRATIONS — user sees their own submissions & statuses
    # -------------------------------------------------------------------
    path('my-registrations/', views.my_registrations, name='my_registrations'),

    # -------------------------------------------------------------------
    # PUBLIC VERIFICATION
    # -------------------------------------------------------------------
    path('verify/<int:pk>/', views.verify_certificate, name='verify_certificate'),

    # -------------------------------------------------------------------
    # PROTECTED REGISTRAR ENDPOINTS (Staff Only)
    # -------------------------------------------------------------------
    path('registrar/', views.registrar_dashboard, name='registrar_dashboard'),
    path('registrar/update-status/<int:pk>/<str:new_status>/', views.update_status, name='update_status'),
    path('registrar/export-csv/', views.export_registrations_csv, name='export_registrations_csv'),
    path('registrar/print/<int:pk>/', views.print_certificate, name='print_certificate'),
]
