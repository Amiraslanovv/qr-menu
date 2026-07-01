from django.urls import path
from . import views

urlpatterns = [

    # ── Auth ────────────────────────────────────────────────
    path("auth/login/",     views.owner_login,    name="login"),
    path("auth/register/",  views.owner_register, name="register"),   # yalnız superadmin
    path("auth/me/",        views.owner_me,        name="me"),

    # ── Public (QR scan) ────────────────────────────────────
    path("menu/<slug:slug>/",     views.public_menu,  name="public_menu"),
    path("menu/<slug:slug>/qr/",  views.qr_code_svg,  name="qr_code"),

    # ── Fayl yükləmə ────────────────────────────────────────
    path("upload/",  views.upload_image,  name="upload"),

    # ── Sahibkar — öz restoranı ─────────────────────────────
    path("owner/restaurant/",              views.owner_restaurant,    name="owner_restaurant"),
    path("owner/categories/",             views.owner_categories,    name="owner_categories"),
    path("owner/categories/<int:pk>/",    views.owner_category_detail, name="owner_category_detail"),
    path("owner/items/",                  views.owner_items,          name="owner_items"),
    path("owner/items/<int:pk>/",         views.owner_item_detail,    name="owner_item_detail"),
    path("owner/items/<int:pk>/toggle/",  views.toggle_item,          name="toggle_item"),
    path("owner/specials/",               views.owner_specials,       name="owner_specials"),
    path("owner/specials/<int:pk>/",      views.owner_special_detail, name="owner_special_detail"),
    path("owner/analytics/",             views.owner_analytics,      name="owner_analytics"),
    path("owner/orders/",                views.owner_orders,          name="owner_orders"),

    # ── WhatsApp webhook ────────────────────────────────────
    path("webhook/whatsapp/<slug:slug>/", views.whatsapp_webhook, name="whatsapp_webhook"),

    # ── Superadmin ──────────────────────────────────────────
    path("admin/restaurants/",  views.admin_all_restaurants, name="admin_restaurants"),
]
