import json, os, requests
from django.shortcuts     import get_object_or_404
from django.contrib.auth.models import User
from django.db.models     import Count
from django.db.models.functions import TruncDate
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers  import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import qrcode, qrcode.image.svg
from io    import BytesIO
from django.http import HttpResponse
import cloudinary, cloudinary.uploader

from .models import Restaurant, Category, MenuItem, DailySpecial, WhatsAppOrder, MenuView
from .serializers import (
    RestaurantPublicSerializer, RestaurantAdminSerializer,
    CategorySerializer, CategoryAdminSerializer,
    MenuItemSerializer, MenuItemAdminSerializer,
    DailySpecialSerializer, DailySpecialAdminSerializer,
    WhatsAppOrderSerializer, OwnerRegisterSerializer,
)

SUPPORTED_LANGS = ("az", "ru", "en")


def get_lang(request):
    lang = request.GET.get("lang", "az").lower()
    return lang if lang in SUPPORTED_LANGS else "az"


# ═══════════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def owner_login(request):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "token": "...", "restaurant_slug": "..." }
    """
    from django.contrib.auth import authenticate
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "İstifadəçi adı və ya şifrə yanlışdır."}, status=400)
    token, _ = Token.objects.get_or_create(user=user)
    slug = ""
    try:
        slug = user.restaurant.slug
    except Exception:
        pass
    return Response({"token": token.key, "username": user.username, "restaurant_slug": slug})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def owner_register(request):
    """
    POST /api/auth/register/   (yalnız superadmin çağıra bilər)
    Yeni restoran sahibi + restoranını eyni anda yaradır.
    """
    ser = OwnerRegisterSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    d = ser.validated_data

    if User.objects.filter(username=d["username"]).exists():
        return Response({"detail": "Bu istifadəçi adı artıq mövcuddur."}, status=400)
    if Restaurant.objects.filter(slug=d["slug"]).exists():
        return Response({"detail": "Bu slug artıq mövcuddur."}, status=400)

    user = User.objects.create_user(
        username=d["username"],
        email=d.get("email", ""),
        password=d["password"],
    )
    restaurant = Restaurant.objects.create(
        owner    = user,
        name_az  = d["restaurant_name"],
        slug     = d["slug"],
        phone    = d.get("phone", ""),
        whatsapp = d.get("whatsapp", ""),
    )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token"            : token.key,
        "username"         : user.username,
        "restaurant_slug"  : restaurant.slug,
        "restaurant_id"    : str(restaurant.id),
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_me(request):
    """GET /api/auth/me/  — giriş etmiş sahibin öz məlumatları"""
    try:
        r = request.user.restaurant
        return Response({
            "username"         : request.user.username,
            "email"            : request.user.email,
            "restaurant_slug"  : r.slug,
            "restaurant_id"    : str(r.id),
            "restaurant_name"  : r.name_az,
        })
    except Restaurant.DoesNotExist:
        return Response({"detail": "Bu istifadəçinin restoranı yoxdur."}, status=404)


# ═══════════════════════════════════════════════════════════════
#  PUBLIC — QR SCAN
# ═══════════════════════════════════════════════════════════════

@api_view(["GET"])
@permission_classes([AllowAny])
def public_menu(request, slug):
    """
    GET /api/menu/<slug>/?lang=az|ru|en
    QR skan olunanda çağırılır. Menyu + analitika.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    lang       = get_lang(request)

    MenuView.objects.create(
        restaurant = restaurant,
        user_agent = request.META.get("HTTP_USER_AGENT", ""),
        lang       = lang,
    )
    ctx  = {"request": request, "lang": lang}
    data = RestaurantPublicSerializer(restaurant, context=ctx).data
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def qr_code_svg(request, slug):
    """GET /api/menu/<slug>/qr/ → SVG QR kod"""
    restaurant = get_object_or_404(Restaurant, slug=slug)
    menu_url   = request.build_absolute_uri(f"/menu/{slug}/")

    factory = qrcode.image.svg.SvgPathImage
    qr      = qrcode.QRCode(
        version         = 1,
        error_correction= qrcode.constants.ERROR_CORRECT_H,
        box_size        = 10,
        border          = 4,
        image_factory   = factory,
    )
    qr.add_data(menu_url)
    qr.make(fit=True)
    img    = qr.make_image()
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/svg+xml")


