#  QR Menyu — V2 (Tam İşlək Sistem)

Django REST API + Vanilla JS Admin Panel  
Çoxdilli (AZ/RU/EN) · Cloudinary şəkillər · WhatsApp Bot · Render.com deploy

---

##  Yerli quraşdırma (localhost)

```bash
# 1. Layihə qovluğuna keç
cd qrmenu/backend

# 2. Virtual mühit yarat
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Asılılıqları quraşdır
pip install -r requirements.txt

# 4. .env faylı yarat
cp .env.example .env
# .env faylını öz məlumatlarınla doldur

# 5. DB migrate et
python manage.py migrate

# 6. Demo məlumatlar yükle
python manage.py seed_demo

# 7. Serveri işə sal
python manage.py runserver
```

---

## Giriş məlumatları (demo)

| Rol | İstifadəçi adı | Şifrə | Giriş yeri |
|-----|----------------|-------|-----------|
| Superadmin | `admin` | `admin123` | `/django-admin/` |
| Restoran sahibi | `kafe_seher` | `kafe123` | `frontend/v2/admin.html` |

---

## 🔗 URL-lər

| URL | Nədir |
|-----|-------|
| `/api/auth/login/` | Token almaq (POST) |
| `/api/auth/register/` | Yeni sahibkar (yalnız superadmin, POST) |
| `/api/auth/me/` | Cari istifadəçi məlumatı (GET) |
| `/api/menu/{slug}/` | Müştəri menyusu, `?lang=az\|ru\|en` (GET) |
| `/api/menu/{slug}/qr/` | SVG QR kod (GET) |
| `/api/upload/` | Cloudinary şəkil yükləmə (POST) |
| `/api/owner/restaurant/` | Öz restoranı (GET/PATCH) |
| `/api/owner/categories/` | Kateqoriyalar (GET/POST) |
| `/api/owner/categories/{id}/` | Kateqoriya detail (PATCH/DELETE) |
| `/api/owner/items/` | Elementlər (GET/POST) |
| `/api/owner/items/{id}/` | Element detail (GET/PATCH/DELETE) |
| `/api/owner/items/{id}/toggle/` | Var/yox toggle (PATCH) |
| `/api/owner/specials/` | Günün təklifi (GET/POST) |
| `/api/owner/specials/{id}/` | Təklif detail (PATCH/DELETE) |
| `/api/owner/analytics/` | Skan statistikası (GET) |
| `/api/owner/orders/` | WhatsApp sifarişlər (GET) |
| `/api/webhook/whatsapp/{slug}/` | Twilio webhook (GET/POST) |
| `/api/admin/restaurants/` | Bütün restoranlar (yalnız superadmin) |
| `/django-admin/` | Django admin paneli |

---

## Çoxdilli menyu

M�ştəri menyusunu istənilən dildə görmək üçün URL-ə `?lang=` parametri əlavə et:

```
/menu/kafe-seher/        → Azərbaycan dili (default)
/menu/kafe-seher/?lang=ru → Rus dili
/menu/kafe-seher/?lang=en → İngilis dili
```

Admin paneldə AZ/RU/EN tabları ilə hər dil üçün mətn daxil et.

---

## Cloudinary quraşdırması

1. [cloudinary.com](https://cloudinary.com) → pulsuz hesab aç
2. Dashboard-da `Cloud Name`, `API Key`, `API Secret` götür
3. `.env` faylına yaz:
```env
CLOUDINARY_CLOUD_NAME=dxxxxxx
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Admin paneldə şəkil yükləmə avtomatik işləyəcək.

---

## WhatsApp Bot quraşdırması

### 1. Twilio hesabı aç (pulsuz)
[twilio.com](https://twilio.com) → Sign up → Console

### 2. WhatsApp Sandbox aktiv et
Messaging → Try it out → Send a WhatsApp message

### 3. Webhook URL-i Twilio-ya daxil et
```
https://your-app.onrender.com/api/webhook/whatsapp/kafe-seher/
```
Twilio Console → Messaging → WhatsApp → Sandbox Settings →
"When a message comes in" sahəsinə bu URL-i yaz.

### 4. .env faylına əlavə et:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

M�ştəri restoranın WhatsApp nömrəsinə sifariş göndərəndə:
1. Sifariş DB-ə yazılır
2. Restoran sahibinə WhatsApp bildirişi gedir
3. Müştəriyə avtomatik "Qəbul edildi" cavabı gedir

---

## Render.com Deploy

### 1. GitHub repo yarat
```bash
git init
git add .
git commit -m "QR Menyu V2"
git remote add origin https://github.com/SENIN_ADIN/qr-menyu.git
git push -u origin main
```

### 2. Render.com-da deploy
- [render.com](https://render.com) → New → Web Service
- GitHub repo-nu qoş
- `render.yaml` avtomatik oxunacaq

### 3. Environment Variables-i Render dashboard-da əlavə et
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`
- `SECRET_KEY` (Render avtomatik generate edir)

### 4. Deploy sonrası superadmin yarat
Render → Shell tabından:
```bash
python manage.py createsuperuser
```

---

## Yeni müştəri (restoran) əlavə etmək

**Django admin vasitəsilə (tövsiyə):**
1. `/django-admin/` → Restoranlar → Əlavə et
2. Sahibi seç (əvvəlcə İstifadəçilər bölməsindən user yarat)
3. Slug, ad, telefon, WhatsApp daxil et → Saxla

**API vasitəsilə (superadmin tokeni ilə):**
```bash
curl -X POST https://your-app.onrender.com/api/auth/register/ \
  -H "Authorization: Token SUPERADMIN_TOKENI" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "restoran_lale",
    "email": "lale@example.com",
    "password": "güclü_şifrə",
    "restaurant_name": "Restoran Lalə",
    "slug": "restoran-lale",
    "phone": "+994501234567",
    "whatsapp": "+994501234567"
  }'
```

Cavabda `token` və `restaurant_slug` gəlir — bunları sahibkara ver.
