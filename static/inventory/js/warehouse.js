/**
 * Inventory Module - Warehouse Management
 * Warehouse CRUD operations with dynamic categories
 */

// API base path - 正确的路径应该是 /inventory/api/
const API_BASE = '/inventory/api/';

// Warehouse categories cache
let warehouseCategories = [];

// Load warehouse categories from API
function loadWarehouseCategories() {
    fetch(API_BASE + 'warehouse-categories/', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
    })
    .then(data => {
        warehouseCategories = data;
    })
    .catch(err => {
        console.error('Failed to load categories:', err);
    });
}

// Helper function to select category
function promptCategory(defaultCategoryId) {
    if (warehouseCategories.length === 0) {
        loadWarehouseCategories();
    }

    let options = '\n请选择仓库类别:\n';
    options += '0. 不选择类别\n';
    warehouseCategories.forEach((cat, index) => {
        const marker = cat.id === defaultCategoryId ? ' [当前]' : '';
        options += `${index + 1}. ${cat.name}${marker}\n`;
    });

    const choice = prompt(options + '\n请输入序号:');
    if (choice === null) return defaultCategoryId;

    const index = parseInt(choice);
    if (index === 0) return null;
    if (index > 0 && index <= warehouseCategories.length) {
        return warehouseCategories[index - 1].id;
    }
    return defaultCategoryId;
}

// Add Warehouse
function showAddWarehouseModal() {
    const name = prompt('请输入仓库名称:');
    if (!name) return;
    const code = prompt('请输入仓库编码:');
    if (!code) return;
    const categoryId = promptCategory(null);
    const address = prompt('请输入仓库地址 (可选):') || '';

    fetch(API_BASE + 'warehouses/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            name: name,
            code: code,
            category: categoryId,
            address: address
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert('添加失败: ' + data.error);
        } else {
            alert('仓库添加成功!');
            location.reload();
        }
    })
    .catch(err => {
        alert('添加失败: ' + err);
    });
}

// Edit Warehouse
function editWarehouse(id, name, code, address, categoryId) {
    const newName = prompt('请输入仓库名称:', name);
    if (!newName) return;
    const newCode = prompt('请输入仓库编码:', code);
    if (!newCode) return;
    const newCategoryId = promptCategory(categoryId);
    const newAddress = prompt('请输入仓库地址:', address || '') || '';

    fetch(API_BASE + 'warehouses/' + id + '/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            name: newName,
            code: newCode,
            category: newCategoryId,
            address: newAddress
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert('更新失败: ' + data.error);
        } else {
            alert('仓库更新成功!');
            location.reload();
        }
    })
    .catch(err => {
        alert('更新失败: ' + err);
    });
}

// Toggle Warehouse Active Status
function toggleWarehouse(id, activate) {
    const url = API_BASE + 'warehouses/' + id + '/';
    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            is_active: activate
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(activate ? '仓库已启用!' : '仓库已停用!');
        location.reload();
    })
    .catch(err => {
        alert('操作失败: ' + err);
    });
}

// ===== Category Management =====

function showCategoryManagerModal() {
    document.getElementById('categoryManagerModal').style.display = 'block';
    loadCategoriesTable();
}

function closeCategoryManagerModal() {
    document.getElementById('categoryManagerModal').style.display = 'none';
}

function loadCategoriesTable() {
    fetch(API_BASE + 'warehouse-categories/', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => {
        if (!res.ok) throw new Error('Failed to load categories');
        return res.json();
    })
    .then(data => {
        // 处理分页响应格式
        const categories = data.results || data;
        warehouseCategories = categories;
        const tbody = document.getElementById('categoryTableBody');
        if (!categories || categories.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">暂无类别</td></tr>';
            return;
        }
        tbody.innerHTML = categories.map(cat => `
            <tr>
                <td>${cat.name}</td>
                <td>${cat.code}</td>
                <td><span class="badge" style="background-color: ${cat.color}; color: white;">${cat.color}</span></td>
                <td><i class="bi ${cat.icon}"></i></td>
                <td>${cat.sort_order}</td>
                <td>${cat.is_active ? '<span class="badge bg-success">启用</span>' : '<span class="badge bg-secondary">禁用</span>'}</td>
                <td>${cat.warehouse_count || 0}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editCategory(${cat.id})">编辑</button>
                    <button class="btn btn-sm ${cat.is_active ? 'btn-outline-warning' : 'btn-outline-success'}"
                            onclick="toggleCategory(${cat.id}, ${!cat.is_active})">
                        ${cat.is_active ? '停用' : '启用'}
                    </button>
                </td>
            </tr>
        `).join('');
    })
    .catch(err => {
        document.getElementById('categoryTableBody').innerHTML = '<tr><td colspan="8" class="text-center text-danger">加载失败: ' + err.message + '</td></tr>';
    });
}

