// static/js/main.js - ERP Main JavaScript
// نسخة مبسطة ومضمونة

console.log('🚀 Loading main.js...');

// ============================================
// 1. Sidebar Toggle - بسيط وفعال
// ============================================
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');

    console.log('Sidebar init:', {
        sidebar: !!sidebar,
        toggle: !!toggle,
        overlay: !!overlay
    });

    if (!sidebar || !toggle || !overlay) {
        console.error('❌ Sidebar elements not found!');
        return;
    }

    console.log('✅ Sidebar elements found');

    // Toggle function
    function toggleSidebar() {
        console.log('🔄 Toggle sidebar');
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
        document.body.classList.toggle('sidebar-open');
    }

    // Events
    toggle.addEventListener('click', toggleSidebar);
    overlay.addEventListener('click', toggleSidebar);

    // ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('show')) {
            toggleSidebar();
        }
    });

    // Close on link click (mobile)
    const links = sidebar.querySelectorAll('.nav-link:not(.collapsed)');
    links.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992) {
                toggleSidebar();
            }
        });
    });

    console.log('✅ Sidebar initialized');
}

// ============================================
// 2. Font Size Controller - مبسط
// ============================================
class FontSizeController {
    constructor() {
        this.body = document.getElementById('mainBody');
        if (!this.body) {
            console.error('❌ mainBody not found');
            return;
        }

        this.currentSize = 'normal';
        this.sizes = {
            'small': 'صغير',
            'normal': 'عادي',
            'large': 'كبير',
            'extra-large': 'كبير جداً'
        };

        this.init();
    }

    init() {
        // Load saved size
        const savedSize = localStorage.getItem('fontSize') || 'normal';
        this.setFontSize(savedSize, false);

        // Create controls
        this.createControls();

        // Attach buttons
        this.attachButtons();

        console.log('✅ Font controller initialized');
    }

    createControls() {
        const navbar = document.querySelector('.navbar-nav.ms-auto');
        if (!navbar) return;

        const fontControls = document.createElement('div');
        fontControls.className = 'nav-item font-controls me-3';
        fontControls.innerHTML = `
            <button class="font-control-btn font-decrease" title="تصغير الخط" aria-label="تصغير الخط">
                <i class="fas fa-minus"></i>
            </button>
            <div class="font-size-indicator" id="fontSizeIndicator">${this.sizes[this.currentSize]}</div>
            <button class="font-control-btn font-increase" title="تكبير الخط" aria-label="تكبير الخط">
                <i class="fas fa-plus"></i>
            </button>
            <button class="font-control-btn font-reset ms-2" title="إعادة تعيين" aria-label="إعادة تعيين">
                <i class="fas fa-undo"></i>
            </button>
        `;
        // حذف حجم الخط
        fontControls.innerHTML = ''

        const lastItem = navbar.lastElementChild;
        navbar.insertBefore(fontControls, lastItem);
    }

    attachButtons() {
        // Navbar buttons
        const decreaseBtn = document.querySelector('.font-decrease');
        const increaseBtn = document.querySelector('.font-increase');
        const resetBtn = document.querySelector('.font-reset');

        if (decreaseBtn) decreaseBtn.addEventListener('click', () => this.decreaseSize());
        if (increaseBtn) increaseBtn.addEventListener('click', () => this.increaseSize());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetSize());

        // Dropdown buttons
        const dropdownBtns = document.querySelectorAll('[data-font-size]');
        dropdownBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.setFontSize(btn.getAttribute('data-font-size'));
            });
        });
    }

    setFontSize(size, notify = true) {
        // Remove all size classes
        Object.keys(this.sizes).forEach(s => {
            this.body.classList.remove(`font-${s}`);
        });

        // Add new class
        this.body.classList.add(`font-${size}`);
        this.currentSize = size;

        // Save
        localStorage.setItem('fontSize', size);

        // Update indicator
        const indicator = document.getElementById('fontSizeIndicator');
        if (indicator) {
            indicator.textContent = this.sizes[size];
        }

        if (notify) {
            this.showNotification(`حجم الخط: ${this.sizes[size]}`);
        }
    }

    increaseSize() {
        const sizes = Object.keys(this.sizes);
        const currentIndex = sizes.indexOf(this.currentSize);
        if (currentIndex < sizes.length - 1) {
            this.setFontSize(sizes[currentIndex + 1]);
        }
    }

    decreaseSize() {
        const sizes = Object.keys(this.sizes);
        const currentIndex = sizes.indexOf(this.currentSize);
        if (currentIndex > 0) {
            this.setFontSize(sizes[currentIndex - 1]);
        }
    }

    resetSize() {
        this.setFontSize('normal');
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            z-index: 9999;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        notification.innerHTML = `<i class="fas fa-font me-2"></i>${message}`;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 1500);
    }
}

