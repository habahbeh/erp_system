# apps/core/views/price_views.py
"""
Views لقوائم الأسعار وأسعار المواد - ملف كامل
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
)
from django.db.models import Q, Count, Avg, Min, Max
from django.http import JsonResponse
from decimal import Decimal
import json

from ..models import PriceList, PriceListItem, Item, ItemVariant
from ..forms.price_forms import PriceListForm, PriceListItemForm, BulkPriceUpdateForm
from ..mixins import CompanyMixin, AuditLogMixin


# ===== قوائم الأسعار - CRUD =====

class PriceListListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة قوائم الأسعار مع DataTable"""
    template_name = 'core/price_lists/price_list_list.html'
    permission_required = 'core.view_pricelist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة قوائم الأسعار'),
            'can_add': self.request.user.has_perm('core.add_pricelist'),
            'add_url': reverse('core:price_list_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('قوائم الأسعار'), 'url': ''}
            ],
        })
        return context


class PriceListCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin,
                          AuditLogMixin, CreateView):
    """إضافة قائمة أسعار جديدة"""
    model = PriceList
    form_class = PriceListForm
    template_name = 'core/price_lists/price_list_form.html'
    permission_required = 'core.add_pricelist'
    success_url = reverse_lazy('core:price_list_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة قائمة أسعار جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('قوائم الأسعار'), 'url': reverse('core:price_list_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ قائمة الأسعار'),
            'cancel_url': reverse('core:price_list_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة قائمة الأسعار "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class PriceListUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin,
                          AuditLogMixin, UpdateView):
    """تعديل قائمة أسعار"""
    model = PriceList
    form_class = PriceListForm
    template_name = 'core/price_lists/price_list_form.html'
    permission_required = 'core.change_pricelist'
    success_url = reverse_lazy('core:price_list_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل قائمة الأسعار: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('قوائم الأسعار'), 'url': reverse('core:price_list_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:price_list_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث قائمة الأسعار "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class PriceListDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل قائمة أسعار"""
    model = PriceList
    template_name = 'core/price_lists/price_list_detail.html'
    context_object_name = 'price_list'
    permission_required = 'core.view_pricelist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات قائمة الأسعار
        items_count = self.object.items.filter(is_active=True).count()

        # حساب متوسط الأسعار
        price_stats = self.object.items.filter(is_active=True).aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )

        context.update({
            'title': _('قائمة الأسعار: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_pricelist'),
            'can_delete': self.request.user.has_perm('core.delete_pricelist'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('قوائم الأسعار'), 'url': reverse('core:price_list_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:price_list_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:price_list_delete', kwargs={'pk': self.object.pk}),
            'items_url': reverse('core:price_list_items', kwargs={'pk': self.object.pk}),
            'items_count': items_count,
            'avg_price': price_stats['avg_price'] or Decimal('0'),
            'min_price': price_stats['min_price'] or Decimal('0'),
            'max_price': price_stats['max_price'] or Decimal('0'),
        })
        return context


class PriceListDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin,
                          AuditLogMixin, DeleteView):
    """حذف قائمة أسعار"""
    model = PriceList
    template_name = 'core/price_lists/price_list_confirm_delete.html'
    permission_required = 'core.delete_pricelist'
    success_url = reverse_lazy('core:price_list_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد الأسعار المرتبطة
        items_count = self.object.items.count()

        context.update({
            'title': _('حذف قائمة الأسعار: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('قوائم الأسعار'), 'url': reverse('core:price_list_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:price_list_list'),
            'items_count': items_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        price_list_name = self.object.name

        # منع حذف القائمة الافتراضية
        if self.object.is_default:
            messages.error(
                request,
                _('لا يمكن حذف قائمة الأسعار الافتراضية')
            )
            return redirect('core:price_list_list')

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف قائمة الأسعار "%(name)s" بنجاح') % {'name': price_list_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذه القائمة لوجود بيانات مرتبطة بها')
            )
            return redirect('core:price_list_list')


# ===== إدارة أسعار المواد =====

class ItemPricesView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """صفحة إدارة أسعار مادة معين في جميع قوائم الأسعار"""
    template_name = 'core/items/item_prices.html'
    permission_required = 'core.view_pricelistitem'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        item_id = self.kwargs.get('item_id')
        item = get_object_or_404(Item, pk=item_id, company=self.request.current_company)

        price_lists = PriceList.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        # ✅ التعديل الأساسي: تغيير هيكل البيانات
        if item.has_variants:
            variants = item.variants.filter(is_active=True).select_related('company')

            variants_data = []
            for variant in variants:
                prices_dict = {}
                for price_list in price_lists:
                    try:
                        price_item = PriceListItem.objects.get(
                            price_list=price_list,
                            item=item,
                            variant=variant,
                            is_active=True
                        )
                        prices_dict[str(price_list.id)] = str(price_item.price)
                    except PriceListItem.DoesNotExist:
                        prices_dict[str(price_list.id)] = ''

                variants_data.append({
                    'variant': variant,
                    'prices': prices_dict  # ✅ dict بسيط {price_list_id: price}
                })

            context['variants_data'] = variants_data
        else:
            prices_dict = {}
            for price_list in price_lists:
                try:
                    price_item = PriceListItem.objects.get(
                        price_list=price_list,
                        item=item,
                        variant__isnull=True,
                        is_active=True
                    )
                    prices_dict[str(price_list.id)] = str(price_item.price)
                except PriceListItem.DoesNotExist:
                    prices_dict[str(price_list.id)] = ''

            context['prices'] = prices_dict  # ✅ {price_list_id: price}

        context.update({
            'item': item,
            'price_lists': price_lists,
            'title': _('إدارة أسعار: %(name)s') % {'name': item.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المواد'), 'url': reverse('core:item_list')},
                {'title': item.name, 'url': reverse('core:item_detail', kwargs={'pk': item.pk})},
                {'title': _('إدارة الأسعار'), 'url': ''}
            ],
        })
        return context


def update_item_prices(request, item_id):
    """حفظ أسعار مادة معين في جميع قوائم الأسعار"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if not request.user.has_perm('core.change_pricelistitem'):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)

    item = get_object_or_404(Item, pk=item_id, company=request.current_company)

    try:
        # حذف الأسعار القديمة
        PriceListItem.objects.filter(item=item).delete()

        updated_count = 0
        errors = []

        if item.has_variants:
            # معالجة أسعار المتغيرات
            for key, value in request.POST.items():
                if not key.startswith('price_'):
                    continue

                try:
                    # تنسيق: price_<price_list_id>_<variant_id>
                    parts = key.split('_')
                    if len(parts) != 3:
                        continue

                    price_list_id = int(parts[1])
                    variant_id = int(parts[2])

                    if not value or value.strip() == '':
                        continue

                    price_value = Decimal(value.strip())

                    if price_value <= 0:
                        continue

                    # التحقق من وجود قائمة الأسعار والمتغير
                    price_list = PriceList.objects.get(
                        pk=price_list_id,
                        company=request.current_company
                    )

                    variant = ItemVariant.objects.get(
                        pk=variant_id,
                        item=item
                    )

                    # إنشاء السعر
                    PriceListItem.objects.create(
                        price_list=price_list,
                        item=item,
                        variant=variant,
                        price=price_value
                    )
                    updated_count += 1

                except (ValueError, PriceList.DoesNotExist, ItemVariant.DoesNotExist, IndexError) as e:
                    errors.append(f"خطأ في {key}: {str(e)}")
                    continue
        else:
            # معالجة أسعار مادة بدون متغيرات
            for key, value in request.POST.items():
                if not key.startswith('price_'):
                    continue

                try:
                    price_list_id = int(key.split('_')[1])

                    if not value or value.strip() == '':
                        continue

                    price_value = Decimal(value.strip())

                    if price_value <= 0:
                        continue

                    price_list = PriceList.objects.get(
                        pk=price_list_id,
                        company=request.current_company
                    )

                    PriceListItem.objects.create(
                        price_list=price_list,
                        item=item,
                        variant=None,
                        price=price_value
                    )
                    updated_count += 1

                except (ValueError, PriceList.DoesNotExist) as e:
                    errors.append(f"خطأ في {key}: {str(e)}")
                    continue

        return JsonResponse({
            'success': True,
            'message': f'تم تحديث {updated_count} سعر بنجاح',
            'updated_count': updated_count,
            'errors': errors if errors else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'حدث خطأ: {str(e)}'
        }, status=500)


# ===== إدارة أمواد قائمة أسعار معينة =====

class PriceListItemsView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """صفحة إدارة أصناف قائمة أسعار - بـ DataTable"""
    template_name = 'core/price_lists/price_list_items.html'
    permission_required = 'core.view_pricelistitem'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        price_list_id = self.kwargs.get('pk')
        price_list = get_object_or_404(
            PriceList,
            pk=price_list_id,
            company=self.request.current_company
        )

        context.update({
            'price_list': price_list,
            'title': _('إدارة أصناف: %(name)s') % {'name': price_list.name},
            'can_change': self.request.user.has_perm('core.change_pricelistitem'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('قوائم الأسعار'), 'url': reverse('core:price_list_list')},
                {'title': price_list.name, 'url': reverse('core:price_list_detail', kwargs={'pk': price_list.pk})},
                {'title': _('إدارة الأصناف'), 'url': ''}
            ],
        })
        return context


def bulk_update_prices(request, price_list_id):
    """تحديث أسعار متعددة بالجملة في قائمة أسعار - POST endpoint"""
    if request.method != 'POST':
        return redirect('core:price_list_items', pk=price_list_id)

    if not request.user.has_perm('core.change_pricelistitem'):
        messages.error(request, _('ليس لديك صلاحية تعديل الأسعار'))
        return redirect('core:price_list_items', pk=price_list_id)

    # الحصول على قائمة الأسعار
    price_list = get_object_or_404(
        PriceList,
        pk=price_list_id,
        company=request.current_company
    )

    form = BulkPriceUpdateForm(request.POST, request=request)

    if form.is_valid():
        update_type = form.cleaned_data['update_type']
        value = form.cleaned_data['value']
        operation = form.cleaned_data.get('operation')
        round_to = form.cleaned_data.get('round_to')
        category = form.cleaned_data.get('category')
        brand = form.cleaned_data.get('brand')

        # فلترة الأسعار المراد تحديثها
        price_items = PriceListItem.objects.filter(
            price_list=price_list,
            is_active=True
        ).select_related('item')

        # تطبيق الفلاتر الإضافية
        if category:
            price_items = price_items.filter(item__category=category)

        if brand:
            price_items = price_items.filter(item__brand=brand)

        updated_count = 0

        for price_item in price_items:
            old_price = price_item.price
            new_price = old_price

            # تطبيق التحديث حسب النوع
            if update_type == 'percentage':
                percentage = value / Decimal('100')
                if operation == 'add':
                    new_price = old_price * (Decimal('1') + percentage)
                else:  # subtract
                    new_price = old_price * (Decimal('1') - percentage)

            elif update_type == 'fixed':
                if operation == 'add':
                    new_price = old_price + value
                else:  # subtract
                    new_price = old_price - value

            elif update_type == 'set':
                new_price = value

            # التقريب إذا طُلب
            if round_to:
                new_price = (new_price / round_to).quantize(Decimal('1')) * round_to

            # التأكد من أن السعر موجب
            if new_price > 0:
                price_item.price = new_price
                price_item.save()
                updated_count += 1

        messages.success(
            request,
            _('تم تحديث %(count)d سعر بنجاح') % {'count': updated_count}
        )
    else:
        messages.error(request, _('يرجى تصحيح الأخطاء في النموذج'))

    return redirect('core:price_list_items', pk=price_list_id)


def update_price_list_items(request, pk):
    """حفظ أسعار جميع المواد في قائمة أسعار معينة"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    if not request.user.has_perm('core.change_pricelistitem'):
        return JsonResponse({'success': False, 'error': 'ليس لديك صلاحية'}, status=403)

    price_list = get_object_or_404(PriceList, pk=pk, company=request.current_company)

    try:
        # حذف الأسعار القديمة لهذه القائمة
        PriceListItem.objects.filter(price_list=price_list).delete()

        updated_count = 0

        for key, value in request.POST.items():
            if not key.startswith('price_'):
                continue

            try:
                # تنسيق: price_<item_id> أو price_<item_id>_<variant_id>
                parts = key.split('_')
                item_id = int(parts[1])
                variant_id = int(parts[2]) if len(parts) == 3 else None

                if not value or value.strip() == '':
                    continue

                price_value = Decimal(value.strip())

                if price_value <= 0:
                    continue

                item = Item.objects.get(pk=item_id, company=request.current_company)

                variant = None
                if variant_id:
                    variant = ItemVariant.objects.get(pk=variant_id, item=item)

                PriceListItem.objects.create(
                    price_list=price_list,
                    item=item,
                    variant=variant,
                    price=price_value
                )
                updated_count += 1

            except (ValueError, Item.DoesNotExist, ItemVariant.DoesNotExist):
                continue

        return JsonResponse({
            'success': True,
            'message': f'تم تحديث {updated_count} سعر بنجاح',
            'updated_count': updated_count
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'حدث خطأ: {str(e)}'
        }, status=500)