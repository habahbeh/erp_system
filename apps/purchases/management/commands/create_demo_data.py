"""
أمر إنشاء بيانات تجريبية شاملة لنظام المشتريات
يشمل كل السيناريوهات: طلبات الشراء، طلبات عروض الأسعار، عروض الأسعار،
أوامر الشراء، العقود، محاضر الاستلام، الفواتير
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية شاملة لنظام المشتريات'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='حذف البيانات التجريبية الموجودة قبل الإنشاء'
        )

    def handle(self, *args, **options):
        from apps.core.models import (
            Company, Branch, Warehouse, Currency,
            PaymentMethod, UnitOfMeasure, ItemCategory,
            Item, BusinessPartner
        )
        from apps.purchases.models import (
            PurchaseInvoice, PurchaseInvoiceItem,
            PurchaseOrder, PurchaseOrderItem,
            PurchaseRequest, PurchaseRequestItem,
            PurchaseQuotationRequest, PurchaseQuotationRequestItem,
            PurchaseQuotation, PurchaseQuotationItem,
            PurchaseContract, PurchaseContractItem,
            GoodsReceipt, GoodsReceiptLine
        )

        self.stdout.write(self.style.NOTICE('═' * 60))
        self.stdout.write(self.style.NOTICE('   إنشاء بيانات تجريبية شاملة لنظام المشتريات'))
        self.stdout.write(self.style.NOTICE('═' * 60))

        # الحصول على الشركة الأولى
        company = Company.objects.first()
        if not company:
            self.stdout.write(self.style.ERROR('لا توجد شركة في النظام!'))
            return

        # حذف البيانات القديمة إذا طُلب
        if options['clean']:
            self.stdout.write(self.style.WARNING('\nحذف البيانات التجريبية القديمة...'))

            # حذف بترتيب عكسي للعلاقات
            GoodsReceiptLine.objects.filter(
                goods_receipt__company=company,
                goods_receipt__notes__contains='[DEMO]'
            ).delete()
            GoodsReceipt.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            PurchaseInvoiceItem.objects.filter(
                invoice__company=company,
                invoice__notes__contains='[DEMO]'
            ).delete()
            PurchaseInvoice.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            PurchaseOrderItem.objects.filter(
                order__company=company,
                order__notes__contains='[DEMO]'
            ).delete()
            PurchaseOrder.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            PurchaseContractItem.objects.filter(
                contract__company=company,
                contract__notes__contains='[DEMO]'
            ).delete()
            PurchaseContract.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            PurchaseQuotationItem.objects.filter(
                quotation__company=company,
                quotation__notes__contains='[DEMO]'
            ).delete()
            PurchaseQuotation.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            PurchaseQuotationRequestItem.objects.filter(
                quotation_request__company=company,
                quotation_request__notes__contains='[DEMO]'
            ).delete()
            PurchaseQuotationRequest.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            PurchaseRequestItem.objects.filter(
                request__company=company,
                request__notes__contains='[DEMO]'
            ).delete()
            PurchaseRequest.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            BusinessPartner.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            Item.objects.filter(
                company=company,
                notes__contains='[DEMO]'
            ).delete()

            self.stdout.write(self.style.SUCCESS('تم حذف البيانات القديمة'))

        # الحصول على البيانات الأساسية
        branch = Branch.objects.filter(company=company).first()
        warehouse = Warehouse.objects.filter(company=company).first()
        currency = Currency.objects.filter(code='JOD').first()
        if not currency:
            currency = Currency.objects.first()
        payment_method = PaymentMethod.objects.filter(company=company).first()
        uom = UnitOfMeasure.objects.filter(company=company).first()
        category = ItemCategory.objects.filter(company=company).first()
        user = User.objects.filter(is_active=True, is_staff=True).first()

        if not all([branch, warehouse, currency, payment_method, uom, category, user]):
            self.stdout.write(self.style.ERROR('بعض البيانات الأساسية غير موجودة!'))
            missing = []
            if not branch: missing.append('الفرع')
            if not warehouse: missing.append('المستودع')
            if not currency: missing.append('العملة')
            if not payment_method: missing.append('طريقة الدفع')
            if not uom: missing.append('وحدة القياس')
            if not category: missing.append('فئة الأصناف')
            if not user: missing.append('المستخدم')
            self.stdout.write(f'  الناقص: {", ".join(missing)}')
            return

        # ========== 1. إنشاء الموردين ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('1. إنشاء الموردين...'))
        suppliers = []
        supplier_names = [
            ('شركة المعدات الصناعية', 'Industrial Equipment Co.'),
            ('مؤسسة التوريدات العامة', 'General Supplies Est.'),
            ('شركة الخليج للتجارة', 'Gulf Trading Company'),
            ('مصنع الحديد والصلب', 'Iron & Steel Factory'),
            ('شركة البناء الحديث', 'Modern Construction Co.'),
            ('مؤسسة الإلكترونيات', 'Electronics Foundation'),
            ('شركة المواد الكيميائية', 'Chemical Materials Co.'),
            ('مصانع البلاستيك المتحدة', 'United Plastics Factory'),
        ]

        for i, (name_ar, name_en) in enumerate(supplier_names):
            supplier, created = BusinessPartner.objects.get_or_create(
                company=company,
                code=f'SUP-DEMO-{i+1:03d}',
                defaults={
                    'name': name_ar,
                    'name_en': name_en,
                    'partner_type': 'supplier',
                    'phone': f'079{random.randint(1000000, 9999999)}',
                    'email': f'supplier{i+1}@demo.com',
                    'notes': '[DEMO] مورد تجريبي',
                    'is_active': True,
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'  ✓ {name_ar}')

        self.stdout.write(f'  إجمالي: {len(suppliers)} موردين')

        # ========== 2. إنشاء المواد ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('2. إنشاء المواد...'))
        items = []
        item_data = [
            ('حديد تسليح 12مم', 'Rebar 12mm', Decimal('850.000')),
            ('أسمنت بورتلاندي', 'Portland Cement', Decimal('5.500')),
            ('طوب أحمر', 'Red Brick', Decimal('0.150')),
            ('رمل ناعم', 'Fine Sand', Decimal('25.000')),
            ('حصى مدرج', 'Graded Gravel', Decimal('30.000')),
            ('خشب صنوبر', 'Pine Wood', Decimal('180.000')),
            ('بلاط سيراميك 40×40', 'Ceramic Tiles 40x40', Decimal('12.000')),
            ('أنابيب PVC 4 بوصة', 'PVC Pipes 4 inch', Decimal('8.500')),
            ('أسلاك كهربائية 2.5مم', 'Electric Wires 2.5mm', Decimal('0.450')),
            ('مفاتيح كهربائية', 'Electric Switches', Decimal('2.500')),
            ('دهان زيتي أبيض', 'White Oil Paint', Decimal('35.000')),
            ('معجون حوائط', 'Wall Putty', Decimal('15.000')),
            ('سيليكون شفاف', 'Clear Silicone', Decimal('4.500')),
            ('مسامير 5سم', 'Nails 5cm', Decimal('3.000')),
            ('براغي ستانلس', 'Stainless Screws', Decimal('0.250')),
            ('شريط لاصق كهربائي', 'Electrical Tape', Decimal('1.500')),
            ('قفازات عمل', 'Work Gloves', Decimal('2.000')),
            ('نظارات حماية', 'Safety Glasses', Decimal('5.000')),
            ('خوذة أمان', 'Safety Helmet', Decimal('12.000')),
            ('حذاء سلامة', 'Safety Boots', Decimal('45.000')),
        ]

        for i, (name_ar, name_en, price) in enumerate(item_data):
            item, created = Item.objects.get_or_create(
                company=company,
                code=f'ITM-DEMO-{i+1:03d}',
                defaults={
                    'name': name_ar,
                    'name_en': name_en,
                    'category': category,
                    'base_uom': uom,
                    'currency': currency,
                    'notes': '[DEMO] مادة تجريبية',
                    'is_active': True,
                }
            )
            items.append((item, price))
            if created:
                self.stdout.write(f'  ✓ {name_ar}')

        self.stdout.write(f'  إجمالي: {len(items)} مادة')

        # ========== 3. إنشاء طلبات الشراء ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('3. إنشاء طلبات الشراء (Purchase Requests)...'))
        purchase_requests = []
        pr_purposes = [
            'مشروع بناء المبنى الجديد',
            'صيانة المستودع الرئيسي',
            'تجهيز خط الإنتاج',
            'مستلزمات السلامة المهنية',
            'تجديد مخزون المواد الأساسية',
        ]

        for i in range(10):
            pr_date = date.today() - timedelta(days=random.randint(30, 90))
            status = random.choice(['draft', 'submitted', 'approved', 'rejected', 'ordered'])

            pr = PurchaseRequest.objects.create(
                company=company,
                date=pr_date,
                purpose=random.choice(pr_purposes),
                required_date=pr_date + timedelta(days=random.randint(7, 30)),
                priority=random.choice(['low', 'normal', 'high', 'urgent']),
                status=status,
                notes='[DEMO] طلب شراء تجريبي',
                created_by=user,
            )

            # إضافة بنود
            num_items = random.randint(2, 5)
            selected_items = random.sample(items, min(num_items, len(items)))
            for item, price in selected_items:
                PurchaseRequestItem.objects.create(
                    request=pr,
                    item=item,
                    item_description=item.name,
                    quantity=Decimal(str(random.randint(5, 50))),
                    unit=uom.name,
                    estimated_price=price,
                )

            purchase_requests.append(pr)
            self.stdout.write(f'  ✓ {pr.number} ({pr.get_status_display()})')

        self.stdout.write(f'  إجمالي: {len(purchase_requests)} طلب شراء')

        # ========== 4. إنشاء طلبات عروض الأسعار (RFQ) ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('4. إنشاء طلبات عروض الأسعار (RFQ)...'))
        rfqs = []
        rfq_subjects = [
            'توريد مواد بناء - المرحلة الأولى',
            'معدات سلامة مهنية - عقد سنوي',
            'مواد كهربائية - مشروع التوسعة',
            'مستلزمات صيانة دورية',
        ]

        for i in range(6):
            rfq_date = date.today() - timedelta(days=random.randint(15, 60))
            status = random.choice(['draft', 'sent', 'receiving', 'evaluating', 'awarded'])

            rfq = PurchaseQuotationRequest.objects.create(
                company=company,
                date=rfq_date,
                subject=random.choice(rfq_subjects) + f' #{i+1}',
                description='طلب عروض أسعار للمواد المطلوبة',
                submission_deadline=rfq_date + timedelta(days=14),
                required_delivery_date=rfq_date + timedelta(days=30),
                currency=currency,
                payment_terms='30 يوم من تاريخ الفاتورة',
                delivery_terms='التسليم في المستودع الرئيسي',
                status=status,
                notes='[DEMO] طلب عرض أسعار تجريبي',
                created_by=user,
            )

            # إضافة بنود
            num_items = random.randint(3, 6)
            selected_items = random.sample(items, min(num_items, len(items)))
            for item, price in selected_items:
                PurchaseQuotationRequestItem.objects.create(
                    quotation_request=rfq,
                    item=item,
                    item_description=item.name,
                    specifications=f'مواصفات {item.name}',
                    quantity=Decimal(str(random.randint(10, 100))),
                    unit=uom.name,
                    estimated_price=price,
                )

            rfqs.append(rfq)
            self.stdout.write(f'  ✓ {rfq.number} ({rfq.get_status_display()})')

        self.stdout.write(f'  إجمالي: {len(rfqs)} طلب عرض أسعار')

        # ========== 5. إنشاء عروض الأسعار (Quotations) ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('5. إنشاء عروض الأسعار من الموردين...'))
        quotations = []

        for rfq in rfqs[:4]:  # عروض لأول 4 طلبات
            # كل طلب يحصل على 2-3 عروض من موردين مختلفين
            selected_suppliers = random.sample(suppliers, min(3, len(suppliers)))

            for supplier in selected_suppliers:
                qt_date = rfq.date + timedelta(days=random.randint(3, 10))
                status = random.choice(['draft', 'received', 'under_evaluation', 'accepted', 'rejected'])

                qt = PurchaseQuotation.objects.create(
                    company=company,
                    quotation_request=rfq,
                    supplier=supplier,
                    date=qt_date,
                    valid_until=qt_date + timedelta(days=30),
                    supplier_quotation_number=f'QT-{supplier.code}-{random.randint(1000, 9999)}',
                    currency=currency,
                    payment_terms='30 يوم صافي',
                    delivery_terms='تسليم خلال أسبوعين',
                    delivery_period_days=random.randint(7, 21),
                    warranty_period_months=random.choice([0, 6, 12]),
                    discount_amount=Decimal(str(random.randint(0, 100))),
                    score=Decimal(str(random.randint(60, 95))) if status in ['under_evaluation', 'accepted', 'rejected'] else None,
                    status=status,
                    is_awarded=(status == 'accepted'),
                    notes='[DEMO] عرض سعر تجريبي',
                    created_by=user,
                )

                # نسخ بنود من RFQ مع أسعار مختلفة
                for rfq_item in rfq.items.all():
                    price_variation = Decimal(str(random.uniform(0.9, 1.15)))
                    unit_price = (rfq_item.estimated_price or Decimal('10')) * price_variation

                    PurchaseQuotationItem.objects.create(
                        quotation=qt,
                        rfq_item=rfq_item,
                        item=rfq_item.item,
                        description=rfq_item.item_description,
                        quantity=rfq_item.quantity,
                        unit=rfq_item.unit,
                        unit_price=unit_price.quantize(Decimal('0.001')),
                        discount_percentage=Decimal(str(random.choice([0, 5, 10]))),
                        tax_rate=Decimal('16'),
                    )

                qt.calculate_totals()
                quotations.append(qt)
                self.stdout.write(f'  ✓ {qt.number} - {supplier.name[:20]} ({qt.get_status_display()})')

        self.stdout.write(f'  إجمالي: {len(quotations)} عرض سعر')

        # ========== 6. إنشاء عقود الشراء ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('6. إنشاء عقود الشراء...'))
        contracts = []

        for i in range(4):
            supplier = random.choice(suppliers)
            start_date = date.today() - timedelta(days=random.randint(0, 180))

            contract = PurchaseContract.objects.create(
                company=company,
                supplier=supplier,
                contract_date=start_date - timedelta(days=7),
                start_date=start_date,
                end_date=start_date + timedelta(days=365),
                currency=currency,
                payment_terms='صافي 30 يوم',
                delivery_terms='التسليم في مستودعات الشركة',
                quality_standards='ISO 9001',
                status=random.choice(['draft', 'active', 'active', 'completed']),
                approved=(random.choice([True, False])),
                notes='[DEMO] عقد شراء تجريبي',
                created_by=user,
            )

            # إضافة بنود العقد
            num_items = random.randint(3, 6)
            selected_items = random.sample(items, min(num_items, len(items)))
            for item, price in selected_items:
                PurchaseContractItem.objects.create(
                    contract=contract,
                    item=item,
                    item_description=item.name,
                    unit=uom,
                    contracted_quantity=Decimal(str(random.randint(100, 1000))),
                    unit_price=price,
                    min_order_quantity=Decimal('10'),
                    discount_percentage=Decimal(str(random.choice([0, 5, 10, 15]))),
                )

            contracts.append(contract)
            self.stdout.write(f'  ✓ {contract.number} - {supplier.name[:20]} ({contract.get_status_display()})')

        self.stdout.write(f'  إجمالي: {len(contracts)} عقد')

        # ========== 7. إنشاء أوامر الشراء ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('7. إنشاء أوامر الشراء...'))
        orders = []
        statuses = ['draft', 'pending_approval', 'approved', 'sent', 'partial', 'completed']

        for i in range(15):
            order_date = date.today() - timedelta(days=random.randint(0, 60))
            supplier = random.choice(suppliers)
            status = random.choice(statuses)

            order = PurchaseOrder.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                date=order_date,
                status=status,
                notes='[DEMO] أمر شراء تجريبي',
                created_by=user,
            )

            # إضافة بنود
            num_items = random.randint(2, 6)
            selected_items = random.sample(items, min(num_items, len(items)))
            for item, price in selected_items:
                qty = Decimal(str(random.randint(5, 100)))
                try:
                    PurchaseOrderItem.objects.create(
                        order=order,
                        item=item,
                        quantity=qty,
                        unit_price=price,
                    )
                except Exception:
                    pass

            orders.append(order)
            self.stdout.write(f'  ✓ {order.number} ({order.get_status_display()})')

        self.stdout.write(f'  إجمالي: {len(orders)} أمر شراء')

        # ========== 8. إنشاء محاضر استلام البضاعة ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('8. إنشاء محاضر استلام البضاعة...'))
        goods_receipts = []

        # اختيار أوامر شراء مكتملة أو جزئية لإنشاء محاضر استلام
        completed_orders = [o for o in orders if o.status in ['sent', 'partial', 'completed']]

        for order in completed_orders[:8]:
            try:
                gr = GoodsReceipt.objects.create(
                    company=company,
                    branch=branch,
                    date=order.date + timedelta(days=random.randint(3, 14)),
                    purchase_order=order,
                    supplier=order.supplier,
                    warehouse=warehouse,
                    delivery_note_number=f'DN-{random.randint(10000, 99999)}',
                    received_by=user,
                    quality_check_status=random.choice(['pending', 'passed', 'partial']),
                    status=random.choice(['draft', 'confirmed']),
                    notes='[DEMO] محضر استلام تجريبي',
                    created_by=user,
                )

                # إضافة سطور الاستلام
                for po_item in order.lines.all():
                    received_qty = po_item.quantity * Decimal(str(random.uniform(0.8, 1.0)))
                    GoodsReceiptLine.objects.create(
                        goods_receipt=gr,
                        purchase_order_line=po_item,
                        item=po_item.item,
                        ordered_quantity=po_item.quantity,
                        received_quantity=received_qty.quantize(Decimal('0.001')),
                        rejected_quantity=Decimal('0'),
                        unit_price=po_item.unit_price,
                    )

                goods_receipts.append(gr)
                self.stdout.write(f'  ✓ {gr.number} ({gr.get_status_display()})')
            except Exception as e:
                self.stdout.write(f'  ⚠ تخطي: {str(e)[:50]}')

        self.stdout.write(f'  إجمالي: {len(goods_receipts)} محضر استلام')

        # ========== 9. إنشاء فواتير المشتريات ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('9. إنشاء فواتير المشتريات...'))
        invoices = []
        invoice_types = ['purchase', 'purchase', 'purchase', 'return']

        for i in range(30):
            inv_date = date.today() - timedelta(days=random.randint(0, 90))
            supplier = random.choice(suppliers)
            inv_type = random.choice(invoice_types)

            discount_type = random.choice(['percentage', 'amount'])
            discount_value = Decimal('0')
            if discount_type == 'percentage':
                discount_value = Decimal(str(random.choice([0, 5, 10, 15])))
            else:
                discount_value = Decimal(str(random.randint(0, 100)))

            invoice = PurchaseInvoice.objects.create(
                company=company,
                branch=branch,
                warehouse=warehouse,
                supplier=supplier,
                currency=currency,
                payment_method=payment_method,
                date=inv_date,
                invoice_type=inv_type,
                discount_type=discount_type,
                discount_value=discount_value,
                supplier_invoice_number=f'INV-{random.randint(1000, 9999)}',
                notes='[DEMO] فاتورة تجريبية',
                created_by=user,
            )

            # إضافة بنود
            num_items = random.randint(1, 8)
            selected_items = random.sample(items, min(num_items, len(items)))
            for item, price in selected_items:
                qty = Decimal(str(random.randint(1, 50)))
                tax_rate = Decimal(str(random.choice([0, 16])))
                PurchaseInvoiceItem.objects.create(
                    invoice=invoice,
                    item=item,
                    quantity=qty,
                    unit=uom,
                    unit_price=price,
                    tax_rate=tax_rate,
                    tax_included=random.choice([True, False]),
                )

            invoice.calculate_totals()
            invoice.save()
            invoices.append(invoice)
            self.stdout.write(f'  ✓ {invoice.number} ({inv_type})')

        self.stdout.write(f'  إجمالي: {len(invoices)} فاتورة')

        # ========== 10. ترحيل بعض الفواتير ==========
        self.stdout.write('\n' + self.style.HTTP_INFO('10. ترحيل بعض الفواتير محاسبياً...'))
        posted_count = 0

        # اختيار فواتير شراء عشوائية للترحيل
        purchase_invoices = [inv for inv in invoices if inv.invoice_type == 'purchase']
        invoices_to_post = random.sample(purchase_invoices, min(10, len(purchase_invoices)))

        for invoice in invoices_to_post:
            try:
                invoice.post(user)
                posted_count += 1
                self.stdout.write(f'  ✓ تم ترحيل {invoice.number}')
            except Exception as e:
                self.stdout.write(f'  ⚠ فشل ترحيل {invoice.number}: {str(e)[:30]}')

        self.stdout.write(f'  إجمالي المرحّلة: {posted_count} فاتورة')

        # ========== ملخص النتائج ==========
        self.stdout.write('\n' + self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('   تم إنشاء البيانات التجريبية بنجاح!'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(f'\n  📦 الموردون: {len(suppliers)}')
        self.stdout.write(f'  📦 المواد: {len(items)}')
        self.stdout.write(f'  📋 طلبات الشراء: {len(purchase_requests)}')
        self.stdout.write(f'  📝 طلبات عروض الأسعار: {len(rfqs)}')
        self.stdout.write(f'  💰 عروض الأسعار: {len(quotations)}')
        self.stdout.write(f'  📄 عقود الشراء: {len(contracts)}')
        self.stdout.write(f'  🛒 أوامر الشراء: {len(orders)}')
        self.stdout.write(f'  📥 محاضر الاستلام: {len(goods_receipts)}')
        self.stdout.write(f'  🧾 الفواتير: {len(invoices)}')
        self.stdout.write(f'  ✅ الفواتير المرحّلة: {posted_count}')

        self.stdout.write('\n' + self.style.NOTICE('لحذف البيانات التجريبية:'))
        self.stdout.write('  python manage.py create_demo_data --clean')
