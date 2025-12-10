# Claude Code Prompt: Oracle-Style LOV & Keyboard-First Invoice System

## 🎯 المطلوب
تطبيق نظام فاتورة مشتريات احترافي مع:
1. **Keyboard-First Autocomplete** للحقول الرئيسية (المورد، المخزن، طريقة الدفع، أمر الشراء)
2. **Oracle-Style LOV (List of Values)** لاختيار الأصناف في الجدول
3. **Fuzzy Search** - البحث بأحرف متفرقة غير متتالية

---

## 📋 الجزء الأول: Keyboard-First Autocomplete للحقول

### 1.1 البنية HTML
```html
<div class="autocomplete-container">
    <div class="autocomplete-wrapper">
        <input type="text" 
               class="form-control autocomplete-field" 
               id="supplier" 
               data-type="supplier" 
               placeholder="ابدأ الكتابة..."
               autocomplete="off">
        <button type="button" class="clear-btn" data-for="supplier">
            <span class="material-icons">close</span>
        </button>
    </div>
    <div class="autocomplete-dropdown" id="supplierDropdown"></div>
</div>
```

### 1.2 CSS المطلوب
```css
.autocomplete-container { position: relative; }
.autocomplete-wrapper { position: relative; display: flex; align-items: center; }
.autocomplete-wrapper .form-control { padding-left: 35px; flex: 1; }

/* زر المسح */
.clear-btn {
    position: absolute;
    left: 8px;
    width: 24px;
    height: 24px;
    border: none;
    background: transparent;
    color: #999;
    cursor: pointer;
    display: none;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    z-index: 10;
}
.clear-btn:hover { background-color: #ffebee; color: #c62828; }
.clear-btn.show { display: flex; }

/* القائمة المنسدلة */
.autocomplete-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 2px solid #1976d2;
    border-top: none;
    border-radius: 0 0 6px 6px;
    max-height: 250px;
    overflow-y: auto;
    z-index: 1000;
    display: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    margin-top: -2px;
}
.autocomplete-dropdown.show { display: block; }

.autocomplete-item {
    padding: 10px 12px;
    cursor: pointer;
    border-bottom: 1px solid #eee;
}
.autocomplete-item:hover,
.autocomplete-item.selected { background-color: #e3f2fd; }
.autocomplete-item strong { color: #1976d2; display: block; }
.autocomplete-item small { color: #666; font-size: 12px; }
```

