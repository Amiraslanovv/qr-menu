from django.contrib import admin
from .models import Restaurant, Category, MenuItem, DailySpecial, MenuView, WhatsAppOrder, Order, Table, QRScan


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ("name_az", "name_ru", "icon", "order", "is_active")


class DailySpecialInline(admin.TabularInline):
    model = DailySpecial
    extra = 1
    fields = ("title_az", "special_price", "original_price", "is_active")


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display  = ("name_az", "slug", "phone", "is_active", "created_at")
    list_filter   = ("is_active",)
    search_fields = ("name_az", "slug", "phone")
    prepopulated_fields = {"slug": ("name_az",)}
    inlines       = [CategoryInline, DailySpecialInline]
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Əsas məlumatlar", {
            "fields": ("id", "owner", "slug", "is_active")
        }),
        ("Ad (çoxdilli)", {
            "fields": ("name_az", "name_ru", "name_en")
        }),
        ("Təsvir (çoxdilli)", {
            "fields": ("description_az", "description_ru", "description_en"),
            "classes": ("collapse",),
        }),
        ("Ünvan (çoxdilli)", {
            "fields": ("address_az", "address_ru", "address_en"),
            "classes": ("collapse",),
        }),
        ("Əlaqə", {
            "fields": ("phone", "whatsapp", "wifi_password", "currency")
        }),
        ("Şəkillər (Cloudinary URL)", {
            "fields": ("logo", "cover_image"),
            "classes": ("collapse",),
        }),
        ("Tarixlər", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


class MenuItemInline(admin.TabularInline):
    model  = MenuItem
    extra  = 1
    fields = ("name_az", "price", "is_available", "is_popular", "order")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ("name_az", "restaurant", "icon", "order", "is_active")
    list_filter   = ("restaurant", "is_active")
    inlines       = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display   = ("name_az", "category", "price", "is_available", "is_popular")
    list_filter    = ("category__restaurant", "is_available", "is_popular")
    search_fields  = ("name_az", "name_ru")
    list_editable  = ("is_available", "is_popular")


@admin.register(DailySpecial)
class DailySpecialAdmin(admin.ModelAdmin):
    list_display = ("title_az", "restaurant", "special_price", "is_active")
    list_filter  = ("restaurant", "is_active")


@admin.register(MenuView)
class MenuViewAdmin(admin.ModelAdmin):
    list_display  = ("restaurant", "scanned_at", "lang")
    list_filter   = ("restaurant", "lang")
    readonly_fields = ("restaurant", "scanned_at", "user_agent", "lang")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ("id", "restaurant", "table_number", "total_price", "status", "payment_method", "created_at")
    list_filter   = ("restaurant", "status", "payment_method")
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at", "items_json")
    search_fields = ("customer_name", "customer_phone")


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "label", "restaurant", "is_active")
    list_filter  = ("restaurant", "is_active")


@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "table_number", "scanned_at", "lang")
    list_filter  = ("restaurant", "lang")
    readonly_fields = ("session_id", "scanned_at", "expires_at")