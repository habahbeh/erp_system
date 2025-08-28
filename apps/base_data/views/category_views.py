# apps/base_data/views/category_views.py
"""
Views تصنيفات الأصناف - 4 مستويات
CRUD كامل + Bootstrap 5 + RTL + Tree structure
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
from django.views import View

from ..models import ItemCategory, Item
from ..forms import ItemCategoryForm, ItemCategoryQuickAddForm
from apps.core.mixins import CompanyMixin, AjaxResponseMixin
from apps.core.utils import generate_code


class ItemCategoryListView(LoginRequiredMixin, CompanyMixin, ListView):
    """عرض قائمة تصنيفات الأصناف - شجرة التصنيفات"""
    model = ItemCategory
    template_name = 'base_data/categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        queryset = ItemCategory.objects.filter(
            company=self.request.user.company
        ).select_related('parent')

        # عرض شجري - الأصناف الرئيسية أولاً
        return queryset.order_by('level', 'parent__name', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        stats = ItemCategory.objects.filter(
            company=self.request.user.company
        ).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            level_1=Count('id', filter=Q(level=1)),
            level_2=Count('id', filter=Q(level=2)),
            level_3=Count('id', filter=Q(level=3)),
            level_4=Count('id', filter=Q(level=4))
        )

        # بناء الشجرة
        categories_tree = self._build_tree()

        context.update({
            'page_title': _('تصنيفات الأصناف'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('البيانات الأساسية'), 'url': '#'},
                {'title': _('تصنيفات الأصناف'), 'active': True}
            ],
            'stats': stats,
            'categories_tree': categories_tree,
            'can_add': self.request.user.has_perm('base_data.add_itemcategory'),
            'can_change': self.request.user.has_perm('base_data.change_itemcategory'),
            'can_delete': self.request.user.has_perm('base_data.delete_itemcategory'),
        })
        return context

    def _build_tree(self):
        """بناء شجرة التصنيفات"""
        categories = list(self.get_queryset())
        tree = []

        # إنشاء dictionary للوصول السريع
        category_dict = {cat.id: cat for cat in categories}

        # إضافة children list لكل تصنيف
        for cat in categories:
            cat.children = []
            cat.item_count = Item.objects.filter(
                category=cat,
                company=self.request.user.company
            ).count()

        # بناء الشجرة
        for cat in categories:
            if cat.parent_id:
                if cat.parent_id in category_dict:
                    category_dict[cat.parent_id].children.append(cat)
            else:
                tree.append(cat)

        return tree


class ItemCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, CreateView):
    """إنشاء تصنيف جديد"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'base_data/categories/form.html'
    permission_required = 'base_data.add_itemcategory'
    success_url = reverse_lazy('base_data:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parent_id = self.request.GET.get('parent')
        parent_category = None
        if parent_id:
            try:
                parent_category = ItemCategory.objects.get(
                    pk=parent_id,
                    company=self.request.user.company
                )
                # تعيين الأب الافتراضي في النموذج
                context['form'].fields['parent'].initial = parent_category
            except ItemCategory.DoesNotExist:
                pass

        context.update({
            'page_title': _('إضافة تصنيف جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات الأصناف'), 'url': reverse('base_data:category_list')},
                {'title': _('إضافة جديد'), 'active': True}
            ],
            'submit_text': _('حفظ التصنيف'),
            'cancel_url': reverse('base_data:category_list'),
            'parent_category': parent_category,
        })
        return context

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            form.instance.code = generate_code('CAT', self.request.user.company)

        self.object = form.save()
        messages.success(
            self.request,
            _('تم إنشاء التصنيف "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('base_data:category_detail', kwargs={'pk': self.object.pk})


class ItemCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, UpdateView):
    """تعديل تصنيف"""
    model = ItemCategory
    form_class = ItemCategoryForm
    template_name = 'base_data/categories/form.html'
    permission_required = 'base_data.change_itemcategory'
    context_object_name = 'category'

    def get_queryset(self):
        return ItemCategory.objects.filter(company=self.request.user.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': _('تعديل التصنيف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات الأصناف'), 'url': reverse('base_data:category_list')},
                {'title': self.object.name, 'active': True}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('base_data:category_detail', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:category_delete', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        self.object = form.save()

        messages.success(
            self.request,
            _('تم تحديث التصنيف "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return redirect('base_data:category_detail', pk=self.object.pk)


class ItemCategoryDetailView(LoginRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل التصنيف"""
    model = ItemCategory
    template_name = 'base_data/categories/detail.html'
    context_object_name = 'category'

    def get_queryset(self):
        return ItemCategory.objects.filter(
            company=self.request.user.company
        ).select_related('parent', 'created_by', 'updated_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # التصنيفات الفرعية
        children = ItemCategory.objects.filter(
            parent=self.object,
            company=self.request.user.company
        ).order_by('name')

        # الأصناف في هذا التصنيف
        items = Item.objects.filter(
            category=self.object,
            company=self.request.user.company
        ).select_related('unit')[:20]  # أول 20 صنف

        # إحصائيات
        stats = {
            'children_count': children.count(),
            'items_count': Item.objects.filter(
                category=self.object,
                company=self.request.user.company
            ).count(),
            'active_items': Item.objects.filter(
                category=self.object,
                company=self.request.user.company,
                is_active=True,
                is_inactive=False
            ).count(),
        }

        # مسار التصنيف (breadcrumb)
        path = []
        current = self.object
        while current:
            path.insert(0, current)
            current = current.parent

        context.update({
            'page_title': self.object.name,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات الأصناف'), 'url': reverse('base_data:category_list')},
                {'title': self.object.name, 'active': True}
            ],
            'children': children,
            'items': items,
            'stats': stats,
            'path': path,
            'can_change': self.request.user.has_perm('base_data.change_itemcategory'),
            'can_delete': self.request.user.has_perm('base_data.delete_itemcategory'),
            'can_add_child': self.object.level < 4,  # أقصى 4 مستويات
            'edit_url': reverse('base_data:category_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('base_data:category_delete', kwargs={'pk': self.object.pk}),
            'add_child_url': reverse('base_data:category_create') + f'?parent={self.object.pk}',
        })
        return context


class ItemCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DeleteView):
    """حذف تصنيف"""
    model = ItemCategory
    template_name = 'base_data/categories/delete.html'
    permission_required = 'base_data.delete_itemcategory'
    success_url = reverse_lazy('base_data:category_list')
    context_object_name = 'category'

    def get_queryset(self):
        return ItemCategory.objects.filter(company=self.request.user.company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # فحص الاستخدامات
        children_count = ItemCategory.objects.filter(
            parent=self.object,
            company=self.request.user.company
        ).count()

        items_count = Item.objects.filter(
            category=self.object,
            company=self.request.user.company
        ).count()

        context.update({
            'page_title': _('حذف التصنيف: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('تصنيفات الأصناف'), 'url': reverse('base_data:category_list')},
                {'title': self.object.name, 'url': reverse('base_data:category_detail', kwargs={'pk': self.object.pk})},
                {'title': _('حذف'), 'active': True}
            ],
            'children_count': children_count,
            'items_count': items_count,
            'can_delete': children_count == 0 and items_count == 0,
            'cancel_url': reverse('base_data:category_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # فحص إمكانية الحذف
        children_count = ItemCategory.objects.filter(
            parent=self.object,
            company=request.user.company
        ).count()

        items_count = Item.objects.filter(
            category=self.object,
            company=request.user.company
        ).count()

        if children_count > 0 or items_count > 0:
            messages.error(
                request,
                _('لا يمكن حذف التصنيف "%(name)s" لأنه يحتوي على تصنيفات فرعية أو أصناف') % {
                    'name': self.object.name
                }
            )
            return redirect('base_data:category_detail', pk=self.object.pk)

        name = self.object.name
        self.object.delete()

        messages.success(
            request,
            _('تم حذف التصنيف "%(name)s" بنجاح') % {'name': name}
        )
        return redirect(self.success_url)


class CategoryQuickAddView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin, CreateView):
    """إضافة سريعة للتصنيف عبر AJAX"""
    model = ItemCategory
    form_class = ItemCategoryQuickAddForm
    template_name = 'base_data/categories/quick_add.html'
    permission_required = 'base_data.add_itemcategory'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user

        if not form.instance.code:
            form.instance.code = generate_code('CAT', self.request.user.company)

        self.object = form.save()

        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('تم إنشاء التصنيف بنجاح'),
                'category': {
                    'id': self.object.pk,
                    'code': self.object.code,
                    'name': self.object.name,
                    'level': self.object.level,
                    'parent': self.object.parent.name if self.object.parent else None,
                }
            })

        messages.success(self.request, _('تم إنشاء التصنيف بنجاح'))
        return redirect('base_data:category_list')

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': _('يرجى تصحيح الأخطاء'),
                'errors': form.errors
            })
        return super().form_invalid(form)


class CategorySelectView(LoginRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """بحث التصنيفات للـ Select2"""

    def get(self, request):
        term = request.GET.get('term', '')
        page = int(request.GET.get('page', 1))
        page_size = 20
        level = request.GET.get('level')  # فلتر المستوى

        queryset = ItemCategory.objects.filter(
            company=request.user.company,
            is_active=True
        ).select_related('parent')

        if level:
            queryset = queryset.filter(level=int(level))

        if term:
            queryset = queryset.filter(
                Q(code__icontains=term) |
                Q(name__icontains=term) |
                Q(name_en__icontains=term)
            )

        total_count = queryset.count()
        start = (page - 1) * page_size
        categories = queryset.order_by('level', 'name')[start:start + page_size]

        results = []
        for category in categories:
            # بناء النص مع المستوى
            text = '  ' * (category.level - 1) + category.name
            if category.code:
                text = f"{category.code} - {text}"

            results.append({
                'id': category.pk,
                'text': text,
                'level': category.level,
                'code': category.code or '',
                'parent': category.parent.name if category.parent else '',
            })

        return JsonResponse({
            'results': results,
            'pagination': {
                'more': start + page_size < total_count
            }
        })


class CategoryMoveView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AjaxResponseMixin, View):
    """نقل تصنيف لتصنيف أب آخر"""
    permission_required = 'base_data.change_itemcategory'

    def post(self, request, pk):
        category = get_object_or_404(ItemCategory, pk=pk, company=request.user.company)
        new_parent_id = request.POST.get('new_parent_id')

        if new_parent_id:
            try:
                new_parent = ItemCategory.objects.get(
                    pk=new_parent_id,
                    company=request.user.company
                )

                # التحقق من عدم إنشاء حلقة مفرغة
                if category.pk == new_parent.pk:
                    return JsonResponse({
                        'success': False,
                        'message': _('لا يمكن جعل التصنيف أباً لنفسه')
                    })

                # التحقق من المستوى الأقصى
                if new_parent.level >= 4:
                    return JsonResponse({
                        'success': False,
                        'message': _('تجاوز العمق الأقصى للتصنيفات (4 مستويات)')
                    })

                category.parent = new_parent
                category.save()

            except ItemCategory.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': _('التصنيف الأب غير موجود')
                })
        else:
            # جعله تصنيف رئيسي
            category.parent = None
            category.save()

        category.updated_by = request.user
        category.save()

        return JsonResponse({
            'success': True,
            'message': _('تم نقل التصنيف بنجاح'),
            'new_level': category.level
        })