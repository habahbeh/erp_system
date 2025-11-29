#!/usr/bin/env python
"""
تحليل نماذج المخزون باستخدام Django Model Introspection
Analyze inventory models using Django's _meta API
"""

import django
import os
import sys
from pathlib import Path

# إعداد Django
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.db import models
from decimal import Decimal
import inspect


def analyze_model(model_class):
    """
    تحليل شامل لنموذج Django
    Comprehensive analysis of a Django model
    """
    meta = model_class._meta

    analysis = {
        'name': model_class.__name__,
        'app_label': meta.app_label,
        'db_table': meta.db_table,
        'verbose_name': str(meta.verbose_name),
        'verbose_name_plural': str(meta.verbose_name_plural),
        'abstract': meta.abstract,
        'fields': [],
        'relations': [],
        'reverse_relations': [],
        'methods': [],
        'managers': [],
        'indexes': [],
        'constraints': [],
        'ordering': meta.ordering,
        'permissions': meta.permissions,
        'unique_together': meta.unique_together,
    }

    # الحقول (Fields)
    for field in meta.get_fields():
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'null': getattr(field, 'null', None),
            'blank': getattr(field, 'blank', None),
            'unique': getattr(field, 'unique', None),
            'db_index': getattr(field, 'db_index', None),
            'default': getattr(field, 'default', None),
            'choices': getattr(field, 'choices', None),
            'help_text': getattr(field, 'help_text', ''),
        }

        # معلومات إضافية للعلاقات
        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
            field_info.update({
                'related_model': field.related_model.__name__,
                'on_delete': str(field.remote_field.on_delete),
                'related_name': field.remote_field.related_name,
            })
            analysis['relations'].append(field_info)
        elif isinstance(field, models.ManyToManyField):
            field_info.update({
                'related_model': field.related_model.__name__,
                'related_name': field.remote_field.related_name,
            })
            analysis['relations'].append(field_info)
        elif hasattr(field, 'is_relation') and field.is_relation:
            # Reverse relations
            field_info.update({
                'related_model': field.related_model.__name__,
                'accessor_name': field.get_accessor_name(),
            })
            analysis['reverse_relations'].append(field_info)
        else:
            analysis['fields'].append(field_info)

    # الـ Methods
    for name in dir(model_class):
        if not name.startswith('_'):
            attr = getattr(model_class, name)
            if callable(attr) and not isinstance(attr, type):
                # فحص إذا كان method وليس property
                try:
                    sig = inspect.signature(attr)
                    method_info = {
                        'name': name,
                        'signature': str(sig),
                        'doc': inspect.getdoc(attr) or '',
                    }

                    # استبعاد Django built-in methods
                    if not any(name.startswith(prefix) for prefix in [
                        'check', 'clean', 'validate', 'full_clean',
                        'save', 'delete', 'get_', 'from_db'
                    ]) or name in ['post', 'unpost', 'approve', 'send', 'receive', 'cancel',
                                    'populate_lines', 'process_adjustments', 'create_journal_entry']:
                        analysis['methods'].append(method_info)
                except (ValueError, TypeError):
                    pass

    # Managers
    for name, manager in meta.managers_map.items():
        analysis['managers'].append({
            'name': name,
            'type': manager.__class__.__name__,
        })

    # Indexes
    for index in meta.indexes:
        analysis['indexes'].append({
            'fields': index.fields,
            'name': index.name,
        })

    # Constraints
    for constraint in meta.constraints:
        analysis['constraints'].append({
            'name': constraint.name,
            'type': constraint.__class__.__name__,
        })

    return analysis