### 1.3 JavaScript Class الكامل
```javascript
class KeyboardAutocomplete {
    constructor(input) {
        this.input = input;
        this.type = input.dataset.type;
        this.dropdown = document.getElementById(input.id + 'Dropdown');
        this.clearBtn = document.querySelector(`[data-for="${input.id}"]`);
        this.selectedIndex = -1;
        this.items = [];
        this.isFirstKeyAfterFocus = false;
        this.init();
    }

    init() {
        this.input.addEventListener('input', () => { 
            this.handleInput(); 
            this.updateClearBtn(); 
        });
        this.input.addEventListener('focus', () => this.handleFocus());
        this.input.addEventListener('blur', () => setTimeout(() => this.hideDropdown(), 150));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clear());
        }
        this.updateClearBtn();
    }

    updateClearBtn() {
        if (this.clearBtn) {
            this.clearBtn.classList.toggle('show', this.input.value.trim() !== '');
        }
    }

    clear() {
        this.input.value = '';
        this.input.dataset.selectedId = '';
        this.hideDropdown();
        this.updateClearBtn();
        this.input.focus();
    }

    handleInput() { 
        this.filter(this.input.value.toLowerCase()); 
    }
    
    handleFocus() { 
        this.isFirstKeyAfterFocus = true; 
        this.filter(this.input.value.toLowerCase()); 
    }

    handleKeydown(e) {
        // التحقق من الحرف القابل للطباعة
        const isPrintable = e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey;
        
        // ⭐ أول حرف بعد التركيز - يمسح ويبدأ من جديد
        if (this.isFirstKeyAfterFocus && isPrintable) {
            this.input.value = '';
            this.isFirstKeyAfterFocus = false;
            return; // يترك الحرف يُكتب
        }
        
        if (isPrintable) this.isFirstKeyAfterFocus = false;
        
        // إذا القائمة مغلقة
        if (!this.dropdown.classList.contains('show')) {
            if (e.key === 'Enter') { 
                e.preventDefault(); 
                this.navigateNext(); 
                return; 
            }
            if (!['Tab','Enter','ArrowLeft','ArrowRight','Escape'].includes(e.key)) {
                setTimeout(() => this.filter(this.input.value.toLowerCase()), 0);
            }
            return;
        }
        
        // إذا القائمة مفتوحة
        switch(e.key) {
            case 'ArrowDown': 
                e.preventDefault(); 
                this.selectNext(); 
                break;
            case 'ArrowUp': 
                e.preventDefault(); 
                this.selectPrev(); 
                break;
            case 'Enter': 
                e.preventDefault(); 
                e.stopPropagation();
                if (this.selectedIndex >= 0 && this.items.length > 0) {
                    this.select(this.selectedIndex);
                } else {
                    this.hideDropdown();
                    this.navigateNext();
                }
                break;
            case 'Escape': 
                e.preventDefault(); 
                this.hideDropdown(); 
                break;
            case 'ArrowLeft': 
            case 'ArrowRight':
                this.hideDropdown();
                this.navigateNext(e.key === 'ArrowRight' ? 'prev' : 'next');
                e.preventDefault();
                break;
        }
    }

    filter(query) {
        const data = dataSources[this.type];
        if (!data) return;
        
        this.items = data.filter(item => 
            item.name.toLowerCase().includes(query) || 
            (item.code && item.code.toLowerCase().includes(query))
        );
        this.render();
    }

    render() {
        if (this.items.length === 0) {
            this.dropdown.innerHTML = '<div class="autocomplete-item no-results">لا توجد نتائج</div>';
            this.dropdown.classList.add('show');
            return;
        }
        
        this.dropdown.innerHTML = this.items.map((item, i) => {
            let content = `<strong>${item.name}</strong>`;
            if (item.code) {
                content += `<small>${item.code}`;
                if (item.balance) content += ` | رصيد: ${item.balance.toLocaleString()} د.أ`;
                content += `</small>`;
            }
            return `<div class="autocomplete-item ${i === 0 ? 'selected' : ''}" data-index="${i}">${content}</div>`;
        }).join('');
        
        this.selectedIndex = 0;
        this.dropdown.classList.add('show');
        
        // إضافة أحداث النقر
        this.dropdown.querySelectorAll('.autocomplete-item').forEach((el, idx) => {
            if (!el.classList.contains('no-results')) {
                el.addEventListener('click', () => this.select(idx));
            }
        });
    }

    selectNext() { 
        if (this.selectedIndex < this.items.length - 1) { 
            this.selectedIndex++; 
            this.updateSelection(); 
        } 
    }
    
    selectPrev() { 
        if (this.selectedIndex > 0) { 
            this.selectedIndex--; 
            this.updateSelection(); 
        } 
    }
    
    updateSelection() {
        this.dropdown.querySelectorAll('.autocomplete-item').forEach((item, idx) => {
            item.classList.toggle('selected', idx === this.selectedIndex);
        });
        const sel = this.dropdown.querySelector('.selected');
        if (sel) sel.scrollIntoView({ block: 'nearest' });
    }

    select(index) {
        const item = this.items[index];
        if (item) {
            this.input.value = item.name;
            this.input.dataset.selectedId = item.id;
            this.hideDropdown();
            this.updateClearBtn();
            this.navigateNext();
        }
    }

    hideDropdown() { 
        this.dropdown.classList.remove('show'); 
    }

    navigateNext(dir = 'next') {
        const fields = Array.from(document.querySelectorAll(
            'input:not([readonly]):not([type="button"]), select, textarea'
        ));
        const idx = fields.indexOf(this.input);
        if (dir === 'next' && idx < fields.length - 1) fields[idx + 1].focus();
        else if (dir === 'prev' && idx > 0) fields[idx - 1].focus();
    }
}
```

### 1.4 اختصارات لوحة المفاتيح للـ Autocomplete
| المفتاح | الوظيفة |
|---------|---------|
| `↑` `↓` | التنقل بين النتائج |
| `Enter` | اختيار العنصر المحدد والانتقال للحقل التالي |
| `Escape` | إغلاق القائمة |
| `←` `→` | الانتقال بين الحقول |
| أي حرف بعد Focus | يمسح القيمة القديمة ويبدأ من جديد |
| زر X | مسح الحقل |

---

