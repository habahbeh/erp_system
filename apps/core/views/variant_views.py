# apps/core/views/variant_views.py
"""
Views لخصائص ومتغيرات المواد
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction

from ..models import VariantAttribute, VariantValue
from ..forms.variant_forms import VariantAttributeWithValuesForm
from ..mixins import CompanyMixin, AuditLogMixin


class VariantAttributeListView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, TemplateView):
    """قائمة خصائص المتغيرات مع DataTable"""
    template_name = 'core/variants/attribute_list.html'
    permission_required = 'core.view_variantattribute'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('إدارة خصائص المتغيرات'),
            'can_add': self.request.user.has_perm('core.add_variantattribute'),
            'add_url': reverse('core:variant_attribute_create'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('خصائص المتغيرات'), 'url': ''}
            ],
        })
        return context


class VariantAttributeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                 TemplateView):
    """إضافة خاصية متغير جديدة مع قيمها"""
    template_name = 'core/variants/attribute_form.html'
    permission_required = 'core.add_variantattribute'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # إنشاء النموذج المجمع
        form = VariantAttributeWithValuesForm(request=self.request)

        context.update({
            'title': _('إضافة خاصية متغير جديدة'),
            'form': form,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('خصائص المتغيرات'), 'url': reverse('core:variant_attribute_list')},
                {'title': _('إضافة جديد'), 'url': ''}
            ],
            'submit_text': _('حفظ الخاصية والقيم'),
            'cancel_url': reverse('core:variant_attribute_list'),
        })
        return context

    def post(self, request, *args, **kwargs):
        """معالجة إرسال النموذج"""
        print("POST data received:", dict(request.POST))

        form = VariantAttributeWithValuesForm(data=request.POST, request=request)

        print("Form is_bound:", form.is_bound)
        print("Form is_valid:", form.is_valid())

        if form.is_valid():
            # طباعة البيانات المنظفة للـ formset
            print("Formset cleaned_data:")
            for i, form_data in enumerate(form.values_formset.cleaned_data):
                if form_data:
                    print(f"  Form {i}: {form_data}")

            # التحقق من وجود قيم صالحة يدوياً
            valid_values = []
            for value_form in form.values_formset:
                if (value_form.cleaned_data and
                        not value_form.cleaned_data.get('DELETE', False) and
                        value_form.cleaned_data.get('value')):
                    valid_values.append(value_form)

            print(f"Valid values found: {len(valid_values)}")

            if len(valid_values) == 0:
                messages.error(request, _('يجب إضافة قيمة واحدة على الأقل للخاصية'))
                context = self.get_context_data()
                context['form'] = form
                return self.render_to_response(context)

            try:
                with transaction.atomic():
                    print("Saving form...")
                    attribute, values = form.save()
                    print(f"Saved attribute: {attribute}")
                    print(f"Saved values: {[v.value for v in values]}")

                messages.success(
                    request,
                    _('تم إضافة خاصية المتغير "%(name)s" مع %(count)d قيم بنجاح') % {
                        'name': attribute.name,
                        'count': len(values)
                    }
                )
                return redirect('core:variant_attribute_list')

            except Exception as e:
                print(f"Error saving: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'حدث خطأ أثناء الحفظ: {str(e)}')
        else:
            print("Form errors:", form.errors)
            messages.error(request, _('يرجى تصحيح الأخطاء أدناه'))

        # في حالة الخطأ، عرض النموذج مع الأخطاء
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class VariantAttributeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin,
                                 TemplateView):
    """تعديل خاصية متغير مع قيمها"""
    template_name = 'core/variants/attribute_form.html'
    permission_required = 'core.change_variantattribute'

    def get_object(self):
        """الحصول على الخاصية"""
        return get_object_or_404(
            VariantAttribute,
            pk=self.kwargs['pk'],
            company=self.request.current_company
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على الخاصية
        attribute = self.get_object()

        # إنشاء النموذج المجمع
        form = VariantAttributeWithValuesForm(
            instance=attribute,
            request=self.request
        )

        context.update({
            'title': _('تعديل خاصية المتغير: %(name)s') % {'name': attribute.name},
            'form': form,
            'attribute': attribute,
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('خصائص المتغيرات'), 'url': reverse('core:variant_attribute_list')},
                {'title': _('تعديل'), 'url': ''}
            ],
            'submit_text': _('حفظ التعديلات'),
            'cancel_url': reverse('core:variant_attribute_list'),
            'is_update': True,
        })
        return context

    def post(self, request, *args, **kwargs):
        """معالجة إرسال النموذج"""
        attribute = self.get_object()
        print("POST data received:", dict(request.POST))

        # طباعة البيانات المفصلة للـ values
        for key, value in request.POST.items():
            if key.startswith('values-'):
                print(f"  {key}: {value}")

        form = VariantAttributeWithValuesForm(
            data=request.POST,
            instance=attribute,
            request=request
        )

        print("Form is_valid:", form.is_valid())

        if form.is_valid():
            # طباعة تفاصيل أكثر عن الـ formset
            print("Formset forms details:")
            for i, form_instance in enumerate(form.values_formset.forms):
                if form_instance.cleaned_data:
                    print(f"  Form {i}:")
                    print(f"    Instance PK: {form_instance.instance.pk}")
                    print(f"    Cleaned data: {form_instance.cleaned_data}")
                    print(f"    DELETE: {form_instance.cleaned_data.get('DELETE', False)}")
                    print(f"    Value: {form_instance.cleaned_data.get('value', '')}")

            try:
                with transaction.atomic():
                    print("Updating form...")
                    attribute, values = form.save()
                    print(f"Updated attribute: {attribute}")
                    print(f"Updated values: {[f'{v.value} (id: {v.pk})' for v in values]}")

                messages.success(
                    request,
                    _('تم تحديث خاصية المتغير "%(name)s" بنجاح') % {
                        'name': attribute.name
                    }
                )
                return redirect('core:variant_attribute_list')

            except Exception as e:
                print(f"Error updating: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'حدث خطأ أثناء الحفظ: {str(e)}')
        else:
            print("Form errors:", form.errors)
            messages.error(request, _('يرجى تصحيح الأخطاء أدناه'))

        # في حالة الخطأ، عرض النموذج مع الأخطاء
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class VariantAttributeDetailView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, DetailView):
    """عرض تفاصيل خاصية المتغير"""
    model = VariantAttribute
    template_name = 'core/variants/attribute_detail.html'
    context_object_name = 'attribute'
    permission_required = 'core.view_variantattribute'

    def get_queryset(self):
        """فلترة حسب الشركة"""
        return super().get_queryset().filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # الحصول على القيم المرتبطة
        values = self.object.values.all().order_by('sort_order', 'value')

        context.update({
            'title': _('تفاصيل خاصية المتغير: %(name)s') % {'name': self.object.name},
            'can_change': self.request.user.has_perm('core.change_variantattribute'),
            'can_delete': self.request.user.has_perm('core.delete_variantattribute'),
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('خصائص المتغيرات'), 'url': reverse('core:variant_attribute_list')},
                {'title': _('التفاصيل'), 'url': ''}
            ],
            'edit_url': reverse('core:variant_attribute_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse('core:variant_attribute_delete', kwargs={'pk': self.object.pk}),
            'values': values,
            'values_count': values.count(),
        })
        return context


class VariantAttributeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, CompanyMixin, AuditLogMixin, DeleteView):
    """حذف خاصية متغير"""
    model = VariantAttribute
    template_name = 'core/variants/attribute_confirm_delete.html'
    permission_required = 'core.delete_variantattribute'
    success_url = reverse_lazy('core:variant_attribute_list')

    def get_queryset(self):
        """فلترة حسب الشركة"""
        return super().get_queryset().filter(company=self.request.current_company)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # عدد القيم المرتبطة
        values_count = self.object.values.count()

        # عدد المتغيرات المستخدمة
        # TODO: إضافة عدد متغيرات المواد التي تستخدم هذه الخاصية
        used_in_variants = 0

        context.update({
            'title': _('حذف خاصية المتغير: %(name)s') % {'name': self.object.name},
            'breadcrumbs': [
                {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
                {'title': _('خصائص المتغيرات'), 'url': reverse('core:variant_attribute_list')},
                {'title': _('حذف'), 'url': ''}
            ],
            'cancel_url': reverse('core:variant_attribute_list'),
            'values_count': values_count,
            'used_in_variants': used_in_variants,
        })
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        attribute_name = self.object.name

        try:
            response = super().delete(request, *args, **kwargs)
            messages.success(
                request,
                _('تم حذف خاصية المتغير "%(name)s" بنجاح') % {'name': attribute_name}
            )
            return response
        except Exception as e:
            messages.error(
                request,
                _('لا يمكن حذف هذه الخاصية لوجود بيانات مرتبطة بها')
            )
            return redirect('core:variant_attribute_list')