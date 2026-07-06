from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0002_table_order_qrscan"),
    ]

    operations = [
        migrations.AddField(model_name="restaurant", name="theme",
            field=models.CharField(choices=[("dark","Tünd"),("light","Açıq"),("custom","Özəl")],
                                   default="dark", max_length=10, verbose_name="Mövzu")),
        migrations.AddField(model_name="restaurant", name="accent_color",
            field=models.CharField(default="#d4a853", max_length=7, verbose_name="Vurğu rəngi")),
        migrations.AddField(model_name="restaurant", name="bg_color",
            field=models.CharField(default="#0f0f0f", max_length=7, verbose_name="Fon rəngi")),
        migrations.AddField(model_name="restaurant", name="surface_color",
            field=models.CharField(default="#1c1c1e", max_length=7, verbose_name="Kart rəngi")),
        migrations.AddField(model_name="restaurant", name="text_color",
            field=models.CharField(default="#f5f5f5", max_length=7, verbose_name="Mətn rəngi")),
        migrations.AddField(model_name="restaurant", name="font_family",
            field=models.CharField(choices=[("system","Sistem"),("inter","Inter"),
                                            ("playfair","Playfair"),("roboto","Roboto")],
                                   default="system", max_length=20, verbose_name="Şrift")),
        migrations.AddField(model_name="restaurant", name="menu_layout",
            field=models.CharField(choices=[("card","Kart"),("list","Siyahı"),("grid","Grid")],
                                   default="card", max_length=10, verbose_name="Layout")),
        migrations.AddField(model_name="restaurant", name="show_prices",
            field=models.BooleanField(default=True, verbose_name="Qiymətlər görünsün")),
        migrations.AddField(model_name="restaurant", name="show_images",
            field=models.BooleanField(default=True, verbose_name="Şəkillər görünsün")),
        migrations.AddField(model_name="restaurant", name="border_radius",
            field=models.IntegerField(default=14, verbose_name="Kart bucaq radiusu")),
    ]
