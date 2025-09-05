# apps/core/forms/variant_forms.py
"""
نماذج خصائص ومتغيرات الأصناف
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import VariantAttribute, VariantValue


class VariantAttributeForm(forms.ModelForm):
    """نموذج إضافة/تعديل خاصية المتغير"""

    class Meta:
        model = VariantAttribute
        fields = [
            'name', 'name_en', 'display_name', 'is_required', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم الخاصية'),
                'required': True
            }),
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Attribute Name')
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('اسم العرض (اختياري)')
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['name_en'].required = False
        self.fields['display_name'].required = False

        # تخصيص التسميات
        self.fields['name'].label = _('اسم الخاصية')
        self.fields['name_en'].label = _('الاسم الإنجليزي')
        self.fields['display_name'].label = _('اسم العرض')
        self.fields['is_required'].label = _('خاصية إجبارية')
        self.fields['sort_order'].label = _('ترتيب العرض')

        # Help texts
        self.fields['name'].help_text = _('اسم الخاصية (مثل: اللون، الحجم)')
        self.fields['display_name'].help_text = _('الاسم الذي يظهر للمستخدم (اختياري)')
        self.fields['is_required'].help_text = _('هل هذه الخاصية إجبارية عند إنشاء المتغيرات؟')
        self.fields['sort_order'].help_text = _('ترتيب ظهور الخاصية (الأصغر أولاً)')

    def clean_name(self):
        """التحقق من عدم تكرار اسم الخاصية"""
        name = self.cleaned_data.get('name')
        if name and self.request:
            company = self.request.current_company
            queryset = VariantAttribute.objects.filter(company=company, name=name)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError(_('هذا الاسم مستخدم مسبقاً'))
        return name

    def save(self, commit=True):
        """حفظ مع إضافة الشركة"""
        instance = super().save(commit=False)

        if self.request:
            if getattr(instance, 'company_id', None) is None:
                instance.company = self.request.current_company
            if getattr(instance, 'created_by_id', None) is None:
                instance.created_by = self.request.user

        if commit:
            instance.save()
        return instance


class VariantValueForm(forms.ModelForm):
    """نموذج قيمة المتغير"""

    class Meta:
        model = VariantValue
        fields = ['value', 'value_en', 'display_value', 'sort_order']
        widgets = {
            'value': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('القيمة'),
                'required': True
            }),
            'value_en': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('Value')
            }),
            'display_value': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': _('قيمة العرض')
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': 0,
                'value': 0
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # جعل بعض الحقول اختيارية
        self.fields['value_en'].required = False
        self.fields['display_value'].required = False
        self.fields['sort_order'].required = False


# Formset للقيم
VariantValueFormSet = forms.inlineformset_factory(
    VariantAttribute,
    VariantValue,
    form=VariantValueForm,
    extra=0,  # لا نريد نماذج إضافية
    can_delete=True,
    can_order=False,
    min_num=1,  # على الأقل قيمة واحدة
    validate_min=True,
)


class VariantAttributeWithValuesForm(forms.Form):
    """نموذج مجمع للخاصية مع قيمها"""

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        # إضافة نموذج الخاصية
        self.attribute_form = VariantAttributeForm(
            data=self.data if self.is_bound else None,
            instance=self.instance,
            request=self.request,
            prefix='attribute'
        )

        # إضافة formset للقيم
        self.values_formset = VariantValueFormSet(
            data=self.data if self.is_bound else None,
            instance=self.instance,
            prefix='values'
        )

    def is_valid(self):
        """التحقق من صحة النموذج والـ formset"""
        print("Checking form validity...")

        attribute_valid = self.attribute_form.is_valid()
        print(f"Attribute form valid: {attribute_valid}")
        if not attribute_valid:
            print("Attribute form errors:", self.attribute_form.errors)

        formset_valid = self.values_formset.is_valid()
        print(f"Formset valid: {formset_valid}")
        if not formset_valid:
            print("Formset errors:", self.values_formset.errors)
            print("Formset non form errors:", self.values_formset.non_form_errors())

            # طباعة أخطاء كل نموذج فرعي
            for i, form in enumerate(self.values_formset):
                if form.errors:
                    print(f"Form {i} errors:", form.errors)

        return attribute_valid and formset_valid

    def save(self, commit=True):
        """حفظ الخاصية والقيم مع معالجة الحذف يدوياً"""
        if not self.is_valid():
            raise ValueError("Cannot save invalid form")

        print("Starting save process...")

        # حفظ الخاصية أولاً
        attribute = self.attribute_form.save(commit=commit)
        print(f"Saved attribute: {attribute}")

        values = []

        if commit:
            # معالجة كل نموذج في الـ formset يدوياً
            for i, form in enumerate(self.values_formset.forms):
                print(f"Processing form {i}: {form.cleaned_data}")

                if form.cleaned_data:
                    # التحقق من الحذف أولاً
                    if form.cleaned_data.get('DELETE', False):
                        print(f"Form {i}: Marked for deletion")
                        # حذف العنصر إذا كان موجود في قاعدة البيانات
                        if form.instance.pk:
                            print(f"Deleting existing instance: {form.instance}")
                            form.instance.delete()
                        continue

                    # إذا كان هناك قيمة صالحة، احفظها
                    value = form.cleaned_data.get('value', '').strip()
                    if value:
                        print(f"Form {i}: Saving value '{value}'")

                        # تحديث أو إنشاء instance
                        instance = form.instance
                        instance.attribute = attribute
                        instance.company = attribute.company
                        instance.value = value
                        instance.value_en = form.cleaned_data.get('value_en', '')
                        instance.display_value = form.cleaned_data.get('display_value', '')
                        instance.sort_order = form.cleaned_data.get('sort_order', 0)

                        instance.save()
                        values.append(instance)
                        print(f"Saved value: {instance}")
                    else:
                        print(f"Form {i}: No value provided, skipping")

            print(f"Total saved values: {len(values)}")

        return attribute, values

    @property
    def errors(self):
        """جمع أخطاء النموذج والـ formset"""
        errors = {}
        if self.attribute_form.errors:
            errors.update(self.attribute_form.errors)
        if self.values_formset.errors:
            errors['values'] = self.values_formset.errors
        if self.values_formset.non_form_errors():
            errors['values_non_form'] = self.values_formset.non_form_errors()
        return errors