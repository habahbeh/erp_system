#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لنسخ جميع التحسينات من invoice_form.html إلى order_form.html
يقوم بـ:
1. نسخ CSS الكامل
2. نسخ عمود الرصيد (Stock Column)
3. نسخ Modal رصيد الفروع
4. نسخ JavaScript الكامل
5. استبدال invoice → order في كل مكان
"""

import re
import os
from pathlib import Path

def main():
    # المسارات
    base_dir = Path(__file__).parent
    invoice_template = base_dir / 'apps/purchases/templates/purchases/invoices/invoice_form.html'
    order_template = base_dir / 'apps/purchases/templates/purchases/orders/order_form.html'

    print("🚀 بدء نسخ التحسينات من invoice_form.html إلى order_form.html")
    print("=" * 80)

    # قراءة الملفات
    print("📖 قراءة invoice_form.html...")
    with open(invoice_template, 'r', encoding='utf-8') as f:
        invoice_content = f.read()

    print("📖 قراءة order_form.html...")
    with open(order_template, 'r', encoding='utf-8') as f:
        order_content = f.read()

    # 1. استخراج ونسخ CSS المتقدم
    print("\n1️⃣ استخراج CSS المتقدم...")
    css_enhancements = extract_css_enhancements(invoice_content)
    order_content = add_css_enhancements(order_content, css_enhancements)
    print(f"   ✅ تم إضافة {len(css_enhancements)} سطر CSS")

    # 2. إضافة عمود الرصيد في header
    print("\n2️⃣ إضافة عمود الرصيد في table header...")
    order_content = add_stock_column_header(order_content)
    print("   ✅ تم إضافة عمود الرصيد في الـ header")

    # 3. إضافة عمود الرصيد في body
    print("\n3️⃣ إضافة عمود الرصيد في table body...")
    order_content = add_stock_column_body(order_content)
    print("   ✅ تم إضافة عمود الرصيد في الـ body")

    # 4. إضافة Modal رصيد الفروع
    print("\n4️⃣ إضافة Modal رصيد الفروع...")
    modal_html = extract_multi_branch_modal(invoice_content)
    order_content = add_multi_branch_modal(order_content, modal_html)
    print("   ✅ تم إضافة Modal رصيد الفروع")

    # 5. إضافة JavaScript الكامل
    print("\n5️⃣ إضافة JavaScript الكامل...")
    js_code = extract_javascript_enhancements(invoice_content)
    order_content = add_javascript_enhancements(order_content, js_code)
    print(f"   ✅ تم إضافة {len(js_code)} سطر JavaScript")

    # 6. استبدال invoice → order في كل مكان
    print("\n6️⃣ استبدال invoice → order...")
    order_content = replace_invoice_with_order(order_content)
    print("   ✅ تم استبدال جميع المراجع")

    # حفظ الملف
    print("\n💾 حفظ order_form.html...")
    with open(order_template, 'w', encoding='utf-8') as f:
        f.write(order_content)

    print("\n" + "=" * 80)
    print("✅ تم النسخ بنجاح!")
    print(f"📊 حجم الملف الجديد: {len(order_content):,} حرف")
    print(f"📁 الموقع: {order_template}")
    print("\n🔍 الخطوة التالية: اختبر الصفحة على http://127.0.0.1:8000/purchases/orders/create/")


def extract_css_enhancements(content):
    """استخراج CSS المتقدم من invoice_form"""
    css_additions = """
/* ========================================
   Stock Column Styles - NEW
======================================== */
.col-stock {
    min-width: 100px;
}

.stock-info-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.25rem;
}

.stock-badge {
    font-size: 0.85rem;
    padding: 0.35rem 0.6rem;
    border-radius: 0.25rem;
    white-space: nowrap;
    cursor: help;
}

.stock-badge i {
    font-size: 0.75rem;
}

/* ========================================
   Multi-Branch Stock Modal - NEW
======================================== */
#multiBranchStockModal .modal-content {
    border-radius: 0.5rem;
    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
}

#multiBranchStockModal .modal-header {
    border-top-left-radius: 0.5rem;
    border-top-right-radius: 0.5rem;
}

#multi-branch-stock-loading {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ========================================
   Autocomplete Enhancements - NEW
======================================== */
.autocomplete-wrapper {
    position: relative;
    display: flex;
    align-items: stretch;
}

.autocomplete-search-input {
    flex: 1;
    border-top-left-radius: 0.375rem !important;
    border-bottom-left-radius: 0.375rem !important;
    border-left: none !important;
}

