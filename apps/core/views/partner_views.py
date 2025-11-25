# في apps/core/views/partner_views.py - استبدال بالكامل

"""
Views للعملاء (العملاء والموردين) مع المرفقات والمندوبين المتعددين
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.shortcuts import redirect
from django.db import transaction

from ..models import BusinessPartner, PartnerRepresentative
from ..forms.partner_forms import BusinessPartnerForm, PartnerRepresentativeFormSet
from ..mixins import CompanyBranchMixin, CompanyMixin, AuditLogMixin


class BusinessPartnerListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, TemplateView):
    """قائمة العملاء مع DataTable"""
    template_name = 'core/partners/partner_list.html'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة العملاء'),
            'can_add': self.request.user.has_perm('core.add_businesspartner'),
            'add_url': reverse('core:partner_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': ''}
            ],
        })
        return context


class BusinessPartnerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin,
                                CreateView):
    """إضافة عميل جديد مع المندوبين"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'core/partners/partner_form.html'
    permission_required = 'core.add_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['representative_formset'] = PartnerRepresentativeFormSet(
                self.request.POST
            )
        else:
            # للإنشاء الجديد - إنشاء FormSet فارغ
            context['representative_formset'] = PartnerRepresentativeFormSet(
                queryset=PartnerRepresentative.objects.none()
            )

        context.update({
            'title': _('إضافة عميل جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ العميل'),
            'cancel_url': reverse('core:partner_list'),
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        representative_formset = context['representative_formset']

        with transaction.atomic():
            # حفظ العميل أولاً
            self.object = form.save()

            # ربط FormSet بالعميل المحفوظ
            representative_formset.instance = self.object

            if representative_formset.is_valid():
                # حفظ المندوبين
                representatives = representative_formset.save(commit=False)
                for representative in representatives:
                    representative.company = self.request.current_company
                    representative.created_by = self.request.user
                    representative.save()

                # حذف المندوبين المحذوفين
                for obj in representative_formset.deleted_objects:
                    obj.delete()

                messages.success(
                    self.request,
                    _('تم إضافة العميل "%(name)s" بنجاح مع %(count)d مندوب') % {
                        'name': self.object.name,
                        'count': len(representatives)
                    }
                )
                return super().form_valid(form)
            else:
                # إذا فشل FormSet، احذف العميل المحفوظ
                transaction.set_rollback(True)
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin,
                                UpdateView):
    """تعديل عميل مع المندوبين"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'core/partners/partner_form.html'
    permission_required = 'core.change_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['representative_formset'] = PartnerRepresentativeFormSet(
                self.request.POST,
                instance=self.object
            )
        else:
            context['representative_formset'] = PartnerRepresentativeFormSet(
                instance=self.object
            )

        context.update({
            'title': _('تعديل العميل: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:partner_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        representative_formset = context['representative_formset']

        with transaction.atomic():
            # حفظ العميل
            self.object = form.save()

            if representative_formset.is_valid():
                # حفظ المندوبين
                representatives = representative_formset.save(commit=False)
                for representative in representatives:
                    if not representative.company:
                        representative.company = self.request.current_company
                    if not representative.created_by:
                        representative.created_by = self.request.user
                    representative.save()

                # حذف المندوبين المحذوفين
                for obj in representative_formset.deleted_objects:
                    obj.delete()

                messages.success(
                    self.request,
                    _('تم تحديث العميل "%(name)s" بنجاح') % {'name': self.object.name}
                )
                return super().form_valid(form)
            else:
                transaction.set_rollback(True)
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل العميل مع المندوبين والمرفقات"""
    model = BusinessPartner
    template_name = 'core/partners/partner_detail.html'
    context_object_name = 'partner'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # جلب المندوبين
        representatives = self.object.representatives.all().order_by('-is_primary', 'representative_name')

        context.update({
            'title': _('تفاصيل العميل: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_businesspartner'),
            'can_delete': self.request.user.has_perm('core.delete_businesspartner'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:partner_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:partner_delete', kwargs={'pk': self.object.pk}),
            'representatives': representatives,
            'effective_tax_status': self.object.get_effective_tax_status(),
            'is_tax_exempt_active': self.object.is_tax_exempt_active(),
        })
        return context


class BusinessPartnerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, AuditLogMixin,
                                DeleteView):
    """حذف عميل"""
    model = BusinessPartner
    template_name = 'core/partners/partner_confirm_delete.html'
    permission_required = 'core.delete_businesspartner'
    success_url = reverse_lazy('core:partner_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عد المندوبين المرتبطين
        representatives_count = self.object.representatives.count()

        context.update({
            'title': _('حذف العميل: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:partner_list'),
            'representatives_count': representatives_count,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        partner_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف العميل "%(name)s" بنجاح') % {'name': partner_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا العميل لوجود بيانات مرتبطة به')
            )
            return redirect('core:partner_list')


# AJAX Views
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


@login_required
@require_POST
def partner_create_ajax(request):
    """إنشاء شريك تجاري عبر AJAX"""
    try:
        # التحقق من الصلاحيات
        if not request.user.has_perm('core.add_businesspartner'):
            return JsonResponse({
                'success': False,
                'error': 'ليس لديك صلاحية لإضافة موردين'
            }, status=403)

        # الحصول على البيانات
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        tax_number = request.POST.get('tax_number', '').strip()
        address = request.POST.get('address', '').strip()
        partner_type = request.POST.get('partner_type', 'supplier')
        is_active = request.POST.get('is_active', 'true') == 'true'

        # التحقق من الحقول المطلوبة
        errors = {}
        if not name:
            errors['name'] = 'الاسم مطلوب'
        if not code:
            errors['code'] = 'رمز المورد مطلوب'

        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors,
                'error': 'يرجى تعبئة جميع الحقول المطلوبة'
            }, status=400)

        # إنشاء المورد
        with transaction.atomic():
            supplier = BusinessPartner.objects.create(
                company=request.current_company,
                created_by=request.user,
                name=name,
                code=code,
                email=email or '',
                phone=phone or '',
                mobile=mobile or '',
                tax_number=tax_number or '',
                address=address or '',
                partner_type=partner_type,
                is_active=is_active,
                # الحقول المطلوبة الأخرى
                account_type='credit',  # افتراضي: ذمم
                tax_status='taxable',   # افتراضي: خاضع
                credit_limit=0,          # افتراضي: 0
                credit_period=0          # افتراضي: 0
            )

        return JsonResponse({
            'success': True,
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'code': supplier.code,
                'email': supplier.email,
                'phone': supplier.phone,
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def item_search_ajax(request):
    """البحث في المنتجات عبر AJAX للاستخدام مع Select2"""
    try:
        search_term = request.GET.get('q', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = 20

        from ..models import Item

        # البحث في المنتجات مع prefetch للمتغيرات والأسعار
        items = Item.objects.filter(
            company=request.current_company,
            is_active=True
        ).select_related(
            'base_uom', 'category'
        ).prefetch_related(
            'variants',
            'price_list_items__price_list'
        )

        if search_term:
            # البحث في كل كلمة من كلمات البحث
            search_words = search_term.split()
            from django.db.models import Q

            for word in search_words:
                items = items.filter(
                    Q(name__icontains=word) |
                    Q(name_en__icontains=word) |
                    Q(code__icontains=word) |
                    Q(barcode__icontains=word)
                )

        # حساب العدد الإجمالي
        total_count = items.count()

        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        items = items[start:end]

        # تحويل النتائج إلى JSON
        results = []
        for item in items:
            # جمع المتغيرات النشطة
            variants = []
            for variant in item.variants.filter(is_active=True):
                variant_data = {
                    'id': variant.id,
                    'code': variant.code,
                    'barcode': variant.barcode or '',
                }
                # إضافة السمات إذا كانت موجودة
                if hasattr(variant, 'attribute_values') and variant.attribute_values:
                    variant_data['attributes'] = variant.attribute_values
                variants.append(variant_data)

            # جمع الأسعار من قوائم الأسعار النشطة
            prices = []
            default_price = None
            for price_item in item.price_list_items.filter(
                price_list__is_active=True
            ).select_related('price_list'):
                price_data = {
                    'price_list_name': price_item.price_list.name,
                    'price': str(price_item.price),
                    'is_default': price_item.price_list.is_default
                }
                prices.append(price_data)

                # حفظ السعر الافتراضي
                if price_item.price_list.is_default:
                    default_price = str(price_item.price)

            results.append({
                'id': item.id,
                'text': f"{item.code} - {item.name}",
                'name': item.name,
                'code': item.code,
                'unit': item.base_uom.name if item.base_uom else '',
                'unit_id': item.base_uom.id if item.base_uom else None,
                'variants': variants,
                'prices': prices,
                'default_price': default_price
            })

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': end < total_count
            }
        })

    except Exception as e:
        return JsonResponse({
            'results': [],
            'error': str(e)
        }, status=500)


class PartnerItemPricesView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض أسعار المواد للشريك التجاري (مورد/عميل)"""
    model = BusinessPartner
    template_name = 'core/partners/partner_item_prices.html'
    context_object_name = 'partner'
    permission_required = 'core.view_businesspartner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.core.models import PartnerItemPrice

        # Get all item prices for this partner
        item_prices = PartnerItemPrice.objects.filter(
            partner=self.object,
            company=self.current_company
        ).select_related(
            'item', 'item_variant'
        ).order_by('-last_purchase_date', '-last_sale_date')

        # Separate into purchase and sales prices
        purchase_prices = item_prices.filter(last_purchase_price__isnull=False)
        sales_prices = item_prices.filter(last_sale_price__isnull=False)

        context.update({
            'title': _('أسعار المواد - %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('العملاء'), 'url': reverse('core:partner_list')},
                {'title': self.object.name, 'url': reverse('core:partner_detail', kwargs={'pk': self.object.pk})},
                {'title': _('أسعار المواد'), 'url': ''}
            ],
            'item_prices': item_prices,
            'purchase_prices': purchase_prices,
            'sales_prices': sales_prices,
            'is_supplier': self.object.is_supplier(),
            'is_customer': self.object.is_customer(),
        })
        return context