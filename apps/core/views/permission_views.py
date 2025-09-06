# apps/core/views/permission_views.py
"""
Views إدارة الصلاحيات المخصصة
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, FormView
from django.db.models import Q, Count
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import render

from ..models import CustomPermission, PermissionGroup, UserProfile
from ..forms.permission_forms import (
    CustomPermissionForm, PermissionGroupForm, BulkPermissionAssignForm, CopyUserPermissionsForm
)
from ..mixins import UserMixin, AuditLogMixin

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required


User = get_user_model()


class CustomPermissionListView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, TemplateView):
    """قائمة الصلاحيات المخصصة"""
    template_name = 'core/permissions/permission_list.html'
    permission_required = 'core.view_custompermission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_permissions = CustomPermission.objects.count()
        active_permissions = CustomPermission.objects.filter(is_active=True).count()

        # تجميع حسب التصنيف
        category_stats = CustomPermission.objects.values('category').annotate(
            count=Count('id')
        ).order_by('category')

        context.update({
            'title': _('إدارة الصلاحيات المخصصة'),
            'can_add': self.request.user.has_perm('core.add_custompermission'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الصلاحيات المخصصة'), 'url': ''}
            ],
            'total_permissions': total_permissions,
            'active_permissions': active_permissions,
            'inactive_permissions': total_permissions - active_permissions,
            'category_stats': category_stats,
        })
        return context


class CustomPermissionCreateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, CreateView):
    """إضافة صلاحية مخصصة جديدة"""
    model = CustomPermission
    form_class = CustomPermissionForm
    template_name = 'core/permissions/permission_form.html'
    permission_required = 'core.add_custompermission'
    success_url = reverse_lazy('core:permission_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة صلاحية مخصصة جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الصلاحيات المخصصة'), 'url': reverse('core:permission_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ الصلاحية'),
            'cancel_url': reverse('core:permission_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة الصلاحية "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class CustomPermissionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, UpdateView):
    """تعديل صلاحية مخصصة"""
    model = CustomPermission
    form_class = CustomPermissionForm
    template_name = 'core/permissions/permission_form.html'
    permission_required = 'core.change_custompermission'
    success_url = reverse_lazy('core:permission_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل الصلاحية: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الصلاحيات المخصصة'), 'url': reverse('core:permission_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:permission_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث الصلاحية "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class CustomPermissionDetailView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, DetailView):
    """تفاصيل الصلاحية المخصصة"""
    model = CustomPermission
    template_name = 'core/permissions/permission_detail.html'
    context_object_name = 'permission'
    permission_required = 'core.view_custompermission'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # المستخدمون الذين لديهم هذه الصلاحية
        users_with_permission = self.object.users.filter(is_active=True)

        # المجموعات التي تحتوي على هذه الصلاحية
        groups_with_permission = self.object.groups.all()

        # مجموعات الصلاحيات المخصصة
        permission_groups = PermissionGroup.objects.filter(
            permissions=self.object, is_active=True
        )

        context.update({
            'title': _('تفاصيل الصلاحية: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_custompermission'),
            'can_delete': self.request.user.has_perm('core.delete_custompermission'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الصلاحيات المخصصة'), 'url': reverse('core:permission_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:permission_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:permission_delete', kwargs={'pk': self.object.pk}),
            'users_with_permission': users_with_permission,
            'groups_with_permission': groups_with_permission,
            'permission_groups': permission_groups,
        })
        return context


class CustomPermissionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, DeleteView):
    """حذف صلاحية مخصصة"""
    model = CustomPermission
    template_name = 'core/permissions/permission_confirm_delete.html'
    permission_required = 'core.delete_custompermission'
    success_url = reverse_lazy('core:permission_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف الصلاحية: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('الصلاحيات المخصصة'), 'url': reverse('core:permission_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:permission_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        permission_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف الصلاحية "%(name)s" بنجاح') % {'name': permission_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذه الصلاحية لوجود بيانات مرتبطة بها')
            )
            return redirect('core:permission_list')


# مجموعات الصلاحيات
class PermissionGroupListView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, TemplateView):
    """قائمة مجموعات الصلاحيات"""
    template_name = 'core/permissions/group_list.html'
    permission_required = 'core.view_permissiongroup'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات
        total_groups = PermissionGroup.objects.count()
        active_groups = PermissionGroup.objects.filter(is_active=True).count()

        context.update({
            'title': _('إدارة مجموعات الصلاحيات'),
            'can_add': self.request.user.has_perm('core.add_permissiongroup'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('مجموعات الصلاحيات'), 'url': ''}
            ],
            'total_groups': total_groups,
            'active_groups': active_groups,
            'inactive_groups': total_groups - active_groups,
        })
        return context


class PermissionGroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, CreateView):
    """إضافة مجموعة صلاحيات جديدة"""
    model = PermissionGroup
    form_class = PermissionGroupForm
    template_name = 'core/permissions/group_form.html'
    permission_required = 'core.add_permissiongroup'
    success_url = reverse_lazy('core:group_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة مجموعة صلاحيات جديدة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('مجموعات الصلاحيات'), 'url': reverse('core:group_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ المجموعة'),
            'cancel_url': reverse('core:group_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة مجموعة الصلاحيات "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class PermissionGroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, UpdateView):
    """تعديل مجموعة صلاحيات"""
    model = PermissionGroup
    form_class = PermissionGroupForm
    template_name = 'core/permissions/group_form.html'
    permission_required = 'core.change_permissiongroup'
    success_url = reverse_lazy('core:group_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل مجموعة الصلاحيات: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('مجموعات الصلاحيات'), 'url': reverse('core:group_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:group_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث مجموعة الصلاحيات "%(name)s" بنجاح') % {'name': self.object.name}
        )
        return response


class PermissionGroupDetailView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, DetailView):
    """تفاصيل مجموعة الصلاحيات"""
    model = PermissionGroup
    template_name = 'core/permissions/group_detail.html'
    context_object_name = 'group'
    permission_required = 'core.view_permissiongroup'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # المستخدمون في هذه المجموعة
        users_in_group = UserProfile.objects.filter(
            permission_groups=self.object,
            user__is_active=True
        ).select_related('user')

        # تجميع الصلاحيات حسب التصنيف
        permissions_by_category = self.object.get_permissions_by_category()

        context.update({
            'title': _('تفاصيل مجموعة الصلاحيات: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_permissiongroup'),
            'can_delete': self.request.user.has_perm('core.delete_permissiongroup'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('مجموعات الصلاحيات'), 'url': reverse('core:group_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:group_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:group_delete', kwargs={'pk': self.object.pk}),
            'users_in_group': users_in_group,
            'permissions_by_category': permissions_by_category,
        })
        return context


class PermissionGroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, DeleteView):
    """حذف مجموعة صلاحيات"""
    model = PermissionGroup
    template_name = 'core/permissions/group_confirm_delete.html'
    permission_required = 'core.delete_permissiongroup'
    success_url = reverse_lazy('core:group_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف مجموعة الصلاحيات: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('مجموعات الصلاحيات'), 'url': reverse('core:group_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:group_detail', kwargs={'pk': self.object.pk}),
        })
        return context


# العمليات المتقدمة
class BulkPermissionAssignView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, FormView):
    """تعيين صلاحيات متعددة"""
    template_name = 'core/permissions/bulk_assign.html'
    form_class = BulkPermissionAssignForm
    permission_required = 'core.change_userprofile'
    success_url = reverse_lazy('core:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعيين صلاحيات متعددة'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('تعيين صلاحيات متعددة'), 'url': ''}
            ],
            'submit_text': _('تطبيق التغييرات'),
            'cancel_url': reverse('core:user_list'),
        })
        return context

    def form_valid(self, form):
        users = form.cleaned_data['users']
        permission_groups = form.cleaned_data['permission_groups']
        custom_permissions = form.cleaned_data['custom_permissions']
        action_type = form.cleaned_data['action_type']

        updated_count = 0

        for user in users:
            # إنشاء profile إذا لم يكن موجوداً
            profile, created = UserProfile.objects.get_or_create(user=user)

            if action_type == 'add':
                # إضافة الصلاحيات
                if permission_groups:
                    profile.permission_groups.add(*permission_groups)
                if custom_permissions:
                    for perm in custom_permissions:
                        perm.users.add(user)

            elif action_type == 'replace':
                # استبدال الصلاحيات
                if permission_groups:
                    profile.permission_groups.set(permission_groups)
                if custom_permissions:
                    # إزالة من جميع الصلاحيات المخصصة
                    CustomPermission.objects.filter(users=user).update(
                        users=CustomPermission.objects.exclude(users=user)
                    )
                    # إضافة الجديدة
                    for perm in custom_permissions:
                        perm.users.add(user)

            elif action_type == 'remove':
                # إزالة الصلاحيات
                if permission_groups:
                    profile.permission_groups.remove(*permission_groups)
                if custom_permissions:
                    for perm in custom_permissions:
                        perm.users.remove(user)

            updated_count += 1

        messages.success(
            self.request,
            _('تم تحديث صلاحيات %(count)d مستخدم بنجاح') % {'count': updated_count}
        )
        return super().form_valid(form)


class CopyUserPermissionsView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, FormView):
    """نسخ صلاحيات بين المستخدمين"""
    template_name = 'core/permissions/copy_permissions.html'
    form_class = CopyUserPermissionsForm
    permission_required = 'core.change_userprofile'
    success_url = reverse_lazy('core:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('نسخ صلاحيات بين المستخدمين'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('نسخ صلاحيات'), 'url': ''}
            ],
            'submit_text': _('نسخ الصلاحيات'),
            'cancel_url': reverse('core:user_list'),
        })
        return context

    def form_valid(self, form):
        source_user = form.cleaned_data['source_user']
        target_users = form.cleaned_data['target_users']
        copy_options = form.cleaned_data['copy_options']
        replace_existing = form.cleaned_data['replace_existing']

        # الحصول على profile المصدر
        source_profile = getattr(source_user, 'profile', None)

        copied_count = 0

        for target_user in target_users:
            # إنشاء profile للمستخدم الهدف إذا لم يكن موجوداً
            target_profile, created = UserProfile.objects.get_or_create(user=target_user)

            # نسخ مجموعات الصلاحيات المخصصة
            if 'permission_groups' in copy_options and source_profile:
                if replace_existing:
                    target_profile.permission_groups.set(source_profile.permission_groups.all())
                else:
                    target_profile.permission_groups.add(*source_profile.permission_groups.all())

            # نسخ الصلاحيات المخصصة المباشرة
            if 'custom_permissions' in copy_options:
                source_custom_perms = CustomPermission.objects.filter(users=source_user)
                if replace_existing:
                    # إزالة جميع الصلاحيات المخصصة الحالية
                    CustomPermission.objects.filter(users=target_user).update(
                        users=CustomPermission.objects.exclude(users=target_user)
                    )
                # إضافة صلاحيات المصدر
                for perm in source_custom_perms:
                    perm.users.add(target_user)

            # نسخ مجموعات Django
            if 'django_groups' in copy_options:
                if replace_existing:
                    target_user.groups.set(source_user.groups.all())
                else:
                    target_user.groups.add(*source_user.groups.all())

            # نسخ صلاحيات Django المباشرة
            if 'user_permissions' in copy_options:
                if replace_existing:
                    target_user.user_permissions.set(source_user.user_permissions.all())
                else:
                    target_user.user_permissions.add(*source_user.user_permissions.all())

            copied_count += 1

        messages.success(
            self.request,
            _('تم نسخ صلاحيات %(source)s إلى %(count)d مستخدم بنجاح') % {
                'source': source_user.get_full_name() or source_user.username,
                'count': copied_count
            }
        )
        return super().form_valid(form)


@login_required
@permission_required('core.add_permissiongroup')
@require_http_methods(["POST"])
def create_default_permission_groups(request):
    """إنشاء مجموعات الصلاحيات الافتراضية"""
    try:
        # إنشاء مجموعات افتراضية
        default_groups = [
            {
                'name': 'موظف مبيعات',
                'description': 'صلاحيات أساسية لموظف المبيعات',
                'custom_permissions': ['apply_discount', 'modify_sales_price'],
                'django_permissions': ['view_item', 'view_businesspartner']
            },
            {
                'name': 'مدير مبيعات',
                'description': 'صلاحيات إدارية للمبيعات',
                'custom_permissions': ['approve_sales_order', 'void_sales_invoice'],
                'django_permissions': ['add_item', 'change_item']
            },
            {
                'name': 'محاسب',
                'description': 'صلاحيات المحاسبة والتقارير المالية',
                'custom_permissions': ['manual_journal_entry', 'financial_reports'],
                'django_permissions': ['view_item', 'view_businesspartner']
            },
            {
                'name': 'أمين مخزون',
                'description': 'صلاحيات إدارة المخازن والمخزون',
                'custom_permissions': ['stock_adjustment', 'inventory_count'],
                'django_permissions': ['view_item', 'change_item']
            }
        ]

        created_count = 0
        company = getattr(request, 'current_company', None)

        for group_data in default_groups:
            # التحقق من عدم وجود المجموعة مسبقاً
            if not PermissionGroup.objects.filter(
                    name=group_data['name'],
                    company=company
            ).exists():
                # إنشاء المجموعة
                group = PermissionGroup.objects.create(
                    name=group_data['name'],
                    description=group_data['description'],
                    company=company,
                    is_active=True
                )

                # إضافة الصلاحيات المخصصة
                custom_perms = CustomPermission.objects.filter(
                    code__in=group_data['custom_permissions'],
                    is_active=True
                )
                group.permissions.add(*custom_perms)

                # إضافة صلاحيات Django
                from django.contrib.auth.models import Permission
                django_perms = Permission.objects.filter(
                    codename__in=group_data['django_permissions']
                )
                group.django_permissions.add(*django_perms)

                created_count += 1

        return JsonResponse({
            'success': True,
            'message': f'تم إنشاء {created_count} مجموعة صلاحيات افتراضية',
            'created_count': created_count
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)