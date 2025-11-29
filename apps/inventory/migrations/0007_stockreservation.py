# Generated manually for StockReservation model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('inventory', '0006_alter_stockin_options_alter_stocktransfer_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاريخ التعديل')),
                ('is_active', models.BooleanField(default=True, verbose_name='نشط')),
                ('quantity', models.DecimalField(
                    decimal_places=3,
                    max_digits=12,
                    validators=[django.core.validators.MinValueValidator(Decimal('0.001'))],
                    verbose_name='الكمية المحجوزة'
                )),
                ('reference_type', models.CharField(
                    help_text='مثل: sales_order, quotation',
                    max_length=50,
                    verbose_name='نوع المرجع'
                )),
                ('reference_id', models.IntegerField(verbose_name='رقم المرجع')),
                ('status', models.CharField(
                    choices=[
                        ('active', 'نشط'),
                        ('confirmed', 'مؤكد'),
                        ('released', 'محرر'),
                        ('expired', 'منتهي')
                    ],
                    default='active',
                    max_length=20,
                    verbose_name='الحالة'
                )),
                ('expires_at', models.DateTimeField(
                    help_text='وقت انتهاء صلاحية الحجز',
                    verbose_name='ينتهي في'
                )),
                ('confirmed_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='تاريخ التأكيد'
                )),
                ('released_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='تاريخ التحرير'
                )),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='stock_reservations',
                    to='core.company',
                    verbose_name='الشركة'
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_stock_reservations',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='أنشئ بواسطة'
                )),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='reservations',
                    to='core.item',
                    verbose_name='المادة'
                )),
                ('item_stock', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reservations',
                    to='inventory.itemstock',
                    verbose_name='رصيد المادة'
                )),
                ('item_variant', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='reservations',
                    to='core.itemvariant',
                    verbose_name='المتغير'
                )),
                ('reserved_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='stock_reservations',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='حجز بواسطة'
                )),
                ('warehouse', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='reservations',
                    to='core.warehouse',
                    verbose_name='المستودع'
                )),
            ],
            options={
                'verbose_name': 'حجز مخزون',
                'verbose_name_plural': 'حجوزات المخزون',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='stockreservation',
            index=models.Index(fields=['status', 'expires_at'], name='inventory_s_status_2e7d89_idx'),
        ),
        migrations.AddIndex(
            model_name='stockreservation',
            index=models.Index(fields=['reference_type', 'reference_id'], name='inventory_s_referen_d8f4a3_idx'),
        ),
        migrations.AddIndex(
            model_name='stockreservation',
            index=models.Index(fields=['item', 'warehouse'], name='inventory_s_item_id_b5c8e2_idx'),
        ),
    ]
