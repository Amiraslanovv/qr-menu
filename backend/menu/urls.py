from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────
    path("auth/login/",     views.owner_login,    name="login"),
    path("auth/register/",  views.owner_register, name="register"),
    path("auth/me/",        views.owner_me,        name="me"),

    # ── Public menyu ────────────────────────────────────────
    path("menu/<slug:slug>/",        views.public_menu,    name="public_menu"),
    path("menu/<slug:slug>/qr/",     views.qr_code_svg,    name="qr_code"),
    path("menu/<slug:slug>/scan/",   views.register_scan,  name="register_scan"),
    path("menu/<slug:slug>/order/",  views.place_order,    name="place_order"),

    # ── Session yoxlama ─────────────────────────────────────
    path("session/verify/",  views.verify_session, name="verify_session"),

    # ── Sifariş statusu (müştəri üçün) ─────────────────────
    path("order/<int:order_id>/status/", views.order_status, name="order_status"),

    # ── Şəkil yükləmə ───────────────────────────────────────
    path("upload/",  views.upload_image, name="upload"),

    # ── ABB Pay ─────────────────────────────────────────────
    path("payment/abb/callback/", views.abb_payment_callback, name="abb_callback"),

    # ── Sahibkar ────────────────────────────────────────────
    path("owner/restaurant/",              views.owner_restaurant,      name="owner_restaurant"),
    path("owner/categories/",             views.owner_categories,      name="owner_categories"),
    path("owner/categories/<int:pk>/",    views.owner_category_detail, name="owner_category_detail"),
    path("owner/items/",                  views.owner_items,            name="owner_items"),
    path("owner/items/<int:pk>/",         views.owner_item_detail,      name="owner_item_detail"),
    path("owner/items/<int:pk>/toggle/",  views.toggle_item,            name="toggle_item"),
    path("owner/specials/",               views.owner_specials,         name="owner_specials"),
    path("owner/specials/<int:pk>/",      views.owner_special_detail,   name="owner_special_detail"),
    path("owner/analytics/",             views.owner_analytics,        name="owner_analytics"),

    # ── Masalar ─────────────────────────────────────────────
    path("owner/tables/",                      views.owner_tables,          name="owner_tables"),
    path("owner/tables/create/",               views.create_table,          name="create_table"),
    path("owner/tables/<int:table_id>/qr/",    views.table_qr_svg,          name="table_qr"),
    path("owner/tables/<int:table_id>/regen/", views.regenerate_table_code, name="regen_table"),
    path("owner/tables/<int:table_id>/",       views.delete_table,          name="delete_table"),

    # ── Sifarişlər ──────────────────────────────────────────
    path("owner/orders/",                        views.owner_orders_list,   name="owner_orders"),
    path("owner/orders/<int:order_id>/status/",  views.update_order_status, name="order_status_update"),

    # ── WhatsApp webhook ────────────────────────────────────
    path("webhook/whatsapp/<slug:slug>/", views.whatsapp_webhook, name="whatsapp_webhook"),

    # ── Superadmin ──────────────────────────────────────────
    path("admin/restaurants/", views.admin_all_restaurants, name="admin_restaurants"),
]
