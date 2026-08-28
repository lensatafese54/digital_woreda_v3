from django.urls import path
from . import views

urlpatterns = [
    # -------------------------------------------------------------------
    # PUBLIC ENDPOINTS
    # -------------------------------------------------------------------
    # Homepage (Public registration submission & public search)
    path('', views.index, name='index'),

    # Public verification page (opened when scanning certificate QR code)
    path('verify/<int:pk>/', views.verify_certificate, name='verify_certificate'),

    # -------------------------------------------------------------------
    # PROTECTED REGISTRAR ENDPOINTS (Staff Only)
    # -------------------------------------------------------------------
    # Main registrar review dashboard
    path('registrar/', views.registrar_dashboard, name='registrar_dashboard'),

    # Approve, reject, or pending status update action
    path('registrar/update-status/<int:pk>/<str:new_status>/', views.update_status, name='update_status'),

    # Export filtered dashboard records to CSV
    path('registrar/export-csv/', views.export_registrations_csv, name='export_registrations_csv'),

    # Printable official birth certificate layout
    path('registrar/print/<int:pk>/', views.print_certificate, name='print_certificate'),
]