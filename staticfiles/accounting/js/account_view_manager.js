/* ═══════════════════════════════════════════════════════════
   Account View Manager - Fixed Version
   ═══════════════════════════════════════════════════════════ */

class AccountViewManager {
    constructor() {
        this.currentMode = localStorage.getItem('accountViewMode') || 'list';
        this.treeData = null;
        this.selectedAccountId = null;
        this.searchTimeout = null;
        this.isLoading = false;

        this.urls = {
            hierarchy: null,
            detailMini: null
        };

        // ⏳ لا نهيئ مباشرة، ننتظر DOM
    }

    init() {
        console.log('🚀 Initializing Account View Manager...');

        // Event Listeners للأزرار
        const viewModeButtons = document.querySelectorAll('input[name="viewMode"]');
        console.log('📻 Found view mode buttons:', viewModeButtons.length);

        viewModeButtons.forEach(radio => {
            radio.addEventListener('change', (e) => {
                console.log('🔘 View mode changed to:', e.target.value);
                this.switchView(e.target.value);
            });
        });

        // تحديد الزر النشط
        const activeButton = document.getElementById(`${this.currentMode}View`);
        if (activeButton) {
            activeButton.checked = true;
            console.log('✅ Active button set to:', this.currentMode);
        }

        // Tree Search
        const treeSearch = document.getElementById('treeSearch');
        if (treeSearch) {
            treeSearch.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.searchInTree(e.target.value);
                }, 300);
            });
        }

        // ✅ إظهار العرض الحالي فقط في البداية
        this.switchView(this.currentMode, true);

        console.log('✅ Account View Manager initialized');
    }

    switchView(mode, isInitial = false) {
    console.log(`🔄 Switching to ${mode} view (initial: ${isInitial})...`);

    // إخفاء جميع العروض
    document.querySelectorAll('.view-container').forEach(container => {
        container.style.display = 'none';
    });

    // إظهار العرض المختار
    const container = document.getElementById(`${mode}ViewContainer`);
    if (container) {
        container.style.display = 'block';
        console.log(`✅ Container ${mode}ViewContainer displayed`);
    } else {
        console.error(`❌ Container ${mode}ViewContainer not found`);
        return;
    }

    // ✅ معالجة كل نوع
    if (mode === 'list') {
        // DataTable
        if (window.accountsDataTable) {
            console.log('📊 Adjusting DataTable columns...');
            setTimeout(() => {
                try {
                    window.accountsDataTable.columns.adjust().draw();
                    console.log('✅ DataTable adjusted');
                } catch (e) {
                    console.error('❌ DataTable adjust error:', e);
                }
            }, 100);
        }
    } else if (mode === 'tree') {
        // ✅ التحقق من وجود DOM content
        const treeContainer = document.getElementById('accountsTree');
        const treeLoading = document.getElementById('treeLoading');
        const hasContent = treeContainer && treeContainer.children.length > 0;

        console.log(`🌳 Tree state - hasData: ${!!this.treeData}, hasContent: ${hasContent}, isLoading: ${this.isLoading}`);

        if (!this.treeData && !this.isLoading) {
            // لا توجد بيانات، نحمّل
            console.log('📥 Loading tree data for first time...');
            this.loadTreeView();
        } else if (this.treeData && !hasContent) {
            // البيانات موجودة لكن DOM فارغ - نعيد render
            console.log('🔄 Data exists but DOM empty, re-rendering tree...');
            if (treeLoading) treeLoading.style.display = 'none';
            this.renderTree('accountsTree', this.treeData);
            if (treeContainer) treeContainer.style.display = 'block';
        } else if (this.treeData && hasContent) {
            // كل شيء جاهز، فقط أظهر
            console.log('✅ Tree data and DOM ready, showing...');
            if (treeLoading) treeLoading.style.display = 'none';
            if (treeContainer) treeContainer.style.display = 'block';
        } else if (this.isLoading) {
            console.log('⏳ Tree is currently loading...');
        }
    } else if (mode === 'dual') {
        // ✅ نفس المنطق للـ Dual View
        const dualContainer = document.getElementById('dualTreeNav');
        const dualLoading = document.getElementById('dualTreeLoading');
        const hasContent = dualContainer && dualContainer.children.length > 0;

        console.log(`🔀 Dual state - hasData: ${!!this.treeData}, hasContent: ${hasContent}, isLoading: ${this.isLoading}`);

        if (!this.treeData && !this.isLoading) {
            // لا توجد بيانات، نحمّل
            console.log('📥 Loading dual view data for first time...');
            this.loadDualView();
        } else if (this.treeData && !hasContent) {
            // البيانات موجودة لكن DOM فارغ - نعيد render
            console.log('🔄 Data exists but DOM empty, re-rendering dual...');
            if (dualLoading) dualLoading.style.display = 'none';
            this.renderTree('dualTreeNav', this.treeData);
            if (dualContainer) dualContainer.style.display = 'block';
        } else if (this.treeData && hasContent) {
            // كل شيء جاهز، فقط أظهر
            console.log('✅ Dual data and DOM ready, showing...');
            if (dualLoading) dualLoading.style.display = 'none';
            if (dualContainer) dualContainer.style.display = 'block';
        } else if (this.isLoading) {
            console.log('⏳ Dual view is currently loading...');
        }
    }

    // حفظ التفضيل
    this.currentMode = mode;
    localStorage.setItem('accountViewMode', mode);

    console.log(`✓ Switched to ${mode} view`);
}

    async loadTreeView() {
        if (this.isLoading) {
            console.log('⚠️ Already loading tree...');
            return;
        }

        console.log('📥 Loading tree view...');
        this.isLoading = true;

        const loadingEl = document.getElementById('treeLoading');
        const treeEl = document.getElementById('accountsTree');

        if (loadingEl) loadingEl.style.display = 'block';
        if (treeEl) treeEl.style.display = 'none';

        try {
            const url = this.urls.hierarchy || '/accounting/ajax/accounts/hierarchy/';
            console.log('🌐 Fetching from:', url);

            const response = await fetch(url);
            const data = await response.json();

            console.log('📦 Received data:', data);

            if (data.success) {
                this.treeData = data.tree;
                console.log('🌳 Tree data stored, rendering...');
                this.renderTree('accountsTree', this.treeData);

                if (loadingEl) loadingEl.style.display = 'none';
                if (treeEl) treeEl.style.display = 'block';

                console.log('✅ Tree loaded and displayed successfully');
            } else {
                throw new Error(data.error || 'فشل تحميل الشجرة');
            }
        } catch (error) {
            console.error('❌ Error loading tree:', error);
            this.showError('فشل تحميل الهيكل الهرمي: ' + error.message);

            if (loadingEl) {
                loadingEl.innerHTML = `
                    <div class="alert alert-danger m-3">
                        <i class="fas fa-exclamation-triangle"></i>
                        خطأ في تحميل الشجرة: ${error.message}
                        <button class="btn btn-sm btn-outline-danger ms-3" onclick="viewManager.retryLoad('tree')">
                            <i class="fas fa-redo"></i> إعادة المحاولة
                        </button>
                    </div>
                `;
            }
        } finally {
            this.isLoading = false;
        }
    }

    async loadDualView() {
        if (this.isLoading) {
            console.log('⚠️ Already loading dual view...');
            return;
        }

        console.log('📥 Loading dual view...');
        this.isLoading = true;

        const loadingEl = document.getElementById('dualTreeLoading');
        const treeEl = document.getElementById('dualTreeNav');

        if (loadingEl) loadingEl.style.display = 'block';
        if (treeEl) treeEl.style.display = 'none';

        try {
            const url = this.urls.hierarchy || '/accounting/ajax/accounts/hierarchy/';
            console.log('🌐 Fetching from:', url);

            const response = await fetch(url);
            const data = await response.json();

            console.log('📦 Received data:', data);

            if (data.success) {
                this.treeData = data.tree;
                console.log('🌳 Tree data stored, rendering dual...');
                this.renderTree('dualTreeNav', this.treeData);

                if (loadingEl) loadingEl.style.display = 'none';
                if (treeEl) treeEl.style.display = 'block';

                console.log('✅ Dual view loaded and displayed');
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('❌ Error loading dual view:', error);
            this.showError('فشل تحميل العرض المزدوج: ' + error.message);

            if (loadingEl) {
                loadingEl.innerHTML = `
                    <div class="alert alert-danger m-3">
                        <i class="fas fa-exclamation-triangle"></i>
                        خطأ: ${error.message}
                        <button class="btn btn-sm btn-outline-danger ms-3" onclick="viewManager.retryLoad('dual')">
                            <i class="fas fa-redo"></i> إعادة المحاولة
                        </button>
                    </div>
                `;
            }
        } finally {
            this.isLoading = false;
        }
    }

    renderTree(containerId, nodes, level = 0) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`❌ Container ${containerId} not found`);
            return;
        }

        if (level === 0) {
            container.innerHTML = '';
            console.log(`🧹 Cleared container: ${containerId}`);
        }

        nodes.forEach(node => {
            const nodeElement = this.createTreeNode(node, level, containerId);
            container.appendChild(nodeElement);

            if (node.children && node.children.length > 0) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'tree-children';
                childrenContainer.id = `children-${node.id}-${containerId}`;

                this.renderTreeRecursive(childrenContainer, node.children, level + 1, containerId);
                container.appendChild(childrenContainer);
            }
        });

        console.log(`✅ Rendered ${nodes.length} nodes in ${containerId}`);
    }

    renderTreeRecursive(container, nodes, level, containerId) {
        nodes.forEach(node => {
            const nodeElement = this.createTreeNode(node, level, containerId);
            container.appendChild(nodeElement);

            if (node.children && node.children.length > 0) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'tree-children';
                childrenContainer.id = `children-${node.id}-${containerId}`;

                this.renderTreeRecursive(childrenContainer, node.children, level + 1, containerId);
                container.appendChild(childrenContainer);
            }
        });
    }

    createTreeNode(node, level, containerId) {
        const div = document.createElement('div');

        let classes = `tree-node tree-level-${level}`;
        if (node.has_children) {
            classes += ' has-children';
        } else {
            classes += ' leaf';
        }
        if (node.is_suspended) {
            classes += ' suspended';
        }
        if (node.is_cash_account) {
            classes += ' cash-account';
        } else if (node.is_bank_account) {
            classes += ' bank-account';
        }

        div.className = classes;
        div.dataset.accountId = node.id;
        div.dataset.accountCode = node.code;
        div.dataset.accountName = node.name;

        let html = '';

        // ✅ Toggle Icon مع ID فريد
        if (node.has_children) {
            html += `<span class="tree-toggle expanded" data-node-id="${node.id}" data-container-id="${containerId}"></span>`;
        } else {
            html += `<span class="tree-toggle empty"></span>`;
        }

        html += `
            <span class="tree-code">${node.code}</span>
            <span class="tree-name">${node.name}</span>
        `;

        if (node.has_children && node.children_count > 0) {
            html += `<span class="badge badge-children account-badge">${node.children_count}</span>`;
        }

        if (node.is_suspended) {
            html += `<span class="badge bg-danger account-badge">موقوف</span>`;
        } else if (!node.accept_entries) {
            html += `<span class="badge bg-warning text-dark account-badge">أب</span>`;
        }

        html += `<div class="tree-actions ms-auto">`;

        html += `
            <button class="tree-action-btn btn-view" onclick="viewManager.viewAccount(${node.id}); event.stopPropagation();" title="عرض">
                <i class="fas fa-eye"></i>
            </button>
        `;

        html += `
            <button class="tree-action-btn btn-edit" onclick="window.location.href='${node.edit_url}'; event.stopPropagation();" title="تعديل">
                <i class="fas fa-edit"></i>
            </button>
        `;

        if (level < 3) {
            html += `
                <button class="tree-action-btn btn-add" onclick="viewManager.addChildAccount(${node.id}); event.stopPropagation();" title="إضافة حساب فرعي">
                    <i class="fas fa-plus"></i>
                </button>
            `;
        }

        if (!node.has_children && node.delete_url) {
            html += `
                <button class="tree-action-btn btn-delete" onclick="viewManager.deleteAccount(${node.id}); event.stopPropagation();" title="حذف">
                    <i class="fas fa-trash"></i>
                </button>
            `;
        }

        html += `</div>`;

        div.innerHTML = html;

        // ✅ Events
        const toggle = div.querySelector('.tree-toggle');
        if (toggle && !toggle.classList.contains('empty')) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const nodeId = toggle.dataset.nodeId;
                const containerId = toggle.dataset.containerId;
                this.toggleNode(nodeId, containerId);
            });
        }

        div.addEventListener('click', (e) => {
            e.stopPropagation();
            this.selectNode(node.id);
        });

        div.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showContextMenu(e, node);
        });

        return div;
    }

    // ✅ إصلاح دالة Toggle
    toggleNode(nodeId, containerId) {
        console.log(`🔄 Toggling node ${nodeId} in ${containerId}`);

        const childrenId = `children-${nodeId}-${containerId}`;
        const childrenContainer = document.getElementById(childrenId);
        const toggleIcon = document.querySelector(`[data-node-id="${nodeId}"][data-container-id="${containerId}"]`);

        console.log('📦 Children container:', childrenContainer);
        console.log('🔘 Toggle icon:', toggleIcon);

        if (childrenContainer && toggleIcon) {
            const isCollapsed = childrenContainer.classList.contains('collapsed');

            if (isCollapsed) {
                // Expand
                console.log('📖 Expanding...');
                childrenContainer.classList.remove('collapsed');
                childrenContainer.style.maxHeight = childrenContainer.scrollHeight + 'px';
                toggleIcon.classList.remove('collapsed');
                toggleIcon.classList.add('expanded');

                // إزالة max-height بعد الانتهاء من الـ transition
                setTimeout(() => {
                    if (!childrenContainer.classList.contains('collapsed')) {
                        childrenContainer.style.maxHeight = 'none';
                    }
                }, 300);
            } else {
                // Collapse
                console.log('📕 Collapsing...');
                childrenContainer.style.maxHeight = childrenContainer.scrollHeight + 'px';

                // Force reflow
                childrenContainer.offsetHeight;

                childrenContainer.classList.add('collapsed');
                childrenContainer.style.maxHeight = '0';
                toggleIcon.classList.remove('expanded');
                toggleIcon.classList.add('collapsed');
            }
        } else {
            console.error('❌ Children container or toggle not found!');
            console.error('Looking for ID:', childrenId);
        }
    }

    selectNode(accountId) {
        document.querySelectorAll('.tree-node').forEach(node => {
            node.classList.remove('selected');
        });

        const node = document.querySelector(`[data-account-id="${accountId}"]`);
        if (node) {
            node.classList.add('selected');
            this.selectedAccountId = accountId;
            node.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        if (this.currentMode === 'dual') {
            this.loadAccountDetails(accountId);
        }
    }

    async loadAccountDetails(accountId) {
        const detailsContainer = document.getElementById('accountDetails');
        if (!detailsContainer) return;

        detailsContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">جاري التحميل...</span>
                </div>
                <p class="text-muted mt-3">جاري تحميل التفاصيل...</p>
            </div>
        `;

        try {
            const url = `/accounting/ajax/accounts/${accountId}/mini/`;
            const response = await fetch(url);

            if (response.ok) {
                const html = await response.text();
                detailsContainer.innerHTML = html;
            } else {
                throw new Error('فشل تحميل التفاصيل');
            }
        } catch (error) {
            console.error('❌ Error loading details:', error);
            detailsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    خطأ في تحميل التفاصيل: ${error.message}
                </div>
            `;
        }
    }

    viewAccount(accountId) {
        const node = this.findNodeById(accountId);
        if (node && node.detail_url) {
            window.location.href = node.detail_url;
        }
    }

    addChildAccount(parentId) {
        window.location.href = `/accounting/accounts/create/?parent_id=${parentId}`;
    }

    deleteAccount(accountId) {
        const node = this.findNodeById(accountId);

        Swal.fire({
            title: 'هل أنت متأكد؟',
            text: `سيتم حذف الحساب: ${node.code} - ${node.name}`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'نعم، احذف',
            cancelButtonText: 'إلغاء'
        }).then((result) => {
            if (result.isConfirmed) {
                this.performDelete(accountId);
            }
        });
    }

    async performDelete(accountId) {
        try {
            const response = await fetch(`/accounting/accounts/${accountId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: 'تم الحذف',
                    text: 'تم حذف الحساب بنجاح',
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    this.retryLoad(this.currentMode);
                });
            } else {
                throw new Error('فشل الحذف');
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'خطأ',
                text: 'فشل حذف الحساب: ' + error.message
            });
        }
    }

    showContextMenu(event, node) {
        const existingMenu = document.getElementById('treeContextMenu');
        if (existingMenu) existingMenu.remove();

        const menu = document.createElement('div');
        menu.id = 'treeContextMenu';
        menu.className = 'tree-context-menu';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';

        let menuHtml = `
            <div class="context-menu-item" onclick="viewManager.viewAccount(${node.id})">
                <i class="fas fa-eye"></i> عرض التفاصيل
            </div>
            <div class="context-menu-item" onclick="window.location.href='${node.edit_url}'">
                <i class="fas fa-edit"></i> تعديل
            </div>
        `;

        if (node.level < 3) {
            menuHtml += `
                <div class="context-menu-item" onclick="viewManager.addChildAccount(${node.id})">
                    <i class="fas fa-plus"></i> إضافة حساب فرعي
                </div>
            `;
        }

        menuHtml += `<div class="context-menu-divider"></div>`;

        if (!node.has_children && node.delete_url) {
            menuHtml += `
                <div class="context-menu-item text-danger" onclick="viewManager.deleteAccount(${node.id})">
                    <i class="fas fa-trash"></i> حذف
                </div>
            `;
        }

        menu.innerHTML = menuHtml;
        document.body.appendChild(menu);

        setTimeout(() => {
            document.addEventListener('click', function closeMenu() {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            });
        }, 100);
    }

    searchInTree(query) {
        const nodes = document.querySelectorAll('.tree-node');
        const lowerQuery = query.toLowerCase().trim();

        if (!lowerQuery) {
            nodes.forEach(node => {
                node.classList.remove('search-match', 'search-dimmed');
                node.style.display = 'flex';
            });
            return;
        }

        let hasMatches = false;

        nodes.forEach(node => {
            const code = node.dataset.accountCode || '';
            const name = node.dataset.accountName || '';
            const text = (code + ' ' + name).toLowerCase();

            if (text.includes(lowerQuery)) {
                node.classList.add('search-match');
                node.classList.remove('search-dimmed');
                node.style.display = 'flex';
                hasMatches = true;
                this.showParents(node);
            } else {
                node.classList.remove('search-match');
                node.classList.add('search-dimmed');
            }
        });

        if (!hasMatches) {
            this.showInfo('لا توجد نتائج للبحث');
        }
    }

    showParents(node) {
        let current = node.parentElement;

        while (current && !current.id.includes('accountsTree') && !current.id.includes('dualTreeNav')) {
            if (current.classList.contains('tree-children')) {
                current.classList.remove('collapsed');
                current.style.maxHeight = 'none';

                const parentId = current.id.match(/children-(\d+)/)[1];
                const toggles = document.querySelectorAll(`[data-node-id="${parentId}"]`);
                toggles.forEach(toggle => {
                    toggle.classList.remove('collapsed');
                    toggle.classList.add('expanded');
                });
            }

            if (current.classList.contains('tree-node')) {
                current.style.display = 'flex';
                current.classList.remove('search-dimmed');
            }

            current = current.parentElement;
        }
    }

    findNodeById(id, nodes = null) {
        if (!nodes) nodes = this.treeData;
        if (!nodes) return null;

        for (let node of nodes) {
            if (node.id === id) return node;
            if (node.children && node.children.length > 0) {
                const found = this.findNodeById(id, node.children);
                if (found) return found;
            }
        }
        return null;
    }

    getCsrfToken() {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    retryLoad(mode) {
        this.treeData = null;
        this.isLoading = false;

        if (mode === 'tree') {
            const loading = document.getElementById('treeLoading');
            if (loading) {
                loading.innerHTML = `
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                    <p class="text-muted mt-3">جاري تحميل الهيكل الهرمي...</p>
                `;
            }
            this.loadTreeView();
        } else if (mode === 'dual') {
            this.loadDualView();
        }
    }

    formatNumber(value) {
        return new Intl.NumberFormat('ar-SA', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

    showError(message) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'error',
                title: 'خطأ',
                text: message,
                confirmButtonText: 'حسناً'
            });
        } else {
            alert('خطأ: ' + message);
        }
    }

    showInfo(message) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'info',
                title: 'معلومة',
                text: message,
                timer: 2000,
                showConfirmButton: false
            });
        }
    }

    setUrls(urls) {
        this.urls = { ...this.urls, ...urls };
        console.log('🔗 URLs set:', this.urls);
    }
}

// Global Functions

function expandAll() {
    document.querySelectorAll('.tree-children').forEach(container => {
        container.classList.remove('collapsed');
        container.style.maxHeight = 'none';
    });

    document.querySelectorAll('.tree-toggle:not(.empty)').forEach(toggle => {
        toggle.classList.remove('collapsed');
        toggle.classList.add('expanded');
    });
}

function collapseAll() {
    document.querySelectorAll('.tree-children').forEach(container => {
        container.classList.add('collapsed');
        container.style.maxHeight = '0';
    });

    document.querySelectorAll('.tree-toggle:not(.empty)').forEach(toggle => {
        toggle.classList.remove('expanded');
        toggle.classList.add('collapsed');
    });
}

function resetTree() {
    if (window.viewManager) {
        window.viewManager.retryLoad(window.viewManager.currentMode);
    }
}

function clearTreeSearch() {
    const searchInput = document.getElementById('treeSearch');
    if (searchInput) {
        searchInput.value = '';

        document.querySelectorAll('.tree-node').forEach(node => {
            node.classList.remove('search-match', 'search-dimmed');
            node.style.display = 'flex';
        });
    }
}

// ✅ Auto-Initialize بعد تحميل DOM كاملاً
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initViewManager);
} else {
    initViewManager();
}

function initViewManager() {
    console.log('🎬 Initializing View Manager after DOM ready');
    window.viewManager = new AccountViewManager();

    // إعطاء وقت للصفحة لتحميل كل شيء
    setTimeout(() => {
        if (typeof ACCOUNT_URLS !== 'undefined') {
            window.viewManager.setUrls(ACCOUNT_URLS);
        }

        window.viewManager.init();
    }, 100);
}

// Auto-Initialize
document.addEventListener('DOMContentLoaded', function() {
    window.viewManager = new AccountViewManager();

    if (typeof ACCOUNT_URLS !== 'undefined') {
        window.viewManager.setUrls(ACCOUNT_URLS);
    }

    console.log('✅ Account View Manager ready');
});