.autocomplete-dropdown-btn {
    width: 28px;
    padding: 0;
    border: 1px solid #dee2e6;
    background: #f8f9fa;
    border-top-right-radius: 0.375rem;
    border-bottom-right-radius: 0.375rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
    flex-shrink: 0;
}

.autocomplete-dropdown-btn:hover {
    background: #e9ecef;
    border-color: #86b7fe;
}

.autocomplete-dropdown-btn i {
    font-size: 10px;
    color: #6c757d;
}

.autocomplete-list {
    position: absolute;
    top: 100%;
    right: 0;
    left: 0;
    z-index: 1050;
    max-height: 300px;
    overflow-y: auto;
    background: white;
    border: 1px solid #dee2e6;
    border-top: none;
    border-radius: 0 0 0.375rem 0.375rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    display: none;
}

.autocomplete-list.show {
    display: block;
}

.autocomplete-item {
    padding: 0.5rem 0.75rem;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.1s;
}

.autocomplete-item:hover,
.autocomplete-item.active {
    background-color: #0d6efd;
    color: white;
}

.autocomplete-item:last-child {
    border-bottom: none;
}

.autocomplete-item small {
    display: block;
    opacity: 0.8;
    font-size: 0.75rem;
}

.autocomplete-loading {
    padding: 0.5rem 0.75rem;
    text-align: center;
    color: #6c757d;
}

/* ========================================
   Column Settings - NEW
======================================== */
.column-settings-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border: 1px solid #dee2e6;
    margin-bottom: 0.5rem;
    border-radius: 0.375rem;
    background: #fff;
}

.column-settings-item .column-name {
    flex: 1;
    font-weight: 500;
}

.column-settings-item.column-hidden {
    opacity: 0.5;
    background: #f8f9fa;
}
"""
    return css_additions


def add_css_enhancements(order_content, css_additions):
    """إضافة CSS المتقدم إلى order_form"""
    # البحث عن نهاية <style>
    style_end = order_content.find('</style>')
    if style_end == -1:
        print("   ⚠️ لم يتم العثور على </style>")
        return order_content

    # إضافة CSS قبل </style>
    order_content = order_content[:style_end] + css_additions + '\n' + order_content[style_end:]
    return order_content


def add_stock_column_header(order_content):
    """إضافة عمود الرصيد في table header"""
    stock_header_html = """                        <th style="width: 100px;" class="col-stock">
                            <i class="fas fa-boxes text-info me-1"></i>رصيد
                            <button type="button" class="btn btn-xs btn-link p-0 ms-1"
                                    style="font-size: 10px;" title="رصيد الفرع الحالي">
                                <i class="fas fa-info-circle"></i>
                            </button>
                        </th>
"""

    # البحث عن <th>المادة</th> وإضافة عمود الرصيد بعدها
    pattern = r'(<th[^>]*>المادة</th>)'
    replacement = r'\1\n' + stock_header_html
    order_content = re.sub(pattern, replacement, order_content)

    return order_content


def add_stock_column_body(order_content):
    """إضافة عمود الرصيد في table body"""
    stock_body_html = """                            <td class="col-stock text-center">
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
                            </td>
"""

    # البحث عن المادة في body وإضافة عمود الرصيد بعدها
    # نبحث عن <td class... item...> ونضيف بعدها
    pattern = r'({{ item_form\.item\|add_class:"item-select" }}[^\n]*</div>[^\n]*</td>)'
    replacement = r'\1\n' + stock_body_html
    order_content = re.sub(pattern, replacement, order_content)

    return order_content


def extract_multi_branch_modal(invoice_content):
    """استخراج Modal رصيد الفروع من invoice_form"""
    modal_html = """
<!-- Multi-Branch Stock Modal -->
<div class="modal fade" id="multiBranchStockModal" tabindex="-1" aria-labelledby="multiBranchStockModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-primary text-white">
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                <h5 class="modal-title" id="multiBranchStockModalLabel">
                    <i class="fas fa-building me-2"></i>
                    رصيد المخزون في كل الفروع
                </h5>
            </div>
            <div class="modal-body">
                <!-- Loading Spinner -->
                <div id="multi-branch-stock-loading" class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                    <p class="mt-2 text-muted">جاري جلب البيانات...</p>
                </div>

                <!-- Content -->
                <div id="multi-branch-stock-content" style="display: none;">
                    <div class="table-responsive">
                        <table class="table table-sm table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>الفرع</th>
                                    <th>المخزن</th>
                                    <th class="text-end">الكمية</th>
                                    <th class="text-end">محجوز</th>
                                    <th class="text-end">متاح</th>
                                    <th class="text-end">متوسط التكلفة</th>
                                </tr>
                            </thead>
                            <tbody id="multi-branch-stock-tbody">
                                <!-- سيتم ملؤها بالـ JavaScript -->
                            </tbody>
                            <tfoot id="multi-branch-stock-footer" class="table-secondary fw-bold">
                                <!-- سيتم ملؤها بالـ JavaScript -->
                            </tfoot>
                        </table>
                    </div>
                </div>

                <!-- No Data Message -->
                <div id="multi-branch-stock-no-data" style="display: none;" class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    لا توجد بيانات مخزون لهذه المادة
                </div>
            </div>
        </div>
    </div>
