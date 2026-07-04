from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include("menu.urls")),
    # Frontend səhifələri
    path("menu/<slug:slug>/", TemplateView.as_view(template_name="menu.html"), name="menu_page"),
    path("admin-panel/", TemplateView.as_view(template_name="admin_panel.html"), name="admin_panel"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "QR Menyu — Admin Panel"
admin.site.site_title = "QR Menyu"
admin.site.index_title = "İdarəetmə paneli"