## 📋 الجزء الثاني: Oracle-Style LOV للأصناف

### 2.1 البنية HTML للـ Modal
```html
<div class="lov-overlay" id="lovOverlay">
    <div class="lov-window" onclick="event.stopPropagation()">
        <!-- Header -->
        <div class="lov-header">
            <div class="lov-title">
                <span class="material-icons">search</span>
                اختيار صنف
            </div>
            <button class="lov-close" onclick="LOV.close()">
                <span class="material-icons">close</span>
            </button>
        </div>
        
        <!-- Search Box -->
        <div class="lov-search-box">
            <div class="lov-search-wrapper">
                <span class="material-icons">search</span>
                <input type="text" 
                       class="lov-search-input" 
                       id="lovInput" 
                       placeholder="ابحث بالاسم أو الكود... (أحرف متفرقة مدعومة)" 
                       autocomplete="off">
            </div>
            <div class="lov-hints">
                <span><kbd>↑</kbd> <kbd>↓</kbd> تنقل</span>
                <span><kbd>Enter</kbd> اختيار</span>
                <span><kbd>Esc</kbd> إغلاق</span>
            </div>
        </div>
        
        <!-- Table -->
        <div class="lov-content">
            <div class="lov-table-wrap">
                <table class="lov-table">
                    <thead>
                        <tr>
                            <th>الكود</th>
                            <th>اسم الصنف</th>
                            <th>الوحدة</th>
                            <th>السعر</th>
                        </tr>
                    </thead>
                    <tbody id="lovBody"></tbody>
                </table>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="lov-footer">
            <div class="lov-count">
                <strong id="lovCount">0</strong> نتيجة
            </div>
            <div class="lov-buttons">
                <button class="lov-btn lov-btn-cancel" onclick="LOV.close()">إلغاء</button>
                <button class="lov-btn lov-btn-select" onclick="LOV.select()">اختيار</button>
            </div>
        </div>
    </div>
</div>
```

### 2.2 CSS للـ LOV
```css
.lov-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.6);
    z-index: 99999;
    align-items: center;
    justify-content: center;
}
.lov-overlay.active { display: flex; }

.lov-window {
    background: white;
    border-radius: 10px;
    width: 95%;
    max-width: 850px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    animation: lovSlideIn 0.2s ease-out;
}

@keyframes lovSlideIn {
    from { opacity: 0; transform: scale(0.95) translateY(-10px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
}

.lov-header {
    background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
    color: white;
    padding: 14px 20px;
    border-radius: 10px 10px 0 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.lov-search-box {
    padding: 14px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #eee;
}

.lov-search-wrapper { position: relative; }
.lov-search-wrapper .material-icons {
    position: absolute;
    right: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: #888;
}

.lov-search-input {
    width: 100%;
    padding: 12px 50px 12px 14px;
    border: 2px solid #1976d2;
    border-radius: 8px;
    font-size: 15px;
}
.lov-search-input:focus {
    outline: none;
    box-shadow: 0 0 0 4px rgba(25,118,210,0.2);
}

.lov-table { width: 100%; border-collapse: collapse; }
.lov-table th {
    padding: 11px 14px;
    text-align: right;
    background: #f1f3f4;
    position: sticky;
    top: 0;
}
.lov-table td { padding: 11px 14px; border-bottom: 1px solid #eee; }
.lov-table tbody tr { cursor: pointer; }
.lov-table tbody tr:hover { background: #f5f7fa; }
.lov-table tbody tr.active {
    background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
}
.lov-table tbody tr.active td { font-weight: 600; color: #1565c0; }
.lov-table tbody tr.active td:first-child::before {
    content: '▸ ';
    color: #1976d2;
}

/* تمييز نتائج البحث */
.lov-match {
    background: #fff59d;
    padding: 1px 3px;
    border-radius: 2px;
}
```

