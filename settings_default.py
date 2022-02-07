"""
Django settings for siddata_backend project with default values.
Fit file to your system an rename to settings.py

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import sys


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(BASE_DIR, 'docs/source'))
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

ROOT_URLCONF = 'backend.urls'

# Server base URL
BASE_URL = "http://localhost:8000"

# Base url to serve media files
MEDIA_URL = "media/"

# Path where media is stored
MEDIA_ROOT = os.path.join(BASE_DIR, 'siddata_backend/media')

# Path to static image files
IMAGE_FILE_DIR = "%s/backend/images" % BASE_DIR

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
IMAGE_URL = "{}/static/images/".format(BASE_URL)

# Django serves static files from each app's static directory
# In STATICFILES_DIRS you can configure where to look for static files.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "siddata_backend/static"),
]

# URL for static files (will be handled by apache in production)
STATIC_URL = '/static/'

# Directory where apache will look for static files.
# Use manage.py collectstatic to copy all static files to this folder.
STATIC_ROOT = os.path.join(BASE_DIR, 'collected_apache_static/')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ADMINS = [
    # ('Max', 'mmuster@example.de')
]

EMAIL_HOST = ''             # enter SMTP server here
EMAIL_HOST_USER = ''        # enter SMTP server's user here
EMAIL_HOST_PASSWORD = ''    # enter SMTP server's user's password here
EMAIL_USE_TLS = True
EMAIL_PORT = 587

ALLOWED_HOSTS = []

# List of URLs that are allowed to make cross-site HTTP requests
# https://pypi.org/project/django-cors-headers/
CORS_ALLOWED_ORIGINS = []

# SECURITY WARNING: don't run with debug turned on in production!

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'import_export',
    'corsheaders',
    'rest_framework',
    'backend.apps.BackendConfig',
    'apps.bert_app.apps.BertAppConfig',
    'haystack',
    'django_apscheduler',
    'sphinxdoc',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'siddata_backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': {
        #postgressql
        'ENGINE': 'django.db.backends.postgresql',
         'NAME': 'siddata',
         'USER': 'siddata',
         'PASSWORD': '',
         'HOST': 'localhost',
         #'PORT': '',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# MOOC Repositories
"""
How to get the udemy client credentials: 
    1. Go to udemy.com and log in.
    2. Go to profile (hover over profile image in the upper right corner) > account settings > API-Client.
    3. Copy the Client-ID to 'USER' and the Client-Password to 'PASSWORD'
"""
MOOC_CLIENTS = {
    'UDEMY': {
        'BASE_URL': 'https://www.udemy.com/',
        'API_URL': 'https://www.udemy.com/api-2.0/',
        # enter udemy client id
        'USER': '',
        # enter udemy client password
        'PASSWORD': ''
    }
}

# OER Repositories
OER_REPOS = {
    'TWILLO': {
        'BASE_URL': 'https://www.twillo.de'
    }
}
# auth urls
LOGIN_URL = 'login'  # refers to name of route in backend/urls.py
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# enable server to receive a larger amount of studip data
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['require_debug_true']
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false']
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

if DEBUG:
    # make all loggers use the console.
    for logger in LOGGING['loggers']:
        LOGGING['loggers'][logger]['handlers'] = ['console']
        LOGGING['loggers'][logger]['propagate'] = True

# settings for ERM visualization by graph_models
# see https://wadewilliams.com/technology-software/generating-erd-for-django-applications/
# and https://django-extensions.readthedocs.io/en/latest/graph_models.html
GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}

# seafile-model-downloader
SIDDATA_SEAFILE_SERVER = 'https://myshare.uni-osnabrueck.de'
SIDDATA_SEAFILE_REPOID = '0b3948a7-9483-4e26-a7bb-a123496ddfcf' #for modelupdown v2
# SIDDATA_SEAFILE_REPOID = 'b20a34c4-69cf-4e7c-a3f2-8f597095cea5' #for modelupdown v1
SIDDATA_SEAFILE_REPOWRITE_ACC = ''
SIDDATA_SEAFILE_REPOREAD_ACC = ''
SIDDATA_SEAFILE_REPOREAD_PASSWORD = ''

# see https://git.siddata.de/uos/siddata_backend/src/branch/f_model_downloader/doc/model_updownloader.md on how to
# get the passwords!
# alternatively you can also use your own rz-login and password (but you may want to save them as environment-variables
# and only load these here using `os.getenv(varname)`!
SIDDATA_SEAFILE_REPO_BASEPATH = "backend_synced_models"
SIDDATA_SEAFILE_MODEL_VERSIONS = {"Sidbert": 1, "Other": 1}

SERVERSTART_IGNORE_MODELUPDOWN_ERRORS = True

DEFAULT_LOG_LEVEL = "DEBUG"
assert DEFAULT_LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
QUIET_SCHEDULER = True

# https://medium.com/@mrgrantanderson/replacing-cron-and-running-background-tasks-in-django-using-apscheduler-and-django-apscheduler-d562646c062e
# This scheduler config will:
# - Store jobs in the project database
# - Execute jobs in threads inside the application process
SCHEDULER_CONFIG = {
    "apscheduler.jobstores.default": {
        "class": "django_apscheduler.jobstores:DjangoJobStore"
    },
    'apscheduler.executors.processpool': {
        "type": "threadpool"
    },
}
SCHEDULER_AUTOSTART = True

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    },
}