def print_model_report(analysis):
    """
    طباعة تقرير مفصل للنموذج
    Print detailed model report
    """
    print("=" * 80)
    print(f"📦 {analysis['name']}")
    print("=" * 80)
    print(f"App: {analysis['app_label']}")
    print(f"Table: {analysis['db_table']}")
    print(f"Verbose: {analysis['verbose_name']} / {analysis['verbose_name_plural']}")
    print(f"Abstract: {analysis['abstract']}")

    if analysis['ordering']:
        print(f"Ordering: {', '.join(analysis['ordering'])}")

    # الحقول
    if analysis['fields']:
        print(f"\n📝 Fields ({len(analysis['fields'])})")
        print("-" * 80)
        for field in analysis['fields']:
            null_str = "NULL" if field.get('null') else "NOT NULL"
            unique_str = "UNIQUE" if field.get('unique') else ""
            index_str = "INDEXED" if field.get('db_index') else ""

            attrs = [null_str, unique_str, index_str]
            attrs = [a for a in attrs if a]

            print(f"  • {field['name']:30} {field['type']:20} [{', '.join(attrs)}]")

            if field.get('choices'):
                print(f"    Choices: {len(field['choices'])} options")
            if field.get('default') not in [None, models.NOT_PROVIDED]:
                print(f"    Default: {field['default']}")

    # العلاقات
    if analysis['relations']:
        print(f"\n🔗 Relations ({len(analysis['relations'])})")
        print("-" * 80)
        for rel in analysis['relations']:
            rel_type = rel['type']
            related = rel.get('related_model', '?')
            related_name = rel.get('related_name', 'N/A')
            on_delete = rel.get('on_delete', '')

            print(f"  • {rel['name']:30} → {related:20} ({rel_type})")
            if related_name:
                print(f"    Related name: {related_name}")
            if on_delete:
                print(f"    On delete: {on_delete}")

    # العلاقات العكسية
    if analysis['reverse_relations']:
        print(f"\n⬅️  Reverse Relations ({len(analysis['reverse_relations'])})")
        print("-" * 80)
        for rel in analysis['reverse_relations'][:5]:  # أول 5 فقط
            print(f"  • {rel.get('accessor_name', rel['name']):30} ← {rel.get('related_model', '?')}")

    # الـ Methods المهمة
    important_methods = ['post', 'unpost', 'approve', 'send', 'receive', 'cancel',
                        'populate_lines', 'process_adjustments', 'create_journal_entry',
                        'is_expired', 'days_to_expiry', 'get_expiry_status',
                        'get_available_quantity', 'reserve_quantity', 'release_reserved_quantity']

    relevant_methods = [m for m in analysis['methods']
                       if m['name'] in important_methods]

    if relevant_methods:
        print(f"\n⚙️  Important Methods ({len(relevant_methods)})")
        print("-" * 80)
        for method in relevant_methods:
            print(f"  • {method['name']}{method['signature']}")
            if method['doc']:
                doc_lines = method['doc'].split('\n')[:2]  # أول سطرين
                for line in doc_lines:
                    print(f"    {line.strip()}")

    # Indexes
    if analysis['indexes']:
        print(f"\n🔍 Indexes ({len(analysis['indexes'])})")
        print("-" * 80)
        for idx in analysis['indexes']:
            print(f"  • {idx.get('name', 'unnamed')}: ({', '.join(idx['fields'])})")

    # Constraints
    if analysis['constraints']:
        print(f"\n🔒 Constraints ({len(analysis['constraints'])})")
        print("-" * 80)
        for const in analysis['constraints']:
            print(f"  • {const['name']} ({const['type']})")

    # Unique Together
    if analysis['unique_together']:
        print(f"\n🔑 Unique Together")
        print("-" * 80)
        for fields in analysis['unique_together']:
            print(f"  • ({', '.join(fields)})")

    print()


def main():
    """
    تحليل جميع نماذج المخزون
    Analyze all inventory models
    """
    print("\n" + "=" * 80)
    print("🔍 تحليل نماذج المخزون باستخدام Django Model Introspection")
    print("   Inventory Models Analysis using Django _meta API")
    print("=" * 80 + "\n")

    # الحصول على تطبيق المخزون
    try:
        inventory_app = apps.get_app_config('inventory')
    except LookupError:
        print("❌ تطبيق المخزون غير موجود!")
        return

    # جميع النماذج
    models_list = inventory_app.get_models()

    print(f"📊 تم العثور على {len(models_list)} نموذج في تطبيق المخزون\n")

    # النماذج المهمة بالترتيب
    important_models = [
        'StockIn', 'StockOut', 'StockTransfer', 'StockCount',
        'StockDocumentLine', 'StockTransferLine', 'StockCountLine',
        'ItemStock', 'StockMovement', 'Batch', 'StockReservation'
    ]

    # تحليل النماذج المهمة أولاً
    for model_name in important_models:
        model = None
        for m in models_list:
            if m.__name__ == model_name:
                model = m
                break

        if model:
            analysis = analyze_model(model)
            print_model_report(analysis)

    # النماذج الأخرى
    other_models = [m for m in models_list
                    if m.__name__ not in important_models]

    if other_models:
        print("\n" + "=" * 80)
        print("📦 نماذج أخرى")
        print("=" * 80 + "\n")

        for model in other_models:
            analysis = analyze_model(model)
            print_model_report(analysis)

    # إحصائيات شاملة
    print("\n" + "=" * 80)
    print("📈 الإحصائيات الشاملة")
    print("=" * 80)

    total_fields = 0
    total_relations = 0
    total_methods = 0

    for model in models_list:
        analysis = analyze_model(model)
        total_fields += len(analysis['fields'])
        total_relations += len(analysis['relations'])

        important_methods = ['post', 'unpost', 'approve', 'send', 'receive', 'cancel',
                            'populate_lines', 'process_adjustments', 'create_journal_entry']
        relevant = [m for m in analysis['methods'] if m['name'] in important_methods]
        total_methods += len(relevant)

    print(f"\nإجمالي النماذج: {len(models_list)}")
    print(f"إجمالي الحقول: {total_fields}")
    print(f"إجمالي العلاقات: {total_relations}")
    print(f"إجمالي الـ Methods المهمة: {total_methods}")

    print("\n" + "=" * 80)
    print("✅ انتهى التحليل")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
