# Path: apps/assets/apps.py
"""
تكوين تطبيق الأصول الثابتة
"""

from django.apps import AppConfig


class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assets'
    verbose_name = 'إدارة الأصول الثابتة'

    def ready(self):
        """تفعيل الـ Signals عند تحميل التطبيق"""
        import apps.assets.signals