</div>
"""
    return modal_html


def add_multi_branch_modal(order_content, modal_html):
    """إضافة Modal قبل </body> أو نهاية المحتوى"""
    # البحث عن {% endblock %}
    pattern = r'({% endblock %})'
    replacement = modal_html + '\n' + r'\1'
    order_content = re.sub(pattern, replacement, order_content, count=1)

    return order_content


def extract_javascript_enhancements(invoice_content):
    """استخراج JavaScript المحسّن"""
    js_code = """
<script>
$(document).ready(function() {
    // ============================================
    // التحسينات الجديدة - Stock Info & Live Search
    // ============================================

    const USE_LIVE_SEARCH = {{ use_live_search|default:False|lower }};

    // ========================================
    // 1. Update Stock Info Function
    // ========================================
    function updateStockInfo($row) {
        const itemId = $row.find('.item-select').val();
        const variantId = $row.find('.variant-select').val();

        if (!itemId) {
            $row.find('.stock-value').text('-');
            $row.find('.stock-badge')
                .removeClass('bg-success bg-warning bg-danger text-white text-dark')
                .addClass('bg-light text-dark');
            return;
        }

        const $stockBadge = $row.find('.stock-badge');
        const $stockValue = $row.find('.stock-value');

        $.ajax({
            url: '{% url "purchases:order_get_item_stock_current_branch_ajax" %}',
            data: {
                item_id: itemId,
                variant_id: variantId || ''
            },
            success: function(response) {
                if (response.success) {
                    const available = parseFloat(response.available);
                    $stockValue.text(available.toFixed(3));

                    // Color coding based on availability
                    $stockBadge.removeClass('bg-success bg-warning bg-danger bg-light text-dark text-white');
                    if (available > 10) {
                        $stockBadge.addClass('bg-success text-white');
                    } else if (available > 0) {
                        $stockBadge.addClass('bg-warning text-dark');
                    } else {
                        $stockBadge.addClass('bg-danger text-white');
                    }

                    // Tooltip
                    const tooltip = `إجمالي: ${response.quantity}\\nمحجوز: ${response.reserved}\\nمتاح: ${response.available}`;
                    $stockBadge.attr('title', tooltip);
                } else {
                    $stockValue.text('-');
                }
            },
            error: function() {
                console.error('Error fetching stock info');
            }
        });
    }

    // ========================================
    // 2. Auto-fill Supplier Price Function
    // ========================================
    function autoFillSupplierPrice($row) {
        const supplierId = $('#id_supplier').val();
        const itemId = $row.find('.item-select').val();
        const variantId = $row.find('.variant-select').val();
        const $priceInput = $row.find('.price-input');

        if (!supplierId || !itemId) {
            return;
        }

        // لا تستبدل القيمة المُدخلة يدوياً
        if ($priceInput.val() && parseFloat($priceInput.val()) > 0) {
            return;
        }

        $.ajax({
            url: '{% url "purchases:order_get_supplier_item_price_ajax" %}',
            data: {
                supplier_id: supplierId,
                item_id: itemId,
                variant_id: variantId || ''
            },
            success: function(response) {
                if (response.success && response.has_price) {
                    // ملء السعر
                    $priceInput.val(parseFloat(response.last_price).toFixed(3));

                    // خلفية صفراء مؤقتة للتمييز
                    $priceInput.css('background-color', '#fff3cd');
                    setTimeout(function() {
                        $priceInput.css('background-color', '');
                    }, 2000);

                    // Tooltip مع معلومات السعر
                    const tooltip = `آخر سعر شراء: ${response.last_price}\\nالتاريخ: ${response.last_date || 'غير محدد'}\\nالكمية: ${response.last_quantity || 'غير محدد'}`;
                    $priceInput.attr('title', tooltip);

                    // حساب الإجمالي
                    calculateItemTotal($row);
                    calculateTotals();
                }
            },
            error: function() {
                console.error('Error fetching supplier price');
            }
        });
    }

    // ========================================
    // 3. Multi-Branch Stock Modal Handler
    // ========================================
    $(document).on('click', '.btn-show-multi-branch-stock', function() {
        const $row = $(this).closest('tr');
        const itemId = $row.find('.item-select').val();
        const variantId = $row.find('.variant-select').val();

        if (!itemId) {
            Swal.fire({
                title: 'تنبيه',
                text: 'يرجى اختيار المادة أولاً',
                icon: 'warning',
                confirmButtonText: 'حسناً'
            });
            return;
        }

        // فتح Modal
        const modal = new bootstrap.Modal(document.getElementById('multiBranchStockModal'));
        modal.show();

        // عرض Loading
        $('#multi-branch-stock-loading').show();
        $('#multi-branch-stock-content').hide();
        $('#multi-branch-stock-no-data').hide();

        // جلب البيانات
        $.ajax({
            url: '{% url "purchases:order_get_item_stock_multi_branch_ajax" %}',
            data: {
                item_id: itemId,
                variant_id: variantId || ''
            },
            success: function(response) {
                $('#multi-branch-stock-loading').hide();

                if (response.success && response.has_stock && response.branches.length > 0) {
                    // ملء الجدول
                    let html = '';
                    response.branches.forEach(function(branch) {
                        const available = parseFloat(branch.available);
                        let rowClass = '';
                        if (available > 10) {
                            rowClass = 'table-success';
                        } else if (available > 0) {
                            rowClass = 'table-warning';
                        } else {
                            rowClass = 'table-danger';
                        }

                        html += `<tr class="${rowClass}">
                            <td>${branch.branch_name}</td>
                            <td>${branch.warehouse_name}</td>
                            <td class="text-end">${parseFloat(branch.quantity).toFixed(3)}</td>
                            <td class="text-end">${parseFloat(branch.reserved).toFixed(3)}</td>
                            <td class="text-end"><strong>${available.toFixed(3)}</strong></td>
                            <td class="text-end">${parseFloat(branch.average_cost).toFixed(3)}</td>
                        </tr>`;
                    });

                    $('#multi-branch-stock-tbody').html(html);

                    // Footer - الإجمالي
                    const footer = `<tr>
                        <th colspan="2">الإجمالي</th>
                        <th class="text-end">${parseFloat(response.total_quantity).toFixed(3)}</th>
                        <th class="text-end">-</th>
                        <th class="text-end"><strong>${parseFloat(response.total_available).toFixed(3)}</strong></th>
                        <th class="text-end">-</th>
                    </tr>`;
                    $('#multi-branch-stock-footer').html(footer);

                    $('#multi-branch-stock-content').show();
                } else {
                    $('#multi-branch-stock-no-data').show();
                }
            },
            error: function() {
                $('#multi-branch-stock-loading').hide();
                Swal.fire({
                    title: 'خطأ',
                    text: 'حدث خطأ أثناء جلب البيانات',
                    icon: 'error',
                    confirmButtonText: 'حسناً'
                });
            }
        });
    });

    // ========================================
    // 4. AJAX Live Search للمواد
    // ========================================
    if (USE_LIVE_SEARCH) {
        let searchTimeout = null;
        let itemsCache = {};

        function initItemLiveSearch($input) {
            $input.on('input', function() {
                const term = $(this).val().trim();
                const $wrapper = $(this).closest('.autocomplete-wrapper');
                const $autocompleteList = $wrapper.find('.autocomplete-list');

                clearTimeout(searchTimeout);

                if (term.length < 2) {
                    $autocompleteList.hide();
                    return;
                }

                // Check cache
                if (itemsCache[term]) {
                    displaySearchResults(itemsCache[term], $autocompleteList, $input);
                    return;
                }

                // Show loading
                $autocompleteList.html('<div class="autocomplete-loading"><i class="fas fa-spinner fa-spin"></i> جاري البحث...</div>').show();

                searchTimeout = setTimeout(function() {
                    $.ajax({
                        url: '{% url "purchases:order_item_search_ajax" %}',
                        data: { term: term, limit: 20 },
                        success: function(response) {
                            if (response.success) {
                                itemsCache[term] = response.items;
                                displaySearchResults(response.items, $autocompleteList, $input);
                            } else {
                                $autocompleteList.html('<div class="autocomplete-loading text-danger">خطأ في البحث</div>');
                            }
                        },
                        error: function() {
                            $autocompleteList.html('<div class="autocomplete-loading text-danger">خطأ في البحث</div>');
                        }
                    });
                }, 300); // Debounce 300ms
            });

            // Hide on click outside
            $(document).on('click', function(e) {
                if (!$(e.target).closest('.autocomplete-wrapper').length) {
                    $('.autocomplete-list').hide();
                }
            });
        }

        function displaySearchResults(items, $autocompleteList, $input) {
            if (items.length === 0) {
                $autocompleteList.html('<div class="autocomplete-loading">لا توجد نتائج</div>').show();
                return;
            }

            let html = '';
            items.forEach(function(item) {
                const stock = parseFloat(item.current_branch_stock || 0);
                const reserved = parseFloat(item.current_branch_reserved || 0);
                const available = stock - reserved;

                let stockBadge = '';
                if (available > 10) {
                    stockBadge = `<span class="badge bg-success">متاح: ${available.toFixed(1)}</span>`;
                } else if (available > 0) {
                    stockBadge = `<span class="badge bg-warning text-dark">متاح: ${available.toFixed(1)}</span>`;
                } else {
                    stockBadge = `<span class="badge bg-danger">غير متوفر</span>`;
                }

                html += `<div class="autocomplete-item" data-item='${JSON.stringify(item)}'>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${item.name}</strong>
                            <small class="d-block text-muted">${item.code} | ${item.base_uom_name}</small>
                        </div>
                        <div>
                            ${stockBadge}
                        </div>
                    </div>
                </div>`;
            });

            $autocompleteList.html(html).show();

            // Click handler
            $autocompleteList.find('.autocomplete-item').on('click', function(e) {
                e.stopPropagation();
                const itemData = JSON.parse($(this).attr('data-item'));
                selectItem(itemData, $input);
                $autocompleteList.hide();
            });
        }

        function selectItem(itemData, $input) {
            const $row = $input.closest('tr');
            const $select = $row.find('.item-select');

            // Update select
            if ($select.find(`option[value="${itemData.id}"]`).length === 0) {
                $select.append(`<option value="${itemData.id}">${itemData.name}</option>`);
            }
            $select.val(itemData.id).trigger('change');

            // Update display
            $input.val(itemData.name);

            // Update stock
            updateStockInfo($row);

            // Auto-fill price
            autoFillSupplierPrice($row);

            // Update tax rate
            $row.find('.tax-rate-input').val(parseFloat(itemData.tax_rate));
        }

        // Initialize for existing rows
        $('.item-search-input').each(function() {
            initItemLiveSearch($(this));
        });

        // Initialize for new rows
        $(document).on('click', '#btn-add-line', function() {
            setTimeout(function() {
                $('.item-search-input').each(function() {
                    if (!$(this).data('live-search-initialized')) {
                        initItemLiveSearch($(this));
                        $(this).data('live-search-initialized', true);
                    }
                });
            }, 100);
        });
    }

    // ========================================
    // 5. Event Handlers
    // ========================================

    // عند تغيير المادة
    $(document).on('change', '.item-select', function() {
        const $row = $(this).closest('tr');
        updateStockInfo($row);
        autoFillSupplierPrice($row);
    });

    // عند تغيير المورد - update all prices
    $('#id_supplier').on('change', function() {
        $('#items-tbody tr').each(function() {
            autoFillSupplierPrice($(this));
        });
    });

    // Initialize stock info for existing rows
    $('#items-tbody tr').each(function() {
        updateStockInfo($(this));
    });
});
</script>
"""
    return js_code


def add_javascript_enhancements(order_content, js_code):
    """إضافة JavaScript قبل {% endblock extra_js %}"""
    # البحث عن {% endblock extra_js %} أو {% endblock %}
    pattern = r'({% endblock extra_js %}|{% endblock %})'
    replacement = js_code + '\n' + r'\1'
    order_content = re.sub(pattern, replacement, order_content, count=1)

    return order_content


def replace_invoice_with_order(content):
    """استبدال invoice → order في كل مكان"""
    # استبدال URLs
    content = content.replace('purchases:get_supplier_item_price_ajax', 'purchases:order_get_supplier_item_price_ajax')
    content = content.replace('purchases:get_item_stock_multi_branch_ajax', 'purchases:order_get_item_stock_multi_branch_ajax')
    content = content.replace('purchases:get_item_stock_current_branch_ajax', 'purchases:order_get_item_stock_current_branch_ajax')
    content = content.replace('purchases:item_search_ajax', 'purchases:order_item_search_ajax')
    content = content.replace('purchases:save_invoice_draft_ajax', 'purchases:save_order_draft_ajax')

    # استبدال متغيرات
    content = content.replace('invoiceForm', 'orderForm')
    content = content.replace('invoice_id', 'order_id')

    return content


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ حدث خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
