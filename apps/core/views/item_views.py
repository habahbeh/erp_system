# apps/core/views/item_views.py
"""
Views للأصناف والتصنيفات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import json
import logging
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django_filters.views import FilterView
from django.http import JsonResponse

from ..models import (
    Item, ItemCategory, Brand, UnitOfMeasure, VariantAttribute,
    ItemVariant, ItemVariantAttributeValue, VariantValue, PriceList, PriceListItem
)
from ..forms.item_forms import ItemForm, ItemCategoryForm, ItemVariantFormSet, VariantAttributeSelectionForm
from ..mixins import CompanyMixin, AuditLogMixin
from ..decorators import branch_required
# permission_required_with_message removed - using PermissionRequiredMixin instead
from ..filters import ItemFilter, ItemCategoryFilter


class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة المواد مع DataTable"""
    template_name = 'core/items/item_list.html'
    permission_required = 'core.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة المواد'),
            'can_add': self.request.user.has_perm('core.add_item'),
            'add_url': reverse('core:item_create'),
        })
        return context


class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة مادة جديد"""
    model = Item
    form_class = ItemForm
    template_name = 'core/items/item_form_wizard.html'
    permission_required = 'core.add_item'
    success_url = reverse_lazy('core:item_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ✅ تعريف logger في البداية
        import logging
        logger = logging.getLogger(__name__)

        # تأكد من وجود current_company
        company = getattr(self.request, 'current_company', None) or self.current_company

        if self.request.POST:
            context['variant_formset'] = ItemVariantFormSet(
                self.request.POST,
                self.request.FILES
            )
            context['attribute_form'] = VariantAttributeSelectionForm(
                self.request.POST,
                company=company
            )
        else:
            context['variant_formset'] = ItemVariantFormSet()
            context['attribute_form'] = VariantAttributeSelectionForm(
                company=company
            )

        # إضافة خصائص المتغيرات مع القيم
        context['variant_attributes'] = VariantAttribute.objects.filter(
            company=company,
            is_active=True
        ).prefetch_related('values').order_by('sort_order', 'name')

        # ✅ إضافة وحدات القياس للـ UOM Conversions
        import json
        uom_qs = UnitOfMeasure.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        context['uom_list'] = uom_qs

        # تحويل وحدات القياس إلى JSON للـ JavaScript
        uom_data = []
        for uom in uom_qs:
            uom_data.append({
                'id': uom.id,
                'name': uom.name,
                'symbol': uom.symbol,
            })
        context['uom_list_json'] = json.dumps(uom_data)

        context.update({
            'title': _('إضافة مادة جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المواد'), 'url': reverse('core:item_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ المادة'),
            'cancel_url': reverse('core:item_list'),
            'is_update': False,  # للتمييز بين إضافة وتعديل
            'wizard_mode': True,  # ✅ تفعيل وضع الـ wizard
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        attribute_form = context['attribute_form']

        if form.is_valid():
            # حفظ المادة أولاً
            response = super().form_valid(form)

            # إذا كان المادة له متغيرات
            if self.object.has_variants:
                # الحصول على بيانات المتغيرات المولدة من JavaScript
                generated_variants_json = self.request.POST.get('generated_variants', '[]')

                try:
                    import json
                    generated_variants = json.loads(generated_variants_json)

                    if generated_variants:
                        # توليد المتغيرات
                        created_variants = self.create_variants_from_json(generated_variants)

                        messages.success(
                            self.request,
                            _('تم إضافة المادة "%(name)s" مع %(count)d متغير بنجاح') % {
                                'name': self.object.name,
                                'count': len(created_variants)
                            }
                        )
                    else:
                        messages.warning(
                            self.request,
                            _('تم إضافة المادة "%(name)s" بدون متغيرات') % {
                                'name': self.object.name
                            }
                        )
                except json.JSONDecodeError:
                    messages.error(
                        self.request,
                        _('خطأ في بيانات المتغيرات. تم حفظ المادة بدون متغيرات.')
                    )
            else:
                # مادة عادية بدون متغيرات
                messages.success(
                    self.request,
                    _('تم إضافة المادة "%(name)s" بنجاح') % {
                        'name': self.object.name
                    }
                )

            # ✅ حفظ تحويلات وحدات القياس
            conversions_saved = self.save_uom_conversions()

            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def create_variants_from_json(self, variants_data):
        """إنشاء المتغيرات من البيانات المرسلة من JavaScript"""
        created_variants = []
        logger = logging.getLogger(__name__)
        company = getattr(self.request, 'current_company', None) or self.current_company

        for variant_data in variants_data:
            try:
                # إنشاء المتغير
                variant = ItemVariant.objects.create(
                    item=self.object,
                    company=company,
                    code=variant_data['code'],
                    catalog_number=f"{self.object.catalog_number or self.object.code}-{variant_data['index']:03d}" if self.object.catalog_number else
                    variant_data['code'],
                    notes=f"متغير مولد تلقائياً: {variant_data['description']}"
                )

                # ربط المتغير بقيم الخصائص
                combination = variant_data.get('combination', [])
                for attr_value_data in combination:
                    try:
                        # البحث عن قيمة الخاصية
                        variant_value = VariantValue.objects.get(
                            id=attr_value_data['id'],
                            company=company
                        )

                        # إنشاء الربط
                        ItemVariantAttributeValue.objects.create(
                            variant=variant,
                            attribute=variant_value.attribute,
                            value=variant_value,
                            company=company
                        )
                    except VariantValue.DoesNotExist:
                        logger.warning(f"VariantValue with id {attr_value_data['id']} not found")
                        continue

                created_variants.append(variant)

            except Exception as e:
                # تسجيل الخطأ وإكمال المعالجة
                logger.error(f"خطأ في إنشاء المتغير: {e}")
                continue

        return created_variants

    def save_uom_conversions(self):
        """
        حفظ تحويلات وحدات القياس

        ملاحظة: التحويل يتم دائماً إلى وحدة القياس الأساسية للمادة (base_uom)
        """
        import logging
        from decimal import Decimal
        from apps.core.models import UoMConversion, UnitOfMeasure

        logger = logging.getLogger(__name__)
        saved_count = 0
        deleted_count = 0

        logger.info(f"🔄 save_uom_conversions called for item {self.object.id}")

        # الحصول على وحدة القياس الأساسية للمادة
        base_uom = self.object.base_uom
        if not base_uom:
            logger.warning(f"⚠️ No base_uom set for item {self.object.id}")
            return 0

        logger.info(f"✅ base_uom: {base_uom.name}")

        # ✅ تتبع وحدات القياس الموجودة في POST data
        kept_from_uom_ids = []

        # فحص جميع حقول POST
        conversion_fields = [key for key in self.request.POST.keys() if key.startswith('conversion_from_uom_')]
        logger.info(f"📊 Found {len(conversion_fields)} conversion fields in POST data")
        logger.info(f"📋 Conversion fields: {conversion_fields}")

        for key, value in self.request.POST.items():
            if key.startswith('conversion_from_uom_'):
                try:
                    # استخراج index من اسم الحقل
                    index = key.split('_')[-1]
                    logger.info(f"  Processing conversion index: {index}")

                    from_uom_id = self.request.POST.get(f'conversion_from_uom_{index}')
                    factor = self.request.POST.get(f'conversion_factor_{index}')

                    logger.info(f"    from_uom_id: {from_uom_id}, factor: {factor}")

                    if not from_uom_id or not factor:
                        logger.warning(f"    ⚠️ Skipping - missing data")
                        continue

                    from_uom_id = int(from_uom_id)
                    factor = Decimal(factor.strip())

                    if factor <= 0:
                        logger.warning(f"    ⚠️ Skipping - invalid factor: {factor}")
                        continue

                    # الحصول على وحدة القياس المصدر
                    from_uom = UnitOfMeasure.objects.get(
                        pk=from_uom_id,
                        company=self.request.current_company
                    )

                    # تجنب إنشاء تحويل من الوحدة الأساسية إلى نفسها
                    if from_uom.id == base_uom.id:
                        logger.warning(f"    ⚠️ Skipping - from_uom same as base_uom")
                        continue

                    # ✅ إضافة هذه الوحدة إلى قائمة المحفوظات
                    kept_from_uom_ids.append(from_uom_id)

                    # إنشاء الصيغة: 1 [from_uom] = [factor] [base_uom]
                    formula = f'1 {from_uom.name} = {factor} {base_uom.name}'

                    # ✅ استخدام update_or_create بدلاً من create
                    conversion, created = UoMConversion.objects.update_or_create(
                        item=self.object,
                        company=self.request.current_company,
                        from_uom=from_uom,
                        defaults={
                            'conversion_factor': factor,
                            'formula_expression': formula,
                            'notes': f'تحويل من {from_uom.name} إلى الوحدة الأساسية {base_uom.name}'
                        }
                    )
                    saved_count += 1
                    if created:
                        logger.info(f"    ✅ Created conversion: {from_uom.name} → {base_uom.name} (factor: {factor})")
                    else:
                        logger.info(f"    🔄 Updated conversion: {from_uom.name} → {base_uom.name} (factor: {factor})")

                except (ValueError, UnitOfMeasure.DoesNotExist, IndexError) as e:
                    logger.error(f"    ❌ Error saving conversion {index}: {e}")
                    continue

        # ✅ حذف التحويلات التي لم تعد موجودة في الـ form
        logger.info(f"🗑️ Checking for conversions to delete...")
        logger.info(f"   - Kept from_uom_ids: {kept_from_uom_ids}")

        # جلب جميع التحويلات الموجودة
        old_conversions = UoMConversion.objects.filter(
            item=self.object,
            company=self.request.current_company
        )

        # التحويلات المطلوب حذفها = التي ليست في قائمة المحفوظات
        if kept_from_uom_ids:
            conversions_to_delete = old_conversions.exclude(from_uom_id__in=kept_from_uom_ids)
        else:
            # إذا كانت قائمة المحفوظات فارغة، احذف جميع التحويلات
            conversions_to_delete = old_conversions

        deleted_count = conversions_to_delete.count()
        if deleted_count > 0:
            logger.info(f"   - Deleting {deleted_count} conversions...")
            for conv in conversions_to_delete:
                logger.info(f"     ❌ Deleting: {conv.from_uom.name} → {base_uom.name}")
            conversions_to_delete.delete()

        logger.info(f"✅ Total conversions saved: {saved_count}")
        logger.info(f"✅ Total conversions deleted: {deleted_count}")
        return saved_count

    def form_invalid(self, form):
        """رسالة خطأ عند فشل الحفظ"""
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل مادة"""
    model = Item
    form_class = ItemForm
    template_name = 'core/items/item_form_wizard.html'
    permission_required = 'core.change_item'
    success_url = reverse_lazy('core:item_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ✅ تعريف logger في البداية
        import logging
        logger = logging.getLogger(__name__)

        # تأكد من وجود current_company
        company = getattr(self.request, 'current_company', None) or self.current_company

        if self.request.POST:
            context['variant_formset'] = ItemVariantFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object
            )
            context['attribute_form'] = VariantAttributeSelectionForm(
                self.request.POST,
                company=company
            )
        else:
            context['variant_formset'] = ItemVariantFormSet(instance=self.object)
            context['attribute_form'] = VariantAttributeSelectionForm(
                company=company
            )

        # إضافة خصائص المتغيرات مع القيم
        context['variant_attributes'] = VariantAttribute.objects.filter(
            company=company,
            is_active=True
        ).prefetch_related('values').order_by('sort_order', 'name')

        # إضافة المتغيرات الموجودة للعرض
        context['existing_variants'] = self.object.variants.select_related(
            'company'
        ).prefetch_related(
            'variant_attribute_values__attribute',
            'variant_attribute_values__value'
        ).all()

        # ✅ إضافة وحدات القياس للـ UOM Conversions
        import json
        uom_qs = UnitOfMeasure.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        context['uom_list'] = uom_qs

        # تحويل وحدات القياس إلى JSON للـ JavaScript
        uom_data = []
        for uom in uom_qs:
            uom_data.append({
                'id': uom.id,
                'name': uom.name,
                'symbol': uom.symbol,
            })
        context['uom_list_json'] = json.dumps(uom_data)

        # ✅ جلب التحويلات الموجودة للمادة
        from apps.core.models import UoMConversion
        existing_conversions = UoMConversion.objects.filter(
            item=self.object
        ).select_related('from_uom', 'company')

        context['existing_conversions'] = existing_conversions

        # تحويل التحويلات إلى JSON للـ JavaScript
        # ملاحظة: التحويلات تكون دائماً إلى وحدة القياس الأساسية (base_uom)
        conversions_data = []
        for conversion in existing_conversions:
            # إنشاء الصيغة الحالية
            base_uom = self.object.base_uom
            formula = ''
            if base_uom:
                formula = f'1 {conversion.from_uom.name} = {conversion.conversion_factor} {base_uom.name}'

            conversions_data.append({
                'from_uom_id': conversion.from_uom.id,
                'from_uom_name': conversion.from_uom.name,
                'factor': str(conversion.conversion_factor),
                'formula': formula,
            })

        context['existing_conversions_json'] = json.dumps(conversions_data)

        # Debug logging
        logger = logging.getLogger(__name__)
        logger.info(f"📊 ItemUpdateView - Item: {self.object.name} (ID: {self.object.id})")
        logger.info(f"   - Conversions count: {existing_conversions.count()}")
        logger.info(f"   - Conversions JSON: {context['existing_conversions_json']}")

        # إضافة قوائم الأسعار المتاحة
        from ..models import PriceList, PriceListItem
        context['price_lists'] = PriceList.objects.filter(
            company=company,
            is_active=True
        ).order_by('name')

        # إضافة الأسعار الموجودة كـ JSON
        existing_prices = PriceListItem.objects.filter(
            item=self.object
        ).values('id', 'price_list_id', 'variant_id', 'price')

        existing_prices_dict = {}
        for price in existing_prices:
            variant_id = price['variant_id'] or ''
            key = f"{variant_id}_{price['price_list_id']}"
            existing_prices_dict[key] = {
                'id': price['id'],
                'price': str(price['price'])
            }

        context['existing_prices_json'] = json.dumps(existing_prices_dict)

        context.update({
            'title': _('تعديل المادة: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المواد'), 'url': reverse('core:item_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:item_list'),
            'is_update': True,
            'wizard_mode': True,  # ✅ تفعيل وضع الـ wizard
        })
        return context

    def form_valid(self, form):
        """حفظ التعديلات مع معالجة المتغيرات"""
        context = self.get_context_data()
        attribute_form = context['attribute_form']

        if form.is_valid():
            response = super().form_valid(form)

            # حفظ الأسعار من JSON
            self.save_pricing_from_json()

            # إذا كان المادة له متغيرات
            if self.object.has_variants:
                # ✅ في وضع التعديل: نحافظ على المتغيرات الموجودة
                existing_variants = list(self.object.variants.all())

                if existing_variants:
                    messages.success(
                        self.request,
                        _('تم تحديث المادة "%(name)s" مع %(count)d متغير') % {
                            'name': self.object.name,
                            'count': len(existing_variants)
                        }
                    )
                else:
                    # لا توجد متغيرات - يمكن أن يكون هذا خطأ
                    messages.warning(
                        self.request,
                        _('تم تحديث المادة "%(name)s" لكن لا توجد متغيرات') % {
                            'name': self.object.name
                        }
                    )
            else:
                # إلغاء تفعيل المتغيرات - احذف جميع المتغيرات
                deleted_count = 0
                if self.object.variants.exists():
                    deleted_count = self.object.variants.count()
                    self.object.variants.all().delete()

                if deleted_count > 0:
                    messages.success(
                        self.request,
                        _('تم تحديث المادة "%(name)s" وحذف %(count)d متغير') % {
                            'name': self.object.name,
                            'count': deleted_count
                        }
                    )
                else:
                    messages.success(
                        self.request,
                        _('تم تحديث المادة "%(name)s" بنجاح') % {
                            'name': self.object.name
                        }
                    )

            # ✅ حفظ تحويلات وحدات القياس
            conversions_saved = self.save_uom_conversions()

            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def create_variants_from_json(self, variants_data):
        """إنشاء المتغيرات من البيانات المرسلة من JavaScript"""
        created_variants = []
        logger = logging.getLogger(__name__)
        company = getattr(self.request, 'current_company', None) or self.current_company

        for variant_data in variants_data:
            try:
                # إنشاء المتغير
                variant = ItemVariant.objects.create(
                    item=self.object,
                    company=company,
                    code=variant_data['code'],
                    catalog_number=f"{self.object.catalog_number or self.object.code}-{variant_data['index']:03d}" if self.object.catalog_number else
                    variant_data['code'],
                    notes=f"متغير مولد تلقائياً: {variant_data['description']}"
                )

                # ربط المتغير بقيم الخصائص
                combination = variant_data.get('combination', [])
                for attr_value_data in combination:
                    try:
                        variant_value = VariantValue.objects.get(
                            id=attr_value_data['id'],
                            company=company
                        )

                        ItemVariantAttributeValue.objects.create(
                            variant=variant,
                            attribute=variant_value.attribute,
                            value=variant_value,
                            company=company
                        )
                    except VariantValue.DoesNotExist:
                        logger.warning(f"VariantValue with id {attr_value_data['id']} not found")
                        continue

                created_variants.append(variant)

            except Exception as e:
                logger.error(f"خطأ في إنشاء المتغير: {e}")
                continue

        return created_variants

    def save_uom_conversions(self):
        """
        حفظ تحويلات وحدات القياس

        ملاحظة: التحويل يتم دائماً إلى وحدة القياس الأساسية للمادة (base_uom)
        """
        import logging
        from decimal import Decimal
        from apps.core.models import UoMConversion, UnitOfMeasure

        logger = logging.getLogger(__name__)
        saved_count = 0
        deleted_count = 0

        logger.info(f"🔄 save_uom_conversions called for item {self.object.id}")

        # الحصول على وحدة القياس الأساسية للمادة
        base_uom = self.object.base_uom
        if not base_uom:
            logger.warning(f"⚠️ No base_uom set for item {self.object.id}")
            return 0

        logger.info(f"✅ base_uom: {base_uom.name}")

        # ✅ تتبع وحدات القياس الموجودة في POST data
        kept_from_uom_ids = []

        # فحص جميع حقول POST
        conversion_fields = [key for key in self.request.POST.keys() if key.startswith('conversion_from_uom_')]
        logger.info(f"📊 Found {len(conversion_fields)} conversion fields in POST data")
        logger.info(f"📋 Conversion fields: {conversion_fields}")

        for key, value in self.request.POST.items():
            if key.startswith('conversion_from_uom_'):
                try:
                    # استخراج index من اسم الحقل
                    index = key.split('_')[-1]
                    logger.info(f"  Processing conversion index: {index}")

                    from_uom_id = self.request.POST.get(f'conversion_from_uom_{index}')
                    factor = self.request.POST.get(f'conversion_factor_{index}')

                    logger.info(f"    from_uom_id: {from_uom_id}, factor: {factor}")

                    if not from_uom_id or not factor:
                        logger.warning(f"    ⚠️ Skipping - missing data")
                        continue

                    from_uom_id = int(from_uom_id)
                    factor = Decimal(factor.strip())

                    if factor <= 0:
                        logger.warning(f"    ⚠️ Skipping - invalid factor: {factor}")
                        continue

                    # الحصول على وحدة القياس المصدر
                    from_uom = UnitOfMeasure.objects.get(
                        pk=from_uom_id,
                        company=self.request.current_company
                    )

                    # تجنب إنشاء تحويل من الوحدة الأساسية إلى نفسها
                    if from_uom.id == base_uom.id:
                        logger.warning(f"    ⚠️ Skipping - from_uom same as base_uom")
                        continue

                    # ✅ إضافة هذه الوحدة إلى قائمة المحفوظات
                    kept_from_uom_ids.append(from_uom_id)

                    # إنشاء الصيغة: 1 [from_uom] = [factor] [base_uom]
                    formula = f'1 {from_uom.name} = {factor} {base_uom.name}'

                    # ✅ استخدام update_or_create بدلاً من create
                    conversion, created = UoMConversion.objects.update_or_create(
                        item=self.object,
                        company=self.request.current_company,
                        from_uom=from_uom,
                        defaults={
                            'conversion_factor': factor,
                            'formula_expression': formula,
                            'notes': f'تحويل من {from_uom.name} إلى الوحدة الأساسية {base_uom.name}'
                        }
                    )
                    saved_count += 1
                    if created:
                        logger.info(f"    ✅ Created conversion: {from_uom.name} → {base_uom.name} (factor: {factor})")
                    else:
                        logger.info(f"    🔄 Updated conversion: {from_uom.name} → {base_uom.name} (factor: {factor})")

                except (ValueError, UnitOfMeasure.DoesNotExist, IndexError) as e:
                    logger.error(f"    ❌ Error saving conversion {index}: {e}")
                    continue

        # ✅ حذف التحويلات التي لم تعد موجودة في الـ form
        logger.info(f"🗑️ Checking for conversions to delete...")
        logger.info(f"   - Kept from_uom_ids: {kept_from_uom_ids}")

        # جلب جميع التحويلات الموجودة
        old_conversions = UoMConversion.objects.filter(
            item=self.object,
            company=self.request.current_company
        )

        # التحويلات المطلوب حذفها = التي ليست في قائمة المحفوظات
        if kept_from_uom_ids:
            conversions_to_delete = old_conversions.exclude(from_uom_id__in=kept_from_uom_ids)
        else:
            # إذا كانت قائمة المحفوظات فارغة، احذف جميع التحويلات
            conversions_to_delete = old_conversions

        deleted_count = conversions_to_delete.count()
        if deleted_count > 0:
            logger.info(f"   - Deleting {deleted_count} conversions...")
            for conv in conversions_to_delete:
                logger.info(f"     ❌ Deleting: {conv.from_uom.name} → {base_uom.name}")
            conversions_to_delete.delete()

        logger.info(f"✅ Total conversions saved: {saved_count}")
        logger.info(f"✅ Total conversions deleted: {deleted_count}")
        return saved_count

    def save_pricing_from_json(self):
        """
        حفظ بيانات الأسعار من JSON بدلاً من formset
        """
        import json
        import logging
        from decimal import Decimal
        from apps.core.models import PriceListItem, PriceList, ItemVariant

        logger = logging.getLogger(__name__)
        logger.info(f"💰 save_pricing_from_json called for item {self.object.id}")

        # الحصول على بيانات الأسعار من JSON
        pricing_data_json = self.request.POST.get('pricing_data', '[]')

        try:
            pricing_data = json.loads(pricing_data_json)
            logger.info(f"📊 Received {len(pricing_data)} price entries")

            saved_count = 0
            updated_count = 0

            # جمع IDs للأسعار التي تم حفظها (للحفاظ عليها)
            processed_ids = []

            for price_entry in pricing_data:
                try:
                    price_list_id = int(price_entry['price_list_id'])
                    price = Decimal(str(price_entry['price']))
                    variant_id = price_entry.get('variant_id')
                    existing_id = price_entry.get('existing_id')

                    # التحقق من صحة السعر
                    if price <= 0:
                        continue

                    # الحصول على قائمة الأسعار
                    price_list = PriceList.objects.get(
                        pk=price_list_id,
                        company=self.request.current_company
                    )

                    # الحصول على المتغير إن وجد
                    variant = None
                    if variant_id and variant_id != '':
                        variant = ItemVariant.objects.get(
                            pk=int(variant_id),
                            company=self.request.current_company
                        )

                    # حفظ أو تحديث السعر
                    if existing_id:
                        # تحديث سعر موجود
                        try:
                            price_item = PriceListItem.objects.get(pk=int(existing_id))
                            price_item.price = price
                            price_item.save()
                            processed_ids.append(price_item.id)
                            updated_count += 1
                            logger.info(f"  🔄 Updated price: PriceList={price_list.name}, Variant={variant.code if variant else 'N/A'}, Price={price}")
                        except PriceListItem.DoesNotExist:
                            # إذا لم يوجد السعر القديم، أنشئ واحد جديد
                            price_item, created = PriceListItem.objects.get_or_create(
                                item=self.object,
                                price_list=price_list,
                                variant=variant,
                                defaults={'price': price}
                            )
                            if not created:
                                price_item.price = price
                                price_item.save()
                            processed_ids.append(price_item.id)
                            saved_count += 1
                            logger.info(f"  ✅ Created price: PriceList={price_list.name}, Variant={variant.code if variant else 'N/A'}, Price={price}")
                    else:
                        # إنشاء سعر جديد
                        price_item, created = PriceListItem.objects.get_or_create(
                            item=self.object,
                            price_list=price_list,
                            variant=variant,
                            defaults={'price': price}
                        )
                        if not created:
                            price_item.price = price
                            price_item.save()
                            updated_count += 1
                        else:
                            saved_count += 1
                        processed_ids.append(price_item.id)
                        logger.info(f"  ✅ {'Created' if created else 'Updated'} price: PriceList={price_list.name}, Variant={variant.code if variant else 'N/A'}, Price={price}")

                except (ValueError, PriceList.DoesNotExist, ItemVariant.DoesNotExist) as e:
                    logger.error(f"  ❌ Error saving price entry: {e}")
                    continue

            # حذف الأسعار التي لم تعد موجودة في البيانات الجديدة
            if processed_ids:
                deleted_count = PriceListItem.objects.filter(
                    item=self.object
                ).exclude(id__in=processed_ids).delete()[0]
            else:
                # إذا لم يكن هناك أسعار جديدة، احذف كل الأسعار القديمة
                deleted_count = PriceListItem.objects.filter(
                    item=self.object
                ).delete()[0]

            logger.info(f"✅ Pricing saved: {saved_count} new, {updated_count} updated, {deleted_count} deleted")
            return saved_count + updated_count

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing pricing JSON: {e}")
            return 0

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class ItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل المادة"""
    model = Item
    template_name = 'core/items/item_detail.html'
    context_object_name = 'item'
    permission_required = 'core.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إضافة المتغيرات للسياق
        variants = self.object.variants.select_related(
            'company'
        ).prefetch_related(
            'variant_attribute_values__attribute',
            'variant_attribute_values__value'
        ).all()

        # ✅ جلب الأسعار
        from apps.core.models import PriceList, PriceListItem

        # جلب جميع قوائم الأسعار النشطة
        price_lists = PriceList.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('is_default', 'name')  # القائمة الافتراضية أولاً

        # جلب أسعار هذا المادة
        if self.object.has_variants:
            # للمواد بمتغيرات - جلب أسعار كل متغير
            variants_with_prices = []
            for variant in variants:
                variant_prices = PriceListItem.objects.filter(
                    item=self.object,
                    variant=variant
                ).select_related('price_list').order_by('price_list__is_default', 'price_list__name')

                variants_with_prices.append({
                    'variant': variant,
                    'prices': variant_prices
                })

            context['variants_with_prices'] = variants_with_prices
        else:
            # للمواد بدون متغيرات
            item_prices = PriceListItem.objects.filter(
                item=self.object,
                variant__isnull=True
            ).select_related('price_list').order_by('price_list__is_default', 'price_list__name')

            context['item_prices'] = item_prices

        # ✅ جلب تحويلات وحدات القياس
        from apps.core.models import UoMConversion
        uom_conversions = UoMConversion.objects.filter(
            item=self.object,
            variant__isnull=True,
            is_active=True
        ).select_related('from_uom').order_by('from_uom__name')

        context.update({
            'title': _('تفاصيل المادة: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_item'),
            'can_delete': self.request.user.has_perm('core.delete_item'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المواد'), 'url': reverse('core:item_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:item_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:item_delete', kwargs={'pk': self.object.pk}),
            'variants': variants,
            'variants_count': variants.count(),
            'price_lists': price_lists,  # ✅ إضافة قوائم الأسعار
            'price_lists_count': price_lists.count(),  # ✅ عدد القوائم
            'uom_conversions': uom_conversions,  # ✅ إضافة التحويلات
            'uom_conversions_count': uom_conversions.count(),  # ✅ عدد التحويلات
        })
        return context


class ItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف مادة"""
    model = Item
    template_name = 'core/items/item_confirm_delete.html'
    permission_required = 'core.delete_item'
    success_url = reverse_lazy('core:item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف المادة: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المواد'), 'url': reverse('core:item_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:item_list'),
        })
        return context

    def delete(self, request, *args, **kwargs):
        """حذف مع رسالة تأكيد"""
        self.object = self.get_object()
        item_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف المادة "%(name)s" بنجاح') % {'name': item_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا المادة لوجود بيانات مرتبطة به')
            )
            return redirect('core:item_list')


