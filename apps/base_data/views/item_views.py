# apps/base_data/views/item_views.py
"""
Views الخاصة بالأصناف
"""

from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum, F
from core.mixins import AuditLogMixin, CompanyBranchMixin
from ..models import Item, ItemCategory, UnitOfMeasure
from ..forms import ItemForm


class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, ListView):
    """قائمة الأصناف"""
    model = Item
    template_name = 'base_data/item/list.html'
    context_object_name = 'items'
    permission_required = 'base_data.view_item'
    paginate_by = 20

    def get_queryset(self):
        """فلترة والبحث"""
        queryset = super().get_queryset()

        # البحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(barcode__icontains=search) |
                Q(manufacturer__icontains=search)
            )

        # فلترة حسب التصنيف
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # فلترة حسب الحالة
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')

        # فلترة الأصناف التي نفذت
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'out_of_stock':
            # سيتم تطوير هذا لاحقاً مع نظام المخزون
            pass

        return queryset.select_related('category', 'unit')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('الأصناف')
        context['can_add'] = self.request.user.has_perm('base_data.add_item')

        # قائمة التصنيفات للفلترة
        context['categories'] = ItemCategory.objects.filter(
            company=self.request.user.company,
            is_active=True
        )

        return context


class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة صنف جديد"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/item/form.html'
    permission_required = 'base_data.add_item'
    success_url = reverse_lazy('base_data:item_list')

    def get_form_kwargs(self):
        """إضافة الشركة للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        """إضافة البيانات التلقائية"""
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            _('تم إضافة الصنف %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة صنف جديد')
        context['submit_text'] = _('حفظ')
        return context


class ItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, DetailView):
    """تفاصيل الصنف"""
    model = Item
    template_name = 'base_data/item/detail.html'
    context_object_name = 'item'
    permission_required = 'base_data.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.name

        # صلاحيات الأزرار
        context['can_edit'] = self.request.user.has_perm('base_data.change_item')
        context['can_delete'] = self.request.user.has_perm('base_data.delete_item')

        # إحصائيات المخزون (سيتم تطويرها لاحقاً)
        context['current_stock'] = 0
        context['total_purchases'] = 0
        context['total_sales'] = 0

        # حساب هامش الربح
        if self.object.purchase_price > 0:
            profit_margin = ((self.object.sale_price - self.object.purchase_price) / self.object.purchase_price) * 100
            context['profit_margin'] = profit_margin
        else:
            context['profit_margin'] = 0

        return context


class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل الصنف"""
    model = Item
    form_class = ItemForm
    template_name = 'base_data/item/form.html'
    permission_required = 'base_data.change_item'
    success_url = reverse_lazy('base_data:item_list')

    def get_form_kwargs(self):
        """إضافة الشركة للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        """تحديث المستخدم الذي عدّل"""
        form.instance.updated_by = self.request.user

        # التحقق من صلاحية تعديل الأسعار
        if self.object.sale_price != form.instance.sale_price:
            if not self.request.user.has_perm('base_data.modify_prices'):
                messages.error(
                    self.request,
                    _('ليس لديك صلاحية تعديل الأسعار')
                )
                return self.form_invalid(form)

        messages.success(
            self.request,
            _('تم تعديل الصنف %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل الصنف: %(name)s') % {'name': self.object.name}
        context['submit_text'] = _('حفظ التعديلات')
        return context


class ItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف الصنف"""
    model = Item
    template_name = 'base_data/item/confirm_delete.html'
    permission_required = 'base_data.delete_item'
    success_url = reverse_lazy('base_data:item_list')

    def delete(self, request, *args, **kwargs):
        """رسالة نجاح عند الحذف"""
        item = self.get_object()
        messages.success(
            self.request,
            _('تم حذف الصنف %(name)s بنجاح') % {'name': item.name}
        )
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف الصنف')
        context['message'] = _('هل أنت متأكد من حذف الصنف %(name)s؟') % {'name': self.object.name}
        return context