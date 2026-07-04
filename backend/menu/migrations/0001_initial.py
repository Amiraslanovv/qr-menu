import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Restaurant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("name_az", models.CharField(max_length=200, verbose_name="Ad (AZ)")),
                ("name_ru", models.CharField(blank=True, max_length=200, verbose_name="Ad (RU)")),
                ("name_en", models.CharField(blank=True, max_length=200, verbose_name="Ad (EN)")),
                ("slug", models.SlugField(unique=True, verbose_name="URL slug")),
                ("description_az", models.TextField(blank=True, verbose_name="Təsvir (AZ)")),
                ("description_ru", models.TextField(blank=True, verbose_name="Təsvir (RU)")),
                ("description_en", models.TextField(blank=True, verbose_name="Təsvir (EN)")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="Telefon")),
                ("whatsapp", models.CharField(blank=True, max_length=30, verbose_name="WhatsApp")),
                ("address_az", models.TextField(blank=True, verbose_name="Ünvan (AZ)")),
                ("address_ru", models.TextField(blank=True, verbose_name="Ünvan (RU)")),
                ("address_en", models.TextField(blank=True, verbose_name="Ünvan (EN)")),
                ("logo", models.CharField(blank=True, max_length=500, verbose_name="Logo URL")),
                ("cover_image", models.CharField(blank=True, max_length=500, verbose_name="Cover URL")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktivdir")),
                ("wifi_password", models.CharField(blank=True, max_length=100, verbose_name="WiFi şifrəsi")),
                ("currency", models.CharField(default="AZN", max_length=10, verbose_name="Valyuta")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="restaurant", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name":"Restoran","verbose_name_plural":"Restoranlar"},
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("name_az", models.CharField(max_length=100, verbose_name="Ad (AZ)")),
                ("name_ru", models.CharField(blank=True, max_length=100, verbose_name="Ad (RU)")),
                ("name_en", models.CharField(blank=True, max_length=100, verbose_name="Ad (EN)")),
                ("icon", models.CharField(blank=True, max_length=10, verbose_name="Emoji")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Sıra")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktivdir")),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="categories", to="menu.restaurant")),
            ],
            options={"verbose_name":"Kateqoriya","verbose_name_plural":"Kateqoriyalar","ordering":["order"]},
        ),
        migrations.CreateModel(
            name="MenuItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("name_az", models.CharField(max_length=200, verbose_name="Ad (AZ)")),
                ("name_ru", models.CharField(blank=True, max_length=200, verbose_name="Ad (RU)")),
                ("name_en", models.CharField(blank=True, max_length=200, verbose_name="Ad (EN)")),
                ("description_az", models.TextField(blank=True, verbose_name="Təsvir (AZ)")),
                ("description_ru", models.TextField(blank=True, verbose_name="Təsvir (RU)")),
                ("description_en", models.TextField(blank=True, verbose_name="Təsvir (EN)")),
                ("price", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Qiymət")),
                ("image", models.CharField(blank=True, max_length=500, verbose_name="Şəkil URL")),
                ("is_available", models.BooleanField(default=True, verbose_name="Mövcuddur")),
                ("is_popular", models.BooleanField(default=False, verbose_name="Populyar")),
                ("is_new", models.BooleanField(default=False, verbose_name="Yeni")),
                ("allergens", models.CharField(blank=True, max_length=300, verbose_name="Allergenlər")),
                ("weight_or_volume", models.CharField(blank=True, max_length=50, verbose_name="Çəki/Həcm")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Sıra")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="menu.category")),
            ],
            options={"verbose_name":"Menyu elementi","verbose_name_plural":"Menyu elementləri","ordering":["order"]},
        ),
        migrations.CreateModel(
            name="DailySpecial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("title_az", models.CharField(max_length=200, verbose_name="Başlıq (AZ)")),
                ("title_ru", models.CharField(blank=True, max_length=200, verbose_name="Başlıq (RU)")),
                ("title_en", models.CharField(blank=True, max_length=200, verbose_name="Başlıq (EN)")),
                ("description_az", models.TextField(blank=True, verbose_name="Təsvir (AZ)")),
                ("description_ru", models.TextField(blank=True, verbose_name="Təsvir (RU)")),
                ("description_en", models.TextField(blank=True, verbose_name="Təsvir (EN)")),
                ("original_price", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("special_price", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Endirimli qiymət")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Etibarlılıq tarixi")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktivdir")),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="specials", to="menu.restaurant")),
            ],
            options={"verbose_name":"Günün təklifi","verbose_name_plural":"Günün təklifləri"},
        ),
        migrations.CreateModel(
            name="WhatsAppOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("customer_phone", models.CharField(blank=True, max_length=30)),
                ("message", models.TextField(verbose_name="Sifariş mətni")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_notified", models.BooleanField(default=False, verbose_name="Bildiriş göndərildi")),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="whatsapp_orders", to="menu.restaurant")),
            ],
            options={"verbose_name":"WhatsApp Sifariş","verbose_name_plural":"WhatsApp Sifarişlər","ordering":["-created_at"]},
        ),
        migrations.CreateModel(
            name="MenuView",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("scanned_at", models.DateTimeField(auto_now_add=True)),
                ("user_agent", models.TextField(blank=True)),
                ("lang", models.CharField(default="az", max_length=5)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="views", to="menu.restaurant")),
            ],
            options={"verbose_name":"Baxış","verbose_name_plural":"Baxışlar"},
        ),
    ]
