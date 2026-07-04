from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ─────────────────────────────────────────────────
SECRET_KEY    = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
DEBUG         = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost 127.0.0.1").split()

# ── Apps ─────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "menu",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF      = "config.urls"
WSGI_APPLICATION  = "config.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS"   : [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# ── Database ─────────────────────────────────────────────────
# Render.com pulsuz tier üçün SQLite (Postgres üçün aşağıya bax)
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME"  : BASE_DIR / "db.sqlite3",
    }}

# ── CORS ─────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000 http://127.0.0.1:5500 http://localhost:5500"
).split()
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # production-da False et

# CSRF
CSRF_TRUSTED_ORIGINS = [
    "https://qr-menu-ffqs.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ── Cloudinary ───────────────────────────────────────────────
import cloudinary
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
    api_key    = os.environ.get("CLOUDINARY_API_KEY", ""),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", ""),
    secure     = True,
)

# ── Twilio (WhatsApp) ────────────────────────────────────────
TWILIO_ACCOUNT_SID      = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN       = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER  = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

# ── Localisation ─────────────────────────────────────────────
LANGUAGE_CODE = "az"
TIME_ZONE     = "Asia/Baku"
USE_I18N      = True
USE_TZ        = True

# ── Static / Media ───────────────────────────────────────────
STATIC_URL    = "/static/"
STATIC_ROOT   = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── File upload limits ────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ── ABB Pay ──────────────────────────────────────────────────
ABB_PAY_USERNAME = os.environ.get("ABB_PAY_USERNAME", "")
ABB_PAY_PASSWORD = os.environ.get("ABB_PAY_PASSWORD", "")
ABB_PAY_GATEWAY  = os.environ.get("ABB_PAY_GATEWAY", "https://abb-test.gateway.az/payment/rest/")

# ── Security ─────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False  # production-da qapalı

# Brute force qoruması (django-axes)
INSTALLED_APPS += ["axes"]
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_FAILURE_LIMIT      = 10       # 10 yanlış cəhddən sonra blok
AXES_COOLOFF_TIME       = 1        # 1 saat blok
AXES_LOCKOUT_PARAMETERS = ["ip_address"]

# Security headers
SECURE_BROWSER_XSS_FILTER      = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"
SECURE_REFERRER_POLICY         = "same-origin"

# Production-da HTTPS məcburi
if not DEBUG:
    SECURE_SSL_REDIRECT         = True
    SESSION_COOKIE_SECURE       = True
    CSRF_COOKIE_SECURE          = True
    SECURE_HSTS_SECONDS         = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True