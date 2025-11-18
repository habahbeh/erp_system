# apps/core/views/price_calculator_views.py
"""
Views for Price Calculator and Bulk Operations
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from apps.core.models import PricingRule, PriceList, ItemCategory, Item, PriceListItem
from apps.core.forms.pricing_forms import (
    BulkPriceUpdateForm, PriceSimulationForm, PriceComparisonForm
)
from apps.core.utils.price_calculator import PriceCalculator
from apps.core.utils.pricing_engine import PricingEngine


class BulkPriceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    View for bulk price updates across multiple items.
    Allows applying percentage changes or recalculating based on rules.
    """
    form_class = BulkPriceUpdateForm
    template_name = 'core/pricing/bulk_update.html'
    permission_required = 'core.change_itemprice'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        operation_type = form.cleaned_data['operation_type']
        price_list = form.cleaned_data.get('price_list')
        categories = form.cleaned_data.get('categories')
        items = form.cleaned_data.get('items')
        percentage_change = form.cleaned_data.get('percentage_change')
        apply_rules = form.cleaned_data.get('apply_rules', False)
        apply_changes = form.cleaned_data.get('apply_changes', False)

        calculator = PriceCalculator(self.request.current_company)

        # Build filter for items
        items_qs = Item.objects.filter(
            company=self.request.current_company,
            is_active=True
        )

        if categories:
            items_qs = items_qs.filter(category__in=categories)

        if items:
            items_qs = items_qs.filter(pk__in=[item.pk for item in items])

        if operation_type == 'PERCENTAGE_CHANGE':
            # Apply percentage change
            try:
                result = calculator.bulk_update_prices(
                    rule=None,
                    percentage_change=percentage_change,
                    items=list(items_qs),
                    categories=list(categories) if categories else None,
                    price_list=price_list,
                    apply=apply_changes
                )

                if apply_changes:
                    messages.success(
                        self.request,
                        _('تم تحديث %(count)d سعر بنجاح') % {'count': result['updated_count']}
                    )
                else:
                    messages.info(
                        self.request,
                        _('معاينة: سيتم تحديث %(count)d سعر') % {'count': len(result['preview'])}
                    )

                # Store result in session for display
                self.request.session['bulk_update_result'] = {
                    'operation': 'percentage_change',
                    'updated_count': result.get('updated_count', 0),
                    'preview': result.get('preview', [])[:50],  # Limit preview
                    'total_items': len(result.get('preview', [])),
                    'applied': apply_changes
                }

            except Exception as e:
                messages.error(
                    self.request,
                    _('حدث خطأ أثناء التحديث: %(error)s') % {'error': str(e)}
                )

        elif operation_type == 'RECALCULATE':
            # Recalculate prices using pricing engine
            try:
                engine = PricingEngine(self.request.current_company)
                updated_count = 0
                preview = []

                with transaction.atomic():
                    for item in items_qs[:1000]:  # Limit to prevent timeout
                        # Get or calculate price
                        result = engine.calculate_price(
                            item=item,
                            variant=None,
                            uom=item.base_uom,
                            quantity=Decimal('1'),
                            price_list=price_list,
                            customer=None,
                            check_date=None,
                            apply_rules=apply_rules
                        )

                        if price_list:
                            # Update specific price list
                            price_list_item, created = PriceListItem.objects.get_or_create(
                                item=item,
                                variant=None,
                                price_list=price_list,
                                uom=item.base_uom,
                                defaults={
                                    'price': result.final_price
                                }
                            )

                            if not created and apply_changes:
                                old_price = price_list_item.price
                                price_list_item.price = result.final_price
                                price_list_item.save()

                                preview.append({
                                    'item': item.name,
                                    'old_price': float(old_price),
                                    'new_price': float(result.final_price),
                                    'change': float(result.final_price - old_price)
                                })
                                updated_count += 1
                            elif created and apply_changes:
                                preview.append({
                                    'item': item.name,
                                    'old_price': None,
                                    'new_price': float(result.final_price),
                                    'change': None
                                })
                                updated_count += 1
                            else:
                                # Preview mode
                                preview.append({
                                    'item': item.name,
                                    'old_price': float(price_list_item.price) if not created else None,
                                    'new_price': float(result.final_price),
                                    'change': float(result.final_price - price_list_item.price) if not created else None
                                })

                    if not apply_changes:
                        transaction.set_rollback(True)

                if apply_changes:
                    messages.success(
                        self.request,
                        _('تم إعادة حساب %(count)d سعر بنجاح') % {'count': updated_count}
                    )
                else:
                    messages.info(
                        self.request,
                        _('معاينة: سيتم إعادة حساب %(count)d سعر') % {'count': len(preview)}
                    )

                self.request.session['bulk_update_result'] = {
                    'operation': 'recalculate',
                    'updated_count': updated_count,
                    'preview': preview[:50],
                    'total_items': len(preview),
                    'applied': apply_changes
                }

            except Exception as e:
                messages.error(
                    self.request,
                    _('حدث خطأ أثناء إعادة الحساب: %(error)s') % {'error': str(e)}
                )

        return self.render_to_response(self.get_context_data(
            form=form,
            result=self.request.session.get('bulk_update_result')
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('تحديث الأسعار بالجملة')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': _('تحديث جماعي'), 'url': ''}
        ]

        context['submit_text'] = _('تطبيق التغييرات')
        context['cancel_url'] = reverse('core:pricing_rule_list')

        # Get result from session if exists
        if 'bulk_update_result' in self.request.session and 'result' not in kwargs:
            context['result'] = self.request.session.pop('bulk_update_result')

        return context


class PriceSimulatorView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    View for simulating price changes before applying them.
    Shows impact on items, categories, and profit margins.
    """
    form_class = PriceSimulationForm
    template_name = 'core/pricing/simulator.html'
    permission_required = 'core.view_pricingrule'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        pricing_rule = form.cleaned_data.get('pricing_rule')
        percentage_change = form.cleaned_data.get('percentage_change')
        items = form.cleaned_data.get('items')
        categories = form.cleaned_data.get('categories')
        price_list = form.cleaned_data.get('price_list')
        preview_count = form.cleaned_data.get('preview_count', 50)

        calculator = PriceCalculator(self.request.current_company)

        # Build items list
        items_list = []
        if items:
            items_list.extend(items)

        if categories:
            category_items = Item.objects.filter(
                company=self.request.current_company,
                category__in=categories,
                is_active=True
            )
            items_list.extend(category_items)

        # Remove duplicates
        items_list = list(set(items_list))

        try:
            result = calculator.simulate_price_change(
                rule=pricing_rule,
                percentage_change=percentage_change,
                items=items_list if items_list else None,
                categories=list(categories) if categories else None,
                price_list=price_list,
                preview_count=preview_count
            )

            messages.success(
                self.request,
                _('تم محاكاة %(count)d سعر بنجاح') % {'count': result['total_affected']}
            )

            # Store result in session
            self.request.session['simulation_result'] = result

        except Exception as e:
            messages.error(
                self.request,
                _('حدث خطأ أثناء المحاكاة: %(error)s') % {'error': str(e)}
            )
            result = None

        return self.render_to_response(self.get_context_data(
            form=form,
            result=result
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('محاكي الأسعار')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': _('محاكي الأسعار'), 'url': ''}
        ]

        context['submit_text'] = _('محاكاة التغييرات')
        context['cancel_url'] = reverse('core:pricing_rule_list')

        # Get result from session if exists
        if 'simulation_result' in self.request.session and 'result' not in kwargs:
            context['result'] = self.request.session.pop('simulation_result')

        return context


class PriceComparisonView(LoginRequiredMixin, FormView):
    """
    View for comparing prices across multiple price lists.
    Useful for analyzing pricing strategies and competitiveness.
    """
    form_class = PriceComparisonForm
    template_name = 'core/pricing/comparison.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.current_company
        return kwargs

    def form_valid(self, form):
        items = form.cleaned_data.get('items')
        categories = form.cleaned_data.get('categories')
        price_lists = form.cleaned_data.get('price_lists')
        include_all_lists = form.cleaned_data.get('include_all_lists', False)

        calculator = PriceCalculator(self.request.current_company)

        # Build items list
        items_list = list(items) if items else []

        if categories:
            category_items = Item.objects.filter(
                company=self.request.current_company,
                category__in=categories,
                is_active=True
            )
            items_list.extend(category_items)

        # Remove duplicates
        items_list = list(set(items_list))

        try:
            result = calculator.compare_price_lists(
                items=items_list if items_list else None,
                categories=list(categories) if categories else None,
                price_lists=list(price_lists) if price_lists and not include_all_lists else None,
                include_all_lists=include_all_lists
            )

            messages.success(
                self.request,
                _('تم مقارنة %(items)d مادة عبر %(lists)d قائمة أسعار') % {
                    'items': result['total_items'],
                    'lists': result['total_price_lists']
                }
            )

            # Store result in session
            self.request.session['comparison_result'] = result

        except Exception as e:
            messages.error(
                self.request,
                _('حدث خطأ أثناء المقارنة: %(error)s') % {'error': str(e)}
            )
            result = None

        return self.render_to_response(self.get_context_data(
            form=form,
            result=result
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('مقارنة الأسعار')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': _('مقارنة الأسعار'), 'url': ''}
        ]

        context['submit_text'] = _('مقارنة الأسعار')
        context['cancel_url'] = reverse('core:pricing_rule_list')

        # Get result from session if exists
        if 'comparison_result' in self.request.session and 'result' not in kwargs:
            context['result'] = self.request.session.pop('comparison_result')

        return context


class PriceReportView(LoginRequiredMixin, TemplateView):
    """
    View for generating comprehensive price reports.
    Includes all items, variants, UoMs, and price lists.
    """
    template_name = 'core/pricing/report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter parameters
        price_list_id = self.request.GET.get('price_list')
        category_ids = self.request.GET.getlist('categories')
        include_variants = self.request.GET.get('include_variants', '1') == '1'
        include_inactive = self.request.GET.get('include_inactive', '0') == '1'

        calculator = PriceCalculator(self.request.current_company)

        # Get price list
        price_list = None
        if price_list_id:
            price_list = PriceList.objects.filter(
                company=self.request.current_company,
                pk=price_list_id
            ).first()

        # Get categories
        categories = None
        if category_ids:
            categories = ItemCategory.objects.filter(
                company=self.request.current_company,
                pk__in=category_ids
            )

        # Generate report
        try:
            report = calculator.generate_price_report(
                price_list=price_list,
                categories=list(categories) if categories else None,
                include_variants=include_variants,
                include_inactive=include_inactive
            )

            context['report'] = report

        except Exception as e:
            messages.error(
                self.request,
                _('حدث خطأ أثناء إنشاء التقرير: %(error)s') % {'error': str(e)}
            )
            context['report'] = None

        context['title'] = _('تقرير الأسعار')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('قواعد التسعير'), 'url': reverse('core:pricing_rule_list')},
            {'title': _('تقرير الأسعار'), 'url': ''}
        ]

        # Filter options
        context['price_lists'] = PriceList.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        context['categories'] = ItemCategory.objects.filter(
            company=self.request.current_company,
            is_active=True
        ).order_by('name')

        # Selected filters
        context['selected_price_list'] = price_list
        context['selected_categories'] = categories
        context['include_variants'] = include_variants
        context['include_inactive'] = include_inactive

        return context


class ItemPriceCalculatorView(LoginRequiredMixin, TemplateView):
    """
    View for calculating all prices for a specific item.
    Shows prices across all price lists and UoMs.
    """
    template_name = 'core/pricing/item_calculator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        item_id = kwargs.get('item_id')
        variant_id = self.request.GET.get('variant')
        include_uoms = self.request.GET.get('include_uoms', '1') == '1'

        calculator = PriceCalculator(self.request.current_company)

        # Get item
        item = Item.objects.filter(
            company=self.request.current_company,
            pk=item_id
        ).first()

        if not item:
            messages.error(self.request, _('المادة غير موجودة'))
            return context

        # Get variant if specified
        variant = None
        if variant_id:
            from apps.core.models import ItemVariant
            variant = ItemVariant.objects.filter(
                item=item,
                pk=variant_id
            ).first()

        # Calculate all prices
        try:
            result = calculator.calculate_all_prices(
                item=item,
                variant=variant,
                include_uoms=include_uoms
            )

            context['calculation_result'] = result

        except Exception as e:
            messages.error(
                self.request,
                _('حدث خطأ أثناء حساب الأسعار: %(error)s') % {'error': str(e)}
            )
            context['calculation_result'] = None

        context['title'] = _('حاسبة أسعار المادة')
        context['breadcrumbs'] = [
            {'title': _('الرئيسية'), 'url': reverse('core:dashboard')},
            {'title': _('المواد'), 'url': reverse('core:item_list')},
            {'title': item.name, 'url': reverse('core:item_detail', args=[item.pk])},
            {'title': _('حاسبة الأسعار'), 'url': ''}
        ]

        context['item'] = item
        context['variant'] = variant
        context['include_uoms'] = include_uoms

        # Get variants for selection
        if hasattr(item, 'variants'):
            context['variants'] = item.variants.filter(is_active=True)

        return context
