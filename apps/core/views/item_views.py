# apps/core/views/item_views.py
"""
Views للأصناف والتصنيفات
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView,  TemplateView
from django.db.models import Q
from django_filters.views import FilterView

from ..models import Item, ItemCategory, Brand, UnitOfMeasure
from ..forms.item_forms import ItemForm, ItemCategoryForm, ItemVariantFormSet
from ..mixins import CompanyMixin, AuditLogMixin
from ..decorators import branch_required, permission_required_with_message
from ..filters import ItemFilter, ItemCategoryFilter


class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة الأصناف مع DataTable"""
    template_name = 'core/items/item_list.html'
    permission_required = 'core.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة الأصناف'),
            'can_add': self.request.user.has_perm('core.add_item'),
            'add_url': reverse('core:item_create'),
        })
        return context

class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, CreateView):
    """إضافة صنف جديد"""
    model = Item
    form_class = ItemForm
    template_name = 'core/items/item_form_with_variants.html'
    permission_required = 'core.add_item'
    success_url = reverse_lazy('core:item_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.POST:
            context['variant_formset'] = ItemVariantFormSet(self.request.POST, self.request.FILES)
        else:
            context['variant_formset'] = ItemVariantFormSet()

        context.update({
            'title': _('إضافة صنف جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('core:item_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ الصنف'),
            'cancel_url': reverse('core:item_list'),
        })
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        variant_formset = context['variant_formset']

        if form.is_valid() and variant_formset.is_valid():
            # لا تستدعي form.save() مباشرة، بل استدعي super() ليتم تشغيل الـ mixin
            response = super().form_valid(form)  # هذا سيشغل الـ mixin ويضيف الشركة

            # الآن احفظ المتغيرات
            variant_formset.instance = self.object
            variant_formset.save()

            messages.success(
                self.request,
                _('تم إضافة الصنف "%(name)s" مع متغيراته بنجاح') % {'name': self.object.name}
            )
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        """رسالة خطأ عند فشل الحفظ"""
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, UpdateView):
    """تعديل صنف"""
    model = Item
    form_class = ItemForm
    template_name = 'core/items/item_form.html'
    permission_required = 'core.change_item'
    success_url = reverse_lazy('core:item_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل الصنف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('core:item_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:item_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        """حفظ التعديلات مع رسالة نجاح"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث الصنف "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class ItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """تفاصيل الصنف"""
    model = Item
    template_name = 'core/items/item_detail.html'
    context_object_name = 'item'
    permission_required = 'core.view_item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تفاصيل الصنف: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_item'),
            'can_delete': self.request.user.has_perm('core.delete_item'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('core:item_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:item_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:item_delete', kwargs={'pk': self.object.pk}),
        })
        return context


class ItemDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف صنف"""
    model = Item
    template_name = 'core/items/item_confirm_delete.html'
    permission_required = 'core.delete_item'
    success_url = reverse_lazy('core:item_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف الصنف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الأصناف'), 'url': reverse('core:item_list')},
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
                _('تم حذف الصنف "%(name)s" بنجاح') % {'name': item_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا الصنف لوجود بيانات مرتبطة به')
            )
            return redirect('core:item_list')


# ===== تصنيفات الأصناف =====

class ItemCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, FilterView):
    """قائمة تصنيفات الأصناف"""
    model = ItemCategory
    template_name = 'core/items/category_list.html'
    context_object_name = 'categories'
    permission_required = 'core.view_itemcategory'
    paginate_by = 25
    filterset_class = ItemCategoryFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة تصنيفات الأصناف'),
            'can_add': self.request.user.has_perm('core.add_itemcategory'),
            'can_change': self.request.user.has_perm('core.change_itemcategory'),
            'can_delete': self.request.user.has_perm('core.delete_itemcategory'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات الأصناف'), 'url': ''}
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


class ItemCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                             CreateView):
    """إضافة تصنيف جديد"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'core/items/category_form.html'
    permission_required = 'core.add_itemcategory'
    success_url = reverse_lazy('core:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة تصنيف جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات الأصناف'), 'url': reverse('core:category_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ التصنيف'),
            'cancel_url': reverse('core:category_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة التصنيف "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class ItemCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                             UpdateView):
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
                {'title': _('تصنيفات الأصناف'), 'url': reverse('core:category_list')},
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


class ItemCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                             DeleteView):
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
                {'title': _('تصنيفات الأصناف'), 'url': reverse('core:category_list')},
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