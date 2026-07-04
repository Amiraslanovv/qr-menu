from django.db import models
from django.contrib.auth.models import User
import uuid


class Restaurant(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner        = models.OneToOneField(User, on_delete=models.CASCADE,
                                        related_name="restaurant", null=True, blank=True)
    name_az      = models.CharField(max_length=200, verbose_name="Ad (AZ)")
    name_ru      = models.CharField(max_length=200, blank=True, verbose_name="Ad (RU)")
    name_en      = models.CharField(max_length=200, blank=True, verbose_name="Ad (EN)")
    slug         = models.SlugField(unique=True, verbose_name="URL slug")
    description_az = models.TextField(blank=True, verbose_name="Təsvir (AZ)")
    description_ru = models.TextField(blank=True, verbose_name="Təsvir (RU)")
    description_en = models.TextField(blank=True, verbose_name="Təsvir (EN)")
    phone        = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    whatsapp     = models.CharField(max_length=30, blank=True, verbose_name="WhatsApp")
    address_az   = models.TextField(blank=True, verbose_name="Ünvan (AZ)")
    address_ru   = models.TextField(blank=True, verbose_name="Ünvan (RU)")
    address_en   = models.TextField(blank=True, verbose_name="Ünvan (EN)")
    # Cloudinary URL-ləri (cloudinary_storage ilə idarə olunur)
    logo         = models.CharField(max_length=500, blank=True, verbose_name="Logo URL (Cloudinary)")
    cover_image  = models.CharField(max_length=500, blank=True, verbose_name="Cover URL (Cloudinary)")
    is_active    = models.BooleanField(default=True, verbose_name="Aktivdir")
    wifi_password = models.CharField(max_length=100, blank=True, verbose_name="WiFi şifrəsi")
    currency     = models.CharField(max_length=10, default="AZN", verbose_name="Valyuta")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restoran"
        verbose_name_plural = "Restoranlar"

    def __str__(self):
        return self.name_az

    def get_name(self, lang="az"):
        return getattr(self, f"name_{lang}", None) or self.name_az

    def get_description(self, lang="az"):
        return getattr(self, f"description_{lang}", None) or self.description_az

    def get_address(self, lang="az"):
        return getattr(self, f"address_{lang}", None) or self.address_az


class Category(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="categories")
    name_az    = models.CharField(max_length=100, verbose_name="Ad (AZ)")
    name_ru    = models.CharField(max_length=100, blank=True, verbose_name="Ad (RU)")
    name_en    = models.CharField(max_length=100, blank=True, verbose_name="Ad (EN)")
    icon       = models.CharField(max_length=10, blank=True, verbose_name="Emoji")
    order      = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    is_active  = models.BooleanField(default=True, verbose_name="Aktivdir")

    class Meta:
        verbose_name = "Kateqoriya"
        verbose_name_plural = "Kateqoriyalar"
        ordering = ["order"]

    def __str__(self):
        return f"{self.restaurant.name_az} → {self.name_az}"

    def get_name(self, lang="az"):
        return getattr(self, f"name_{lang}", None) or self.name_az


class MenuItem(models.Model):
    category         = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    name_az          = models.CharField(max_length=200, verbose_name="Ad (AZ)")
    name_ru          = models.CharField(max_length=200, blank=True, verbose_name="Ad (RU)")
    name_en          = models.CharField(max_length=200, blank=True, verbose_name="Ad (EN)")
    description_az   = models.TextField(blank=True, verbose_name="Təsvir (AZ)")
    description_ru   = models.TextField(blank=True, verbose_name="Təsvir (RU)")
    description_en   = models.TextField(blank=True, verbose_name="Təsvir (EN)")
    price            = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Qiymət")
    # Cloudinary URL
    image            = models.CharField(max_length=500, blank=True, verbose_name="Şəkil URL (Cloudinary)")
    is_available     = models.BooleanField(default=True, verbose_name="Mövcuddur")
    is_popular       = models.BooleanField(default=False, verbose_name="Populyar")
    is_new           = models.BooleanField(default=False, verbose_name="Yeni")
    allergens        = models.CharField(max_length=300, blank=True, verbose_name="Allergenlər")
    weight_or_volume = models.CharField(max_length=50, blank=True, verbose_name="Çəki/Həcm")
    order            = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menyu elementi"
        verbose_name_plural = "Menyu elementləri"
        ordering = ["order"]

    def __str__(self):
        return f"{self.category.restaurant.name_az} → {self.name_az}"

    def get_name(self, lang="az"):
        return getattr(self, f"name_{lang}", None) or self.name_az

    def get_description(self, lang="az"):
        return getattr(self, f"description_{lang}", None) or self.description_az


class DailySpecial(models.Model):
    restaurant     = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="specials")
    title_az       = models.CharField(max_length=200, verbose_name="Başlıq (AZ)")
    title_ru       = models.CharField(max_length=200, blank=True, verbose_name="Başlıq (RU)")
    title_en       = models.CharField(max_length=200, blank=True, verbose_name="Başlıq (EN)")
    description_az = models.TextField(blank=True, verbose_name="Təsvir (AZ)")
    description_ru = models.TextField(blank=True, verbose_name="Təsvir (RU)")
    description_en = models.TextField(blank=True, verbose_name="Təsvir (EN)")
    original_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    special_price  = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Endirimli qiymət")
    valid_until    = models.DateField(null=True, blank=True, verbose_name="Etibarlılıq tarixi")
    is_active      = models.BooleanField(default=True, verbose_name="Aktivdir")

    class Meta:
        verbose_name = "Günün təklifi"
        verbose_name_plural = "Günün təklifləri"

    def __str__(self):
        return f"{self.restaurant.name_az} → {self.title_az}"

    def get_title(self, lang="az"):
        return getattr(self, f"title_{lang}", None) or self.title_az

    def get_description(self, lang="az"):
        return getattr(self, f"description_{lang}", None) or self.description_az


