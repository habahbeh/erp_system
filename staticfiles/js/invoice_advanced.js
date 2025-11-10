/**
 * ============================================================================
 * ADVANCED INVOICE FEATURES
 * ============================================================================
 * المميزات المتقدمة للفواتير:
 * 1. البحث السريع للمواد (Quick Item Search)
 * 2. تمييز الضريبة بالألوان (Tax Color Coding)
 * 3. نظام الموافقات للدفع الآجل (Credit Approval System)
 * 4. دعم الكيبورد الكامل (Full Keyboard Support)
 * 5. عرض آخر سعر وسجل المبيعات (Price History)
 * 6. التحكم في أعمدة الجدول (Column Control)
 * 7. شريط الحالة المحسن (Enhanced Status Bar)
 */

(function() {
    'use strict';

    // ========================================================================
    // CONFIGURATION
    // ========================================================================
    const CONFIG = {
        colors: {
            taxExempt: '#d4edda',    // أخضر فاتح - معفى من الضريبة
            taxable: '#f8d7da',       // أحمر فاتح - خاضع للضريبة
            focused: '#FFFACD'        // أصفر فاتح - الحقل النشط
        },
        keyboard: {
            shortcuts: {
                save: 'F9',
                cancel: 'Escape',
                addRow: 'F2',
                search: 'F3',
                dropdown: 'F4',
                refresh: 'F5',
                deleteRow: 'Ctrl+D',
                nextField: 'Tab',
                prevField: 'Shift+Tab'
            }
        },
        search: {
            minChars: 2,           // الحد الأدنى لعدد الأحرف للبحث
            delay: 300,            // التأخير بالميلي ثانية
            maxResults: 10         // أقصى عدد للنتائج
        }
    };

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================

    /**
     * عرض رسالة في شريط الحالة
     */
    function updateStatusBar(message, type = 'info') {
        const statusBar = document.querySelector('.oracle-status-bar');
        if (!statusBar) return;

        const messageElement = statusBar.querySelector('.status-message') || createStatusMessage();
        messageElement.textContent = message;
        messageElement.className = `status-message status-${type}`;
    }

    function createStatusMessage() {
        const statusBar = document.querySelector('.oracle-status-bar');
        const messageEl = document.createElement('span');
        messageEl.className = 'status-message';
        statusBar.appendChild(messageEl);
        return messageEl;
    }

    /**
     * إضافة CSS ديناميكي
     */
    function injectCSS() {
        const style = document.createElement('style');
        style.textContent = `
            /* Tax Status Colors */
            .tax-exempt-row {
                background-color: ${CONFIG.colors.taxExempt} !important;
            }

            .taxable-row {
                background-color: ${CONFIG.colors.taxable} !important;
            }

            /* Autocomplete Dropdown */
            .item-autocomplete {
                position: absolute;
                background: white;
                border: 2px solid #808080;
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                min-width: 400px;
            }

            .item-autocomplete-item {
                padding: 6px 10px;
                cursor: pointer;
                border-bottom: 1px solid #E0E0E0;
                font-size: 11px;
            }

            .item-autocomplete-item:hover,
            .item-autocomplete-item.selected {
                background-color: #4A90E2;
                color: white;
            }

            .item-autocomplete-item-code {
                font-weight: bold;
                color: #000080;
            }

            .item-autocomplete-item-name {
                color: #000;
            }

            .item-autocomplete-item-price {
                float: right;
                color: #006600;
                font-weight: bold;
            }

            /* Status Bar Enhanced */
            .status-message {
                padding: 2px 8px;
                margin-left: 10px;
                border-radius: 2px;
            }

            .status-message.status-info {
                background-color: #D1ECF1;
                color: #0C5460;
            }

            .status-message.status-warning {
                background-color: #FFF3CD;
                color: #856404;
            }

            .status-message.status-error {
                background-color: #F8D7DA;
                color: #721C24;
            }

            .status-message.status-success {
                background-color: #D4EDDA;
                color: #155724;
            }

            /* Column Control Menu */
            .column-control-menu {
                position: absolute;
                background: white;
                border: 2px solid #808080;
                padding: 10px;
                z-index: 1001;
                box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                min-width: 200px;
            }

            .column-control-item {
                display: block;
                padding: 4px 0;
            }

            .column-control-item input[type="checkbox"] {
                margin-right: 6px;
            }

            /* Price History Modal */
            .price-history-modal {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #D4D0C8;
                border: 2px solid #808080;
                padding: 15px;
                z-index: 2000;
                max-width: 800px;
                max-height: 600px;
                overflow: auto;
                box-shadow: 4px 4px 8px rgba(0,0,0,0.4);
            }

            .price-history-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                z-index: 1999;
            }

            .price-history-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }

            .price-history-table th,
            .price-history-table td {
                border: 1px solid #808080;
                padding: 4px 8px;
                font-size: 11px;
                text-align: right;
            }

            .price-history-table th {
                background-color: #E0E0E0;
                font-weight: bold;
            }

            .price-history-table tr:hover {
                background-color: #FFFACD;
            }

            /* Approval Pending Indicator */
            .approval-pending {
                color: #FF6600;
                font-weight: bold;
                animation: blink 1s infinite;
            }

            @keyframes blink {
                50% { opacity: 0.5; }
            }

            /* Keyboard Shortcut Hint */
            .keyboard-hint {
                font-size: 10px;
                color: #666;
                margin-left: 5px;
            }
        `;
        document.head.appendChild(style);
    }

    // ========================================================================
    // 1. QUICK ITEM SEARCH (البحث السريع للمواد)
    // ========================================================================

    class ItemAutoComplete {
        constructor(inputElement) {
            this.input = inputElement;
            this.dropdown = null;
            this.selectedIndex = -1;
            this.results = [];
            this.timeout = null;

            this.init();
        }

        init() {
            this.input.addEventListener('input', (e) => this.handleInput(e));
            this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
            this.input.addEventListener('blur', () => {
                // تأخير الإخفاء للسماح بالنقر على النتائج
                setTimeout(() => this.hide(), 200);
            });
        }

        handleInput(e) {
            const value = e.target.value.trim();

            clearTimeout(this.timeout);

            if (value.length < CONFIG.search.minChars) {
                this.hide();
                return;
            }

            this.timeout = setTimeout(() => {
                this.search(value);
            }, CONFIG.search.delay);
        }

        async search(query) {
            try {
                // بحث مختصر - يدعم الأحرف الأولى
                const response = await fetch(`/ajax/items/search/?q=${encodeURIComponent(query)}&quick=1&limit=${CONFIG.search.maxResults}`);
                const data = await response.json();

                this.results = data.results || [];
                this.show();
            } catch (error) {
                console.error('Search error:', error);
                updateStatusBar('خطأ في البحث', 'error');
            }
        }

        show() {
            if (this.results.length === 0) {
                this.hide();
                return;
            }

            if (!this.dropdown) {
                this.dropdown = document.createElement('div');
                this.dropdown.className = 'item-autocomplete';
                document.body.appendChild(this.dropdown);
            }

            // تحديد موقع القائمة
            const rect = this.input.getBoundingClientRect();
            this.dropdown.style.top = `${rect.bottom + window.scrollY}px`;
            this.dropdown.style.left = `${rect.left + window.scrollX}px`;

            // ملء النتائج
            this.dropdown.innerHTML = this.results.map((item, index) => `
                <div class="item-autocomplete-item" data-index="${index}" data-item-id="${item.id}">
                    <span class="item-autocomplete-item-code">${item.code}</span> -
                    <span class="item-autocomplete-item-name">${item.name}</span>
                    <span class="item-autocomplete-item-price">${item.price} ${item.currency}</span>
                    ${item.stock ? `<br><small>رصيد: ${item.stock}</small>` : ''}
                </div>
            `).join('');

            // إضافة مستمعي الأحداث
            this.dropdown.querySelectorAll('.item-autocomplete-item').forEach(el => {
                el.addEventListener('click', () => this.select(parseInt(el.dataset.index)));
            });

            this.dropdown.style.display = 'block';
            this.selectedIndex = -1;
        }

        hide() {
            if (this.dropdown) {
                this.dropdown.style.display = 'none';
            }
        }

        handleKeyDown(e) {
            if (!this.dropdown || this.dropdown.style.display === 'none') return;

            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.selectedIndex = Math.min(this.selectedIndex + 1, this.results.length - 1);
                    this.highlight();
                    break;

                case 'ArrowUp':
                    e.preventDefault();
                    this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                    this.highlight();
                    break;

                case 'Enter':
                    e.preventDefault();
                    if (this.selectedIndex >= 0) {
                        this.select(this.selectedIndex);
                    }
                    break;

                case 'Escape':
                    e.preventDefault();
                    this.hide();
                    break;
            }
        }

        highlight() {
            const items = this.dropdown.querySelectorAll('.item-autocomplete-item');
            items.forEach((item, index) => {
                item.classList.toggle('selected', index === this.selectedIndex);
            });
        }

        select(index) {
            const item = this.results[index];
            if (!item) return;

            // ملء حقول السطر
            const row = this.input.closest('tr');
            this.fillRowData(row, item);

            this.hide();
            updateStatusBar(`تم اختيار: ${item.name}`, 'success');

            // الانتقال للحقل التالي
            const nextInput = row.querySelector('.col-quantity input, .col-quantity select');
            if (nextInput) nextInput.focus();
        }

        fillRowData(row, item) {
            // تعبئة ID المادة
            const itemSelect = row.querySelector('[name$="-item"]');
            if (itemSelect) {
                // إضافة option جديد إذا لم يكن موجود
                let option = itemSelect.querySelector(`option[value="${item.id}"]`);
                if (!option) {
                    option = new Option(item.name, item.id, true, true);
                    itemSelect.add(option);
                }
                itemSelect.value = item.id;
                $(itemSelect).trigger('change'); // تفعيل Select2
            }

            // تعبئة البيان
            const descInput = row.querySelector('[name$="-description"]');
            if (descInput && !descInput.value) {
                descInput.value = item.name;
            }

            // تعبئة السعر
            const priceInput = row.querySelector('[name$="-unit_price"]');
            if (priceInput) {
                priceInput.value = item.price || 0;
            }

            // تعبئة معدل الضريبة
            const taxInput = row.querySelector('[name$="-tax_rate"]');
            if (taxInput) {
                taxInput.value = item.tax_rate || 0;
            }

            // تطبيق تمييز الضريبة بالألوان
            applyTaxColorCoding(row, item.is_tax_exempt);

            // عرض آخر سعر للعميل (إذا كان موجود)
            if (item.last_price) {
                showLastPriceNotification(row, item);
            }
        }
    }

    // ========================================================================
    // 2. TAX COLOR CODING (تمييز الضريبة بالألوان)
    // ========================================================================

    function applyTaxColorCoding(row, isTaxExempt) {
        row.classList.remove('tax-exempt-row', 'taxable-row');

        if (isTaxExempt) {
            row.classList.add('tax-exempt-row');
        } else {
            row.classList.add('taxable-row');
        }
    }

    function updateAllRowColors() {
        document.querySelectorAll('.oracle-grid-row').forEach(row => {
            const taxInput = row.querySelector('[name$="-tax_rate"]');
            if (taxInput) {
                const taxRate = parseFloat(taxInput.value) || 0;
                applyTaxColorCoding(row, taxRate === 0);
            }
        });
    }

    // ========================================================================
    // 3. PAYMENT APPROVAL SYSTEM (نظام الموافقات)
    // ========================================================================

    function setupPaymentApproval() {
        const paymentMethodSelect = document.querySelector('[name="payment_method"]');
        if (!paymentMethodSelect) return;

        paymentMethodSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const paymentType = selectedOption.textContent.toLowerCase();

            // إذا كان الدفع "ذمم" أو "آجل"
            if (paymentType.includes('ذمم') || paymentType.includes('آجل') || paymentType.includes('credit')) {
                requestCreditApproval();
            } else {
                clearApprovalStatus();
            }
        });
    }

    async function requestCreditApproval() {
        const supplierId = document.querySelector('[name="supplier"]')?.value;
        if (!supplierId) {
            alert('يرجى اختيار المورد أولاً');
            return;
        }

        try {
            updateStatusBar('جاري طلب الموافقة على الدفع الآجل...', 'warning');

            const response = await fetch('/purchases/request-credit-approval/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    supplier_id: supplierId,
                    amount: calculateTotal()
                })
            });

            const data = await response.json();

            if (data.approved) {
                updateStatusBar('✓ تمت الموافقة على الدفع الآجل', 'success');
            } else if (data.pending) {
                updateStatusBar('⏳ بانتظار موافقة المسؤول المباشر', 'warning');
                showApprovalPendingIndicator();
            } else {
                updateStatusBar('✗ تم رفض الدفع الآجل: ' + data.reason, 'error');
                // إعادة تعيين طريقة الدفع إلى نقدي
                document.querySelector('[name="payment_method"]').selectedIndex = 0;
            }
        } catch (error) {
            console.error('Approval error:', error);
            updateStatusBar('خطأ في طلب الموافقة', 'error');
        }
    }

    function showApprovalPendingIndicator() {
        const statusBar = document.querySelector('.oracle-status-bar');
        if (!statusBar) return;

        const indicator = document.createElement('span');
        indicator.className = 'approval-pending';
        indicator.textContent = ' ⏳ بانتظار الموافقة';
        indicator.id = 'approval-indicator';
        statusBar.appendChild(indicator);
    }

    function clearApprovalStatus() {
        const indicator = document.getElementById('approval-indicator');
        if (indicator) indicator.remove();
    }

    // ========================================================================
    // 4. KEYBOARD SUPPORT (دعم الكيبورد)
    // ========================================================================

    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // F9 - حفظ
            if (e.key === 'F9') {
                e.preventDefault();
                document.querySelector('button[type="submit"]')?.click();
                updateStatusBar('جاري الحفظ...', 'info');
            }

            // F2 - إضافة سطر جديد
            if (e.key === 'F2') {
                e.preventDefault();
                addNewRow();
                updateStatusBar('تم إضافة سطر جديد', 'success');
            }

            // F3 - فتح البحث في السطر النشط
            if (e.key === 'F3') {
                e.preventDefault();
                const activeRow = document.activeElement.closest('.oracle-grid-row');
                if (activeRow) {
                    const itemInput = activeRow.querySelector('.col-item input, .col-item select');
                    if (itemInput) itemInput.focus();
                }
            }

            // F5 - تحديث
            if (e.key === 'F5') {
                e.preventDefault();
                location.reload();
            }

            // Ctrl+D - حذف السطر النشط
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                const activeRow = document.activeElement.closest('.oracle-grid-row');
                if (activeRow) {
                    deleteRow(activeRow);
                }
            }
        });

        // Enter في الحقول - الانتقال للحقل التالي
        document.querySelectorAll('.oracle-input, .oracle-select').forEach(input => {
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    focusNext(this);
                }
            });
        });
    }

    function focusNext(currentElement) {
        const focusableElements = Array.from(document.querySelectorAll(
            'input:not([readonly]):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])'
        ));

        const currentIndex = focusableElements.indexOf(currentElement);
        const nextElement = focusableElements[currentIndex + 1];

        if (nextElement) {
            nextElement.focus();
        }
    }

    function addNewRow() {
        const addButton = document.querySelector('.oracle-toolbar-btn[onclick*="addRow"]');
        if (addButton) addButton.click();
    }

    function deleteRow(row) {
        const deleteCheckbox = row.querySelector('[name$="-DELETE"]');
        if (deleteCheckbox) {
            deleteCheckbox.checked = true;
            row.style.opacity = '0.5';
            row.style.textDecoration = 'line-through';
            updateStatusBar('تم تحديد السطر للحذف', 'warning');
        }
    }

    // ========================================================================
    // 5. PRICE HISTORY (سجل الأسعار)
    // ========================================================================

    function showLastPriceNotification(row, item) {
        if (!item.last_price || !item.last_sale_date) return;

        const priceInput = row.querySelector('[name$="-unit_price"]');
        if (!priceInput) return;

        // عرض رسالة بآخر سعر
        const currentPrice = parseFloat(priceInput.value) || 0;
        const lastPrice = parseFloat(item.last_price);
        const priceDiff = ((currentPrice - lastPrice) / lastPrice * 100).toFixed(2);

        if (Math.abs(priceDiff) > 5) { // إذا كان الفرق أكثر من 5%
            const message = `تنبيه: آخر سعر كان ${lastPrice} (${item.last_sale_date}). الفرق: ${priceDiff}%`;
            updateStatusBar(message, 'warning');
        }

        // إضافة أيقونة لعرض سجل الأسعار
        addPriceHistoryIcon(priceInput, item.id);
    }

    function addPriceHistoryIcon(priceInput, itemId) {
        const cell = priceInput.closest('td');
        if (!cell || cell.querySelector('.price-history-icon')) return;

        const icon = document.createElement('span');
        icon.className = 'price-history-icon';
        icon.innerHTML = ' 📊';
        icon.style.cursor = 'pointer';
        icon.title = 'عرض سجل الأسعار';

        icon.addEventListener('click', () => showPriceHistoryModal(itemId));

        cell.appendChild(icon);
    }

    async function showPriceHistoryModal(itemId) {
        try {
            const supplierId = document.querySelector('[name="supplier"]')?.value;
            const response = await fetch(`/purchases/price-history/?item=${itemId}&supplier=${supplierId}`);
            const data = await response.json();

            // إنشاء overlay
            const overlay = document.createElement('div');
            overlay.className = 'price-history-overlay';

            // إنشاء modal
            const modal = document.createElement('div');
            modal.className = 'price-history-modal';
            modal.innerHTML = `
                <h3>سجل أسعار المادة</h3>
                <p><strong>المادة:</strong> ${data.item_name}</p>
                <p><strong>آخر سعر:</strong> ${data.last_price || 'لا يوجد'}</p>

                <table class="price-history-table">
                    <thead>
                        <tr>
                            <th>التاريخ</th>
                            <th>رقم الفاتورة</th>
                            <th>الكمية</th>
                            <th>السعر</th>
                            <th>الخصم%</th>
                            <th>الإجمالي</th>
                            <th>الفرع</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.history.map(record => `
                            <tr>
                                <td>${record.date}</td>
                                <td>${record.invoice_number}</td>
                                <td>${record.quantity}</td>
                                <td>${record.unit_price}</td>
                                <td>${record.discount_percentage}%</td>
                                <td>${record.total}</td>
                                <td>${record.branch}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div style="margin-top: 15px; text-align: center;">
                    <button class="oracle-toolbar-btn" onclick="this.closest('.price-history-modal').previousElementSibling.remove(); this.closest('.price-history-modal').remove();">
                        إغلاق
                    </button>
                </div>
            `;

            document.body.appendChild(overlay);
            document.body.appendChild(modal);

            overlay.addEventListener('click', () => {
                overlay.remove();
                modal.remove();
            });
        } catch (error) {
            console.error('Price history error:', error);
            updateStatusBar('خطأ في عرض سجل الأسعار', 'error');
        }
    }

    // ========================================================================
    // 6. COLUMN CONTROL (التحكم في الأعمدة)
    // ========================================================================

    function setupColumnControl() {
        const toolbar = document.querySelector('.oracle-toolbar');
        if (!toolbar) return;

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'oracle-toolbar-btn';
        button.innerHTML = '⚙️ الأعمدة';
        button.title = 'التحكم في عرض الأعمدة';

        button.addEventListener('click', showColumnControlMenu);

        toolbar.appendChild(button);
    }

    function showColumnControlMenu(e) {
        e.stopPropagation();

        // إزالة القائمة السابقة إن وجدت
        document.querySelector('.column-control-menu')?.remove();

        const menu = document.createElement('div');
        menu.className = 'column-control-menu';

        const columns = [
            { key: 'variant', label: 'المتغير' },
            { key: 'description', label: 'البيان' },
            { key: 'unit', label: 'الوحدة' },
            { key: 'discount-pct', label: 'خصم%' },
            { key: 'discount-amt', label: 'مبلغ الخصم' },
            { key: 'tax-rate', label: 'ضريبة%' },
            { key: 'tax-included', label: 'شامل' }
        ];

        menu.innerHTML = `
            <strong>عرض/إخفاء الأعمدة:</strong>
            <hr>
            ${columns.map(col => `
                <label class="column-control-item">
                    <input type="checkbox"
                           class="column-toggle"
                           data-column="${col.key}"
                           ${!isColumnHidden(col.key) ? 'checked' : ''}>
                    ${col.label}
                </label>
            `).join('')}
            <hr>
            <button class="oracle-toolbar-btn" onclick="this.closest('.column-control-menu').remove();">
                إغلاق
            </button>
        `;

        // وضع القائمة بجانب الزر
        const rect = e.target.getBoundingClientRect();
        menu.style.top = `${rect.bottom}px`;
        menu.style.left = `${rect.left}px`;

        document.body.appendChild(menu);

        // إضافة مستمعي الأحداث
        menu.querySelectorAll('.column-toggle').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleColumn(this.dataset.column, this.checked);
                saveColumnPreferences();
            });
        });

        // إغلاق عند النقر خارج القائمة
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target)) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 100);
    }

    function toggleColumn(columnKey, show) {
        const table = document.getElementById('items-table');
        if (!table) return;

        const headerCell = table.querySelector(`th.col-${columnKey}`);
        const columnIndex = headerCell ? Array.from(headerCell.parentNode.children).indexOf(headerCell) : -1;

        if (columnIndex === -1) return;

        // إخفاء/إظهار العمود
        if (show) {
            headerCell.style.display = '';
            table.querySelectorAll(`tbody tr`).forEach(row => {
                const cell = row.children[columnIndex];
                if (cell) cell.style.display = '';
            });
        } else {
            headerCell.style.display = 'none';
            table.querySelectorAll(`tbody tr`).forEach(row => {
                const cell = row.children[columnIndex];
                if (cell) cell.style.display = 'none';
            });
        }
    }

    function isColumnHidden(columnKey) {
        const preferences = JSON.parse(localStorage.getItem('invoice_column_preferences') || '{}');
        return preferences[columnKey] === false;
    }

    function saveColumnPreferences() {
        const preferences = {};
        document.querySelectorAll('.column-toggle').forEach(checkbox => {
            preferences[checkbox.dataset.column] = checkbox.checked;
        });
        localStorage.setItem('invoice_column_preferences', JSON.stringify(preferences));
    }

    function loadColumnPreferences() {
        const preferences = JSON.parse(localStorage.getItem('invoice_column_preferences') || '{}');
        Object.keys(preferences).forEach(column => {
            toggleColumn(column, preferences[column]);
        });
    }

    // ========================================================================
    // 7. ENHANCED STATUS BAR (شريط الحالة المحسن)
    // ========================================================================

    function enhanceStatusBar() {
        const statusBar = document.querySelector('.oracle-status-bar');
        if (!statusBar) return;

        // إضافة معلومات إضافية
        const info = document.createElement('div');
        info.style.cssText = 'display: flex; gap: 20px; align-items: center; flex-grow: 1;';
        info.innerHTML = `
            <span><strong>الحالة:</strong> <span id="status-state">مسودة</span></span>
            <span><strong>عدد السطور:</strong> <span id="status-rows">0</span></span>
            <span><strong>الإجمالي:</strong> <span id="status-total">0.000</span></span>
            <span class="keyboard-hint">F9: حفظ | F2: سطر جديد | F3: بحث | Ctrl+D: حذف</span>
        `;

        statusBar.insertBefore(info, statusBar.firstChild);

        // تحديث العداد
        updateStatusBarCounters();
    }

    function updateStatusBarCounters() {
        const rows = document.querySelectorAll('.oracle-grid-row:not([style*="display: none"])');
        document.getElementById('status-rows').textContent = rows.length;

        const total = calculateTotal();
        document.getElementById('status-total').textContent = total.toFixed(3);
    }

    // ========================================================================
    // HELPER FUNCTIONS
    // ========================================================================

    function calculateTotal() {
        let total = 0;
        document.querySelectorAll('[name$="-subtotal"]').forEach(input => {
            total += parseFloat(input.value) || 0;
        });
        return total;
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    function init() {
        // تطبيق CSS
        injectCSS();

        // إعداد البحث السريع لكل حقل مادة
        document.querySelectorAll('.col-item input[type="text"]').forEach(input => {
            new ItemAutoComplete(input);
        });

        // تطبيق تمييز الضريبة على السطور الموجودة
        updateAllRowColors();

        // إعداد نظام الموافقات
        setupPaymentApproval();

        // إعداد اختصارات الكيبورد
        setupKeyboardShortcuts();

        // إعداد التحكم في الأعمدة
        setupColumnControl();
        loadColumnPreferences();

        // تحسين شريط الحالة
        enhanceStatusBar();

        // رسالة ترحيب
        updateStatusBar('جاهز للعمل - F9 للحفظ | F2 سطر جديد', 'info');

        console.log('✓ Advanced Invoice Features Loaded');
    }

    // تشغيل عند تحميل الصفحة
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // تصدير الدوال للاستخدام الخارجي
    window.InvoiceAdvancedFeatures = {
        init,
        updateStatusBar,
        updateAllRowColors,
        showPriceHistoryModal,
        updateStatusBarCounters
    };

})();
