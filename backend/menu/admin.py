from django.contrib import admin
from .models import Restaurant, Category, MenuItem, DailySpecial, MenuView

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ("name_az", "icon", "order", "is_active")

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ("name_az", "price", "is_available", "is_popular", "order")

class DailySpecialInline(admin.TabularInline):
    model = DailySpecial
    extra = 1
    fields = ("title_az", "special_price", "original_price", "valid_until", "is_active")

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name_az", "slug", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name_az", "slug", "phone")
    prepopulated_fields = {"slug": ("name_az",)}
    inlines = [CategoryInline, DailySpecialInline]
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Əsas məlumatlar", {
            "fields": ("id", "name_az", "slug", "description_az", "is_active")
        }),
        ("Əlaqə", {
            "fields": ("phone", "whatsapp", "address_az", "wifi_password")
        }),
        ("Görünüş", {
            "fields": ("logo", "cover_image", "currency")
        }),
        ("Tarixlər", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_az", "restaurant", "icon", "order", "is_active")
    list_filter = ("restaurant", "is_active")
    inlines = [MenuItemInline]

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name_az", "category", "price", "is_available", "is_popular", "is_new")
    list_filter = ("category__restaurant", "is_available", "is_popular")
    search_fields = ("name_az", "description_az")
    list_editable = ("is_available", "is_popular")

@admin.register(DailySpecial)
class DailySpecialAdmin(admin.ModelAdmin):
    list_display = ("title_az", "restaurant", "special_price", "valid_until", "is_active")
    list_filter = ("restaurant", "is_active")

@admin.register(MenuView)
class MenuViewAdmin(admin.ModelAdmin):
    list_display = ("restaurant", "scanned_at", "user_agent")
    list_filter = ("restaurant",)
    readonly_fields = ("restaurant", "scanned_at", "user_agent")