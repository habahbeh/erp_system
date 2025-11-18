# Generated manually for Week 6 - Performance Optimization
# Date: 2025-11-19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_week2_uom_groups'),
    ]

    operations = [
        # ===================================================================
        # Item Indexes - for faster item lookups and filtering
        # ===================================================================
        migrations.AddIndex(
            model_name='item',
            index=models.Index(
                fields=['company', 'is_active', 'item_type'],
                name='item_company_active_type_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(
                fields=['company', 'item_code'],
                name='item_company_code_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(
                fields=['company', 'category', 'is_active'],
                name='item_category_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='item',
            index=models.Index(
                fields=['company', 'has_variants'],
                name='item_has_variants_idx'
            ),
        ),

        # ===================================================================
        # ItemVariant Indexes - for faster variant lookups
        # ===================================================================
        migrations.AddIndex(
            model_name='itemvariant',
            index=models.Index(
                fields=['item', 'is_active'],
                name='variant_item_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='itemvariant',
            index=models.Index(
                fields=['item', 'sku'],
                name='variant_item_sku_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='itemvariant',
            index=models.Index(
                fields=['sku'],
                name='variant_sku_idx'
            ),
        ),

        # ===================================================================
        # PriceList Indexes - for faster price list queries
        # ===================================================================
        migrations.AddIndex(
            model_name='pricelist',
            index=models.Index(
                fields=['company', 'is_active', 'is_default'],
                name='pricelist_company_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricelist',
            index=models.Index(
                fields=['company', 'code'],
                name='pricelist_company_code_idx'
            ),
        ),

        # ===================================================================
        # PriceListItem Indexes - CRITICAL for pricing performance
        # ===================================================================
        migrations.AddIndex(
            model_name='pricelistitem',
            index=models.Index(
                fields=['price_list', 'item_variant', 'uom'],
                name='priceitem_list_variant_uom_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricelistitem',
            index=models.Index(
                fields=['price_list', 'is_active'],
                name='priceitem_list_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricelistitem',
            index=models.Index(
                fields=['item_variant', 'is_active'],
                name='priceitem_variant_active_idx'
            ),
        ),

        # ===================================================================
        # PricingRule Indexes - for faster rule matching
        # ===================================================================
        migrations.AddIndex(
            model_name='pricingrule',
            index=models.Index(
                fields=['company', 'is_active', 'priority'],
                name='pricingrule_active_priority_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricingrule',
            index=models.Index(
                fields=['company', 'rule_type', 'is_active'],
                name='pricingrule_type_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricingrule',
            index=models.Index(
                fields=['category', 'is_active'],
                name='pricingrule_category_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricingrule',
            index=models.Index(
                fields=['start_date', 'end_date', 'is_active'],
                name='pricingrule_dates_idx'
            ),
        ),

        # ===================================================================
        # UoMConversion Indexes - for faster UoM conversions
        # ===================================================================
        migrations.AddIndex(
            model_name='uomconversion',
            index=models.Index(
                fields=['item', 'from_uom', 'to_uom'],
                name='uomconv_item_from_to_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='uomconversion',
            index=models.Index(
                fields=['item', 'uom_group'],
                name='uomconv_item_group_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='uomconversion',
            index=models.Index(
                fields=['from_uom', 'to_uom'],
                name='uomconv_from_to_idx'
            ),
        ),

        # ===================================================================
        # UnitOfMeasure Indexes - for UoM lookups
        # ===================================================================
        migrations.AddIndex(
            model_name='unitofmeasure',
            index=models.Index(
                fields=['company', 'code'],
                name='uom_company_code_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='uomgroup',
            index=models.Index(
                fields=['company', 'code'],
                name='uomgroup_company_code_idx'
            ),
        ),

        # ===================================================================
        # ItemCategory Indexes - for category filtering
        # ===================================================================
        migrations.AddIndex(
            model_name='itemcategory',
            index=models.Index(
                fields=['company', 'parent', 'is_active'],
                name='category_parent_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='itemcategory',
            index=models.Index(
                fields=['company', 'code'],
                name='category_company_code_idx'
            ),
        ),

        # ===================================================================
        # VariantAttribute Indexes - for variant attribute queries
        # ===================================================================
        migrations.AddIndex(
            model_name='variantattribute',
            index=models.Index(
                fields=['company', 'is_active'],
                name='varattr_company_active_idx'
            ),
        ),

        # ===================================================================
        # VariantAttributeAssignment Indexes - for variant lookups
        # ===================================================================
        migrations.AddIndex(
            model_name='variantattributeassignment',
            index=models.Index(
                fields=['variant', 'attribute'],
                name='varattrassign_variant_attr_idx'
            ),
        ),

        # ===================================================================
        # ItemTemplate Indexes - for template operations
        # ===================================================================
        migrations.AddIndex(
            model_name='itemtemplate',
            index=models.Index(
                fields=['company', 'is_active'],
                name='template_company_active_idx'
            ),
        ),

        # ===================================================================
        # BulkImportJob Indexes - for import job tracking
        # ===================================================================
        migrations.AddIndex(
            model_name='bulkimportjob',
            index=models.Index(
                fields=['company', 'status'],
                name='import_company_status_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='bulkimportjob',
            index=models.Index(
                fields=['created_by', 'created_at'],
                name='import_user_date_idx'
            ),
        ),

        # ===================================================================
        # PriceHistory Indexes - for price history queries
        # ===================================================================
        migrations.AddIndex(
            model_name='pricehistory',
            index=models.Index(
                fields=['price_list_item', 'changed_at'],
                name='pricehistory_item_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='pricehistory',
            index=models.Index(
                fields=['changed_by', 'changed_at'],
                name='pricehistory_user_date_idx'
            ),
        ),
    ]