function showAddCategoryForm() {
    const name = prompt('请输入类别名称:');
    if (!name) return;
    const code = prompt('请输入类别代码 (英文,唯一):');
    if (!code) return;

    // 验证code格式
    if (!/^[a-z_][a-z0-9_]*$/.test(code)) {
        alert('类别代码只能使用小写字母，数字和下划线，且以字母或下划线开头');
        return;
    }

    const color = prompt('请输入颜色 (十六进制如: #2563eb):', '#6c757d') || '#6c757d';
    const icon = prompt('请输入图标 (Bootstrap Icons类名,不需要bi-前缀):', 'building') || 'building';
    const sortOrder = prompt('请输入排序序号 (数字越小越靠前):', '0') || '0';

    fetch(API_BASE + 'warehouse-categories/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            name: name,
            code: code,
            color: color,
            icon: 'bi-' + icon.replace(/^bi-/, ''),
            is_active: true,
            sort_order: parseInt(sortOrder) || 0
        })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => Promise.reject(err));
        }
        return res.json();
    })
    .then(data => {
        alert('类别添加成功!');
        loadCategoriesTable();
        loadWarehouseCategories();
    })
    .catch(err => {
        const errorMsg = err.detail || err.code || JSON.stringify(err);
        alert('添加失败: ' + errorMsg);
    });
}

function editCategory(id) {
    const cat = warehouseCategories.find(c => c.id === id);
    if (!cat) {
        alert('类别不存在');
        return;
    }

    const name = prompt('请输入类别名称:', cat.name);
    if (!name) return;

    const color = prompt('请输入颜色 (十六进制如: #2563eb):', cat.color) || cat.color;
    const icon = prompt('请输入图标 (不需要bi-前缀):', cat.icon.replace(/^bi-/, '')) || cat.icon.replace(/^bi-/, '');
    const sortOrder = prompt('请输入排序序号:', cat.sort_order.toString()) || cat.sort_order.toString();

    fetch(API_BASE + 'warehouse-categories/' + id + '/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            name: name,
            code: cat.code,
            color: color,
            icon: 'bi-' + icon.replace(/^bi-/, ''),
            sort_order: parseInt(sortOrder) || 0
        })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => Promise.reject(err));
        }
        return res.json();
    })
    .then(data => {
        alert('类别更新成功!');
        loadCategoriesTable();
        loadWarehouseCategories();
    })
    .catch(err => {
        const errorMsg = err.detail || err.code || JSON.stringify(err);
        alert('更新失败: ' + errorMsg);
    });
}

function toggleCategory(id, activate) {
    const url = API_BASE + 'warehouse-categories/' + id + '/';
    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            is_active: activate
        })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => Promise.reject(err));
        }
        return res.json();
    })
    .then(data => {
        alert(activate ? '类别已启用!' : '类别已停用!');
        loadCategoriesTable();
        loadWarehouseCategories();
    })
    .catch(err => {
        const errorMsg = err.detail || err.code || JSON.stringify(err);
        alert('操作失败: ' + errorMsg);
    });
}

// ===== Tab Configuration =====

function showTabConfigModal() {
    document.getElementById('tabConfigModal').style.display = 'block';
    loadTabConfigs();
}

function closeTabConfigModal() {
    document.getElementById('tabConfigModal').style.display = 'none';
}

function loadTabConfigs() {
    fetch(API_BASE + 'tab-configs/my_config/', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => {
        if (!res.ok) throw new Error('Failed to load tab configs');
        return res.json();
    })
    .then(data => {
        const container = document.getElementById('tabConfigList');
        const tabNames = {
            'overview': '库存概览',
            'inbound': '入库',
            'outbound': '出库',
            'check': '盘点',
            'report': '库存报表',
            'warehouse': '仓库管理'
        };

        container.innerHTML = data.map(config => `
            <div class="form-check mb-2">
                <input class="form-check-input" type="checkbox" id="tab_${config.tab_key}"
                       data-tab="${config.tab_key}" ${config.is_visible ? 'checked' : ''}>
                <label class="form-check-label" for="tab_${config.tab_key}">
                    ${config.tab_name || tabNames[config.tab_key]}
                </label>
            </div>
        `).join('');
    })
    .catch(err => {
        document.getElementById('tabConfigList').innerHTML = '<p class="text-danger">加载失败: ' + err.message + '</p>';
    });
}

function saveTabConfig() {
    const checkboxes = document.querySelectorAll('#tabConfigList input[type="checkbox"]');
    const configs = [];
    checkboxes.forEach((cb, index) => {
        configs.push({
            tab_key: cb.dataset.tab,
            is_visible: cb.checked,
            sort_order: index
        });
    });

    fetch(API_BASE + 'tab-configs/my_config/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ configs: configs })
    })
    .then(res => res.json())
    .then(data => {
        alert('配置已保存!');
        location.reload();
    })
    .catch(err => {
        alert('保存失败: ' + err);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadWarehouseCategories();
});

// Event delegation
document.addEventListener('click', function(e) {
    // Warehouse toggle active/inactive
    if (e.target.classList.contains('toggle-warehouse-btn')) {
        var btn = e.target;
        var warehouseId = btn.getAttribute('data-id');
        var activate = btn.getAttribute('data-active') === 'true';
        toggleWarehouse(warehouseId, activate);
    }

    // Warehouse edit
    if (e.target.classList.contains('edit-warehouse-btn')) {
        var btn = e.target;
        editWarehouse(
            btn.getAttribute('data-id'),
            btn.getAttribute('data-name'),
            btn.getAttribute('data-code'),
            btn.getAttribute('data-address'),
            btn.getAttribute('data-category-id') ? parseInt(btn.getAttribute('data-category-id')) : null
        );
    }
});

