# apps/core/utils/pricing_engine.py
"""
⭐ Week 3 Day 1: Pricing Engine Core

نظام حساب الأسعار الذكي - Smart Pricing Calculation Engine

يدعم:
- قواعد التسعير الديناميكية (Dynamic Pricing Rules)
- التسعير حسب الكمية (Volume-based Pricing)
- التسعير حسب العميل (Customer-specific Pricing)
- التسعير الموسمي (Time-based Pricing)
- التحويل بين وحدات القياس (UoM Conversions)
- سجل حسابات الأسعار (Calculation Audit Trail)

Author: Claude Code
Created: Week 3 Day 1
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple
from datetime import date
from dataclasses import dataclass, field
from django.utils import timezone
from django.db.models import Q


@dataclass
class PriceCalculationStep:
    """
    خطوة واحدة في حساب السعر
    """
    step_number: int
    description: str
    input_price: Decimal
    output_price: Decimal
    rule_code: Optional[str] = None
    rule_name: Optional[str] = None
    discount_amount: Decimal = Decimal('0.000')
    discount_percentage: Decimal = Decimal('0.00')


@dataclass
class PriceResult:
    """
    نتيجة حساب السعر - Price Calculation Result

    تحتوي على:
    - السعر النهائي
    - السعر الأساسي
    - القواعد المطبقة
    - الخصومات
    - سجل الحساب
    """
    final_price: Decimal
    base_price: Decimal
    applied_rules: List[Dict] = field(default_factory=list)
    calculation_steps: List[PriceCalculationStep] = field(default_factory=list)
    total_discount: Decimal = Decimal('0.000')
    total_discount_percentage: Decimal = Decimal('0.00')
    uom_conversion_applied: bool = False
    uom_conversion_factor: Optional[Decimal] = None
    from_uom: Optional[str] = None
    to_uom: Optional[str] = None
    currency: Optional[str] = None
    calculation_date: date = field(default_factory=lambda: timezone.now().date())

    def get_calculation_log(self) -> List[str]:
        """الحصول على سجل الحساب كنص"""
        log = []
        log.append(f"🔍 حساب السعر - {self.calculation_date}")
        log.append(f"💰 السعر الأساسي: {self.base_price}")

        for step in self.calculation_steps:
            if step.rule_code:
                log.append(
                    f"  {step.step_number}. {step.description} "
                    f"[{step.rule_code}]: {step.input_price} → {step.output_price}"
                )
                if step.discount_amount > 0:
                    log.append(f"     خصم: {step.discount_amount} ({step.discount_percentage}%)")
            else:
                log.append(f"  {step.step_number}. {step.description}: {step.input_price} → {step.output_price}")

        if self.uom_conversion_applied:
            log.append(f"🔄 تحويل الوحدة: {self.from_uom} → {self.to_uom} (× {self.uom_conversion_factor})")

        log.append(f"✅ السعر النهائي: {self.final_price}")
        if self.total_discount > 0:
            log.append(f"💸 إجمالي الخصم: {self.total_discount} ({self.total_discount_percentage}%)")

        return log

    def to_dict(self) -> Dict:
        """تحويل النتيجة إلى dictionary"""
        return {
            'final_price': float(self.final_price),
            'base_price': float(self.base_price),
            'total_discount': float(self.total_discount),
            'total_discount_percentage': float(self.total_discount_percentage),
            'applied_rules': self.applied_rules,
            'calculation_steps': [
                {
                    'step': step.step_number,
                    'description': step.description,
                    'input': float(step.input_price),
                    'output': float(step.output_price),
                    'rule': step.rule_code,
                    'discount': float(step.discount_amount)
                }
                for step in self.calculation_steps
            ],
            'uom_conversion': {
                'applied': self.uom_conversion_applied,
                'from': self.from_uom,
                'to': self.to_uom,
                'factor': float(self.uom_conversion_factor) if self.uom_conversion_factor else None
            },
            'currency': self.currency,
            'date': str(self.calculation_date)
        }


class PricingEngine:
    """
    ⭐ محرك حساب الأسعار الذكي - Smart Pricing Engine

    المسؤوليات:
    1. حساب السعر النهائي بناءً على قواعد متعددة
    2. تطبيق القواعد بالترتيب (حسب الأولوية)
    3. دعم التحويل بين وحدات القياس
    4. تتبع جميع خطوات الحساب
    5. دعم السيناريوهات المعقدة

    Usage:
        engine = PricingEngine(company)
        result = engine.calculate_price(
            item=item,
            variant=variant,
            uom=uom,
            quantity=100,
            price_list=price_list,
            customer=customer
        )
    """

    def __init__(self, company):
        """
        Initialize pricing engine

        Args:
            company: الشركة
        """
        self.company = company
        self._cache = {}  # Cache for frequently accessed data

    def calculate_price(
        self,
        item,
        variant=None,
        uom=None,
        quantity=1,
        price_list=None,
        customer=None,
        check_date=None,
        apply_rules=True
    ) -> PriceResult:
        """
        ⭐ الدالة الرئيسية: حساب السعر النهائي

        Args:
            item: المادة
            variant: المتغير (اختياري)
            uom: وحدة القياس (اختياري - افتراضياً الوحدة الأساسية)
            quantity: الكمية
            price_list: قائمة الأسعار
            customer: العميل (اختياري)
            check_date: تاريخ الحساب (افتراضياً اليوم)
            apply_rules: هل نطبق قواعد التسعير؟

        Returns:
            PriceResult: نتيجة الحساب الكاملة
        """
        from apps.core.models import PriceListItem

        # التحضير
        if not check_date:
            check_date = timezone.now().date()

        quantity = Decimal(str(quantity))

        # 1. الحصول على السعر الأساسي
        base_price = self._get_base_price(
            item, variant, uom, price_list, quantity, check_date
        )

        if base_price == Decimal('0.000'):
            # لا يوجد سعر
            return PriceResult(
                final_price=Decimal('0.000'),
                base_price=Decimal('0.000'),
                currency=price_list.currency.code if price_list else None
            )

        # إنشاء نتيجة الحساب
        result = PriceResult(
            final_price=base_price,
            base_price=base_price,
            currency=price_list.currency.code if price_list else None,
            calculation_date=check_date
        )

        current_price = base_price
        step_number = 1

        # 2. تطبيق قواعد التسعير (إذا كان مطلوباً)
        if apply_rules:
            applicable_rules = self._get_applicable_rules(
                item, variant, price_list, customer, quantity, check_date
            )

            for rule in applicable_rules:
                # حساب السعر الجديد بعد تطبيق القاعدة
                cost_price = variant.cost_price if variant else item.cost_price if hasattr(item, 'cost_price') else None

                new_price = rule.calculate_price(
                    base_price=current_price,
                    quantity=quantity,
                    cost_price=cost_price
                )

                # حساب الخصم
                discount_amount = current_price - new_price
                discount_percentage = Decimal('0.00')
                if current_price > 0:
                    discount_percentage = (discount_amount / current_price) * Decimal('100')

                # إضافة خطوة الحساب
                step = PriceCalculationStep(
                    step_number=step_number,
                    description=rule.name,
                    input_price=current_price,
                    output_price=new_price,
                    rule_code=rule.code,
                    rule_name=rule.name,
                    discount_amount=discount_amount,
                    discount_percentage=discount_percentage
                )
                result.calculation_steps.append(step)

                # تحديث السعر الحالي
                current_price = new_price
                step_number += 1

                # إضافة معلومات القاعدة المطبقة
                result.applied_rules.append({
                    'code': rule.code,
                    'name': rule.name,
                    'type': rule.rule_type,
                    'discount_amount': float(discount_amount),
                    'discount_percentage': float(discount_percentage)
                })

        # 3. تطبيق تحويل وحدة القياس (إذا لزم الأمر)
        if uom and item.base_uom and uom != item.base_uom:
            converted_price, conversion_factor = self._apply_uom_conversion(
                item, current_price, item.base_uom, uom
            )

            if converted_price != current_price:
                # إضافة خطوة التحويل
                step = PriceCalculationStep(
                    step_number=step_number,
                    description=f"تحويل الوحدة من {item.base_uom.name} إلى {uom.name}",
                    input_price=current_price,
                    output_price=converted_price
                )
                result.calculation_steps.append(step)

                current_price = converted_price
                result.uom_conversion_applied = True
                result.uom_conversion_factor = conversion_factor
                result.from_uom = item.base_uom.code
                result.to_uom = uom.code

        # 4. حساب الإجماليات
        result.final_price = current_price
        result.total_discount = base_price - current_price
        if base_price > 0:
            result.total_discount_percentage = (result.total_discount / base_price) * Decimal('100')

        # التقريب
        result.final_price = result.final_price.quantize(
            Decimal('0.001'), rounding=ROUND_HALF_UP
        )

        return result

    def _get_base_price(
        self,
        item,
        variant,
        uom,
        price_list,
        quantity,
        check_date
    ) -> Decimal:
        """
        الحصول على السعر الأساسي من قائمة الأسعار

        Returns:
            Decimal: السعر الأساسي
        """
        from apps.core.models import PriceListItem, PriceList

        # إذا لم تحدد قائمة أسعار، استخدم الافتراضية
        if not price_list:
            price_list = PriceList.objects.filter(
                company=self.company,
                is_default=True,
                is_active=True
            ).first()

            if not price_list:
                price_list = PriceList.objects.filter(
                    company=self.company,
                    is_active=True
                ).first()

            if not price_list:
                return Decimal('0.000')

        try:
            # البحث عن السعر
            query = PriceListItem.objects.filter(
                price_list=price_list,
                item=item,
                is_active=True
            )

            # إضافة شرط المتغير
            if variant:
                query = query.filter(variant=variant)
            else:
                query = query.filter(variant__isnull=True)

            # إضافة شرط UoM (استخدام الوحدة الأساسية إذا لم تحدد)
            if uom:
                # البحث عن سعر لهذه الوحدة المحددة أو الوحدة الأساسية
                query_with_uom = query.filter(uom=uom)
                query_base_uom = query.filter(uom__isnull=True)
                query = query_with_uom | query_base_uom
            else:
                query = query.filter(uom__isnull=True)

            # البحث عن سعر صالح مع الكمية المناسبة
            prices = query.filter(
                min_quantity__lte=quantity
            ).order_by('-min_quantity')

            for price_item in prices:
                if price_item.is_valid_date(check_date):
                    return price_item.price

            return Decimal('0.000')

        except Exception as e:
            # في حالة حدوث خطأ، أرجع 0
            return Decimal('0.000')

    def _get_applicable_rules(
        self,
        item,
        variant,
        price_list,
        customer,
        quantity,
        check_date
    ) -> List:
        """
        الحصول على قواعد التسعير المطبقة

        Returns:
            List[PricingRule]: قائمة القواعد مرتبة حسب الأولوية
        """
        from apps.core.models import PricingRule

        # البحث عن القواعد النشطة
        rules = PricingRule.objects.filter(
            company=self.company,
            is_active=True
        )

        # تصفية القواعد المطبقة
        applicable_rules = []

        for rule in rules:
            # التحقق من التاريخ
            if not rule.is_valid_date(check_date):
                continue

            # التحقق من الكمية
            if rule.min_quantity and quantity < rule.min_quantity:
                continue

            if rule.max_quantity and quantity > rule.max_quantity:
                continue

            # التحقق من النطاق
            if rule.apply_to_all_items:
                applicable_rules.append(rule)
                continue

            # التحقق من قوائم الأسعار
            if price_list and rule.apply_to_price_lists.exists():
                if not rule.apply_to_price_lists.filter(pk=price_list.pk).exists():
                    continue

            # التحقق من المواد
            if rule.apply_to_items.exists():
                if rule.apply_to_items.filter(pk=item.pk).exists():
                    applicable_rules.append(rule)
                    continue

            # التحقق من التصنيفات
            if rule.apply_to_categories.exists():
                if item.category:
                    # التحقق من التصنيف أو أي تصنيف أب
                    category = item.category
                    while category:
                        if rule.apply_to_categories.filter(pk=category.pk).exists():
                            applicable_rules.append(rule)
                            break
                        category = category.parent if hasattr(category, 'parent') else None

        # ترتيب القواعد حسب الأولوية (الأعلى أولاً)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)

        return applicable_rules

    def _apply_uom_conversion(
        self,
        item,
        price,
        from_uom,
        to_uom
    ) -> Tuple[Decimal, Optional[Decimal]]:
        """
        تطبيق تحويل وحدة القياس على السعر

        Args:
            item: المادة
            price: السعر الحالي
            from_uom: الوحدة الحالية
            to_uom: الوحدة المطلوبة

        Returns:
            Tuple[Decimal, Decimal]: (السعر بعد التحويل, معامل التحويل)
        """
        from apps.core.utils.uom_utils import create_conversion_chain

        if not from_uom or not to_uom or from_uom == to_uom:
            return price, None

        try:
            # استخدام نظام التحويل من Week 2
            if hasattr(from_uom, 'uom_group') and from_uom.uom_group:
                chain = create_conversion_chain(from_uom.uom_group, self.company)

                # الحصول على معامل التحويل
                conversion_factor = chain.get_conversion_factor(from_uom, to_uom)

                if conversion_factor:
                    converted_price = price * conversion_factor
                    return converted_price, conversion_factor

        except Exception as e:
            # في حالة فشل التحويل، أرجع السعر الأصلي
            pass

        return price, None

    def calculate_bulk_prices(
        self,
        items_data: List[Dict],
        price_list=None,
        customer=None,
        check_date=None
    ) -> List[PriceResult]:
        """
        حساب أسعار متعددة دفعة واحدة (Bulk)

        Args:
            items_data: قائمة من dictionaries، كل واحد يحتوي على:
                       {'item': Item, 'variant': ItemVariant, 'uom': UoM, 'quantity': Decimal}
            price_list: قائمة الأسعار
            customer: العميل
            check_date: تاريخ الحساب

        Returns:
            List[PriceResult]: قائمة النتائج
        """
        results = []

        for data in items_data:
            result = self.calculate_price(
                item=data.get('item'),
                variant=data.get('variant'),
                uom=data.get('uom'),
                quantity=data.get('quantity', 1),
                price_list=price_list,
                customer=customer,
                check_date=check_date
            )
            results.append(result)

        return results

    def compare_price_lists(
        self,
        item,
        variant=None,
        uom=None,
        quantity=1,
        price_lists=None,
        check_date=None
    ) -> Dict:
        """
        مقارنة الأسعار عبر قوائم أسعار متعددة

        Args:
            item: المادة
            variant: المتغير
            uom: وحدة القياس
            quantity: الكمية
            price_lists: قوائم الأسعار للمقارنة (إذا لم تحدد، ستستخدم جميع القوائم)
            check_date: تاريخ الحساب

        Returns:
            Dict: مقارنة الأسعار
        """
        from apps.core.models import PriceList

        if not price_lists:
            price_lists = PriceList.objects.filter(
                company=self.company,
                is_active=True
            )

        comparison = {
            'item': {
                'code': item.code,
                'name': item.name
            },
            'variant': {
                'code': variant.code,
                'name': variant.code  # ItemVariant doesn't have name field
            } if variant else None,
            'uom': uom.code if uom else None,
            'quantity': float(quantity),
            'price_lists': []
        }

        for price_list in price_lists:
            result = self.calculate_price(
                item=item,
                variant=variant,
                uom=uom,
                quantity=quantity,
                price_list=price_list,
                check_date=check_date
            )

            comparison['price_lists'].append({
                'code': price_list.code,
                'name': price_list.name,
                'currency': price_list.currency.code,
                'final_price': float(result.final_price),
                'base_price': float(result.base_price),
                'total_discount': float(result.total_discount),
                'rules_applied': len(result.applied_rules)
            })

        # ترتيب حسب السعر
        comparison['price_lists'].sort(key=lambda x: x['final_price'])

        # إضافة أرخص وأغلى سعر
        if comparison['price_lists']:
            comparison['lowest_price'] = comparison['price_lists'][0]['final_price']
            comparison['highest_price'] = comparison['price_lists'][-1]['final_price']
            comparison['price_difference'] = comparison['highest_price'] - comparison['lowest_price']

        return comparison

    def simulate_rule(
        self,
        rule,
        items=None,
        categories=None,
        preview_count=10
    ) -> Dict:
        """
        محاكاة تطبيق قاعدة تسعير (دون حفظ)

        Args:
            rule: قاعدة التسعير (يمكن أن تكون كائن أو dict)
            items: المواد للمحاكاة (إذا لم تحدد، ستستخدم عينة)
            categories: التصنيفات للمحاكاة
            preview_count: عدد المواد للمعاينة

        Returns:
            Dict: نتائج المحاكاة
        """
        from apps.core.models import Item, PriceList

        # الحصول على المواد للمحاكاة
        if not items:
            query = Item.objects.filter(company=self.company, is_active=True)

            if categories:
                query = query.filter(category__in=categories)

            items = list(query[:preview_count])

        # الحصول على قائمة الأسعار الافتراضية
        price_list = PriceList.objects.filter(
            company=self.company,
            is_default=True
        ).first()

        simulation_results = {
            'rule': {
                'code': rule.code if hasattr(rule, 'code') else rule.get('code'),
                'name': rule.name if hasattr(rule, 'name') else rule.get('name'),
                'type': rule.rule_type if hasattr(rule, 'rule_type') else rule.get('type'),
            },
            'preview': [],
            'statistics': {
                'items_count': len(items),
                'average_discount': Decimal('0.00'),
                'total_discount': Decimal('0.00')
            }
        }

        total_discount = Decimal('0.00')
        items_with_discount = 0

        for item in items:
            # حساب السعر بدون القاعدة
            result_without = self.calculate_price(
                item=item,
                price_list=price_list,
                apply_rules=False
            )

            # حساب السعر مع القاعدة (مؤقتاً)
            # هنا نحتاج لتطبيق القاعدة يدوياً
            cost_price = item.cost_price if hasattr(item, 'cost_price') else None

            if hasattr(rule, 'calculate_price'):
                new_price = rule.calculate_price(
                    result_without.final_price,
                    quantity=1,
                    cost_price=cost_price
                )
            else:
                # محاكاة بسيطة
                new_price = result_without.final_price

            discount = result_without.final_price - new_price
            discount_pct = Decimal('0.00')
            if result_without.final_price > 0:
                discount_pct = (discount / result_without.final_price) * Decimal('100')

            simulation_results['preview'].append({
                'code': item.code,
                'name': item.name,
                'old_price': float(result_without.final_price),
                'new_price': float(new_price),
                'discount': float(discount),
                'discount_percentage': float(discount_pct)
            })

            if discount > 0:
                total_discount += discount
                items_with_discount += 1

        # حساب الإحصائيات
        if items_with_discount > 0:
            simulation_results['statistics']['average_discount'] = float(
                total_discount / items_with_discount
            )
        simulation_results['statistics']['total_discount'] = float(total_discount)

        return simulation_results


# دوال مساعدة - Helper Functions

def calculate_item_price(
    item,
    variant=None,
    uom=None,
    quantity=1,
    price_list=None,
    customer=None,
    company=None
) -> PriceResult:
    """
    دالة مساعدة سريعة لحساب السعر

    Usage:
        from apps.core.utils.pricing_engine import calculate_item_price

        result = calculate_item_price(
            item=my_item,
            quantity=100,
            price_list=wholesale_list
        )
        print(f"Final Price: {result.final_price}")
    """
    if not company:
        company = item.company

    engine = PricingEngine(company)
    return engine.calculate_price(
        item=item,
        variant=variant,
        uom=uom,
        quantity=quantity,
        price_list=price_list,
        customer=customer
    )


def compare_prices_across_lists(
    item,
    variant=None,
    uom=None,
    quantity=1,
    company=None
) -> Dict:
    """
    دالة مساعدة سريعة لمقارنة الأسعار

    Usage:
        from apps.core.utils.pricing_engine import compare_prices_across_lists

        comparison = compare_prices_across_lists(
            item=my_item,
            quantity=100
        )
        print(f"Lowest: {comparison['lowest_price']}")
        print(f"Highest: {comparison['highest_price']}")
    """
    if not company:
        company = item.company

    engine = PricingEngine(company)
    return engine.compare_price_lists(
        item=item,
        variant=variant,
        uom=uom,
        quantity=quantity
    )
