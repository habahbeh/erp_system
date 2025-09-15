# apps/core/views/user_profile_views.py
"""
Views إدارة ملفات المستخدمين
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, FormView
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import UserProfile, Company, Branch, Warehouse
from ..forms.user_profile_forms import UserProfileForm, BulkUserProfileForm, UserPermissionsForm
from ..mixins import UserMixin, AuditLogMixin


User = get_user_model()


class UserProfileListView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, TemplateView):
    """قائمة ملفات المستخدمين"""
    template_name = 'core/user_profiles/profile_list.html'
    permission_required = 'core.view_userprofile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('ملفات المستخدمين'),
            'can_add': self.request.user.has_perm('core.add_userprofile'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('ملفات المستخدمين'), 'url': ''}
            ],
        })
        return context


class UserProfileDetailView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, DetailView):
    """تفاصيل ملف المستخدم"""
    model = UserProfile
    template_name = 'core/user_profiles/profile_detail.html'
    context_object_name = 'profile'
    permission_required = 'core.view_userprofile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('ملف المستخدم: %(name)s') % {
                'name': self.object.user.get_full_name() or self.object.user.username},
            'can_change': self.request.user.has_perm('core.change_userprofile'),
            'can_delete': self.request.user.has_perm('core.delete_userprofile'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('ملفات المستخدمين'), 'url': reverse('core:profile_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:profile_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:profile_delete', kwargs={'pk': self.object.pk}),
            'permissions_url': reverse('core:user_permissions', kwargs={'user_id': self.object.user.pk}),
        })
        return context


class UserProfileUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, UpdateView):
    """تعديل ملف المستخدم"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'core/user_profiles/profile_form.html'
    permission_required = 'core.change_userprofile'

    def get_success_url(self):
        return reverse('core:profile_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل ملف المستخدم: %(name)s') % {
                'name': self.object.user.get_full_name() or self.object.user.username},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('ملفات المستخدمين'), 'url': reverse('core:profile_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:profile_detail', kwargs={'pk': self.object.pk}),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث ملف المستخدم "%(name)s" بنجاح') % {
                'name': self.object.user.get_full_name() or self.object.user.username}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class BulkUserProfileUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, FormView):
    """تحديث ملفات المستخدمين بشكل جماعي"""
    template_name = 'core/user_profiles/bulk_update.html'
    form_class = BulkUserProfileForm
    permission_required = 'core.change_userprofile'
    success_url = reverse_lazy('core:profile_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تحديث ملفات المستخدمين جماعياً'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('ملفات المستخدمين'), 'url': reverse('core:profile_list')},
                {'title': _('تحديث جماعي'), 'url': ''}
            ],
            'submit_text': _('تحديث الملفات'),
            'cancel_url': reverse('core:profile_list'),
        })
        return context

    def form_valid(self, form):
        users = form.cleaned_data['users']
        updated_count = 0

        for user in users:
            # إنشاء ملف المستخدم إذا لم يكن موجوداً
            profile, created = UserProfile.objects.get_or_create(user=user)

            # تحديث الحقول إذا تم تحديدها
            if form.cleaned_data.get('max_discount_percentage') is not None:
                profile.max_discount_percentage = form.cleaned_data['max_discount_percentage']

            if form.cleaned_data.get('max_credit_limit') is not None:
                profile.max_credit_limit = form.cleaned_data['max_credit_limit']

            profile.save()

            # تحديث الفروع والمستودعات المسموحة
            if form.cleaned_data.get('allowed_branches'):
                profile.allowed_branches.set(form.cleaned_data['allowed_branches'])

            if form.cleaned_data.get('allowed_warehouses'):
                profile.allowed_warehouses.set(form.cleaned_data['allowed_warehouses'])

            updated_count += 1

        messages.success(
            self.request,
            _('تم تحديث %(count)d ملف مستخدم بنجاح') % {'count': updated_count}
        )
        return super().form_valid(form)


@login_required
def user_permissions_view(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        # حفظ المجموعات
        selected_groups = request.POST.getlist('groups')
        user_obj.groups.set(selected_groups)

        # حفظ الصلاحيات المباشرة
        selected_permissions = request.POST.getlist('permissions')
        user_obj.user_permissions.set(selected_permissions)

        messages.success(request, 'تم تحديث الصلاحيات بنجاح')
        return redirect('core:user_detail', pk=user_obj.pk)

    # جلب البيانات
    from django.contrib.auth.models import Group, Permission

    context = {
        'user_obj': user_obj,
        'all_groups': Group.objects.all(),
        'all_permissions': Permission.objects.all().select_related('content_type'),
        'user_groups': user_obj.groups.values_list('id', flat=True),
        'user_permissions': user_obj.user_permissions.values_list('id', flat=True),
    }

    return render(request, 'core/user_profiles/user_permissions.html', context)

@login_required
def create_missing_profiles(request):
    """إنشاء ملفات مفقودة للمستخدمين"""
    if not request.user.has_perm('core.add_userprofile'):
        messages.error(request, _('ليس لديك صلاحية لإنشاء ملفات المستخدمين'))
        return redirect('core:user_list')

    # العثور على المستخدمين بدون ملفات
    users_without_profiles = User.objects.filter(profile__isnull=True)

    if request.user.company:
        users_without_profiles = users_without_profiles.filter(company=request.user.company)

    created_count = 0
    for user in users_without_profiles:
        UserProfile.objects.get_or_create(user=user)
        created_count += 1

    if created_count > 0:
        messages.success(
            request,
            _('تم إنشاء %(count)d ملف مستخدم جديد') % {'count': created_count}
        )
    else:
        messages.info(request, _('جميع المستخدمين لديهم ملفات بالفعل'))

    return redirect('core:profile_list')

class UserProfileDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, DeleteView):
    """حذف ملف المستخدم"""
    model = UserProfile
    template_name = 'core/user_profiles/profile_confirm_delete.html'
    permission_required = 'core.delete_userprofile'
    success_url = reverse_lazy('core:profile_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف ملف المستخدم: %(name)s') % {'name': self.object.user.get_full_name() or self.object.user.username},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('ملفات المستخدمين'), 'url': reverse('core:profile_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:profile_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_name = self.object.user.get_full_name() or self.object.user.username

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف ملف المستخدم "%(name)s" بنجاح') % {'name': user_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف ملف هذا المستخدم لوجود بيانات مرتبطة به')
            )
            return redirect('core:profile_list')

__all__ = [
    'UserProfileListView',
    'UserProfileDetailView',
    'UserProfileUpdateView',
    'UserProfileDeleteView',  # إضافة جديد
    'BulkUserProfileUpdateView',
    'user_permissions_view',
    'create_missing_profiles',
]