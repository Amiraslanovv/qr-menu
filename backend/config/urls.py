from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("menu.urls")),

    # Token auth: POST {username, password} → returns token
    path("api/auth/login/", obtain_auth_token, name="api_token_auth"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customise admin site text
admin.site.site_header = "QR Menyu — Admin Panel"
admin.site.site_title = "QR Menyu"
admin.site.index_title = "İdarəetmə paneli"
