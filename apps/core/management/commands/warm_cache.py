"""
Warm Cache Management Command
==============================

Pre-loads cache with frequently accessed data to improve performance.

Caches:
- Price list items for all active price lists
- UoM conversions for all items
- Item variant lists
- Common pricing calculations

Usage:
    python manage.py warm_cache
    python manage.py warm_cache --pricing-only
    python manage.py warm_cache --uom-only
    python manage.py warm_cache --company=1

Author: Mohammad + Claude
Date: 2025-11-19
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch
from decimal import Decimal
from datetime import datetime

from apps.core.models import (
    Company, Item, ItemVariant, PriceList, PriceListItem,
    UoMConversion, UnitOfMeasure
)
from apps.core.utils.cache_manager import (
    PricingCacheManager, UoMCacheManager,
    ItemCacheManager, PriceListCacheManager
)
from apps.core.utils.pricing_engine import PricingEngine


class Command(BaseCommand):
    help = 'Warm cache with frequently accessed data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=int,
            help='Company ID to warm cache for (optional, defaults to all)',
        )

        parser.add_argument(
            '--pricing-only',
            action='store_true',
            help='Only warm pricing cache',
        )

        parser.add_argument(
            '--uom-only',
            action='store_true',
            help='Only warm UoM conversion cache',
        )

        parser.add_argument(
            '--items-only',
            action='store_true',
            help='Only warm item variant cache',
        )

        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of items to process (default: 100, use 0 for all)',
        )

    def handle(self, *args, **options):
        company_id = options.get('company')
        pricing_only = options.get('pricing_only')
        uom_only = options.get('uom_only')
        items_only = options.get('items_only')
        limit = options.get('limit')

        # Determine which companies to process
        if company_id:
            companies = Company.objects.filter(id=company_id)
            if not companies.exists():
                raise CommandError(f'Company with ID {company_id} does not exist')
        else:
            companies = Company.objects.filter(is_active=True)

        self.stdout.write(
            self.style.SUCCESS(f'Starting cache warming for {companies.count()} company(ies)...')
        )

        total_start = datetime.now()

        for company in companies:
            self.stdout.write(f'\nProcessing company: {company.name_ar} (ID: {company.id})')

            # Warm pricing cache
            if not uom_only and not items_only:
                self.warm_pricing_cache(company, limit)

            # Warm UoM conversion cache
            if not pricing_only and not items_only:
                self.warm_uom_cache(company, limit)

            # Warm item variant cache
            if not pricing_only and not uom_only:
                self.warm_item_cache(company, limit)

        total_duration = (datetime.now() - total_start).total_seconds()

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Cache warming completed in {total_duration:.2f} seconds'
            )
        )

    def warm_pricing_cache(self, company, limit):
        """Warm pricing cache for common scenarios"""
        self.stdout.write('  Warming pricing cache...')
        start = datetime.now()

        # Get active price lists for this company
        price_lists = PriceList.objects.filter(
            company=company,
            is_active=True
        ).prefetch_related(
            Prefetch(
                'items',
                queryset=PriceListItem.objects.select_related(
                    'item_variant',
                    'uom'
                ).filter(is_active=True)
            )
        )

        if not price_lists.exists():
            self.stdout.write(self.style.WARNING('    No active price lists found'))
            return

        cached_count = 0
        engine = PricingEngine()

        for price_list in price_lists:
            items = price_list.items.all()

            if limit and limit > 0:
                items = items[:limit]

            for price_item in items:
                # Cache the price list item data
                variant = price_item.item_variant
                item = variant.item

                # Common quantities to cache
                quantities = [
                    Decimal('1'),
                    Decimal('10'),
                    Decimal('100')
                ]

                for qty in quantities:
                    # Calculate and cache
                    try:
                        result = engine.calculate_price(
                            item=item,
                            variant=variant,
                            quantity=qty,
                            price_list=price_list,
                            uom=price_item.uom,
                            apply_rules=True
                        )

                        # Cache the result
                        PricingCacheManager.cache_price(
                            item_id=item.id,
                            variant_id=variant.id,
                            quantity=qty,
                            price_list_id=price_list.id,
                            uom_id=price_item.uom.id,
                            pricing_result=result,
                            apply_rules=True
                        )

                        cached_count += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'    Error caching price for {variant.sku}: {e}'
                            )
                        )

        duration = (datetime.now() - start).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(
                f'    ✓ Cached {cached_count} pricing calculations in {duration:.2f}s'
            )
        )

    def warm_uom_cache(self, company, limit):
        """Warm UoM conversion cache"""
        self.stdout.write('  Warming UoM conversion cache...')
        start = datetime.now()

        # Get all items with UoM conversions
        items = Item.objects.filter(
            company=company,
            is_active=True
        ).prefetch_related('uom_conversions')

        if limit and limit > 0:
            items = items[:limit]

        cached_count = 0

        for item in items:
            conversions = item.uom_conversions.all()

            for conversion in conversions:
                # Cache the conversion factor
                UoMCacheManager.cache_conversion(
                    item_id=item.id,
                    from_uom_id=conversion.from_uom_id,
                    to_uom_id=conversion.to_uom_id,
                    conversion_factor=conversion.conversion_factor
                )

                cached_count += 1

        duration = (datetime.now() - start).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(
                f'    ✓ Cached {cached_count} UoM conversions in {duration:.2f}s'
            )
        )

    def warm_item_cache(self, company, limit):
        """Warm item variant cache"""
        self.stdout.write('  Warming item variant cache...')
        start = datetime.now()

        # Get all items with variants
        items = Item.objects.filter(
            company=company,
            is_active=True,
            has_variants=True
        ).prefetch_related(
            Prefetch(
                'variants',
                queryset=ItemVariant.objects.filter(is_active=True)
            )
        )

        if limit and limit > 0:
            items = items[:limit]

        cached_count = 0

        for item in items:
            variants = item.variants.all()

            # Serialize variant data
            variant_data = []
            for variant in variants:
                variant_data.append({
                    'id': variant.id,
                    'sku': variant.sku,
                    'name_ar': variant.name_ar,
                    'name_en': variant.name_en,
                    'cost': float(variant.cost) if variant.cost else 0,
                    'base_price': float(variant.base_price) if variant.base_price else 0,
                    'is_active': variant.is_active,
                })

            # Cache the variant list
            ItemCacheManager.cache_variant_list(
                item_id=item.id,
                variants=variant_data
            )

            cached_count += 1

        duration = (datetime.now() - start).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(
                f'    ✓ Cached {cached_count} item variant lists in {duration:.2f}s'
            )
        )