### 2.3 JavaScript Module للـ LOV مع Fuzzy Search
```javascript
const LOV = {
    isOpen: false,
    currentRow: -1,
    filtered: [],
    activeIndex: 0,
    query: '',

    // ⭐ فتح LOV
    open(row, initialQuery = '') {
        this.currentRow = row;
        this.activeIndex = 0;
        this.query = initialQuery || '';
        
        // إيقاف Handsontable
        hot.unlisten();
        
        // إظهار النافذة
        document.getElementById('lovOverlay').classList.add('active');
        this.isOpen = true;
        
        // تعيين قيمة البحث
        const input = document.getElementById('lovInput');
        input.value = this.query;
        
        // تصفية النتائج
        this.filter(this.query);
        
        // التركيز وتحديد النص
        setTimeout(() => {
            input.focus();
            if (this.query) input.select();
        }, 100);
    },

    // ⭐ إغلاق LOV
    close() {
        document.getElementById('lovOverlay').classList.remove('active');
        this.isOpen = false;
        
        // إعادة تفعيل Handsontable
        hot.listen();
        
        // العودة للجدول
        setTimeout(() => hot.selectCell(this.currentRow, 0), 50);
    },

    // ⭐ Fuzzy Search - البحث بأحرف متفرقة
    filter(query) {
        this.query = query;
        const q = query.trim();
        
        if (!q) {
            // بدون بحث - عرض الكل
            this.filtered = ITEMS.map(item => ({
                ...item,
                matchPositions: { name: [], code: [] }
            }));
        } else {
            // تقسيم البحث لأجزاء (بالمسافات)
            const parts = q.split(/\s+/).filter(p => p.length > 0);
            this.filtered = [];
            
            ITEMS.forEach(item => {
                const nameMatch = this.fuzzyMatch(item.name, parts);
                const codeMatch = this.fuzzyMatch(item.code, parts);
                
                if (nameMatch.matched || codeMatch.matched) {
                    this.filtered.push({
                        ...item,
                        matchPositions: {
                            name: nameMatch.positions,
                            code: codeMatch.positions
                        },
                        score: Math.min(
                            nameMatch.matched ? nameMatch.score : 9999,
                            codeMatch.matched ? codeMatch.score : 9999
                        )
                    });
                }
            });
            
            // ترتيب حسب جودة التطابق
            this.filtered.sort((a, b) => a.score - b.score);
        }
        
        this.activeIndex = 0;
        this.render();
    },

    // ⭐ خوارزمية Fuzzy Match
    fuzzyMatch(text, parts) {
        const lowerText = text.toLowerCase();
        const positions = [];
        let lastIndex = 0;
        let totalGap = 0;
        
        for (const part of parts) {
            const index = lowerText.indexOf(part.toLowerCase(), lastIndex);
            
            if (index === -1) {
                return { matched: false, positions: [], score: 9999 };
            }
            
            // تسجيل مواقع الأحرف المطابقة
            for (let i = 0; i < part.length; i++) {
                positions.push(index + i);
            }
            
            totalGap += (index - lastIndex);
            lastIndex = index + part.length;
        }
        
        return { matched: true, positions, score: totalGap };
    },

    // ⭐ تمييز الأحرف المطابقة
    highlight(text, positions) {
        if (!positions || positions.length === 0) return text;
        
        let result = '';
        for (let i = 0; i < text.length; i++) {
            if (positions.includes(i)) {
                result += `<span class="lov-match">${text[i]}</span>`;
            } else {
                result += text[i];
            }
        }
        return result;
    },

    // ⭐ عرض النتائج
    render() {
        const tbody = document.getElementById('lovBody');
        
        if (this.filtered.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="4">
                    <div class="lov-empty">
                        <span class="material-icons">search_off</span>
                        <div>لا توجد نتائج${this.query ? ` لـ "${this.query}"` : ''}</div>
                    </div>
                </td></tr>`;
            document.getElementById('lovCount').textContent = '0';
            return;
        }
        
        tbody.innerHTML = this.filtered.map((item, i) => `
            <tr class="${i === this.activeIndex ? 'active' : ''}" 
                data-idx="${i}"
                onmouseenter="LOV.setActive(${i})"
                onclick="LOV.select()">
                <td>${this.highlight(item.code, item.matchPositions?.code || [])}</td>
                <td><strong>${this.highlight(item.name, item.matchPositions?.name || [])}</strong></td>
                <td>${item.unit}</td>
                <td>${item.price.toFixed(3)}</td>
            </tr>
        `).join('');
        
        document.getElementById('lovCount').textContent = this.filtered.length;
        this.scrollToActive();
    },

    setActive(i) {
        if (i >= 0 && i < this.filtered.length) {
            this.activeIndex = i;
            this.render();
        }
    },

    moveUp() {
        if (this.activeIndex > 0) {
            this.activeIndex--;
            this.render();
        }
    },

    moveDown() {
        if (this.activeIndex < this.filtered.length - 1) {
            this.activeIndex++;
            this.render();
        }
    },

    scrollToActive() {
        const row = document.querySelector('.lov-table tbody tr.active');
        if (row) row.scrollIntoView({ block: 'nearest' });
    },

    // ⭐ اختيار الصنف
    select() {
        if (this.filtered.length === 0 || this.activeIndex < 0) return;
        
        const item = this.filtered[this.activeIndex];
        const row = this.currentRow;
        
        // إغلاق أولاً
        this.close();
        
        // تحديث الجدول
        hot.setDataAtCell([
            [row, 0, item.name],
            [row, 1, item.code],
            [row, 3, item.unit],
            [row, 4, item.price]
        ], 'lov');
        
        // الانتقال لحقل الكمية
        setTimeout(() => hot.selectCell(row, 2), 100);
    }
};
```

### 2.4 Event Handlers للـ LOV Input
```javascript
const lovInput = document.getElementById('lovInput');

