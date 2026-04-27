"""
Django settings for scan2serve project.
"""

from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# Create logs folder automatically
os.makedirs(BASE_DIR / "logs", exist_ok=True)

# SECURITY
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG")

ALLOWED_HOSTS = [
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]

# MEDIA FILES
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ESP32 / API KEYS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
KITCHEN_ESP32_IP = os.getenv("KITCHEN_ESP32_IP")
ESP32_SECRET_TOKEN = os.getenv("ESP32_SECRET_TOKEN")

# APPS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",

    "users",
    "menu",
    "tables",
    "orders",
]

# MIDDLEWARE
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "scan2serve.middleware.UserActivityMiddleware",
    "scan2serve.middleware.LoginAttemptMiddleware",
]

ROOT_URLCONF = "scan2serve.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "scan2serve.wsgi.application"

# DATABASE
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}

# AUTH
AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# LANGUAGE / TIME
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Colombo"
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST FRAMEWORK
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),

    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],

    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "120/min",
        "login_anon": "5/min",
        "login_user": "10/min",
        "register": "3/min",
        "password_reset": "3/min",
        "order_create": "20/min",
        "chatbot": "15/min",
    },
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

# CORS
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",

    # Add your deployed frontend URL here later
    # Example:
    # "https://your-frontend-name.onrender.com",
]

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")

# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "activity": {
            "format": "{asctime} | {levelname} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "activity",
        },

        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/app.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "activity",
        },

        "user_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/user_activity.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "activity",
        },

        "login_attempt_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/user_login_attempt.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "activity",
        },
    },

    "loggers": {
        "myapp": {
            "handlers": ["console", "app_file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },

        "user_activity": {
            "handlers": ["console", "user_file"],
            "level": "INFO",
            "propagate": False,
        },

        "login_attempt": {
            "handlers": ["console", "login_attempt_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
