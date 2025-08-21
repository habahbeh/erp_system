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