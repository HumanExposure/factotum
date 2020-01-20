import os

from django.contrib.messages import constants as messages

from factotum.environment import env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = env.DEBUG
SECRET_KEY = env.SECRET_KEY
ALLOWED_HOSTS = env.ALLOWED_HOSTS

# IPs allowed to see django-debug-toolbar output
INTERNAL_IPS = ("127.0.0.1",)

FILE_UPLOAD_MAX_MEMORY_SIZE = int(env.MAX_UPLOAD_SIZE)
DATA_UPLOAD_MAX_MEMORY_SIZE = int(env.MAX_UPLOAD_SIZE)

INSTALLED_APPS = [
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dashboard.apps.DashboardConfig",
    "feedback.apps.FeedbackConfig",
    "api.apps.ApiConfig",
    "bootstrap_datepicker_plus",
    "widget_tweaks",
    "django.contrib.humanize",
    "factotum",
    "debug_toolbar",
    "taggit",
    "taggit_labels",
    "django_extensions",
    "elastic.apps.ElasticConfig",
    "bulkformsets.apps.BulkFormSetsConfig",
    "docs",
    "celery_usertask",
    "celery_filetask",
    "celery_formtask",
    "celery_djangotest",
    "celery_resultsview",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "crum.CurrentRequestUserMiddleware",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

ROOT_URLCONF = "factotum.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "factotum.db",
        "NAME": env.SQL_DATABASE,
        "USER": env.SQL_USER,
        "PASSWORD": env.SQL_PASSWORD,
        "HOST": env.SQL_HOST,
        "PORT": env.SQL_PORT,
    }
}
if env.QUERY_LOG_DATABASE != env.SQL_DATABASE:
    DATABASES["querylogdb"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env.QUERY_LOG_DATABASE,
        "USER": env.SQL_USER,
        "PASSWORD": env.SQL_PASSWORD,
        "HOST": env.SQL_HOST,
        "PORT": env.SQL_PORT,
    }
DATABASE_ROUTERS = ["factotum.routers.QueryLogRouter"]

ELASTICSEARCH = {
    "default": {
        "HOSTS": [env.ELASTICSEARCH_HOST + ":" + env.ELASTICSEARCH_PORT],
        "INDEX": "dashboard",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{env.REDIS_HOST}:{env.REDIS_PORT}/{env.REDIS_CACHE_DATABASE}",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = True
USE_TZ = False

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "collected_static")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

LOGIN_REDIRECT_URL = "index"
LOGIN_URL = "login"

TAGGIT_CASE_INSENSITIVE = True

MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

DOCS_ROOT = os.path.join(BASE_DIR, "docs/_build/html")

EXTRA = 1

TEST_BROWSER = "chrome"
CHROMEDRIVER_PATH = env.CHROMEDRIVER_PATH

CELERY_BROKER_URL = (
    f"redis://{env.REDIS_HOST}:{env.REDIS_PORT}/{env.REDIS_CELERY_DATABASE}"
)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_FILETASK_ROOT = os.path.join(BASE_DIR, "celeryfiles")

LOGGING = {
    "version": 1,
    "filters": {"test_filter": {"()": "factotum.logging.TestFilter"}},
    "formatters": {
        "console": {
            "format": "%(asctime)s [%(levelname)s] %(message)s",
            "datefmt": "[%d/%b/%Y %H:%M:%S]",
            "class": "logging.Formatter",
        },
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] [INFO] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
            "filters": ["test_filter"],
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
