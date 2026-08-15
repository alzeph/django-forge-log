import os

SECRET_KEY = "test-secret-key"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework",
    "forge_log",
    "tests.testapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "forge_log.middleware.RequestContextMiddleware",
]

DB_BACKEND = os.environ.get("FORGE_LOG_TEST_DB", "sqlite")

if DB_BACKEND == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("FORGE_LOG_PG_NAME", "django_forge_log"),
            "USER": os.environ.get("FORGE_LOG_PG_USER", "django_forge_log"),
            "PASSWORD": os.environ.get("FORGE_LOG_PG_PASSWORD", "django_forge_log"),
            "HOST": os.environ.get("FORGE_LOG_PG_HOST", "localhost"),
            "PORT": os.environ.get("FORGE_LOG_PG_PORT", "5432"),
        }
    }
elif DB_BACKEND == "mysql":
    # "localhost" force le client MySQL à utiliser un socket Unix local
    # plutôt que TCP, même avec un PORT explicite : on force donc 127.0.0.1.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("FORGE_LOG_MYSQL_NAME", "django_forge_log"),
            "USER": os.environ.get("FORGE_LOG_MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("FORGE_LOG_MYSQL_PASSWORD", "django_forge_log"),
            "HOST": os.environ.get("FORGE_LOG_MYSQL_HOST", "127.0.0.1"),
            "PORT": os.environ.get("FORGE_LOG_MYSQL_PORT", "3306"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

FORGE_LOG = {
    "WRITE_BACKEND": "sync",
}

USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "tests.urls"
