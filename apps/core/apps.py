# apps/core/apps.py
"""
إعداد تطبيق النواة
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = _('النظام الأساسي')

    def ready(self):
        """تنفيذ عند جاهزية التطبيق"""
        # استيراد الإشارات
        import apps.core.signals