"""
إعدادات تطبيق النواة
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    label = 'core'
    verbose_name = 'النواة'

    def ready(self):
        """تحميل الإشارات"""
        import apps.core.signals