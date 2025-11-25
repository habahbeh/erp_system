#!/usr/bin/env python3
"""
نسخ التحسينات من order_form.html إلى rfq_form.html
يشمل: CSS، HTML Structure، JavaScript

Created: 2025-01-22
"""

import re
import sys
from pathlib import Path


def extract_css_enhancements(content):
    """استخراج CSS المتقدم من order_form.html"""
    css_pattern = r'<style>(.*?)</style>'
    match = re.search(css_pattern, content, re.DOTALL)

    if match:
        css_content = match.group(1)
        enhancements_start = css_content.find('/* Stock Column Styles */')
        if enhancements_start == -1:
            enhancements_start = css_content.find('.col-stock')

        if enhancements_start != -1:
            return css_content[enhancements_start:]
        else:
            print("⚠️  تحذير: لم يتم العثور على CSS التحسينات")
            return ""

    return ""


def add_css_enhancements(rfq_content, css_additions):
    """إضافة CSS للـ rfq_form.html"""
    style_end = rfq_content.find('</style>')

    if style_end != -1:
        new_content = (
            rfq_content[:style_end] +
            "\n\n    /* ========== Enhanced Styles from Orders ========== */\n" +
            css_additions +
            "\n" +
            rfq_content[style_end:]
        )
        return new_content
    else:
        print("⚠️  لم يتم العثور على <style> tag")
        return rfq_content


def add_stock_column_header(rfq_content):
    """إضافة عمود الرصيد في table header"""
    stock_header_html = '''                        <th style="width: 100px;" class="col-stock">
                            <i class="fas fa-boxes text-info me-1"></i>رصيد
                            <button type="button" class="btn btn-xs btn-link p-0 ms-1"
                                    style="font-size: 10px;" title="رصيد الفرع الحالي">
                                <i class="fas fa-info-circle"></i>
                            </button>
                        </th>'''

    actions_header = rfq_content.find('<th>الإجراءات</th>')

    if actions_header != -1:
        new_content = rfq_content[:actions_header] + stock_header_html + "\n" + rfq_content[actions_header:]
        return new_content
    else:
        print("⚠️  لم يتم العثور على header الإجراءات")
        return rfq_content


def add_stock_column_body(rfq_content):
    """إضافة عمود الرصيد في table body (formset template)"""
    stock_body_html = '''                        <td class="col-stock text-center">
                            <div class="stock-info-cell">
                                <span class="badge bg-light text-dark stock-badge" data-stock="0">
                                    <i class="fas fa-box me-1"></i>
                                    <span class="stock-value">-</span>
                                </span>
                                <button type="button" class="btn btn-xs btn-link p-0 ms-1 btn-show-multi-branch-stock"
                                        title="عرض رصيد كل الفروع">
                                    <i class="fas fa-building text-primary" style="font-size: 12px;"></i>
                                </button>
                            </div>
                        </td>'''

    actions_td_pattern = r'<td class="text-center">\s*<button[^>]+class="btn-delete-line"'
    match = re.search(actions_td_pattern, rfq_content)

    if match:
        insert_pos = match.start()
        new_content = rfq_content[:insert_pos] + stock_body_html + "\n" + rfq_content[insert_pos:]
        return new_content
    else:
        print("⚠️  لم يتم العثور على td الإجراءات في body")
        return rfq_content


def extract_multi_branch_modal(order_content):
    """استخراج Modal رصيد الفروع من order_form.html"""
    modal_start = order_content.find('<div class="modal fade" id="multiBranchStockModal"')
    if modal_start == -1:
        print("⚠️  لم يتم العثور على multiBranchStockModal")
        return ""

    modal_end = order_content.find('</div>\n</div>\n</div>', modal_start)
    if modal_end == -1:
        print("⚠️  لم يتم العثور على نهاية Modal")
        return ""

    modal_end += len('</div>\n</div>\n</div>')

    modal_html = order_content[modal_start:modal_end]
    return modal_html


def add_multi_branch_modal(rfq_content, modal_html):
    """إضافة Modal في نهاية rfq_form.html قبل {% endblock %}"""
    endblock_pos = rfq_content.rfind('{% endblock %}')

    if endblock_pos != -1:
        new_content = (
            rfq_content[:endblock_pos] +
            "\n<!-- Multi-Branch Stock Modal -->\n" +
            modal_html +
            "\n\n" +
            rfq_content[endblock_pos:]
        )
        return new_content
    else:
        print("⚠️  لم يتم العثور على {% endblock %}")
        return rfq_content


def extract_javascript_enhancements(order_content):
    """استخراج JavaScript المتقدم من order_form.html"""
    script_start = order_content.find('<script>')
    if script_start == -1:
        print("⚠️  لم يتم العثور على <script>")
        return ""

    script_end = order_content.rfind('</script>')
    if script_end == -1:
        print("⚠️  لم يتم العثور على </script>")
        return ""

    js_content = order_content[script_start:script_end + len('</script>')]
    return js_content


