"""
إعدادات مشروع نظام ERP
تم إنشاؤه لإدارة الشركات المتعددة
"""

from pathlib import Path
from decouple import config
import os

import sys

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))


# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = ['*']

# تطبيقات النظام
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

THIRD_PARTY_APPS = [
    # سنضيفها لاحقاً
]

LOCAL_APPS = [
    # سنضيف التطبيقات هنا
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # للغات
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.CurrentBranchMiddleware',
]

ROOT_URLCONF = 'config.urls'

# قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}


# إعدادات اللغة
LANGUAGE_CODE = 'ar'
LANGUAGES = [
    ('ar', 'العربية'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Asia/Amman'

# الملفات الثابتة
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# القوالب
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# المستخدم المخصص
AUTH_USER_MODEL = 'core.User'

