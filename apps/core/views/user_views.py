# apps/core/views/user_views.py
"""
Views إدارة المستخدمين
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from ..models import Company, Branch, Warehouse, UserProfile
from ..forms.user_forms import UserForm, UserUpdateForm, ChangePasswordForm
from ..mixins import UserMixin, AuditLogMixin  # تغيير من CompanyMixin إلى UserMixin

User = get_user_model()


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, TemplateView):
    """قائمة المستخدمين مع DataTable"""
    template_name = 'core/users/user_list.html'
    permission_required = 'auth.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة المستخدمين'),
            'can_add': self.request.user.has_perm('auth.add_user'),
            'add_url': reverse('core:user_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': ''}
            ],
        })
        return context


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, CreateView):
    """إضافة مستخدم جديد"""
    model = User
    form_class = UserForm
    template_name = 'core/users/user_form.html'
    permission_required = 'auth.add_user'
    success_url = reverse_lazy('core:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إضافة مستخدم جديد'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ المستخدم'),
            'cancel_url': reverse('core:user_list'),
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم إضافة المستخدم "%(name)s" بنجاح') % {'name': self.object.get_full_name() or self.object.username}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, UpdateView):
    """تعديل مستخدم"""
    model = User
    form_class = UserUpdateForm
    template_name = 'core/users/user_form.html'
    permission_required = 'auth.change_user'
    success_url = reverse_lazy('core:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('تعديل المستخدم: %(name)s') % {'name': self.object.get_full_name() or self.object.username},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:user_list'),
            'is_update': True,
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('تم تحديث المستخدم "%(name)s" بنجاح') % {'name': self.object.get_full_name() or self.object.username}
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, _('يرجى تصحيح الأخطاء أدناه'))
        return super().form_invalid(form)


class UserDetailView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, DetailView):
    """تفاصيل المستخدم"""
    model = User
    template_name = 'core/users/user_detail.html'
    context_object_name = 'user_obj'
    permission_required = 'auth.view_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إحصائيات المستخدم
        user_obj = self.object

        # التحقق من وجود ملف المستخدم
        profile_exists = hasattr(user_obj, 'profile')

        context.update({
            'title': _('تفاصيل المستخدم: %(name)s') % {'name': user_obj.get_full_name() or user_obj.username},
            'can_change': self.request.user.has_perm('auth.change_user'),
            'can_delete': self.request.user.has_perm('auth.delete_user'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:user_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:user_delete', kwargs={'pk': self.object.pk}),
            'change_password_url': reverse('core:user_change_password', kwargs={'pk': self.object.pk}),
            'profile_exists': profile_exists,
            'permissions_url': reverse('core:user_permissions', kwargs={'user_id': self.object.pk}),
        })
        return context


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserMixin, AuditLogMixin, DeleteView):
    """حذف مستخدم"""
    model = User
    template_name = 'core/users/user_confirm_delete.html'
    permission_required = 'auth.delete_user'
    success_url = reverse_lazy('core:user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('حذف المستخدم: %(name)s') % {'name': self.object.get_full_name() or self.object.username},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:user_list'),
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_name = self.object.get_full_name() or self.object.username

        # التحقق من عدم حذف المستخدم الحالي
        if self.object == request.user:
            messages.error(
                request,
                _('لا يمكنك حذف حسابك الشخصي')
            )
            return redirect('core:user_list')

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف المستخدم "%(name)s" بنجاح') % {'name': user_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذا المستخدم لوجود بيانات مرتبطة به')
            )
            return redirect('core:user_list')


@login_required
def change_password_view(request, pk):
    """تغيير كلمة مرور المستخدم"""
    # استخدام get_object_or_404 مع queryset مخصص
    if request.user.is_superuser:
        # مديرو النظام يمكنهم تغيير كلمة مرور أي مستخدم
        user_obj = get_object_or_404(User, pk=pk)
    elif hasattr(request.user, 'company') and request.user.company:
        # المستخدمون العاديون يمكنهم تغيير كلمة مرور مستخدمي شركتهم أو أنفسهم
        user_obj = get_object_or_404(
            User.objects.filter(
                Q(pk=pk) & (Q(company=request.user.company) | Q(pk=request.user.pk))
            )
        )
    else:
        # يمكن للمستخدم تغيير كلمة مروره فقط
        user_obj = get_object_or_404(User, pk=pk)
        if user_obj != request.user:
            messages.error(request, _('ليس لديك صلاحية لتغيير كلمة مرور هذا المستخدم'))
            return redirect('core:user_list')

    # التحقق من الصلاحيات
    if not request.user.has_perm('auth.change_user') and request.user != user_obj:
        messages.error(request, _('ليس لديك صلاحية لتغيير كلمة مرور هذا المستخدم'))
        return redirect('core:user_list')

    if request.method == 'POST':
        form = ChangePasswordForm(user_obj, request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('تم تغيير كلمة المرور بنجاح للمستخدم "%(name)s"') % {
                    'name': user_obj.get_full_name() or user_obj.username
                }
            )
            return redirect('core:user_detail', pk=user_obj.pk)
    else:
        form = ChangePasswordForm(user_obj)

    context = {
        'form': form,
        'user_obj': user_obj,
        'title': _('تغيير كلمة المرور: %(name)s') % {'name': user_obj.get_full_name() or user_obj.username},
        'breadcrumbs': [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المستخدمين'), 'url': reverse('core:user_list')},
            {'title': _('تغيير كلمة المرور'), 'url': ''}
        ],
        'submit_text': _('تغيير كلمة المرور'),
        'cancel_url': reverse('core:user_detail', kwargs={'pk': user_obj.pk}),
    }

    return render(request, 'core/users/change_password.html', context)