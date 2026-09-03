from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# ─────────────────────────────────────────────────────────────────────
# Custom AdminSite: only users with role=ADMIN (is_staff=True AND
# UserProfile.role == ADMIN) can access /admin/.
# Regular users — even if somehow is_staff is True — are blocked.
# ─────────────────────────────────────────────────────────────────────
class SecureAdminSite(AdminSite):
    def has_permission(self, request):
        """
        Both conditions must be true:
          1. user.is_active and user.is_staff  (Django default)
          2. user.profile.role == 'ADMIN'      (our extra check)
        """
        if not request.user.is_active or not request.user.is_staff:
            return False
        try:
            return request.user.profile.role == 'ADMIN'
        except Exception:
            return False


# Replace the default admin site
admin.site.__class__ = SecureAdminSite


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