# ═══════════════════════════════════════════════════════════════
#  CLOUDINARY — ŞƏKIL YÜKLƏMƏ
# ═══════════════════════════════════════════════════════════════

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """
    POST /api/upload/
    Form-data: { "file": <şəkil>, "type": "logo"|"cover"|"item" }
    Returns: { "url": "https://res.cloudinary.com/..." }
    """
    file       = request.FILES.get("file")
    image_type = request.data.get("type", "item")

    if not file:
        return Response({"detail": "Fayl göndərilmədi."}, status=400)

    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        return Response({"detail": "Yalnız JPG, PNG və WEBP icazəlidir."}, status=400)

    if file.size > 5 * 1024 * 1024:
        return Response({"detail": "Fayl ölçüsü 5MB-dan çox ola bilməz."}, status=400)

    folder_map = {"logo": "qrmenu/logos", "cover": "qrmenu/covers", "item": "qrmenu/items"}
    folder     = folder_map.get(image_type, "qrmenu/items")

    try:
        result = cloudinary.uploader.upload(
            file,
            folder          = folder,
            resource_type   = "image",
            transformation  = [{"width": 800, "crop": "limit", "quality": "auto"}],
        )
        return Response({"url": result["secure_url"]})
    except Exception as e:
        return Response({"detail": f"Yükləmə xətası: {str(e)}"}, status=500)


# ═══════════════════════════════════════════════════════════════
#  OWNER — ÖZ RESTORANINI İDARƏ ETMƏSİ
# ═══════════════════════════════════════════════════════════════

