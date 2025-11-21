from django.apps import AppConfig


class PurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchases'
    verbose_name = 'المشتريات'

    def ready(self):
        """تفعيل الإشارات عند تشغيل التطبيق"""
        import apps.purchases.signals  # noqa