lovInput.addEventListener('input', (e) => {
    LOV.filter(e.target.value);
});

lovInput.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        e.stopPropagation();
        LOV.moveDown();
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        e.stopPropagation();
        LOV.moveUp();
    } else if (e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
        LOV.select();
    } else if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        LOV.close();
    } else if (e.key === 'PageDown') {
        e.preventDefault();
        LOV.activeIndex = Math.min(LOV.activeIndex + 5, LOV.filtered.length - 1);
        LOV.render();
    } else if (e.key === 'PageUp') {
        e.preventDefault();
        LOV.activeIndex = Math.max(LOV.activeIndex - 5, 0);
        LOV.render();
    }
});

// إغلاق عند النقر خارج النافذة
document.getElementById('lovOverlay').addEventListener('click', (e) => {
    if (e.target.id === 'lovOverlay') LOV.close();
});

// Escape عام
document.addEventListener('keydown', (e) => {
    if (LOV.isOpen && e.key === 'Escape') {
        e.preventDefault();
        LOV.close();
    }
});
```

### 2.5 اختصارات لوحة المفاتيح للـ LOV
| المفتاح | الوظيفة |
|---------|---------|
| `Enter` أو `F4` | فتح LOV من الجدول |
| `↑` `↓` | التنقل بين الأصناف |
| `Enter` | اختيار الصنف المحدد |
| `Escape` | إغلاق LOV |
| `PageUp` | قفز 5 أصناف للأعلى |
| `PageDown` | قفز 5 أصناف للأسفل |
| كتابة أي نص | بحث فوري (يدعم أحرف متفرقة) |

---

## 📋 الجزء الثالث: Handsontable Integration

### 3.1 إعدادات Handsontable
```javascript
const hot = new Handsontable(document.getElementById('itemsGrid'), {
    data: gridData,
    colHeaders: ['اسم الصنف', 'الكود', 'الكمية', 'الوحدة', 'السعر', 'الإجمالي'],
    columns: [
        { type: 'text', width: 200 },           // اسم الصنف - قابل للتعديل
        { type: 'text', readOnly: true, width: 100 },  // الكود - للقراءة فقط
        { type: 'numeric', width: 80 },         // الكمية
        { type: 'text', readOnly: true, width: 70 },   // الوحدة - للقراءة فقط
        { type: 'numeric', numericFormat: { pattern: '0,0.000' }, width: 90 }, // السعر
        { type: 'numeric', numericFormat: { pattern: '0,0.00' }, readOnly: true, width: 100 } // الإجمالي
    ],
    stretchH: 'all',
    height: 300,
    rowHeaders: true,
    minSpareRows: 1,
    
    // ⭐ مهم جداً: التحكم بالمفاتيح قبل Handsontable
    beforeKeyDown: function(e) {
        // إذا LOV مفتوح - إيقاف كل شيء
        if (LOV.isOpen) {
            e.stopImmediatePropagation();
            return false;
        }
        
        const sel = this.getSelected();
        if (!sel) return;
        
        const row = sel[0][0];
        const col = sel[0][1];
        
        // فقط في عمود اسم الصنف (العمود 0)
        if (col === 0 && (e.key === 'Enter' || e.key === 'F4')) {
            e.preventDefault();
            e.stopImmediatePropagation();
            LOV.open(row, this.getDataAtCell(row, col) || '');
            return false;
        }
    },
    
    // ⭐ حساب الإجمالي تلقائياً
    afterChange: function(changes, source) {
        if (!changes || source === 'loadData' || source === 'lov' || source === 'calc') return;
        
        changes.forEach(([row, col]) => {
            // إذا تغيرت الكمية أو السعر
            if (col === 2 || col === 4) {
                const qty = parseFloat(this.getDataAtCell(row, 2)) || 0;
                const price = parseFloat(this.getDataAtCell(row, 4)) || 0;
                this.setDataAtCell(row, 5, qty * price, 'calc');
            }
        });
        
        updateTotals();
    },
    
    licenseKey: 'non-commercial-and-evaluation'
});
```

---

## 📋 الجزء الرابع: Fuzzy Search Examples

### أمثلة البحث بأحرف متفرقة:
| البحث | النتيجة | التفسير |
|-------|---------|---------|
| `م م` | **م**ضخة **م**ياه | حرفين م متتاليين في الترتيب |
| `م غ` | **م**ضخة **غ**اطسة | م ثم غ |
| `م 5` | **م**ضخة مياه **5**HP | م ثم 5 |
| `ك 16` | **ك**ابل كهرباء **16** | ك ثم 16 |
| `ص 3` | **ص**مام كروي **3** بوصة | ص ثم 3 |
| `محرك 7` | **محرك** كهربائي **7**.5HP | كلمة كاملة ثم رقم |

---

## 📋 الجزء الخامس: Data Sources Structure

```javascript
// مصادر البيانات للـ Autocomplete
const dataSources = {
    supplier: [
        { id: 1, name: 'مؤسسة النور', code: 'SUP-001', balance: 15000 },
        // ...
    ],
    warehouse: [
        { id: 1, name: 'المخزن الرئيسي - عمان' },
        // ...
    ],
    payment: [
        { id: 1, name: 'نقدي' },
        { id: 2, name: 'آجل' },
        // ...
    ],
    po: [
        { id: 0, name: 'بدون أمر شراء' },
        { id: 1, name: 'PO-2024-0045' },
        // ...
    ]
};