def get_owner_restaurant(user):
    """Sahibin restoranını qaytarır, yoxdursa 404"""
    return get_object_or_404(Restaurant, owner=user)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def owner_restaurant(request):
    """
    GET  /api/owner/restaurant/  → öz restoranının məlumatları
    PATCH /api/owner/restaurant/ → yeniləmə (ad, telefon, WiFi, logo URL...)
    """
    restaurant = get_owner_restaurant(request.user)
    if request.method == "GET":
        return Response(RestaurantAdminSerializer(restaurant).data)

    allowed = [
        "name_az","name_ru","name_en",
        "description_az","description_ru","description_en",
        "phone","whatsapp",
        "address_az","address_ru","address_en",
        "logo","cover_image","wifi_password","currency","is_active",
    ]
    for field in allowed:
        if field in request.data:
            setattr(restaurant, field, request.data[field])
    restaurant.save()
    return Response(RestaurantAdminSerializer(restaurant).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def owner_categories(request):
    """GET/POST /api/owner/categories/"""
    restaurant = get_owner_restaurant(request.user)
    if request.method == "GET":
        cats = restaurant.categories.all()
        return Response(CategoryAdminSerializer(cats, many=True).data)

    data = request.data.copy()
    data["restaurant"] = str(restaurant.id)
    ser  = CategoryAdminSerializer(data=data)
    if ser.is_valid():
        ser.save(restaurant=restaurant)
        return Response(ser.data, status=201)
    return Response(ser.errors, status=400)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def owner_category_detail(request, pk):
    """PATCH/DELETE /api/owner/categories/<pk>/"""
    restaurant = get_owner_restaurant(request.user)
    cat        = get_object_or_404(Category, pk=pk, restaurant=restaurant)
    if request.method == "DELETE":
        cat.delete()
        return Response(status=204)
    ser = CategoryAdminSerializer(cat, data=request.data, partial=True)
    if ser.is_valid():
        ser.save()
        return Response(ser.data)
    return Response(ser.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def owner_items(request):
    """GET/POST /api/owner/items/?category=<id>"""
    restaurant = get_owner_restaurant(request.user)
    qs         = MenuItem.objects.filter(category__restaurant=restaurant)
    cat_id     = request.GET.get("category")
    if cat_id:
        qs = qs.filter(category_id=cat_id)

    if request.method == "GET":
        return Response(MenuItemAdminSerializer(qs, many=True).data)

    # Kateqoriyanın bu sahibə aid olduğunu yoxla
    cat_id_post = request.data.get("category")
    get_object_or_404(Category, pk=cat_id_post, restaurant=restaurant)

    ser = MenuItemAdminSerializer(data=request.data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data, status=201)
    return Response(ser.errors, status=400)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def owner_item_detail(request, pk):
    """GET/PATCH/DELETE /api/owner/items/<pk>/"""
    restaurant = get_owner_restaurant(request.user)
    item       = get_object_or_404(MenuItem, pk=pk, category__restaurant=restaurant)
    if request.method == "GET":
        return Response(MenuItemAdminSerializer(item).data)
    if request.method == "DELETE":
        item.delete()
        return Response(status=204)
    ser = MenuItemAdminSerializer(item, data=request.data, partial=True)
    if ser.is_valid():
        ser.save()
        return Response(ser.data)
    return Response(ser.errors, status=400)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_item(request, pk):
    """PATCH /api/owner/items/<pk>/toggle/ — mövcudluğu dəyişir"""
    restaurant = get_owner_restaurant(request.user)
    item       = get_object_or_404(MenuItem, pk=pk, category__restaurant=restaurant)
    item.is_available = not item.is_available
    item.save()
    return Response({"id": item.pk, "is_available": item.is_available})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def owner_specials(request):
    """GET/POST /api/owner/specials/"""
    restaurant = get_owner_restaurant(request.user)
    if request.method == "GET":
        qs = restaurant.specials.all()
        return Response(DailySpecialAdminSerializer(qs, many=True).data)
    ser = DailySpecialAdminSerializer(data=request.data)
    if ser.is_valid():
        ser.save(restaurant=restaurant)
        return Response(ser.data, status=201)
    return Response(ser.errors, status=400)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def owner_special_detail(request, pk):
    """PATCH/DELETE /api/owner/specials/<pk>/"""
    restaurant = get_owner_restaurant(request.user)
    special    = get_object_or_404(DailySpecial, pk=pk, restaurant=restaurant)
    if request.method == "DELETE":
        special.delete()
        return Response(status=204)
    ser = DailySpecialAdminSerializer(special, data=request.data, partial=True)
    if ser.is_valid():
        ser.save()
        return Response(ser.data)
    return Response(ser.errors, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_analytics(request):
    """
    GET /api/owner/analytics/
    Bu ay, bu həftə, bu gün skan sayı + həftəlik qrafik
    """
    from django.utils import timezone
    from datetime import timedelta

    restaurant = get_owner_restaurant(request.user)
    now        = timezone.now()
    views      = restaurant.views.all()

    daily = (
        views.filter(scanned_at__gte=now - timedelta(days=30))
             .annotate(date=TruncDate("scanned_at"))
             .values("date")
             .annotate(count=Count("id"))
             .order_by("date")
    )
    lang_breakdown = (
        views.values("lang").annotate(count=Count("id")).order_by("-count")
    )
    return Response({
        "total_views"    : views.count(),
        "today_views"    : views.filter(scanned_at__date=now.date()).count(),
        "this_week_views": views.filter(scanned_at__gte=now - timedelta(days=7)).count(),
        "this_month_views": views.filter(scanned_at__gte=now - timedelta(days=30)).count(),
        "daily_30"       : list(daily),
        "lang_breakdown" : list(lang_breakdown),
        "total_items"    : MenuItem.objects.filter(category__restaurant=restaurant).count(),
        "total_categories": restaurant.categories.count(),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_orders(request):
    """GET /api/owner/orders/ — WhatsApp sifarişlər"""
    restaurant = get_owner_restaurant(request.user)
    orders     = restaurant.orders.all()[:50]
    return Response(WhatsAppOrderSerializer(orders, many=True).data)


# ═══════════════════════════════════════════════════════════════
#  WHATSAPP WEBHOOK
# ═══════════════════════════════════════════════════════════════

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def whatsapp_webhook(request, slug):
    """
    GET  /api/webhook/whatsapp/<slug>/  → Twilio doğrulama
    POST /api/webhook/whatsapp/<slug>/  → Gələn mesaj

    Müştəri restoranın WhatsApp nömrəsinə mesaj göndərəndə
    bu endpoint çağırılır. Sifarişi DB-ə yazır + sahibə bildiriş göndərir.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug)

    if request.method == "GET":
        return Response({"status": "webhook aktiv"})

    # Twilio formatı
    body   = request.data.get("Body", "").strip()
    caller = request.data.get("From", "").replace("whatsapp:", "")

    if not body:
        return Response({"status": "boş mesaj"})

    # Sifarişi saxla
    order = WhatsAppOrder.objects.create(
        restaurant     = restaurant,
        customer_phone = caller,
        message        = body,
    )

    # Sahibə Twilio vasitəsilə WhatsApp bildirişi göndər
    _send_owner_notification(restaurant, order)

    # Müştəriyə avtomatik cavab (Twilio TwiML)
    menu_url = f"https://yourdomain.com/menu/{slug}/"
    twiml    = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>
    Sifariş qəbul edildi! Tezliklə əlaqə saxlayacağıq. 🍽️
    Menyumuza baxmaq üçün: {menu_url}
  </Message>
</Response>"""
    return HttpResponse(twiml, content_type="application/xml")


def _send_owner_notification(restaurant, order):
    """Twilio API vasitəsilə sahibə bildiriş göndərir"""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")
    to_number   = f"whatsapp:{restaurant.whatsapp}"

    if not all([account_sid, auth_token, from_number, restaurant.whatsapp]):
        return  # Twilio konfiqurasiya edilməyibsə, keç

    try:
        from twilio.rest import Client
        client  = Client(account_sid, auth_token)
        message = (
            f"🔔 Yeni sifariş — {restaurant.name_az}\n"
            f"Müştəri: {order.customer_phone}\n"
            f"Sifariş: {order.message}\n"
            f"Vaxt: {order.created_at:%d.%m.%Y %H:%M}"
        )
        client.messages.create(body=message, from_=from_number, to=to_number)
        order.is_notified = True
        order.save()
    except Exception as e:
        print(f"WhatsApp bildiriş xətası: {e}")


# ═══════════════════════════════════════════════════════════════
#  SUPERADMIN — bütün restoranlar
# ═══════════════════════════════════════════════════════════════

@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_all_restaurants(request):
    """GET /api/admin/restaurants/ — yalnız superadmin"""
    qs  = Restaurant.objects.all().select_related("owner")
    ser = RestaurantAdminSerializer(qs, many=True)
    return Response(ser.data)