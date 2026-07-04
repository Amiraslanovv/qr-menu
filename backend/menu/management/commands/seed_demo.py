"""
python manage.py seed_demo
Çoxdilli (AZ/RU/EN) demo məlumatları yaradır.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from menu.models import Restaurant, Category, MenuItem, DailySpecial

DEMO = {
    "name_az": "Kafe Şəhər", "name_ru": "Кафе Шəhər", "name_en": "Cafe Sheher",
    "slug": "kafe-seher",
    "description_az": "Mingachevirin ən gözəl kafe menyusu",
    "description_ru": "Лучшее кафе-меню в Мингячевире",
    "description_en": "The finest café menu in Mingachevir",
    "phone": "+994 50 000 00 00", "whatsapp": "+994500000000",
    "address_az": "Mingachevir şəh., Heydər Əliyev pr. 12",
    "address_ru": "г. Мингячевир, пр. Гейдара Алиева 12",
    "address_en": "12 Heydar Aliyev Ave, Mingachevir",
    "wifi_password": "kafeSEHER2025", "currency": "AZN",
    "categories": [
        {"name_az":"İçkilər","name_ru":"Напитки","name_en":"Drinks","icon":"☕","items":[
            {"name_az":"Türk qəhvəsi","name_ru":"Турецкий кофе","name_en":"Turkish Coffee",
             "price":"2.50","desc_az":"Ənənəvi üsulla","desc_ru":"Традиционный способ","desc_en":"Traditionally brewed","popular":True},
            {"name_az":"Çay (stəkan)","name_ru":"Чай (стакан)","name_en":"Tea (glass)",
             "price":"0.80","desc_az":"Azərbaycan çayı","desc_ru":"Азербайджанский чай","desc_en":"Azerbaijani tea"},
            {"name_az":"Portağal şirəsi","name_ru":"Апельсиновый сок","name_en":"Orange Juice",
             "price":"3.00","desc_az":"Təzə sıxılmış","desc_ru":"Свежевыжатый","desc_en":"Freshly squeezed","isnew":True},
            {"name_az":"Limonad","name_ru":"Лимонад","name_en":"Lemonade",
             "price":"2.00","desc_az":"Ev hazırlanması","desc_ru":"Домашнее приготовление","desc_en":"Homemade"},
        ]},
        {"name_az":"Yeməklər","name_ru":"Блюда","name_en":"Main Dishes","icon":"🍽️","items":[
            {"name_az":"Plov","name_ru":"Плов","name_en":"Plov",
             "price":"7.00","desc_az":"Ənənəvi Azərbaycan plovu","desc_ru":"Традиционный азербайджанский плов","desc_en":"Traditional Azerbaijani rice dish","weight":"350q","popular":True},
            {"name_az":"Dolma","name_ru":"Долма","name_en":"Dolma",
             "price":"8.00","desc_az":"Üzüm yarpağında ətli dolma","desc_ru":"Долма в виноградных листьях","desc_en":"Meat dolma in grape leaves","weight":"300q"},
            {"name_az":"Kebab (lülə)","name_ru":"Кебаб (люля)","name_en":"Lula Kebab",
             "price":"9.00","desc_az":"Soğan və pomidor ilə","desc_ru":"С луком и помидором","desc_en":"With onion and tomato","weight":"250q","popular":True},
        ]},
        {"name_az":"Salatlar","name_ru":"Салаты","name_en":"Salads","icon":"🥗","items":[
            {"name_az":"Kənd salatı","name_ru":"Деревенский салат","name_en":"Village Salad",
             "price":"4.00","desc_az":"Pomidor, xiyar, soğan","desc_ru":"Помидор, огурец, лук","desc_en":"Tomato, cucumber, onion","weight":"200q"},
            {"name_az":"Çoban salatı","name_ru":"Чабанский салат","name_en":"Shepherd Salad",
             "price":"4.50","desc_az":"Əlavə pendir ilə","desc_ru":"С дополнительным сыром","desc_en":"With extra cheese","weight":"220q"},
        ]},
        {"name_az":"Desert","name_ru":"Десерты","name_en":"Desserts","icon":"🍰","items":[
            {"name_az":"Paklava","name_ru":"Пахлава","name_en":"Baklava",
             "price":"3.00","desc_az":"Ev hazırlanması, qoz ilə","desc_ru":"Домашняя, с грецким орехом","desc_en":"Homemade, with walnut","weight":"100q","popular":True},
            {"name_az":"Şəkərbura","name_ru":"Шекербура","name_en":"Shekerbura",
             "price":"2.50","weight":"80q"},
            {"name_az":"Gündəlik tort","name_ru":"Торт дня","name_en":"Cake of the Day",
             "price":"4.00","desc_az":"Hər gün fərqli","desc_ru":"Каждый день разный","desc_en":"Changes daily","isnew":True},
        ]},
    ],
    "specials": [{
        "title_az":"Günün dəsti: Kebab + Çay",
        "title_ru":"Комбо дня: Кебаб + Чай",
        "title_en":"Daily Set: Kebab + Tea",
        "desc_az":"Lülə kebab + 2 stəkan çay",
        "desc_ru":"Люля-кебаб + 2 стакана чая",
        "desc_en":"Lula kebab + 2 glasses of tea",
        "original_price":"11.30","special_price":"9.00",
    }],
}


class Command(BaseCommand):
    help = "Çoxdilli V2 demo məlumatları yaradır"

    def handle(self, *args, **opts):
        # Superadmin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@qrmenu.az", "admin123")
            self.stdout.write(self.style.SUCCESS("Superadmin: admin / admin123"))

        # Demo sahibkar
        owner, created = User.objects.get_or_create(
            username="kafe_seher",
            defaults={"email":"kafe@example.com"}
        )
        if created:
            owner.set_password("kafe123")
            owner.save()
            self.stdout.write(self.style.SUCCESS("Sahibkar: kafe_seher / kafe123"))

        # Mövcud demoyu sil
        Restaurant.objects.filter(slug=DEMO["slug"]).delete()

        r = Restaurant.objects.create(
            owner=owner,
            name_az=DEMO["name_az"], name_ru=DEMO["name_ru"], name_en=DEMO["name_en"],
            slug=DEMO["slug"],
            description_az=DEMO["description_az"], description_ru=DEMO["description_ru"], description_en=DEMO["description_en"],
            phone=DEMO["phone"], whatsapp=DEMO["whatsapp"],
            address_az=DEMO["address_az"], address_ru=DEMO["address_ru"], address_en=DEMO["address_en"],
            wifi_password=DEMO["wifi_password"], currency=DEMO["currency"],
        )

        for i, cat_d in enumerate(DEMO["categories"]):
            cat = Category.objects.create(
                restaurant=r, icon=cat_d["icon"], order=i,
                name_az=cat_d["name_az"], name_ru=cat_d["name_ru"], name_en=cat_d["name_en"],
            )
            for j, it in enumerate(cat_d["items"]):
                MenuItem.objects.create(
                    category=cat, order=j,
                    name_az=it["name_az"], name_ru=it["name_ru"], name_en=it.get("name_en",""),
                    description_az=it.get("desc_az",""), description_ru=it.get("desc_ru",""), description_en=it.get("desc_en",""),
                    price=it["price"],
                    weight_or_volume=it.get("weight",""),
                    is_popular=it.get("popular",False),
                    is_new=it.get("isnew",False),
                )

        for sp in DEMO["specials"]:
            DailySpecial.objects.create(
                restaurant=r,
                title_az=sp["title_az"], title_ru=sp["title_ru"], title_en=sp["title_en"],
                description_az=sp["desc_az"], description_ru=sp["desc_ru"], description_en=sp["desc_en"],
                original_price=sp["original_price"], special_price=sp["special_price"],
            )

        self.stdout.write(self.style.SUCCESS(f"""
✅ Demo V2 hazır!
   Restoran : {r.name_az}
   Menyu    : /menu/{r.slug}/
   Dil seçimi: /menu/{r.slug}/?lang=ru
   Admin    : /django-admin/  (admin/admin123)
   Sahibkar : kafe_seher / kafe123
"""))

# Bu əmri seed_demo handle() funksiyasının sonuna əlavə et
# Demo masalar ayrıca command olaraq da işə salına bilər:

class Command2:
    """Demo masalar üçün ayrıca əmr — birbaşa seed_demo-ya əlavə edilib"""
    pass

def add_demo_tables(restaurant):
    """Restorana demo masalar əlavə et"""
    import random, string
    from menu.models import Table
    for i in range(1, 6):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        Table.objects.get_or_create(
            restaurant=restaurant, number=i,
            defaults={"label": f"Masa {i}", "secret_code": code}
        )
