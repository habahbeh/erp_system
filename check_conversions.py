import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Item, UoMConversion

items = Item.objects.all()[:5]
for item in items:
    conversions = UoMConversion.objects.filter(item=item, variant__isnull=True)
    print(f'📦 {item.name} (ID: {item.id}):')
    print(f'   - عدد التحويلات: {conversions.count()}')
    for c in conversions:
        print(f'   - {c.from_uom.name} = {c.conversion_factor} {item.base_uom.name if item.base_uom else "N/A"}')
    print()