class WhatsAppOrder(models.Model):
    """WhatsApp vasitəsilə gələn sifarişləri izləmək üçün"""
    restaurant  = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="orders")
    customer_phone = models.CharField(max_length=30, blank=True)
    message     = models.TextField(verbose_name="Sifariş mətni")
    created_at  = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False, verbose_name="Bildiriş göndərildi")

    class Meta:
        verbose_name = "Sifariş"
        verbose_name_plural = "Sifarişlər"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.restaurant.name_az} — {self.created_at:%d.%m.%Y %H:%M}"


class MenuView(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="views")
    scanned_at = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
    lang       = models.CharField(max_length=5, default="az")

    class Meta:
        verbose_name = "Baxış"
        verbose_name_plural = "Baxışlar"


class Table(models.Model):
    """Restoran masaları — hər masanın öz QR kodu var"""
    restaurant   = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="tables")
    number       = models.PositiveIntegerField(verbose_name="Masa nömrəsi")
    label        = models.CharField(max_length=50, blank=True, verbose_name="Ad (məs: VIP, Terasa 1)")
    secret_code  = models.CharField(max_length=8, verbose_name="Gizli kod (ofisant dəyişir)")
    is_active    = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Masa"
        verbose_name_plural = "Masalar"
        unique_together = ("restaurant", "number")
        ordering = ["number"]

    def __str__(self):
        return f"{self.restaurant.name_az} — Masa {self.number}"

    def regenerate_code(self):
        import random, string
        self.secret_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.save()


class Order(models.Model):
    """Müştəri sifarişi"""
    STATUS_CHOICES = [
        ("pending",   "Gözləyir"),
        ("confirmed", "Təsdiqləndi"),
        ("preparing", "Hazırlanır"),
        ("ready",     "Hazırdır"),
        ("paid",      "Ödənilib"),
        ("cancelled", "Ləğv edildi"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("cash",       "Nağd"),
        ("table",      "Masada kart"),
        ("abb_pay",    "ABB Pay"),
        ("apple_pay",  "Apple Pay"),
        ("google_pay", "Google Pay"),
    ]

    restaurant     = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="orders")
    table          = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    table_number   = models.PositiveIntegerField(null=True, blank=True, verbose_name="Masa nömrəsi")
    customer_phone = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    customer_name  = models.CharField(max_length=100, blank=True, verbose_name="Ad")
    items_json     = models.JSONField(default=list, verbose_name="Sifariş elementləri")
    note           = models.TextField(blank=True, verbose_name="Qeyd")
    total_price    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash")
    payment_status = models.CharField(max_length=20, default="unpaid")
    abb_transaction_id = models.CharField(max_length=100, blank=True)
    scan_time      = models.DateTimeField(null=True, blank=True, verbose_name="QR skan vaxtı")
    is_notified    = models.BooleanField(default=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sifariş"
        verbose_name_plural = "Sifarişlər"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.restaurant.name_az} — Masa {self.table_number} — {self.created_at:%d.%m %H:%M}"


class QRScan(models.Model):
    """QR skan qeydi — vaxt limiti üçün"""
    restaurant  = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="qr_scans")
    table       = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    table_number = models.PositiveIntegerField(null=True, blank=True)
    session_id  = models.CharField(max_length=64, unique=True)
    scanned_at  = models.DateTimeField(auto_now_add=True)
    expires_at  = models.DateTimeField()
    user_agent  = models.TextField(blank=True)
    lang        = models.CharField(max_length=5, default="az")

    class Meta:
        verbose_name = "QR Skan"
        verbose_name_plural = "QR Skanlar"

    def is_valid(self):
        from django.utils import timezone
        return timezone.now() < self.expires_at
