from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sales'
    verbose_name = 'المبيعات'

    def ready(self):
        """تفعيل الإشارات عند تشغيل التطبيق"""
        import apps.sales.signals  # noqa
