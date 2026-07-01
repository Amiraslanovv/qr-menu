from rest_framework import serializers
from .models import Restaurant, Category, MenuItem, DailySpecial, WhatsAppOrder


SUPPORTED_LANGS = ("az", "ru", "en")


class MenuItemSerializer(serializers.ModelSerializer):
    """
    Müştəriyə göndərilən element. 'lang' context parametrinə görə
    doğru dildə ad/təsvir qaytarır, fallback AZ-dır.
    """
    name        = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model  = MenuItem
        fields = [
            "id", "name", "description", "price", "image",
            "is_available", "is_popular", "is_new",
            "allergens", "weight_or_volume", "order",
        ]

    def _lang(self):
        return self.context.get("lang", "az")

    def get_name(self, obj):
        return obj.get_name(self._lang())

    def get_description(self, obj):
        return obj.get_description(self._lang())


class MenuItemAdminSerializer(serializers.ModelSerializer):
    """Admin üçün — bütün dil sahələri göstərilir"""
    class Meta:
        model  = MenuItem
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    name  = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ["id", "name", "icon", "order", "items"]

    def _lang(self):
        return self.context.get("lang", "az")

    def get_name(self, obj):
        return obj.get_name(self._lang())

    def get_items(self, obj):
        qs = obj.items.filter(is_available=True) if self.context.get("available_only") else obj.items.all()
        return MenuItemSerializer(qs, many=True, context=self.context).data


class CategoryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = "__all__"


class DailySpecialSerializer(serializers.ModelSerializer):
    title       = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model  = DailySpecial
        fields = ["id", "title", "description", "original_price", "special_price", "valid_until"]

    def _lang(self):
        return self.context.get("lang", "az")

    def get_title(self, obj):
        return obj.get_title(self._lang())

    def get_description(self, obj):
        return obj.get_description(self._lang())


class DailySpecialAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DailySpecial
        fields = "__all__"


class RestaurantPublicSerializer(serializers.ModelSerializer):
    """QR skan olunanda müştəriyə göndərilən tam menyu"""
    name        = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    address     = serializers.SerializerMethodField()
    categories  = serializers.SerializerMethodField()
    specials    = serializers.SerializerMethodField()

    class Meta:
        model  = Restaurant
        fields = [
            "id", "name", "description", "phone",
            "whatsapp", "address", "logo", "cover_image",
            "wifi_password", "currency", "categories", "specials",
        ]

    def _lang(self):
        return self.context.get("lang", "az")

    def get_name(self, obj):        return obj.get_name(self._lang())
    def get_description(self, obj): return obj.get_description(self._lang())
    def get_address(self, obj):     return obj.get_address(self._lang())

    def get_categories(self, obj):
        qs = obj.categories.filter(is_active=True)
        return CategorySerializer(qs, many=True, context=self.context).data

    def get_specials(self, obj):
        qs = obj.specials.filter(is_active=True)
        return DailySpecialSerializer(qs, many=True, context=self.context).data


class RestaurantAdminSerializer(serializers.ModelSerializer):
    """Sahibkar paneli üçün — bütün sahələr + əlavə statistika"""
    total_items  = serializers.SerializerMethodField()
    total_views  = serializers.SerializerMethodField()
    owner_email  = serializers.SerializerMethodField()

    class Meta:
        model  = Restaurant
        fields = "__all__"

    def get_total_items(self, obj):
        return MenuItem.objects.filter(category__restaurant=obj).count()

    def get_total_views(self, obj):
        return obj.views.count()

    def get_owner_email(self, obj):
        return obj.owner.email if obj.owner else None


class WhatsAppOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WhatsAppOrder
        fields = ["id", "customer_phone", "message", "created_at", "is_notified"]


class OwnerRegisterSerializer(serializers.Serializer):
    """Yeni restoran sahibi qeydiyyatı"""
    username        = serializers.CharField(max_length=150)
    email           = serializers.EmailField()
    password        = serializers.CharField(min_length=8, write_only=True)
    restaurant_name = serializers.CharField(max_length=200)
    slug            = serializers.SlugField(max_length=100)
    phone           = serializers.CharField(max_length=30, required=False, allow_blank=True)
    whatsapp        = serializers.CharField(max_length=30, required=False, allow_blank=True)
