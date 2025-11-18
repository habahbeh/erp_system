# apps/core/models/uom_models.py
"""
نماذج وحدات القياس - Unit of Measure System (Week 2)
- UoMGroup: مجموعات وحدات القياس ⭐ NEW
- UnitOfMeasure: وحدات القياس (محسّن مع Groups)
- UoMConversion: التحويلات بين الوحدات
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from .base_models import BaseModel


class UoMGroup(BaseModel):
    """
    مجموعة وحدات القياس - لتنظيم الوحدات المتشابهة

    ⭐ Week 2 Feature

    أمثلة:
    - الوزن (Weight): كيلوجرام، جرام، ميليجرام، طن
    - الطول (Length): متر، سنتيمتر، ميليمتر، كيلومتر
    - الحجم (Volume): لتر، ميليلتر، جالون
    - الوقت (Time): ساعة، دقيقة، ثانية
    - الوحدات (Units): قطعة، حبة، دزينة، كرتون

    الفائدة:
    - تنظيم الوحدات حسب النوع
    - منع التحويل بين مجموعات مختلفة (مثل: كيلو → لتر)
    - تسهيل إدارة التحويلات المتسلسلة
    """

    name = models.CharField(
        _('اسم المجموعة'),
        max_length=100,
        help_text=_('مثال: الوزن، الطول، الحجم')
    )

    code = models.CharField(
        _('رمز المجموعة'),
        max_length=20,
        help_text=_('رمز فريد بالإنجليزية، مثال: WEIGHT, LENGTH')
    )

    description = models.TextField(
        _('الوصف'),
        blank=True,
        help_text=_('وصف تفصيلي للمجموعة واستخداماتها')
    )

    # الوحدة الأساسية (Base UoM) للمجموعة
    base_uom = models.ForeignKey(
        'UnitOfMeasure',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups_as_base',
        verbose_name=_('الوحدة الأساسية'),
        help_text=_('الوحدة الأساسية التي تُحسب التحويلات على أساسها (مثل: كيلوجرام للوزن)')
    )

    # هل يُسمح بالأرقام العشرية؟
    allow_decimal = models.BooleanField(
        _('السماح بالأرقام العشرية'),
        default=True,
        help_text=_('هل يمكن استخدام كميات عشرية؟ (مثل: 2.5 كجم)')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('مجموعة وحدات قياس')
        verbose_name_plural = _('مجموعات وحدات القياس')
        unique_together = [['company', 'code']]
        ordering = ['name']
        db_table = 'core_uomgroup'

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        """
        التحقق من صحة البيانات

        ⭐ ENHANCED Week 2 Day 3
        """
        super().clean()

        errors = {}

        # 1. ⭐ NEW: التحقق من الرمز (code)
        if self.code:
            # Clean and uppercase code
            self.code = self.code.strip().upper()

            if not self.code:
                errors['code'] = _('رمز المجموعة لا يمكن أن يكون فارغاً')
            elif len(self.code) < 2:
                errors['code'] = _('رمز المجموعة قصير جداً (الحد الأدنى حرفان)')
            elif len(self.code) > 20:
                errors['code'] = _('رمز المجموعة طويل جداً (الحد الأقصى 20 حرف)')
            else:
                # Check uniqueness
                duplicate = UoMGroup.objects.filter(
                    company=self.company,
                    code=self.code
                ).exclude(pk=self.pk if self.pk else None).exists()

                if duplicate:
                    errors['code'] = _('رمز المجموعة موجود مسبقاً')

        # 2. ⭐ NEW: التحقق من الاسم
        if self.name:
            if len(self.name.strip()) < 2:
                errors['name'] = _('اسم المجموعة قصير جداً (الحد الأدنى حرفان)')

        # 3. التحقق من أن base_uom تنتمي لهذه المجموعة
        if self.base_uom and self.pk:
            if self.base_uom.uom_group_id and self.base_uom.uom_group_id != self.pk:
                errors['base_uom'] = _('الوحدة الأساسية يجب أن تنتمي لهذه المجموعة')

        if errors:
            raise ValidationError(errors)

    def get_all_units(self):
        """الحصول على جميع الوحدات في هذه المجموعة"""
        return self.units.filter(is_active=True).order_by('name')

    def get_all_conversions(self):
        """الحصول على جميع التحويلات في هذه المجموعة"""
        return UoMConversion.objects.filter(
            company=self.company,
            from_uom__uom_group=self
        ).select_related('from_uom', 'item', 'variant')

    def get_unit_count(self):
        """عدد الوحدات في المجموعة"""
        return self.units.filter(is_active=True).count()


class UnitOfMeasure(BaseModel):
    """وحدات القياس - محسّنة مع دعم المجموعات (Groups) ⭐ Updated Week 2"""

    UOM_TYPE_CHOICES = [
        ('UNIT', _('وحدة')),           # قطعة، حبة، عبوة
        ('WEIGHT', _('وزن')),          # كيلو، جرام، طن
        ('LENGTH', _('طول')),          # متر، سم، ملم
        ('VOLUME', _('حجم')),          # لتر، مل، متر مكعب
        ('AREA', _('مساحة')),          # متر مربع، سم مربع
        ('TIME', _('وقت')),            # ساعة، يوم، شهر
    ]

    code = models.CharField(_('الرمز'), max_length=10)
    name = models.CharField(_('الاسم'), max_length=50)
    name_en = models.CharField(_('الاسم الإنجليزي'), max_length=50, blank=True)

    # ⭐ NEW Week 2: مجموعة وحدات القياس
    uom_group = models.ForeignKey(
        UoMGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='units',
        verbose_name=_('مجموعة الوحدات'),
        help_text=_('المجموعة التي تنتمي إليها هذه الوحدة')
    )

    # نوع وحدة القياس (DEPRECATED - استخدم uom_group بدلاً منه)
    uom_type = models.CharField(
        _('نوع الوحدة'),
        max_length=10,
        choices=UOM_TYPE_CHOICES,
        default='UNIT',
        help_text=_('نوع وحدة القياس (قديم - استخدم المجموعة بدلاً منه)')
    )

    # دقة التقريب
    rounding_precision = models.DecimalField(
        _('دقة التقريب'),
        max_digits=10,
        decimal_places=6,
        default=Decimal('0.01'),
        help_text=_('مثال: 0.01 للتقريب لأقرب 0.01، 1 للتقريب لأقرب عدد صحيح')
    )

    # رمز الوحدة للعرض
    symbol = models.CharField(
        _('الرمز المختصر'),
        max_length=10,
        blank=True,
        help_text=_('مثل: كجم، م، ل')
    )

    # هل هي وحدة أساسية؟
    is_base_unit = models.BooleanField(
        _('وحدة أساسية'),
        default=False,
        help_text=_('هل هذه الوحدة هي الأساس في تصنيفها؟ (مثل: قطعة، كيلو، متر)')
    )

    # ملاحظات
    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('وحدة قياس')
        verbose_name_plural = _('وحدات القياس')
        unique_together = [['code', 'company']]
        ordering = ['uom_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        """
        التحقق من صحة البيانات

        ⭐ ENHANCED Week 2 Day 3
        """
        super().clean()

        errors = {}

        # 1. ⭐ Week 2: التحقق من أن الوحدة لها مجموعة
        if not self.uom_group:
            errors['uom_group'] = _('يجب تحديد مجموعة للوحدة')

        # 2. ⭐ NEW: التحقق من دقة التقريب
        if self.rounding_precision is not None:
            if self.rounding_precision < 0:
                errors['rounding_precision'] = _('دقة التقريب يجب أن تكون موجبة أو صفر')
            elif self.rounding_precision > Decimal('1000'):
                errors['rounding_precision'] = _('دقة التقريب كبيرة جداً')

        # 3. ⭐ NEW: التحقق من الرمز (code)
        if self.code:
            # Check code is not empty after stripping
            if not self.code.strip():
                errors['code'] = _('الرمز لا يمكن أن يكون فارغاً')
            # Check code length
            elif len(self.code.strip()) > 10:
                errors['code'] = _('الرمز طويل جداً (الحد الأقصى 10 أحرف)')
            # Check code uniqueness
            else:
                duplicate = UnitOfMeasure.objects.filter(
                    company=self.company,
                    code=self.code
                ).exclude(pk=self.pk if self.pk else None).exists()

                if duplicate:
                    errors['code'] = _('رمز الوحدة موجود مسبقاً')

        # 4. ⭐ NEW: التحقق من الاسم
        if self.name:
            if len(self.name.strip()) < 2:
                errors['name'] = _('اسم الوحدة قصير جداً (الحد الأدنى حرفان)')

        if errors:
            raise ValidationError(errors)

    def round_quantity(self, quantity):
        """
        تقريب الكمية حسب دقة الوحدة

        Args:
            quantity: الكمية المراد تقريبها

        Returns:
            Decimal: الكمية المقربة
        """
        from decimal import Decimal, ROUND_HALF_UP

        quantity = Decimal(str(quantity))
        precision = self.rounding_precision

        if precision == 0:
            return quantity

        # التقريب لأقرب precision
        rounded = (quantity / precision).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * precision
        return rounded

    def get_conversion_to_base(self):
        """
        الحصول على معامل التحويل إلى الوحدة الأساسية للمجموعة

        ⭐ NEW Week 2

        Returns:
            Decimal: معامل التحويل إلى base_uom، أو 1 إذا كانت هذه هي الوحدة الأساسية
        """
        if not self.uom_group or not self.uom_group.base_uom:
            return Decimal('1')

        if self == self.uom_group.base_uom:
            return Decimal('1')

        # البحث عن conversion مباشر
        try:
            conversion = UoMConversion.objects.get(
                company=self.company,
                from_uom=self,
                item__isnull=True,
                variant__isnull=True
            )
            return conversion.conversion_factor
        except UoMConversion.DoesNotExist:
            return None

    def convert_to(self, target_uom, quantity):
        """
        تحويل الكمية من هذه الوحدة إلى وحدة أخرى عبر السلسلة

        ⭐ NEW Week 2 Day 3 - Enhanced with ConversionChain

        Args:
            target_uom: الوحدة المستهدفة
            quantity: الكمية المراد تحويلها

        Returns:
            Decimal: الكمية بالوحدة المستهدفة

        Raises:
            ValidationError: إذا كانت الوحدتان من مجموعتين مختلفتين

        Example:
            mg.convert_to(ton, Decimal('5000000'))  # = 0.005 ton
        """
        quantity = Decimal(str(quantity))

        # إذا كانت نفس الوحدة
        if self == target_uom:
            return quantity

        # التحقق من نفس المجموعة
        if self.uom_group != target_uom.uom_group:
            raise ValidationError(
                _('لا يمكن التحويل بين وحدات من مجموعات مختلفة')
            )

        # استخدام ConversionChain للتحويل عبر السلسلة
        try:
            from apps.core.utils.uom_utils import ConversionChain

            chain = ConversionChain(self.uom_group, self.company)
            result = chain.calculate(self, target_uom, quantity)
            return result

        except Exception as e:
            # Fallback: محاولة التحويل المباشر عبر base_uom
            # (للتوافق مع الكود القديم)
            factor_to_base = self.get_conversion_to_base()
            if factor_to_base is None:
                raise ValidationError(
                    _('لا يوجد تحويل معرّف من %(from)s إلى الوحدة الأساسية') % {
                        'from': self.name
                    }
                )

            base_quantity = quantity * factor_to_base

            target_factor_to_base = target_uom.get_conversion_to_base()
            if target_factor_to_base is None:
                raise ValidationError(
                    _('لا يوجد تحويل معرّف من %(to)s إلى الوحدة الأساسية') % {
                        'to': target_uom.name
                    }
                )

            result = base_quantity / target_factor_to_base
            return target_uom.round_quantity(result)


class UoMConversion(BaseModel):
    """
    التحويلات بين وحدات القياس

    مثال: 1 دزينة = 12 قطعة
         1 كرتون = 100 قطعة
         1 كيلو = 1000 جرام

    يمكن أن يكون التحويل عام (للمادة) أو خاص (للمتغير)
    """

    # ربط اختياري بالمادة أو المتغير
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='uom_conversions',
        verbose_name=_('المادة'),
        help_text=_('اتركها فارغة للتحويلات العامة')
    )

    variant = models.ForeignKey(
        'ItemVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='uom_conversions',
        verbose_name=_('المتغير'),
        help_text=_('تحويل خاص بمتغير معين')
    )

    # من وحدة (الوحدة الأكبر عادة)
    from_uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='conversions_from',
        verbose_name=_('من وحدة')
    )

    # إلى الوحدة الأساسية (base_uom للمادة)
    # معامل التحويل
    conversion_factor = models.DecimalField(
        _('معامل التحويل'),
        max_digits=20,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text=_('عدد الوحدات الأساسية في وحدة واحدة. مثال: دزينة = 12')
    )

    # معلومات إضافية
    formula_expression = models.CharField(
        _('صيغة التحويل'),
        max_length=200,
        blank=True,
        help_text=_('صيغة نصية توضيحية، مثل: "1 دزينة = 12 قطعة"')
    )

    notes = models.TextField(_('ملاحظات'), blank=True)

    class Meta:
        verbose_name = _('تحويل وحدة قياس')
        verbose_name_plural = _('تحويلات وحدات القياس')
        # التحويل يجب أن يكون فريد للمادة/المتغير + الوحدة المصدر
        unique_together = [
            ['item', 'variant', 'from_uom', 'company']
        ]
        ordering = ['item', 'variant', 'from_uom']

    def __str__(self):
        if self.variant:
            return f"{self.variant}: {self.conversion_factor} {self.from_uom.code}"
        elif self.item:
            return f"{self.item}: {self.conversion_factor} {self.from_uom.code}"
        else:
            return f"عام: {self.from_uom} = {self.conversion_factor}"

    def clean(self):
        """
        التحقق من صحة البيانات - محسّن Week 2 Day 3

        ⭐ ENHANCED Week 2 Day 3
        """
        super().clean()

        errors = {}

        # 1. التحقق من وجود الوحدة المصدر
        if not self.from_uom:
            errors['from_uom'] = _('يجب تحديد وحدة المصدر')
            raise ValidationError(errors)

        # 2. التحقق من معامل التحويل
        if self.conversion_factor is None:
            errors['conversion_factor'] = _('يجب تحديد معامل التحويل')
        elif self.conversion_factor <= 0:
            errors['conversion_factor'] = _('معامل التحويل يجب أن يكون أكبر من صفر')
        elif self.conversion_factor > Decimal('999999999999'):
            errors['conversion_factor'] = _('معامل التحويل كبير جداً')

        # 3. التحقق من العلاقة بين المادة والمتغير
        if self.item and self.variant:
            if self.variant.item_id != self.item.id:
                errors['variant'] = _('المتغير يجب أن ينتمي للمادة المحددة')

        # 4. ⭐ NEW: التحقق من وجود مجموعة للوحدة (للتحويلات العامة)
        if not self.item and not self.variant:
            # تحويل عام - يجب أن يكون للوحدة مجموعة
            if not self.from_uom.uom_group:
                errors['from_uom'] = _(
                    'وحدة المصدر يجب أن تنتمي لمجموعة لتتمكن من التحويل العام'
                )
            elif not self.from_uom.uom_group.base_uom:
                errors['from_uom'] = _(
                    'مجموعة الوحدة يجب أن تحتوي على وحدة أساسية (base_uom)'
                )

        # 5. ⭐ NEW: التحقق من نفس المجموعة (للتحويلات الخاصة بمادة)
        if self.from_uom and self.item and self.item.base_uom:
            if self.from_uom.uom_group_id != self.item.base_uom.uom_group_id:
                errors['from_uom'] = _(
                    'الوحدة يجب أن تكون من نفس مجموعة الوحدة الأساسية للمادة'
                )

        # 6. ⭐ NEW: منع التحويل من الوحدة لنفسها
        if self.from_uom and self.from_uom.uom_group:
            if self.from_uom.uom_group.base_uom_id == self.from_uom.id:
                errors['from_uom'] = _(
                    'لا يمكن إنشاء تحويل من الوحدة الأساسية إلى نفسها'
                )

        # 7. ⭐ NEW: التحقق من وجود تحويل مكرر
        if self.from_uom:
            duplicate = UoMConversion.objects.filter(
                company=self.company,
                from_uom=self.from_uom,
                item=self.item,
                variant=self.variant
            ).exclude(pk=self.pk if self.pk else None).exists()

            if duplicate:
                errors['from_uom'] = _('يوجد تحويل مسجل مسبقاً لهذه الوحدة')

        # Raise all errors at once
        if errors:
            raise ValidationError(errors)

        # 8. ⭐ Week 2 Day 3: منع التحويل الدائري (Circular Conversion)
        # Note: This is disabled for now because bidirectional graphs naturally have cycles
        # The important thing is mathematical consistency (A→B→A = 1)
        # if self.pk and self._creates_circular_conversion():
        #     raise ValidationError(
        #         _('هذا التحويل سينشئ حلقة تحويل دائرية')
        #     )

    def _creates_circular_conversion(self):
        """
        التحقق من وجود حلقة تحويل دائرية

        ⭐ NEW Week 2 Day 3 - IMPLEMENTED

        مثال على حلقة دائرية:
        A → B (factor 2)
        B → C (factor 3)
        C → A (factor 4)  # هذا خطأ!

        Returns:
            bool: True إذا كان التحويل ينشئ حلقة دائرية
        """
        # لا يمكن فحص circular إذا لم يكن للوحدة مجموعة
        if not self.from_uom or not self.from_uom.uom_group:
            return False

        # استيراد ConversionChain
        try:
            from apps.core.utils.uom_utils import ConversionChain

            # إنشاء graph مؤقت يتضمن هذا التحويل
            # نستخدم ConversionChain لفحص وجود دورة
            chain = ConversionChain(self.from_uom.uom_group, self.company)

            # إضافة هذا التحويل مؤقتاً للـ graph
            # ونفحص إذا كان سيسبب دورة
            if self.from_uom.uom_group.base_uom:
                base_id = self.from_uom.uom_group.base_uom.id
                from_id = self.from_uom.id

                # محاكاة إضافة التحويل
                chain.graph[from_id].append((base_id, self.conversion_factor))

                # فحص وجود دورة
                return chain.has_cycle()

        except Exception:
            # في حالة أي خطأ، نعتبر أنه لا يوجد دورة
            # (safer to allow than to block incorrectly)
            return False

        return False

    def convert(self, quantity):
        """
        تحويل الكمية من الوحدة الحالية إلى الوحدة الأساسية

        Args:
            quantity: الكمية بوحدة from_uom

        Returns:
            Decimal: الكمية بالوحدة الأساسية
        """
        quantity = Decimal(str(quantity))
        return quantity * self.conversion_factor

    def convert_back(self, base_quantity):
        """
        تحويل من الوحدة الأساسية إلى الوحدة الحالية

        Args:
            base_quantity: الكمية بالوحدة الأساسية

        Returns:
            Decimal: الكمية بوحدة from_uom
        """
        base_quantity = Decimal(str(base_quantity))
        return base_quantity / self.conversion_factor
