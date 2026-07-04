from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Table",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("number", models.PositiveIntegerField(verbose_name="Masa nömrəsi")),
                ("label", models.CharField(blank=True, max_length=50, verbose_name="Ad")),
                ("secret_code", models.CharField(max_length=8, verbose_name="Gizli kod")),
                ("is_active", models.BooleanField(default=True)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tables", to="menu.restaurant")),
            ],
            options={"verbose_name":"Masa","verbose_name_plural":"Masalar","ordering":["number"],"unique_together":{("restaurant","number")}},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("table_number", models.PositiveIntegerField(blank=True, null=True)),
                ("customer_phone", models.CharField(blank=True, max_length=30)),
                ("customer_name", models.CharField(blank=True, max_length=100)),
                ("items_json", models.JSONField(default=list)),
                ("note", models.TextField(blank=True)),
                ("total_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("status", models.CharField(choices=[("pending","Gözləyir"),("confirmed","Təsdiqləndi"),("preparing","Hazırlanır"),("ready","Hazırdır"),("paid","Ödənilib"),("cancelled","Ləğv edildi")], default="pending", max_length=20)),
                ("payment_method", models.CharField(choices=[("cash","Nağd"),("table","Masada kart"),("abb_pay","ABB Pay"),("apple_pay","Apple Pay"),("google_pay","Google Pay")], default="cash", max_length=20)),
                ("payment_status", models.CharField(default="unpaid", max_length=20)),
                ("abb_transaction_id", models.CharField(blank=True, max_length=100)),
                ("scan_time", models.DateTimeField(blank=True, null=True)),
                ("is_notified", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="orders", to="menu.restaurant")),
                ("table", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="menu.table")),
            ],
            options={"verbose_name":"Sifariş","verbose_name_plural":"Sifarişlər","ordering":["-created_at"]},
        ),
        migrations.CreateModel(
            name="QRScan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True)),
                ("table_number", models.PositiveIntegerField(blank=True, null=True)),
                ("session_id", models.CharField(max_length=64, unique=True)),
                ("scanned_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("user_agent", models.TextField(blank=True)),
                ("lang", models.CharField(default="az", max_length=5)),
                ("restaurant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="qr_scans", to="menu.restaurant")),
                ("table", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="qr_scans_table", to="menu.table")),
            ],
            options={"verbose_name":"QR Skan","verbose_name_plural":"QR Skanlar"},
        ),
    ]
