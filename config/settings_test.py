"""
إعدادات الاختبار - تستخدم SQLite
"""

from .settings import *

# استخدام SQLite للاختبارات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# التأكد من تضمين جميع التطبيقات
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'django_filters',
    'widget_tweaks',
    'rest_framework',
    # Project apps
    'apps.core',
    'apps.accounting',
    'apps.hr',
    'apps.inventory',
    'apps.purchases',
    'apps.sales',
    'apps.assets',
    'apps.reports',
]

# تسريع الاختبارات
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# تعطيل التحقق من التوافق
DEBUG = True

# تعطيل middleware غير ضروري للاختبارات
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# تعطيل الـ logging أثناء الاختبارات
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
