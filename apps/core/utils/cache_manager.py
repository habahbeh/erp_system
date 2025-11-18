"""
Cache Manager for Pricing and UoM System
=========================================

Implements caching strategy for:
- Pricing calculations
- UoM conversion chains
- Item variant lists
- Price list items

Caching Backend: Django's cache framework (supports Redis, Memcached, etc.)

Author: Mohammad + Claude
Date: 2025-11-19
"""

from django.core.cache import cache
from django.conf import settings
from decimal import Decimal
from typing import Optional, Dict, List, Any
import hashlib
import json
from datetime import datetime, timedelta


class CacheManager:
    """Base cache manager with common functionality"""

    # Cache key prefixes
    PREFIX_PRICING = "pricing"
    PREFIX_UOM = "uom"
    PREFIX_ITEM = "item"
    PREFIX_VARIANT = "variant"
    PREFIX_PRICELIST = "pricelist"

    # Default TTL values (in seconds)
    TTL_PRICING = 3600  # 1 hour
    TTL_UOM = 86400  # 24 hours
    TTL_ITEM = 1800  # 30 minutes
    TTL_VARIANT = 1800  # 30 minutes
    TTL_PRICELIST = 3600  # 1 hour

    @staticmethod
    def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate unique cache key from prefix and parameters

        Args:
            prefix: Cache key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            str: Unique cache key
        """
        # Convert all args to strings
        key_parts = [str(prefix)]

        for arg in args:
            if isinstance(arg, Decimal):
                key_parts.append(f"{float(arg):.10f}")
            elif isinstance(arg, datetime):
                key_parts.append(arg.isoformat())
            else:
                key_parts.append(str(arg))

        # Add sorted kwargs
        for key in sorted(kwargs.keys()):
            value = kwargs[key]
            if isinstance(value, Decimal):
                key_parts.append(f"{key}={float(value):.10f}")
            elif isinstance(value, datetime):
                key_parts.append(f"{key}={value.isoformat()}")
            else:
                key_parts.append(f"{key}={value}")

        # Create hash if key is too long
        key_string = ":".join(key_parts)

        if len(key_string) > 200:
            # Hash long keys
            hash_obj = hashlib.md5(key_string.encode())
            return f"{prefix}:hash:{hash_obj.hexdigest()}"

        return key_string

    @staticmethod
    def set_cache(key: str, value: Any, ttl: int) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            bool: True if successful
        """
        try:
            cache.set(key, value, ttl)
            return True
        except Exception as e:
            # Log error but don't fail
            print(f"Cache set error: {e}")
            return False

    @staticmethod
    def get_cache(key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            return cache.get(key)
        except Exception as e:
            # Log error but don't fail
            print(f"Cache get error: {e}")
            return None

    @staticmethod
    def delete_cache(key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            bool: True if successful
        """
        try:
            cache.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "pricing:item:123:*")

        Returns:
            int: Number of keys deleted
        """
        try:
            # This requires Redis backend
            # For other backends, you may need different implementation
            if hasattr(cache, 'delete_pattern'):
                return cache.delete_pattern(pattern)
            else:
                # Fallback: not implemented for non-Redis backends
                return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0


class PricingCacheManager(CacheManager):
    """Cache manager for pricing calculations"""

    @classmethod
    def get_price_cache_key(cls, item_id: int, variant_id: Optional[int],
                          quantity: Decimal, price_list_id: int,
                          uom_id: int, apply_rules: bool = True) -> str:
        """Generate cache key for price calculation"""
        return cls._generate_cache_key(
            cls.PREFIX_PRICING,
            f"item_{item_id}",
            f"variant_{variant_id}",
            f"qty_{quantity}",
            f"pricelist_{price_list_id}",
            f"uom_{uom_id}",
            f"rules_{apply_rules}"
        )

    @classmethod
    def get_cached_price(cls, item_id: int, variant_id: Optional[int],
                        quantity: Decimal, price_list_id: int,
                        uom_id: int, apply_rules: bool = True) -> Optional[Dict]:
        """
        Get cached price calculation result

        Returns:
            Dict with pricing data or None if not cached
        """
        cache_key = cls.get_price_cache_key(
            item_id, variant_id, quantity, price_list_id, uom_id, apply_rules
        )

        return cls.get_cache(cache_key)

    @classmethod
    def cache_price(cls, item_id: int, variant_id: Optional[int],
                   quantity: Decimal, price_list_id: int,
                   uom_id: int, pricing_result: Dict,
                   apply_rules: bool = True, ttl: Optional[int] = None) -> bool:
        """
        Cache price calculation result

        Args:
            item_id: Item ID
            variant_id: Variant ID (optional)
            quantity: Quantity
            price_list_id: Price list ID
            uom_id: Unit of measure ID
            pricing_result: Pricing calculation result to cache
            apply_rules: Whether rules were applied
            ttl: Time to live (uses default if not provided)

        Returns:
            bool: True if cached successfully
        """
        cache_key = cls.get_price_cache_key(
            item_id, variant_id, quantity, price_list_id, uom_id, apply_rules
        )

        return cls.set_cache(
            cache_key,
            pricing_result,
            ttl or cls.TTL_PRICING
        )

    @classmethod
    def invalidate_item_prices(cls, item_id: int) -> int:
        """
        Invalidate all cached prices for an item

        Args:
            item_id: Item ID

        Returns:
            int: Number of keys deleted
        """
        pattern = cls._generate_cache_key(cls.PREFIX_PRICING, f"item_{item_id}") + "*"
        return cls.delete_pattern(pattern)

    @classmethod
    def invalidate_price_list(cls, price_list_id: int) -> int:
        """
        Invalidate all cached prices for a price list

        Args:
            price_list_id: Price list ID

        Returns:
            int: Number of keys deleted
        """
        pattern = f"{cls.PREFIX_PRICING}:*:pricelist_{price_list_id}:*"
        return cls.delete_pattern(pattern)


class UoMCacheManager(CacheManager):
    """Cache manager for UoM conversions"""

    @classmethod
    def get_conversion_cache_key(cls, item_id: int, from_uom_id: int,
                                to_uom_id: int) -> str:
        """Generate cache key for UoM conversion"""
        return cls._generate_cache_key(
            cls.PREFIX_UOM,
            f"item_{item_id}",
            f"from_{from_uom_id}",
            f"to_{to_uom_id}"
        )

    @classmethod
    def get_cached_conversion(cls, item_id: int, from_uom_id: int,
                             to_uom_id: int) -> Optional[Decimal]:
        """
        Get cached conversion factor

        Returns:
            Decimal: Conversion factor or None if not cached
        """
        cache_key = cls.get_conversion_cache_key(item_id, from_uom_id, to_uom_id)
        return cls.get_cache(cache_key)

    @classmethod
    def cache_conversion(cls, item_id: int, from_uom_id: int,
                        to_uom_id: int, conversion_factor: Decimal,
                        ttl: Optional[int] = None) -> bool:
        """
        Cache conversion factor

        Args:
            item_id: Item ID
            from_uom_id: From UoM ID
            to_uom_id: To UoM ID
            conversion_factor: Conversion factor to cache
            ttl: Time to live (uses default if not provided)

        Returns:
            bool: True if cached successfully
        """
        cache_key = cls.get_conversion_cache_key(item_id, from_uom_id, to_uom_id)

        return cls.set_cache(
            cache_key,
            conversion_factor,
            ttl or cls.TTL_UOM
        )

    @classmethod
    def get_conversion_chain_cache_key(cls, item_id: int, from_uom_id: int,
                                      to_uom_id: int) -> str:
        """Generate cache key for conversion chain"""
        return cls._generate_cache_key(
            cls.PREFIX_UOM,
            "chain",
            f"item_{item_id}",
            f"from_{from_uom_id}",
            f"to_{to_uom_id}"
        )

    @classmethod
    def get_cached_conversion_chain(cls, item_id: int, from_uom_id: int,
                                   to_uom_id: int) -> Optional[List[int]]:
        """
        Get cached conversion chain (list of UoM IDs)

        Returns:
            List[int]: List of UoM IDs in conversion path or None
        """
        cache_key = cls.get_conversion_chain_cache_key(item_id, from_uom_id, to_uom_id)
        return cls.get_cache(cache_key)

    @classmethod
    def cache_conversion_chain(cls, item_id: int, from_uom_id: int,
                              to_uom_id: int, chain: List[int],
                              ttl: Optional[int] = None) -> bool:
        """
        Cache conversion chain

        Args:
            item_id: Item ID
            from_uom_id: From UoM ID
            to_uom_id: To UoM ID
            chain: List of UoM IDs in conversion path
            ttl: Time to live (uses default if not provided)

        Returns:
            bool: True if cached successfully
        """
        cache_key = cls.get_conversion_chain_cache_key(item_id, from_uom_id, to_uom_id)

        return cls.set_cache(
            cache_key,
            chain,
            ttl or cls.TTL_UOM
        )

    @classmethod
    def invalidate_item_conversions(cls, item_id: int) -> int:
        """
        Invalidate all cached conversions for an item

        Args:
            item_id: Item ID

        Returns:
            int: Number of keys deleted
        """
        pattern = cls._generate_cache_key(cls.PREFIX_UOM, f"item_{item_id}") + "*"
        return cls.delete_pattern(pattern)


class ItemCacheManager(CacheManager):
    """Cache manager for item data"""

    @classmethod
    def get_variant_list_cache_key(cls, item_id: int) -> str:
        """Generate cache key for item variant list"""
        return cls._generate_cache_key(cls.PREFIX_VARIANT, f"list_{item_id}")

    @classmethod
    def get_cached_variant_list(cls, item_id: int) -> Optional[List[Dict]]:
        """
        Get cached variant list for an item

        Returns:
            List[Dict]: List of variant data or None
        """
        cache_key = cls.get_variant_list_cache_key(item_id)
        return cls.get_cache(cache_key)

    @classmethod
    def cache_variant_list(cls, item_id: int, variants: List[Dict],
                          ttl: Optional[int] = None) -> bool:
        """
        Cache variant list for an item

        Args:
            item_id: Item ID
            variants: List of variant data dictionaries
            ttl: Time to live (uses default if not provided)

        Returns:
            bool: True if cached successfully
        """
        cache_key = cls.get_variant_list_cache_key(item_id)

        return cls.set_cache(
            cache_key,
            variants,
            ttl or cls.TTL_VARIANT
        )

    @classmethod
    def invalidate_item_variants(cls, item_id: int) -> bool:
        """
        Invalidate cached variant list for an item

        Args:
            item_id: Item ID

        Returns:
            bool: True if deleted successfully
        """
        cache_key = cls.get_variant_list_cache_key(item_id)
        return cls.delete_cache(cache_key)


class PriceListCacheManager(CacheManager):
    """Cache manager for price list items"""

    @classmethod
    def get_price_list_items_cache_key(cls, price_list_id: int,
                                      filters: Optional[Dict] = None) -> str:
        """Generate cache key for price list items"""
        if filters:
            return cls._generate_cache_key(
                cls.PREFIX_PRICELIST,
                f"items_{price_list_id}",
                **filters
            )
        return cls._generate_cache_key(
            cls.PREFIX_PRICELIST,
            f"items_{price_list_id}"
        )

    @classmethod
    def get_cached_price_list_items(cls, price_list_id: int,
                                   filters: Optional[Dict] = None) -> Optional[List[Dict]]:
        """
        Get cached price list items

        Returns:
            List[Dict]: List of price list item data or None
        """
        cache_key = cls.get_price_list_items_cache_key(price_list_id, filters)
        return cls.get_cache(cache_key)

    @classmethod
    def cache_price_list_items(cls, price_list_id: int, items: List[Dict],
                              filters: Optional[Dict] = None,
                              ttl: Optional[int] = None) -> bool:
        """
        Cache price list items

        Args:
            price_list_id: Price list ID
            items: List of price list item data dictionaries
            filters: Filters applied (for cache key)
            ttl: Time to live (uses default if not provided)

        Returns:
            bool: True if cached successfully
        """
        cache_key = cls.get_price_list_items_cache_key(price_list_id, filters)

        return cls.set_cache(
            cache_key,
            items,
            ttl or cls.TTL_PRICELIST
        )

    @classmethod
    def invalidate_price_list_items(cls, price_list_id: int) -> int:
        """
        Invalidate all cached items for a price list

        Args:
            price_list_id: Price list ID

        Returns:
            int: Number of keys deleted
        """
        pattern = cls._generate_cache_key(
            cls.PREFIX_PRICELIST,
            f"items_{price_list_id}"
        ) + "*"
        return cls.delete_pattern(pattern)


# ===================================================================
# Convenience Functions
# ===================================================================

def clear_all_pricing_cache():
    """Clear all pricing-related cache"""
    count = 0
    count += CacheManager.delete_pattern(f"{CacheManager.PREFIX_PRICING}:*")
    count += CacheManager.delete_pattern(f"{CacheManager.PREFIX_PRICELIST}:*")
    return count


def clear_all_uom_cache():
    """Clear all UoM-related cache"""
    return CacheManager.delete_pattern(f"{CacheManager.PREFIX_UOM}:*")


def clear_all_item_cache():
    """Clear all item-related cache"""
    count = 0
    count += CacheManager.delete_pattern(f"{CacheManager.PREFIX_ITEM}:*")
    count += CacheManager.delete_pattern(f"{CacheManager.PREFIX_VARIANT}:*")
    return count


def clear_all_cache():
    """Clear all application cache"""
    try:
        cache.clear()
        return True
    except Exception as e:
        print(f"Cache clear error: {e}")
        return False


# ===================================================================
# Usage Examples
# ===================================================================

"""
# Example 1: Cache pricing calculation
from apps.core.utils.cache_manager import PricingCacheManager

# Check cache first
cached_price = PricingCacheManager.get_cached_price(
    item_id=123,
    variant_id=456,
    quantity=Decimal('10'),
    price_list_id=1,
    uom_id=2
)

if cached_price:
    # Use cached result
    print(f"Cached price: {cached_price['final_price']}")
else:
    # Calculate and cache
    result = pricing_engine.calculate_price(...)
    PricingCacheManager.cache_price(
        item_id=123,
        variant_id=456,
        quantity=Decimal('10'),
        price_list_id=1,
        uom_id=2,
        pricing_result=result
    )

# Invalidate when price changes
PricingCacheManager.invalidate_item_prices(item_id=123)


# Example 2: Cache UoM conversion
from apps.core.utils.cache_manager import UoMCacheManager

# Check cache first
factor = UoMCacheManager.get_cached_conversion(
    item_id=123,
    from_uom_id=1,
    to_uom_id=2
)

if factor:
    # Use cached factor
    converted = quantity * factor
else:
    # Calculate and cache
    factor = calculate_conversion_factor(...)
    UoMCacheManager.cache_conversion(
        item_id=123,
        from_uom_id=1,
        to_uom_id=2,
        conversion_factor=factor
    )

# Invalidate when conversion changes
UoMCacheManager.invalidate_item_conversions(item_id=123)
"""
