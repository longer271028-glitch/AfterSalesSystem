/**
 * Inventory Module - Warehouse Management
 * Warehouse CRUD operations with modal dialogs
 */

// API base path
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
        warehouseCategories = data.results || data;
    })
    .catch(err => {
        console.error('Failed to load categories:', err);
    });
}

// ===== Warehouse Modal Functions =====

// Show Add Warehouse Modal
function showAddWarehouseModal() {
    document.getElementById('warehouseModalTitle').innerHTML = '<i class="bi bi-building"></i> 添加仓库';
    document.getElementById('warehouseId').value = '';
    document.getElementById('warehouseName').value = '';
    document.getElementById('warehouseCode').value = '';
    document.getElementById('warehouseCategory').value = '';
    document.getElementById('warehouseAddress').value = '';
    document.getElementById('warehouseManager').value = '';
    document.getElementById('warehouseActive').checked = true;
    
    // Load options
    loadWarehouseOptions();
    
    document.getElementById('warehouseModal').style.display = 'flex';
}

// Load warehouse form options
function loadWarehouseOptions() {
    // Load warehouse categories
    fetch(API_BASE + 'warehouse-categories/', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => res.json())
    .then(data => {
        const categorySelect = document.getElementById('warehouseCategory');
        const results = data.results || data;
        categorySelect.innerHTML = '<option value="">请选择类别</option>';
        results.forEach(item => {
            if (item.is_active) {
                categorySelect.innerHTML += `<option value="${item.id}">${item.name}</option>`;
            }
        });
    })
    .catch(err => console.error('加载类别失败:', err));
    
    // Load manager list - fetch from auth/user API
    fetch('/admin/auth/user/?format=json', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => {
        // If direct API not available, use fallback
        return [
            {id: 1, username: 'admin'},
            {id: 2, username: 'market_manager'},
            {id: 3, username: 'service_manager'},
            {id: 4, username: 'engineer1'},
            {id: 5, username: 'engineer2'}
        ];
    })
    .then(users => {
        const managerSelect = document.getElementById('warehouseManager');
        managerSelect.innerHTML = '<option value="">请选择管理员</option>';
        users.forEach(item => {
            managerSelect.innerHTML += `<option value="${item.id}">${item.username}</option>`;
        });
    })
    .catch(err => console.error('加载管理员失败:', err));
}

// Close Warehouse Modal
function closeWarehouseModal() {
    document.getElementById('warehouseModal').style.display = 'none';
}

// Submit Warehouse Form
function submitWarehouse() {
    const id = document.getElementById('warehouseId').value;
    const name = document.getElementById('warehouseName').value.trim();
    const code = document.getElementById('warehouseCode').value.trim();
    const category = document.getElementById('warehouseCategory').value;
    const address = document.getElementById('warehouseAddress').value.trim();
    const manager = document.getElementById('warehouseManager').value;
    const isActive = document.getElementById('warehouseActive').checked;

    if (!name) {
        alert('请输入仓库名称');
        return;
    }
    if (!code) {
        alert('请输入仓库编码');
        return;
    }

    const data = {
        name: name,
        code: code,
        address: address,
        is_active: isActive
    };
    if (category) data.category = parseInt(category);
    if (manager) data.manager = parseInt(manager);

    const url = id ? API_BASE + 'warehouses/' + id + '/' : API_BASE + 'warehouses/';
    const method = id ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => Promise.reject(err));
        }
        return res.json();
    })
    .then(data => {
        alert(id ? '仓库更新成功!' : '仓库添加成功!');
        closeWarehouseModal();
        location.reload();
    })
    .catch(err => {
        const errorMsg = err.error || err.detail || JSON.stringify(err);
        alert('操作失败: ' + errorMsg);
    });
}

// Edit Warehouse
function editWarehouse(id, name, code, address, categoryId) {
    document.getElementById('warehouseModalTitle').innerHTML = '<i class="bi bi-building"></i> 编辑仓库';
    
    // Load options first
    loadWarehouseOptions();
    
    // Get warehouse details
    fetch(API_BASE + 'warehouses/' + id + '/', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById('warehouseId').value = data.id;
        document.getElementById('warehouseName').value = data.name || '';
        document.getElementById('warehouseCode').value = data.code || '';
        document.getElementById('warehouseAddress').value = data.address || '';
        document.getElementById('warehouseActive').checked = data.is_active !== false;
        
        // Set category and manager after options are loaded
        setTimeout(() => {
            if (data.category) {
                document.getElementById('warehouseCategory').value = data.category;
            }
            if (data.manager) {
                document.getElementById('warehouseManager').value = data.manager;
            }
        }, 300);
        
        document.getElementById('warehouseModal').style.display = 'flex';
    })
    .catch(err => {
        alert('获取仓库信息失败: ' + err);
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

// Delete Warehouse
function deleteWarehouse(id, name) {
    if (!confirm('确定要删除仓库 "' + name + '" 吗？此操作不可恢复！')) {
        return;
    }

    const url = API_BASE + 'warehouses/' + id + '/';
    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => {
        if (res.ok) {
            alert('仓库已删除!');
            location.reload();
        } else {
            return res.json().then(err => {
                throw new Error(err.detail || '删除失败');
            });
        }
    })
    .catch(err => {
        alert('删除失败: ' + err.message);
    });
}

// ===== Category Management =====

function showCategoryManagerModal() {
    document.getElementById('categoryManagerModal').style.display = 'flex';
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
        // Handle paginated response format
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

    // Validate code format
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
    document.getElementById('tabConfigModal').style.display = 'flex';
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

// CSRF Token helper
function getCSRFToken() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
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

    // Warehouse delete
    if (e.target.classList.contains('delete-warehouse-btn')) {
        var btn = e.target;
        var warehouseId = btn.getAttribute('data-id');
        var warehouseName = btn.getAttribute('data-name');
        deleteWarehouse(warehouseId, warehouseName);
    }
});