# ===== تصنيفات المواد =====

class ItemCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FilterView):
    """قائمة تصنيفات المواد"""
    model = ItemCategory
    template_name = 'core/items/category_list.html'
    context_object_name = 'categories'
    permission_required = 'core.view_itemcategory'
    paginate_by = 25
    filterset_class = ItemCategoryFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة تصنيفات المواد'),
            'can_add': self.request.user.has_perm('core.add_itemcategory'),
            'can_change': self.request.user.has_perm('core.change_itemcategory'),
            'can_delete': self.request.user.has_perm('core.delete_itemcategory'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات المواد'), 'url': ''}
            ],
            'add_url': reverse('core:category_create'),
        })
        return context

    def get_queryset(self):
        """فلترة التصنيفات حسب الشركة مع البحث"""
        queryset = super().get_queryset()

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(code__icontains=search)
            )

        return queryset.select_related('parent').order_by('level', 'name')


class ItemCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'core/items/category_form.html'
    permission_required = 'core.add_itemcategory'
    success_url = reverse_lazy('core:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_template_names(self):
        # استخدام template مبسط للمودال
        if self.request.GET.get('modal') or self.request.headers.get('X-Requested-With'):
            return ['core/items/category_form_modal.html']
        return ['core/items/category_form.html']

    def form_valid(self, form):
        response = super().form_valid(form)

        # إذا كان الطلب AJAX
        if self.request.headers.get('X-Requested-With'):
            return JsonResponse({
                'success': True,
                'category_id': self.object.id,
                'category_name': self.object.name
            })

        messages.success(
            self.request,
            _('تم إضافة التصنيف "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        # إذا كان الطلب AJAX
        if self.request.headers.get('X-Requested-With'):
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if error_list else ''

            return JsonResponse({
                'success': False,
                'error': 'يرجى تصحيح الأخطاء',
                'errors': errors
            })

        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إذا كان مودال، تبسيط المحتوى
        if self.request.GET.get('modal'):
            context.update({
                'title': _('إضافة تصنيف جديد'),
                'is_modal': True,
            })
        else:
            context.update({
                'title': _('إضافة تصنيف جديد'),
                'breadcrumbs': [
                    {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                    {'title': _('تصنيفات المواد'), 'url': reverse('core:category_list')},
                    {'title': _('إضافة جديد'), 'url': ''}
                ],
                'submit_text': _('حفظ التصنيف'),
                'cancel_url': reverse('core:category_list'),
            })
        return context


class ItemCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل تصنيف"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'core/items/category_form.html'
    permission_required = 'core.change_itemcategory'
    success_url = reverse_lazy('core:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل التصنيف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات المواد'), 'url': reverse('core:category_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:category_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث التصنيف "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class ItemCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف تصنيف"""
    model = ItemCategory
    template_name = 'core/items/category_confirm_delete.html'
    permission_required = 'core.delete_itemcategory'
    success_url = reverse_lazy('core:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف التصنيف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات المواد'), 'url': reverse('core:category_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:category_list'),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        category_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف التصنيف "%(name)s" بنجاح') % {'name': category_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا التصنيف لوجود بيانات مرتبطة به')
            )
            return redirect('core:category_list')