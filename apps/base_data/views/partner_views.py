# apps/base_data/views/partner_views.py
"""
Views الشركاء التجاريين - العملاء والموردين
CRUD كامل + Bootstrap 5 + RTL + DataTables server-side
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404
from django.db.models import Q, Count, Sum, F
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction

from ..models import BusinessPartner, Customer, Supplier
from ..forms import (
    BusinessPartnerForm, CustomerForm, SupplierForm, BusinessPartnerFilterForm,
    PartnerQuickAddForm, ContactInfoForm, PartnerImportForm, PartnerExportForm
)
from core.mixins import CompanyMixin, AjaxResponseMixin
from core.utils import generate_code


class BusinessPartnerListView(LoginRequiredMixin, CompanyMixin, ListView):
    """عرض قائمة الشركاء التجاريين"""
    model = BusinessPartner
    template_name = 'base_data/partners/list.html'
    context_object_name = 'partners'
    paginate_by = 25

    def get_queryset(self):
        queryset = BusinessPartner.objects.filter(
            company=self.request.user.company
        ).select_related('salesperson', 'branch')

        # تطبيق الفلاتر
        self.filter_form = BusinessPartnerFilterForm(
            data=self.request.GET or None,
            company=self.request.user.company
        )

        if self.filter_form.is_valid():
            queryset = self.filter_form.get_queryset(queryset)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        stats = BusinessPartner.objects.filter(
            company=self.request.user.company
        ).aggregate(
            total=Count('id'),
            customers=Count('id', filter=Q(partner_type__in=['customer', 'both'])),
            suppliers=Count('id', filter=Q(partner_type__in=['supplier', 'both'])),
            active=Count('id', filter=Q(is_active=True))
        )

        context.update({
            'filter_form': self.filter_form,
            'page_title': _('الشركاء التجاريون'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('الشركاء التجاريون'), 'active': True}
            ],
            'stats': stats,
            'can_add': self.request.user.has_perm('base_data.add_businesspartner'),
            'can_change': self.request.user.has_perm('base_data.change_businesspartner'),
            'can_delete': self.request.user.has_perm('base_data.delete_businesspartner'),
        })
        return context


class CustomerListView(BusinessPartnerListView):
    """عرض قائمة العملاء فقط"""
    template_name = 'base_data/customers/list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(partner_type__in=['customer', 'both'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('العملاء'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('العملاء'), 'active': True}
            ],
        })
        return context


class SupplierListView(BusinessPartnerListView):
    """عرض قائمة الموردين فقط"""
    template_name = 'base_data/suppliers/list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(partner_type__in=['supplier', 'both'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('الموردين'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('الموردين'), 'active': True}
            ],
        })
        return context


class BusinessPartnerCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء شريك تجاري جديد"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'base_data/partners/form.html'
    permission_required = 'base_data.add_businesspartner'
    success_url = reverse_lazy('base_data:partner_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('إضافة شريك تجاري جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ الشريك'),
            'cancel_url': reverse('base_data:partner_list'),
        })
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            prefix = 'CUST' if form.instance.partner_type in ['customer', 'both'] else 'SUPP'
            form.instance.code = generate_code(prefix, self.request.user.company)

        self.object = form.save()
        messages.success(
            self.request,
            _('تم إنشاء الشريك "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('base_data:partner_detail', kwargs={'pk': self.object.pk})


class CustomerCreateView(BusinessPartnerCreateView):
    """إنشاء عميل جديد"""
    form_class = CustomerForm
    template_name = 'base_data/customers/form.html'
    success_url = reverse_lazy('base_data:customer_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('إضافة عميل جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('العملاء'), 'url': reverse('base_data:customer_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ العميل'),
            'cancel_url': reverse('base_data:customer_list'),
        })
        return context


class SupplierCreateView(BusinessPartnerCreateView):
    """إنشاء مورد جديد"""
    form_class = SupplierForm
    template_name = 'base_data/suppliers/form.html'
    success_url = reverse_lazy('base_data:supplier_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('إضافة مورد جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الموردين'), 'url': reverse('base_data:supplier_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ المورد'),
            'cancel_url': reverse('base_data:supplier_list'),
        })
        return context


class BusinessPartnerUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل شريك تجاري"""
    model = BusinessPartner
    form_class = BusinessPartnerForm
    template_name = 'base_data/partners/form.html'
    permission_required = 'base_data.change_businesspartner'
    context_object_name = 'partner'

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('تعديل الشريك: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
                {'title': self.object.name, 'active': True}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('base_data:partner_detail', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:partner_delete', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تحديث الشريك "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return redirect('base_data:partner_detail', pk=self.object.pk)

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BusinessPartnerDetailView(LoginRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل الشريك"""
    model = BusinessPartner
    template_name = 'base_data/partners/detail.html'
    context_object_name = 'partner'

    def get_queryset(self):
        return BusinessPartner.objects.filter(
            company=self.request.user.company
        ).select_related('salesperson', 'created_by', 'updated_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات الشريك
        stats = {
            'total_transactions': 0,  # من أنظمة أخرى
            'total_amount': 0,
            'outstanding_balance': 0,
            'last_transaction_date': None,
        }

        context.update({
            'page_title': self.object.name,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
                {'title': self.object.name, 'active': True}
            ],
            'stats': stats,
            'can_change': self.request.user.has_perm('base_data.change_businesspartner'),
            'can_delete': self.request.user.has_perm('base_data.delete_businesspartner'),
            'edit_url': reverse('base_data:partner_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:partner_delete', kwargs={'pk': self.object.pk}),
        })
        return context


class BusinessPartnerDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف شريك تجاري"""
    model = BusinessPartner
    template_name = 'base_data/partners/delete.html'
    permission_required = 'base_data.delete_businesspartner'
    success_url = reverse_lazy('base_data:partner_list')
    context_object_name = 'partner'

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # فحص الاستخدامات
        usage_count = {
            'sales_invoices': 0,  # من نظام المبيعات
            'purchase_invoices': 0,  # من نظام المشتريات
            'transactions': 0,  # من النظام المحاسبي
        }

        context.update({
            'page_title': _('حذف الشريك: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
                {'title': self.object.name, 'url': reverse('base_data:partner_detail', kwargs={'pk': self.object.pk})},
                {'title': _('حذف'), 'active': True}
            ],
            'usage_count': usage_count,
            'can_delete': sum(usage_count.values()) == 0,
            'cancel_url': reverse('base_data:partner_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # فحص إمكانية الحذف (يمكن إضافة فحص المعاملات هنا)
        name = self.object.name
        self.object.delete()

        messages.success(
            request,
            _('تم حذف الشريك "%(name)s" بنجاح') % {'name': name}
        )
        return redirect(self.success_url)


class PartnerQuickAddView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin, CreateView):
    """إضافة سريعة للشريك عبر AJAX"""
    model = BusinessPartner
    form_class = PartnerQuickAddForm
    template_name = 'base_data/partners/quick_add.html'
    permission_required = 'base_data.add_businesspartner'

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            prefix = 'CUST' if form.instance.partner_type in ['customer', 'both'] else 'SUPP'
            form.instance.code = generate_code(prefix, self.request.user.company)

        self.object = form.save()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('تم إنشاء الشريك بنجاح'),
                'partner': {
                    'id': self.object.pk,
                    'code': self.object.code,
                    'name': self.object.name,
                    'partner_type': self.object.get_partner_type_display(),
                    'phone': self.object.phone,
                    'email': self.object.email,
                }
            })

        messages.success(self.request, _('تم إنشاء الشريك بنجاح'))
        return redirect('base_data:partner_list')

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('يرجى تصحيح الأخطاء'),
                'errors': form.errors
            })
        return super().form_invalid(form)


class ContactInfoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تحديث معلومات الاتصال فقط"""
    model = BusinessPartner
    form_class = ContactInfoForm
    template_name = 'base_data/partners/contact_form.html'
    permission_required = 'base_data.change_businesspartner'
    context_object_name = 'partner'

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('تحديث معلومات الاتصال: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
                {'title': self.object.name, 'url': reverse('base_data:partner_detail', kwargs={'pk': self.object.pk})},
                {'title': _('معلومات الاتصال'), 'active': True}
            ],
            'submit_text': _('حفظ التغييرات'),
            'cancel_url': reverse('base_data:partner_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تحديث معلومات الاتصال للشريك "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return redirect('base_data:partner_detail', pk=self.object.pk)


class PartnerToggleActiveView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin):
    """تفعيل/إلغاء تفعيل الشريك"""
    permission_required = 'base_data.change_businesspartner'

    def post(self, request, pk):
        partner = get_object_or_404(BusinessPartner, pk=pk, company=request.user.company)

        partner.is_active = not partner.is_active
        partner.updated_by = request.user
        partner.save()

        status_text = _('نشط') if partner.is_active else _('غير نشط')
        message = _('تم تغيير حالة الشريك "%(name)s" إلى %(status)s') % {
            'name': partner.name,
            'status': status_text
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'is_active': partner.is_active,
                'status_text': status_text
            })

        messages.success(request, message)
        return redirect('base_data:partner_list')


# AJAX Views للـ DataTables
class PartnerDataTableView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin):
    """بيانات الشركاء لـ DataTables"""

    def get(self, request):
        draw = int(request.GET.get('draw', 0))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 25))
        search_value = request.GET.get('search[value]', '')
        order_column = int(request.GET.get('order[0][column]', 0))
        order_dir = request.GET.get('order[0][dir]', 'asc')
        partner_type = request.GET.get('partner_type', '')  # فلتر نوع الشريك

        # الأعمدة
        columns = ['code', 'name', 'partner_type', 'phone', 'email', 'city', 'is_active', 'created_at']
        order_column_name = columns[order_column] if order_column < len(columns) else 'created_at'

        if order_dir == 'desc':
            order_column_name = f'-{order_column_name}'

        # بناء الاستعلام
        queryset = BusinessPartner.objects.filter(
            company=request.user.company
        ).select_related('salesperson')

        # فلتر نوع الشريك
        if partner_type:
            if partner_type == 'both':
                queryset = queryset.filter(partner_type='both')
            else:
                queryset = queryset.filter(
                    Q(partner_type=partner_type) | Q(partner_type='both')
                )

        # البحث
        if search_value:
            queryset = queryset.filter(
                Q(code__icontains=search_value) |
                Q(name__icontains=search_value) |
                Q(phone__icontains=search_value) |
                Q(mobile__icontains=search_value) |
                Q(email__icontains=search_value) |
                Q(contact_person__icontains=search_value)
            )

        # العدد الكلي
        total_count = BusinessPartner.objects.filter(company=request.user.company).count()
        filtered_count = queryset.count()

        # الترتيب والتقسيم
        queryset = queryset.order_by(order_column_name)[start:start + length]

        # تحضير البيانات
        data = []
        for partner in queryset:
            data.append({
                'id': partner.pk,
                'code': partner.code or '',
                'name': partner.name,
                'partner_type': partner.get_partner_type_display(),
                'phone': partner.phone or '',
                'mobile': partner.mobile or '',
                'email': partner.email or '',
                'city': partner.city or '',
                'is_active': partner.is_active,
                'created_at': partner.created_at.strftime('%Y-%m-%d'),
                'actions': self._get_actions_html(partner, request)
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data
        })

    def _get_actions_html(self, partner, request):
        """HTML أزرار الإجراءات"""
        actions = []

        if request.user.has_perm('base_data.view_businesspartner'):
            actions.append(f'''
                <a href="{reverse('base_data:partner_detail', kwargs={'pk': partner.pk})}" 
                   class="btn btn-sm btn-light-primary" title="{_('عرض')}">
                    <i class="fas fa-eye"></i>
                </a>
            ''')

        if request.user.has_perm('base_data.change_businesspartner'):
            actions.append(f'''
                <a href="{reverse('base_data:partner_update', kwargs={'pk': partner.pk})}" 
                   class="btn btn-sm btn-light-warning" title="{_('تعديل')}">
                    <i class="fas fa-edit"></i>
                </a>
            ''')

            active_class = 'btn-success' if partner.is_active else 'btn-secondary'
            active_icon = 'fa-toggle-on' if partner.is_active else 'fa-toggle-off'
            active_title = _('إلغاء التفعيل') if partner.is_active else _('تفعيل')

            actions.append(f'''
                <button onclick="togglePartnerStatus({partner.pk})" 
                        class="btn btn-sm {active_class}" title="{active_title}">
                    <i class="fas {active_icon}"></i>
                </button>
            ''')

        if request.user.has_perm('base_data.delete_businesspartner'):
            actions.append(f'''
                <a href="{reverse('base_data:partner_delete', kwargs={'pk': partner.pk})}" 
                   class="btn btn-sm btn-light-danger" title="{_('حذف')}">
                    <i class="fas fa-trash"></i>
                </a>
            ''')

        return ''.join(actions)


# Views للبحث والتحديد
class PartnerSelectView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin):
    """بحث الشركاء للـ Select2"""

    def get(self, request):
        term = request.GET.get('term', '')
        partner_type = request.GET.get('partner_type', '')  # customer, supplier, both
        page = int(request.GET.get('page', 1))
        page_size = 20

        queryset = BusinessPartner.objects.filter(
            company=request.user.company,
            is_active=True
        )

        # فلتر نوع الشريك
        if partner_type:
            if partner_type == 'both':
                queryset = queryset.filter(partner_type='both')
            else:
                queryset = queryset.filter(
                    Q(partner_type=partner_type) | Q(partner_type='both')
                )

        if term:
            queryset = queryset.filter(
                Q(code__icontains=term) |
                Q(name__icontains=term) |
                Q(phone__icontains=term) |
                Q(mobile__icontains=term) |
                Q(email__icontains=term)
            )

        total_count = queryset.count()
        start = (page - 1) * page_size
        partners = queryset[start:start + page_size]

        results = []
        for partner in partners:
            results.append({
                'id': partner.pk,
                'text': f"{partner.code} - {partner.name}",
                'partner_type': partner.get_partner_type_display(),
                'phone': partner.phone or '',
                'email': partner.email or '',
                'city': partner.city or '',
                'credit_limit': float(partner.credit_limit) if partner.credit_limit else 0,
            })

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': start + page_size < total_count
            }
        })


class CustomerSelectView(PartnerSelectView):
    """بحث العملاء للـ Select2"""

    def get(self, request):
        request.GET = request.GET.copy()
        request.GET['partner_type'] = 'customer'
        return super().get(request)


class SupplierSelectView(PartnerSelectView):
    """بحث الموردين للـ Select2"""

    def get(self, request):
        request.GET = request.GET.copy()
        request.GET['partner_type'] = 'supplier'
        return super().get(request)


class PartnerStatementView(LoginRequiredMixin, CompanyMixin, DetailView):
    """كشف حساب الشريك"""
    model = BusinessPartner
    template_name = 'base_data/partners/statement.html'
    context_object_name = 'partner'

    def get_queryset(self):
        return BusinessPartner.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # هنا يمكن جلب المعاملات من الأنظمة الأخرى
        transactions = []  # قائمة المعاملات

        # حساب الأرصدة
        opening_balance = 0
        total_debit = 0
        total_credit = 0
        closing_balance = 0

        context.update({
            'page_title': _('كشف حساب: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('dashboard')},
                {'title': _('الشركاء التجاريون'), 'url': reverse('base_data:partner_list')},
                {'title': self.object.name, 'url': reverse('base_data:partner_detail', kwargs={'pk': self.object.pk})},
                {'title': _('كشف الحساب'), 'active': True}
            ],
            'transactions': transactions,
            'opening_balance': opening_balance,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'closing_balance': closing_balance,
        })
        return context


class PartnerConvertTypeView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin):
    """تحويل نوع الشريك (عميل إلى مورد أو العكس)"""
    permission_required = 'base_data.change_businesspartner'

    def post(self, request, pk):
        partner = get_object_or_404(BusinessPartner, pk=pk, company=request.user.company)
        new_type = request.POST.get('new_type')

        if new_type not in ['customer', 'supplier', 'both']:
            return JsonResponse({
                'success': False,
                'message': _('نوع الشريك غير صحيح')
            })

        old_type = partner.get_partner_type_display()
        partner.partner_type = new_type
        partner.updated_by = request.user
        partner.save()

        new_type_display = partner.get_partner_type_display()
        message = _('تم تحويل "%(name)s" من %(old_type)s إلى %(new_type)s') % {
            'name': partner.name,
            'old_type': old_type,
            'new_type': new_type_display
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'partner_type': new_type,
                'partner_type_display': new_type_display
            })

        messages.success(request, message)
        return redirect('base_data:partner_detail', pk=partner.pk)