def replace_order_with_rfq(content):
    """استبدال المراجع من order إلى rfq"""
    replacements = {
        # URLs
        'purchases:order_get_supplier_item_price_ajax': 'purchases:rfq_get_supplier_item_price_ajax',
        'purchases:order_get_item_stock_multi_branch_ajax': 'purchases:rfq_get_item_stock_multi_branch_ajax',
        'purchases:order_get_item_stock_current_branch_ajax': 'purchases:rfq_get_item_stock_current_branch_ajax',
        'purchases:order_item_search_ajax': 'purchases:rfq_item_search_ajax',
        'purchases:save_order_draft_ajax': 'purchases:save_rfq_draft_ajax',

        # Form IDs and variables
        'orderForm': 'rfqForm',
        'order_id': 'rfq_id',
        'order-': 'rfq-',
        "'order'": "'rfq'",
        '"order"': '"rfq"',

        # Comments
        'أمر الشراء': 'طلب عرض سعر',
        'أوامر الشراء': 'طلبات عروض أسعار',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    return content


def main():
    """الدالة الرئيسية"""
    print("🚀 بدء نسخ التحسينات من order_form.html إلى rfq_form.html")
    print("=" * 80)

    # المسارات
    base_dir = Path(__file__).parent
    order_form_path = base_dir / 'apps/purchases/templates/purchases/orders/order_form.html'
    rfq_form_path = base_dir / 'apps/purchases/templates/purchases/rfqs/rfq_form.html'

    # التحقق من وجود الملفات
    if not order_form_path.exists():
        print(f"❌ خطأ: لم يتم العثور على {order_form_path}")
        sys.exit(1)

    if not rfq_form_path.exists():
        print(f"❌ خطأ: لم يتم العثور على {rfq_form_path}")
        sys.exit(1)

    # قراءة الملفات
    print("📖 قراءة order_form.html...")
    with open(order_form_path, 'r', encoding='utf-8') as f:
        order_content = f.read()

    print("📖 قراءة rfq_form.html...")
    with open(rfq_form_path, 'r', encoding='utf-8') as f:
        rfq_content = f.read()

    # 1. CSS
    print("\n1️⃣  استخراج CSS المتقدم...")
    css_additions = extract_css_enhancements(order_content)
    if css_additions:
        rfq_content = add_css_enhancements(rfq_content, css_additions)
        print(f"   ✅ تم إضافة {len(css_additions)} حرف CSS")

    # 2. Stock Column Header
    print("\n2️⃣  إضافة عمود الرصيد في table header...")
    rfq_content = add_stock_column_header(rfq_content)
    print("   ✅ تم إضافة عمود الرصيد في الـ header")

    # 3. Stock Column Body
    print("\n3️⃣  إضافة عمود الرصيد في table body...")
    rfq_content = add_stock_column_body(rfq_content)
    print("   ✅ تم إضافة عمود الرصيد في الـ body")

    # 4. Multi-Branch Modal
    print("\n4️⃣  إضافة Modal رصيد الفروع...")
    modal_html = extract_multi_branch_modal(order_content)
    if modal_html:
        rfq_content = add_multi_branch_modal(rfq_content, modal_html)
        print("   ✅ تم إضافة Modal رصيد الفروع")

    # 5. JavaScript
    print("\n5️⃣  إضافة JavaScript الكامل...")
    js_enhancements = extract_javascript_enhancements(order_content)
    if js_enhancements:
        old_script_start = rfq_content.find('<script>')
        old_script_end = rfq_content.rfind('</script>') + len('</script>')

        if old_script_start != -1 and old_script_end != -1:
            rfq_content = (
                rfq_content[:old_script_start] +
                js_enhancements +
                rfq_content[old_script_end:]
            )
            print(f"   ✅ تم إضافة {len(js_enhancements)} حرف JavaScript")
        else:
            print("   ⚠️  لم يتم العثور على <script> القديم، إضافة في النهاية")
            rfq_content += "\n" + js_enhancements

    # 6. استبدال order → rfq
    print("\n6️⃣  استبدال order → rfq...")
    rfq_content = replace_order_with_rfq(rfq_content)
    print("   ✅ تم استبدال جميع المراجع")

    # حفظ الملف
    print("\n💾 حفظ rfq_form.html...")
    with open(rfq_form_path, 'w', encoding='utf-8') as f:
        f.write(rfq_content)

    print("\n" + "=" * 80)
    print("✅ تم النسخ بنجاح!")
    print(f"📊 حجم الملف الجديد: {len(rfq_content):,} حرف")
    print(f"📁 الموقع: {rfq_form_path}")
    print("\n🔍 الخطوة التالية: اختبر الصفحة على http://127.0.0.1:8000/purchases/rfqs/create/")


if __name__ == '__main__':
    main()
