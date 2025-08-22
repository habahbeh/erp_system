# apps/base_data/views/category_views.py
"""
Views الخاصة بتصنيفات الأصناف
"""

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from core.mixins import AuditLogMixin, CompanyBranchMixin
from ..models import ItemCategory
from ..forms import ItemCategoryForm


class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyBranchMixin, ListView):
    """قائمة التصنيفات"""
    model = ItemCategory
    template_name = 'base_data/category/list.html'
    context_object_name = 'categories'
    permission_required = 'base_data.view_itemcategory'
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
                Q(name_en__icontains=search)
            )

        # فلترة حسب المستوى
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)

        # إضافة عدد الأصناف
        queryset = queryset.annotate(items_count=Count('item'))

        return queryset.select_related('parent')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تصنيفات الأصناف')
        context['can_add'] = self.request.user.has_perm('base_data.add_itemcategory')
        return context


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    """إضافة تصنيف جديد"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'base_data/category/form.html'
    permission_required = 'base_data.add_itemcategory'
    success_url = reverse_lazy('base_data:category_list')

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
            _('تم إضافة التصنيف %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('إضافة تصنيف جديد')
        context['submit_text'] = _('حفظ')
        return context


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    """تعديل التصنيف"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'base_data/category/form.html'
    permission_required = 'base_data.change_itemcategory'
    success_url = reverse_lazy('base_data:category_list')

    def get_form_kwargs(self):
        """إضافة الشركة للنموذج"""
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        """تحديث المستخدم الذي عدّل"""
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            _('تم تعديل التصنيف %(name)s بنجاح') % {'name': form.instance.name}
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('تعديل التصنيف: %(name)s') % {'name': self.object.name}
        context['submit_text'] = _('حفظ التعديلات')
        return context


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, DeleteView):
    """حذف التصنيف"""
    model = ItemCategory
    template_name = 'base_data/category/confirm_delete.html'
    permission_required = 'base_data.delete_itemcategory'
    success_url = reverse_lazy('base_data:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('حذف التصنيف')
        context['message'] = _('هل أنت متأكد من حذف التصنيف %(name)s؟') % {'name': self.object.name}

        # التحقق من وجود تصنيفات فرعية
        context['has_children'] = self.object.children.exists()

        # التحقق من وجود أصناف
        context['has_items'] = self.object.item_set.exists()

        return context

    def delete(self, request, *args, **kwargs):
        """منع الحذف إذا كان هناك تصنيفات فرعية أو أصناف"""
        category = self.get_object()

        # التحقق من التصنيفات الفرعية
        if category.children.exists():
            messages.error(
                self.request,
                _('لا يمكن حذف التصنيف %(name)s لأنه يحتوي على تصنيفات فرعية') % {'name': category.name}
            )
            return self.get(request, *args, **kwargs)

        # التحقق من الأصناف
        if category.item_set.exists():
            messages.error(
                self.request,
                _('لا يمكن حذف التصنيف %(name)s لأنه يحتوي على أصناف') % {'name': category.name}
            )
            return self.get(request, *args, **kwargs)

        messages.success(
            self.request,
            _('تم حذف التصنيف %(name)s بنجاح') % {'name': category.name}
        )
        return super().delete(request, *args, **kwargs)