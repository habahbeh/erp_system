# Generated manually to add branch field to PurchaseOrder

from django.db import migrations, models
import django.db.models.deletion


def set_default_branch(apps, schema_editor):
    """Set branch to warehouse's branch for existing purchase orders"""
    PurchaseOrder = apps.get_model('purchases', 'PurchaseOrder')
    Branch = apps.get_model('core', 'Branch')

    for order in PurchaseOrder.objects.all():
        # Get the warehouse's branch
        warehouse = order.warehouse
        if hasattr(warehouse, 'branch') and warehouse.branch:
            order.branch = warehouse.branch
        else:
            # Fallback: get the first branch of the company
            branch = Branch.objects.filter(company=order.company).first()
            if branch:
                order.branch = branch
        order.save(update_fields=['branch'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Adjust based on your core app migrations
        ('purchases', '0006_purchaseinvoice_goods_receipt'),
    ]

    operations = [
        # Step 1: Add branch field as nullable
        migrations.AddField(
            model_name='purchaseorder',
            name='branch',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.branch',
                verbose_name='الفرع'
            ),
        ),
        # Step 2: Populate branch for existing records
        migrations.RunPython(set_default_branch, reverse_code=migrations.RunPython.noop),
        # Step 3: Make branch non-nullable
        migrations.AlterField(
            model_name='purchaseorder',
            name='branch',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='core.branch',
                verbose_name='الفرع'
            ),
        ),
    ]
