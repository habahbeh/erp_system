#!/usr/bin/env python
# tests/inventory/run_tests.py
"""
سكريبت تشغيل اختبارات نظام المخزون
"""

import os
import sys
import subprocess
from datetime import datetime


def run_tests():
    """تشغيل جميع الاختبارات"""

    # إعداد المسار
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(base_dir)

    print("=" * 70)
    print("تشغيل اختبارات نظام المخزون")
    print(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # قائمة ملفات الاختبار
    test_files = [
        'tests/inventory/test_stock_management.py',
        'tests/inventory/test_stock_movements.py',
        'tests/inventory/test_inventory_count.py',
        'tests/inventory/test_valuation.py',
        'tests/inventory/test_batches.py',
        'tests/inventory/test_purchases_integration.py',
        'tests/inventory/test_accounting_integration.py',
        'tests/inventory/test_edge_cases.py',
        'tests/inventory/test_performance.py',
    ]

    results = {}
    total_passed = 0
    total_failed = 0
    total_errors = 0

    for test_file in test_files:
        print(f"\n{'='*70}")
        print(f"تشغيل: {test_file}")
        print("=" * 70)

        # تشغيل الاختبار
        cmd = [
            sys.executable, '-m', 'pytest',
            test_file,
            '-v',
            '--tb=short',
            '--no-header',
            '-q'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 دقائق timeout
            )

            output = result.stdout + result.stderr

            # تحليل النتائج
            passed = output.count(' PASSED')
            failed = output.count(' FAILED')
            errors = output.count(' ERROR')

            total_passed += passed
            total_failed += failed
            total_errors += errors

            results[test_file] = {
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'returncode': result.returncode
            }

            print(output)

        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout في {test_file}")
            results[test_file] = {'passed': 0, 'failed': 0, 'errors': 1, 'returncode': -1}
            total_errors += 1
        except Exception as e:
            print(f"❌ خطأ في تشغيل {test_file}: {e}")
            results[test_file] = {'passed': 0, 'failed': 0, 'errors': 1, 'returncode': -1}
            total_errors += 1

    # طباعة الملخص
    print("\n" + "=" * 70)
    print("ملخص النتائج")
    print("=" * 70)

    for test_file, result in results.items():
        status = "✅" if result['returncode'] == 0 else "❌"
        print(f"{status} {test_file}")
        print(f"   نجح: {result['passed']} | فشل: {result['failed']} | أخطاء: {result['errors']}")

    print("\n" + "-" * 70)
    print(f"الإجمالي: نجح {total_passed} | فشل {total_failed} | أخطاء {total_errors}")
    print("-" * 70)

    # حساب النسبة المئوية
    total_tests = total_passed + total_failed + total_errors
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"نسبة النجاح: {success_rate:.1f}%")

    # حفظ التقرير
    report_file = os.path.join(base_dir, 'reports', 'inv_test_results.md')
    os.makedirs(os.path.dirname(report_file), exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# نتائج اختبارات نظام المخزون\n\n")
        f.write(f"**التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## ملخص\n\n")
        f.write(f"- **نجح:** {total_passed}\n")
        f.write(f"- **فشل:** {total_failed}\n")
        f.write(f"- **أخطاء:** {total_errors}\n")
        if total_tests > 0:
            f.write(f"- **نسبة النجاح:** {success_rate:.1f}%\n")
        f.write("\n## التفاصيل\n\n")

        for test_file, result in results.items():
            status = "✅" if result['returncode'] == 0 else "❌"
            f.write(f"### {status} {test_file}\n\n")
            f.write(f"- نجح: {result['passed']}\n")
            f.write(f"- فشل: {result['failed']}\n")
            f.write(f"- أخطاء: {result['errors']}\n\n")

    print(f"\n📄 تم حفظ التقرير في: {report_file}")

    return total_failed + total_errors == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
