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
    user = authenticate(request=request, username=username, password=password)
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
    GET /api/menu/<slug>/?lang=az|ru|en&masa=3
    QR skan olunanda çağırılır. Menyu məlumatlarını qaytarır.
    """
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    lang       = get_lang(request)

    # Masa parametri gəlirsə — masanın mövcud olduğunu yoxla
    masa_number = request.GET.get("masa")
    if masa_number:
        from .models import Table
        table_exists = Table.objects.filter(
            restaurant=restaurant,
            number=masa_number,
            is_active=True
        ).exists()
        if not table_exists:
            return Response({
                "error": "table_deleted",
                "detail": "Bu masa artıq mövcud deyil. Zəhmət olmasa ofisiantı çağırın."
            }, status=404)

    # Analitika artıq register_scan-da yazılır — burada yazmırıq
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
        # Dizayn sahələri
        "theme","accent_color","bg_color","surface_color",
        "text_color","font_family","menu_layout",
        "show_prices","show_images","border_radius",
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


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auto_translate(request):
    """
    POST /api/translate/
    Body: { "text": "Türk qəhvəsi", "from": "az", "to": ["ru", "en"] }
    Returns: { "ru": "Турецкий кофе", "en": "Turkish Coffee" }
    """
    text      = request.data.get("text", "").strip()
    from_lang = request.data.get("from", "az")
    to_langs  = request.data.get("to", ["ru", "en"])

    if not text:
        return Response({"detail": "Mətn boşdur."}, status=400)

    # Xüsusi isimlər — bu adlar tərcümə edilmir, olduğu kimi saxlanılır
    PROPER_NOUNS = {
        "dolma", "plov", "lavangi", "levengi", "dovga", "düşbərə", "dushbara",
        "paklava", "paklavа", "şəkərbura", "shekerbura", "qutab", "kutab",
        "saj", "kebab", "lula", "lülə", "tikə", "tike", "basturma",
        "lahmacun", "lavash", "lavəş", "ayran", "narsharab", "narşərab",
        "sumakh", "sumaq", "baklava", "doner", "döner", "shawarma", "şavarma",
        "pilaf", "bozbash", "bozbaş", "piti", "kufta", "küftə",
    }

    if text.lower().strip() in PROPER_NOUNS:
        # Xüsusi isimdir — bütün dillər üçün eyni mətni qaytar
        return Response({lang: text for lang in to_langs})

    results = {}
    for lang in to_langs:
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": from_lang,
                "tl": lang,
                "dt": "t",
                "q": text,
            }
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            translated = "".join([item[0] for item in data[0] if item[0]])
            results[lang] = translated
        except Exception as e:
            results[lang] = ""
            print(f"Tərcümə xətası ({lang}): {e}")

    return Response(results)


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


# ═══════════════════════════════════════════════════════════════
#  MASA (TABLE) MANAGEMENT
# ═══════════════════════════════════════════════════════════════

from .models import Table, Order, QRScan


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_tables(request):
    """GET /api/owner/tables/ — bütün masalar"""
    restaurant = get_owner_restaurant(request.user)
    tables = restaurant.tables.all()
    data = [{
        "id": t.id,
        "number": t.number,
        "label": t.label,
        "is_active": t.is_active,
        "menu_url": request.build_absolute_uri(f"/menu/{restaurant.slug}/?masa={t.number}"),
    } for t in tables]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_table(request):
    """POST /api/owner/tables/create/ — yeni masa yarat"""
    restaurant = get_owner_restaurant(request.user)
    number = request.data.get("number")
    label  = request.data.get("label", "")
    if not number:
        return Response({"detail": "Masa nömrəsi vacibdir."}, status=400)
    if Table.objects.filter(restaurant=restaurant, number=number).exists():
        return Response({"detail": f"Masa {number} artıq mövcuddur."}, status=400)
    table = Table.objects.create(
        restaurant=restaurant, number=number, label=label, secret_code="STATIC"
    )
    return Response({
        "id": table.id, "number": table.number,
        "label": table.label,
        "menu_url": f"/menu/{restaurant.slug}/?masa={table.number}",
    }, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def regenerate_table_code(request, table_id):
    """POST /api/owner/tables/<id>/regenerate/ — kodu yenilə (ofisant dəyişdirir)"""
    restaurant = get_owner_restaurant(request.user)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    table.regenerate_code()

    # Bu masanın bütün aktiv sessionlarını sil — köhnə QR artıq işləməsin
    QRScan.objects.filter(table=table).delete()

    return Response({
        "id": table.id, "number": table.number,
        "secret_code": table.secret_code,
        "menu_url": f"/menu/{restaurant.slug}/?masa={table.number}&kod={table.secret_code}",
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_table(request, table_id):
    """DELETE /api/owner/tables/<id>/"""
    restaurant = get_owner_restaurant(request.user)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    table.delete()
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def table_qr_svg(request, table_id):
    """GET /api/owner/tables/<id>/qr/ — masa üçün QR SVG"""
    restaurant = get_owner_restaurant(request.user)
    table = get_object_or_404(Table, id=table_id, restaurant=restaurant)
    menu_url = request.build_absolute_uri(
        f"/menu/{restaurant.slug}/?masa={table.number}"
    )
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=4, image_factory=factory)
    qr.add_data(menu_url)
    qr.make(fit=True)
    img = qr.make_image()
    buffer = BytesIO()
    img.save(buffer)
    svg_content = buffer.getvalue()
    response = HttpResponse(svg_content, content_type="image/svg+xml")
    response["Content-Disposition"] = f'attachment; filename="masa-{table.number}.svg"'
    response["Access-Control-Allow-Origin"] = "*"
    return response


# ═══════════════════════════════════════════════════════════════
#  QR SCAN SESSION (vaxt limiti üçün)
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def register_scan(request, slug):
    from django.utils import timezone
    from datetime import timedelta
    import uuid

    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    masa_number = request.data.get("masa")
    lang = request.data.get("lang", "az")

    table = None
    if masa_number:
        table = Table.objects.filter(
            restaurant=restaurant, number=masa_number, is_active=True
        ).first()
        # Masa silinibsə — sifariş verilməsin
        if not table:
            return Response({
                "valid": False,
                "detail": "Bu masa artıq mövcud deyil. Zəhmət olmasa ofisiantı çağırın."
            }, status=400)

    session_id = str(uuid.uuid4())
    now = timezone.now()
    expires_at = now + timedelta(minutes=45)

    QRScan.objects.create(
        restaurant=restaurant,
        table=table,
        table_number=masa_number,
        session_id=session_id,
        expires_at=expires_at,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        lang=lang,
    )

    # Analitika — eyni cihazdan 1 saatda yalnız 1 view yazılır
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    already_counted = QRScan.objects.filter(
        restaurant=restaurant,
        user_agent=user_agent,
        scanned_at__gte=now - timedelta(hours=1)
    ).exclude(session_id=session_id).exists()

    if not already_counted:
        MenuView.objects.create(
            restaurant=restaurant,
            user_agent=user_agent,
            lang=lang,
        )

    return Response({
        "valid": True,
        "session_id": session_id,
        "expires_at": expires_at.isoformat(),
        "table_number": masa_number,
        "restaurant": restaurant.name_az,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_session(request):
    """
    GET /api/session/verify/?session_id=xxx
    Session hələ etibarlıdırmı yoxla
    """
    from django.utils import timezone
    session_id = request.GET.get("session_id")
    if not session_id:
        return Response({"valid": False, "detail": "Session ID yoxdur."})
    try:
        scan = QRScan.objects.get(session_id=session_id)
        is_valid = timezone.now() < scan.expires_at
        remaining = max(0, int((scan.expires_at - timezone.now()).total_seconds()))
        return Response({
            "valid": is_valid,
            "expires_at": scan.expires_at.isoformat(),
            "remaining_seconds": remaining,
            "table_number": scan.table_number,
        })
    except QRScan.DoesNotExist:
        return Response({"valid": False, "detail": "Session tapılmadı."})


# ═══════════════════════════════════════════════════════════════
#  SİFARİŞ (ORDER)
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def place_order(request, slug):
    """
    POST /api/menu/<slug>/order/
    Body: {
      "session_id": "...",
      "table_number": 5,
      "customer_name": "Anar",
      "customer_phone": "+99450...",
      "items": [{"id": 1, "name": "Plov", "price": 7.00, "qty": 2}],
      "note": "Az duzlu olsun",
      "payment_method": "abb_pay"
    }
    """
    from django.utils import timezone

    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)

    # Session yoxla
    session_id = request.data.get("session_id")
    if session_id:
        try:
            scan = QRScan.objects.get(session_id=session_id)
            if timezone.now() > scan.expires_at:
                return Response({
                    "error": "timeout",
                    "detail": "Sifariş müddəti bitib (45 dəq). Zəhmət olmasa QR-ı yenidən skan edin."
                }, status=400)
            # Masa kodu dəyişibsə session-u etibarsız say
            if scan.table and scan.table_number:
                current_table = Table.objects.filter(
                    restaurant=restaurant, number=scan.table_number
                ).first()
                if current_table and not QRScan.objects.filter(
                    session_id=session_id, table=current_table
                ).exists():
                    return Response({
                        "error": "invalid_session",
                        "detail": "Masa kodu dəyişdirilib. Zəhmət olmasa QR-ı yenidən skan edin."
                    }, status=400)
        except QRScan.DoesNotExist:
            return Response({
                "error": "invalid_session",
                "detail": "Sifariş sessiyası tapılmadı. QR-ı yenidən skan edin."
            }, status=400)

    items = request.data.get("items", [])
    if not items:
        return Response({"detail": "Sifariş boşdur."}, status=400)

    total = sum(float(i.get("price", 0)) * int(i.get("qty", 1)) for i in items)
    table_number = request.data.get("table_number")
    table = None
    if table_number:
        table = Table.objects.filter(restaurant=restaurant, number=table_number).first()

    order = Order.objects.create(
        restaurant     = restaurant,
        table          = table,
        table_number   = table_number,
        customer_name  = request.data.get("customer_name", ""),
        customer_phone = request.data.get("customer_phone", ""),
        items_json     = items,
        note           = request.data.get("note", ""),
        total_price    = total,
        payment_method = request.data.get("payment_method", "cash"),
        scan_time      = timezone.now(),
    )

    # Sahibə WhatsApp bildirişi göndər
    _notify_owner_new_order(restaurant, order)

    # ABB Pay seçilibsə ödəniş linki yarat
    payment_url = None
    if order.payment_method == "abb_pay":
        payment_url = _init_abb_payment(order, request)

    return Response({
        "order_id": order.id,
        "status": order.status,
        "total": str(order.total_price),
        "payment_url": payment_url,
        "message": "Sifarişiniz qəbul edildi! Tezliklə hazırlanacaq. 🍽️",
    }, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
def order_status(request, order_id):
    """GET /api/order/<id>/status/ — sifariş statusu"""
    order = get_object_or_404(Order, id=order_id)
    return Response({
        "id": order.id,
        "status": order.status,
        "status_display": order.get_status_display(),
        "total": str(order.total_price),
        "payment_status": order.payment_status,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def owner_orders_list(request):
    """GET /api/owner/orders/ — bütün sifarişlər (real vaxtda)"""
    restaurant = get_owner_restaurant(request.user)
    status_filter = request.GET.get("status")
    orders = restaurant.orders.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    data = [{
        "id": o.id,
        "table_number": o.table_number,
        "customer_name": o.customer_name,
        "customer_phone": o.customer_phone,
        "items": o.items_json,
        "note": o.note,
        "total": str(o.total_price),
        "status": o.status,
        "status_display": o.get_status_display(),
        "payment_method": o.payment_method,
        "payment_status": o.payment_status,
        "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
    } for o in orders[:100]]
    return Response(data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """PATCH /api/owner/orders/<id>/status/ — statusu dəyiş"""
    restaurant = get_owner_restaurant(request.user)
    order = get_object_or_404(Order, id=order_id, restaurant=restaurant)
    new_status = request.data.get("status")
    valid = [s[0] for s in Order.STATUS_CHOICES]
    if new_status not in valid:
        return Response({"detail": f"Yanlış status. Mümkünlər: {valid}"}, status=400)
    order.status = new_status
    order.save()
    # Müştəriyə WhatsApp bildirişi
    _notify_customer_status(order)
    return Response({"id": order.id, "status": order.status, "status_display": order.get_status_display()})


def _notify_owner_new_order(restaurant, order):
    """Sahibə yeni sifariş bildirişi göndər"""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

    if not all([account_sid, auth_token, from_number, restaurant.whatsapp]):
        return

    items_text = "\n".join([
        f"  • {i.get('name','?')} x{i.get('qty',1)} — {float(i.get('price',0))*int(i.get('qty',1)):.2f} AZN"
        for i in order.items_json
    ])
    message = (
        f"🔔 YENİ SİFARİŞ #{order.id}\n"
        f"🪑 Masa: {order.table_number or '—'}\n"
        f"👤 Müştəri: {order.customer_name or '—'}\n"
        f"📋 Sifariş:\n{items_text}\n"
        f"💰 Cəmi: {order.total_price} AZN\n"
        f"💳 Ödəniş: {order.get_payment_method_display()}\n"
        f"📝 Qeyd: {order.note or '—'}\n"
        f"⏰ Vaxt: {order.created_at.strftime('%H:%M')}"
    )
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_number,
            to=f"whatsapp:{restaurant.whatsapp}"
        )
        order.is_notified = True
        order.save()
    except Exception as e:
        print(f"Twilio xətası: {e}")


def _notify_customer_status(order):
    """Müştəriyə status bildirişi göndər"""
    if not order.customer_phone:
        return
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")
    if not all([account_sid, auth_token, from_number]):
        return
    status_msgs = {
        "confirmed": "✅ Sifarişiniz təsdiqləndi!",
        "preparing": "👨‍🍳 Sifarişiniz hazırlanır...",
        "ready": "🔔 Sifarişiniz hazırdır! Zəhmət olmasa masaya baxın.",
        "paid": "💚 Ödəniş qəbul edildi. Təşəkkür edirik!",
        "cancelled": "❌ Sifarişiniz ləğv edildi. Ətraflı məlumat üçün ofisiantı çağırın.",
    }
    msg = status_msgs.get(order.status)
    if not msg:
        return
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        client.messages.create(
            body=f"{msg}\nSifariş #{order.id} — {order.total_price} AZN",
            from_=from_number,
            to=f"whatsapp:{order.customer_phone}"
        )
    except Exception as e:
        print(f"Müştəri bildiriş xətası: {e}")


# ═══════════════════════════════════════════════════════════════
#  ABB PAY İNTEQRASİYASI
# ═══════════════════════════════════════════════════════════════

def _init_abb_payment(order, request):
    """
    ABB Pay ödəniş sessiyası yaradır.
    Sənəd: https://developers.abb.az/
    Test mühiti: https://abb-test.gateway.az/payment/rest/
    """
    ABB_USERNAME = os.environ.get("ABB_PAY_USERNAME", "")
    ABB_PASSWORD = os.environ.get("ABB_PAY_PASSWORD", "")
    ABB_GATEWAY  = os.environ.get("ABB_PAY_GATEWAY", "https://abb-test.gateway.az/payment/rest/")

    if not all([ABB_USERNAME, ABB_PASSWORD]):
        return None  # ABB konfiqurasiya edilməyibsə keç

    return_url = request.build_absolute_uri(f"/api/payment/abb/callback/?order_id={order.id}")

    try:
        resp = requests.post(f"{ABB_GATEWAY}register.do", data={
            "userName"   : ABB_USERNAME,
            "password"   : ABB_PASSWORD,
            "orderNumber": str(order.id),
            "amount"     : int(float(order.total_price) * 100),  # qəpik cinsindən
            "currency"   : "944",  # AZN ISO kodu
            "returnUrl"  : return_url,
            "description": f"QR Menyu sifariş #{order.id} — Masa {order.table_number}",
            "language"   : "az",
        }, timeout=10)
        data = resp.json()
        if data.get("errorCode") == "0":
            order.abb_transaction_id = data.get("orderId", "")
            order.payment_status = "pending"
            order.save()
            return data.get("formUrl")  # Müştərini bu URL-ə yönləndir
        else:
            print(f"ABB Pay xətası: {data.get('errorMessage')}")
            return None
    except Exception as e:
        print(f"ABB Pay bağlantı xətası: {e}")
        return None


@csrf_exempt
@api_view(["GET"])
@permission_classes([AllowAny])
def abb_payment_callback(request):
    """
    GET /api/payment/abb/callback/?order_id=<id>&orderId=<abb_id>
    ABB Pay ödənişdən sonra müştərini buraya yönləndirir.
    """
    order_id = request.GET.get("order_id")
    abb_order_id = request.GET.get("orderId")

    if not order_id:
        return HttpResponse("Sifariş tapılmadı.", status=400)

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Sifariş tapılmadı.", status=404)

    # ABB-dən ödəniş statusunu yoxla
    ABB_USERNAME = os.environ.get("ABB_PAY_USERNAME", "")
    ABB_PASSWORD = os.environ.get("ABB_PAY_PASSWORD", "")
    ABB_GATEWAY  = os.environ.get("ABB_PAY_GATEWAY", "https://abb-test.gateway.az/payment/rest/")

    try:
        resp = requests.post(f"{ABB_GATEWAY}getOrderStatus.do", data={
            "userName": ABB_USERNAME,
            "password": ABB_PASSWORD,
            "orderId" : abb_order_id or order.abb_transaction_id,
            "language": "az",
        }, timeout=10)
        data = resp.json()
        # orderStatus: 2 = uğurlu ödəniş
        if data.get("orderStatus") == 2:
            order.payment_status = "paid"
            order.status = "paid"
            order.save()
            _notify_owner_new_order(order.restaurant, order)
            return HttpResponse("""
                <html><body style="font-family:sans-serif;text-align:center;padding:40px">
                <h2>✅ Ödəniş uğurla tamamlandı!</h2>
                <p>Sifariş #{} — {} AZN</p>
                <p>Masa: {}</p>
                <script>setTimeout(()=>window.close(),3000)</script>
                </body></html>
            """.format(order.id, order.total_price, order.table_number))
        else:
            order.payment_status = "failed"
            order.save()
            return HttpResponse("""
                <html><body style="font-family:sans-serif;text-align:center;padding:40px">
                <h2>❌ Ödəniş uğursuz oldu</h2>
                <p>Zəhmət olmasa yenidən cəhd edin və ya nağd ödəyin.</p>
                </body></html>
            """)
    except Exception as e:
        print(f"ABB callback xətası: {e}")
        return HttpResponse("Xəta baş verdi.", status=500)


# ═══════════════════════════════════════════════════════════════
#  RATE LIMITING MIDDLEWARE (DDoS əleyhinə)
# ═══════════════════════════════════════════════════════════════
# views.py-da order və scan endpoint-lərinə rate limit əlavə et

from django.core.cache import cache

def check_rate_limit(ip, key, limit=30, window=60):
    """
    IP üzrə rate limiting.
    limit: icazə verilən maksimum request sayı
    window: saniyə cinsindən zaman pəncərəsi
    """
    cache_key = f"ratelimit:{key}:{ip}"
    count = cache.get(cache_key, 0)
    if count >= limit:
        return False  # limitə çatıb
    cache.set(cache_key, count + 1, window)
    return True


def get_client_ip(request):
    """Real IP-ni al (proxy arxasında da işləyir)"""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")