// ============================================
// 3. Coming Soon Handler
// ============================================
function initComingSoon() {
    document.querySelectorAll('[data-feature]').forEach(element => {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            const feature = this.getAttribute('data-feature');

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'info',
                    title: 'قريباً',
                    text: `وحدة ${feature} قيد التطوير وستكون متاحة قريباً`,
                    confirmButtonText: 'حسناً',
                    confirmButtonColor: '#0d6efd'
                });
            } else {
                alert(`وحدة ${feature} قيد التطوير وستكون متاحة قريباً`);
            }
        });
    });
    console.log('✅ Coming soon handler initialized');
}

// ============================================
// 4. Company Switcher
// ============================================
function initCompanySwitcher() {
    window.switchCompany = function(companyId) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'جاري التبديل...',
                text: 'يتم تبديل الشركة الآن',
                allowOutsideClick: false,
                didOpen: () => Swal.showLoading()
            });

            fetch(`/core/switch-company/${companyId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'تم التبديل بنجاح',
                        showConfirmButton: false,
                        timer: 1000
                    }).then(() => window.location.reload());
                } else {
                    throw new Error(data.message || 'حدث خطأ');
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: 'خطأ',
                    text: error.message || 'حدث خطأ أثناء التبديل'
                });
            });
        }
    };

    // Add event listeners to company items
    document.querySelectorAll('[data-company-id]').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const companyId = this.getAttribute('data-company-id');
            window.switchCompany(companyId);
        });
    });

    console.log('✅ Company switcher initialized');
}

// ============================================
// 5. Form Enhancements
// ============================================
function initFormEnhancements() {
    // Prevent double submit
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>جاري الحفظ...';

                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });
    console.log('✅ Form enhancements initialized');
}

// ============================================
// 6. Delete Confirmation
// ============================================
function initDeleteConfirmation() {
    document.querySelectorAll('[data-confirm-delete]').forEach(element => {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            const message = this.getAttribute('data-confirm-delete');
            const url = this.getAttribute('href');

            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'هل أنت متأكد؟',
                    text: message || 'لن تتمكن من التراجع عن هذا!',
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#3085d6',
                    confirmButtonText: 'نعم، احذف',
                    cancelButtonText: 'إلغاء'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = url;
                    }
                });
            } else {
                if (confirm(message || 'هل أنت متأكد؟')) {
                    window.location.href = url;
                }
            }
        });
    });
    console.log('✅ Delete confirmation initialized');
}

// ============================================
// 7. Utility Functions
// ============================================
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

// ============================================
// 8. Initialize Everything
// ============================================
let fontController;

document.addEventListener('DOMContentLoaded', function() {
    console.log('📦 DOM Content Loaded');

    // Initialize all modules
    initSidebar();
    fontController = new FontSizeController();
    initComingSoon();
    initCompanySwitcher();
    initFormEnhancements();
    initDeleteConfirmation();
    initArabicNumbers(); // تحويل الأرقام إلى العربية

    // Make fontController global
    window.fontController = fontController;

    console.log('✅ ERP System initialized successfully');
});

// ============================================
// 9. Global Utilities
// ============================================
window.ERPUtils = {
    formatNumber: function(num) {
        return num.toLocaleString('ar-EG');
    },
    formatCurrency: function(amount, currency = 'JOD') {
        return new Intl.NumberFormat('ar-JO', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('ar-JO', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    // تحويل الأرقام الإنجليزية إلى عربية
    toArabicNumbers: function(str) {
        const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
        return String(str).replace(/[0-9]/g, function(digit) {
            return arabicNumbers[digit];
        });
    },
    // تحويل جميع الأرقام في عنصر HTML
    convertNumbersInElement: function(element) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        const nodesToUpdate = [];
        let node;

        while (node = walker.nextNode()) {
            if (node.nodeValue && /\d/.test(node.nodeValue)) {
                nodesToUpdate.push(node);
            }
        }

        nodesToUpdate.forEach(node => {
            node.nodeValue = this.toArabicNumbers(node.nodeValue);
        });
    }
};

// ============================================
// 10. Auto Convert Numbers to Arabic
// ============================================
function initArabicNumbers() {
    // تحويل الأرقام عند تحميل الصفحة
    const contentArea = document.querySelector('.main-content') || document.body;

    // تحويل الأرقام الموجودة
    if (contentArea) {
        window.ERPUtils.convertNumbersInElement(contentArea);
    }

    // مراقبة التغييرات الديناميكية
    if (contentArea && typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        window.ERPUtils.convertNumbersInElement(node);
                    } else if (node.nodeType === Node.TEXT_NODE && /\d/.test(node.nodeValue)) {
                        node.nodeValue = window.ERPUtils.toArabicNumbers(node.nodeValue);
                    }
                });
            });
        });

        observer.observe(contentArea, {
            childList: true,
            subtree: true,
            characterData: false
        });
    }

    console.log('✅ Arabic numbers converter initialized');
}

console.log('✅ main.js loaded successfully');