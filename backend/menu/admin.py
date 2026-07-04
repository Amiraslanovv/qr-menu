from django.contrib import admin
from .models import Restaurant, Category, MenuItem, DailySpecial, MenuView, WhatsAppOrder


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


@admin.register(WhatsAppOrder)
class WhatsAppOrderAdmin(admin.ModelAdmin):
    list_display  = ("restaurant", "customer_phone", "created_at", "is_notified")
    list_filter   = ("restaurant", "is_notified")
    readonly_fields = ("restaurant", "customer_phone", "message", "created_at")


from .models import Table, Order, QRScan


class TableInline(admin.TabularInline):
    model  = Table
    extra  = 1
    fields = ("number", "label", "secret_code", "is_active")
    readonly_fields = ("secret_code",)


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("number", "label", "restaurant", "secret_code", "is_active")
    list_filter  = ("restaurant", "is_active")
    actions      = ["regenerate_codes"]

    def regenerate_codes(self, request, queryset):
        for table in queryset:
            table.regenerate_code()
        self.message_user(request, f"{queryset.count()} masanın kodu yeniləndi.")
    regenerate_codes.short_description = "Seçilmiş masaların kodunu yenilə"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ("id", "restaurant", "table_number", "customer_name",
                     "total_price", "status", "payment_method", "payment_status", "created_at")
    list_filter   = ("restaurant", "status", "payment_method", "payment_status")
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at", "items_json", "abb_transaction_id")
    search_fields = ("customer_name", "customer_phone")

    fieldsets = (
        ("Sifariş məlumatları", {
            "fields": ("restaurant", "table", "table_number", "customer_name",
                       "customer_phone", "items_json", "note", "total_price")
        }),
        ("Status", {
            "fields": ("status", "payment_method", "payment_status", "abb_transaction_id")
        }),
        ("Tarixlər", {
            "fields": ("scan_time", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "table_number", "scanned_at", "expires_at", "lang")
    list_filter  = ("restaurant", "lang")
    readonly_fields = ("session_id", "scanned_at", "expires_at")