// الأصناف للـ LOV
const ITEMS = [
    { id: 1, name: 'مضخة مياه 2HP', code: 'PUMP-001', unit: 'قطعة', price: 250.000 },
    { id: 2, name: 'مضخة غاطسة 4 بوصة', code: 'PUMP-004', unit: 'قطعة', price: 580.000 },
    { id: 3, name: 'محرك كهربائي 5HP', code: 'MOTOR-001', unit: 'قطعة', price: 450.000 },
    // ...
];
```

---

## 📋 الجزء السادس: Initialization

```javascript
document.addEventListener('DOMContentLoaded', () => {
    // تفعيل Autocomplete لكل الحقول
    document.querySelectorAll('.autocomplete-field').forEach(input => {
        new KeyboardAutocomplete(input);
    });
    
    // قيم افتراضية
    document.getElementById('warehouse').value = 'المخزن الرئيسي - عمان';
    document.getElementById('supplier').value = 'مؤسسة النور';
    document.getElementById('paymentMethod').value = 'آجل';
    
    // إظهار أزرار المسح للقيم الموجودة
    document.querySelectorAll('.clear-btn').forEach(btn => {
        const input = document.getElementById(btn.dataset.for);
        if (input && input.value.trim()) btn.classList.add('show');
    });
    
    // أحداث تحديث الإجماليات
    document.getElementById('shippingCost').addEventListener('change', updateTotals);
    document.getElementById('additionalDiscount').addEventListener('change', updateTotals);
    
    updateTotals();
});
```

---

## ⚠️ نقاط مهمة جداً

1. **`hot.unlisten()` و `hot.listen()`**: ضروري لإيقاف Handsontable عن التقاط الأحداث أثناء فتح LOV

2. **`e.stopImmediatePropagation()`**: لمنع الأحداث من الوصول لـ Handsontable

3. **`isFirstKeyAfterFocus`**: لمسح الحقل عند أول حرف بعد التركيز

4. **Fuzzy Search**: يجب أن تكون الأجزاء بالترتيب لكن ليس متتالية

5. **z-index: 99999**: للـ LOV overlay ليظهر فوق كل شيء

6. **source === 'lov'**: لتمييز التغييرات من LOV عن التغييرات اليدوية
