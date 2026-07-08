/* 用户权限管理JavaScript */
(function() {
    'use strict';

    let usersData = [];
    let pagePermissions = [];
    let currentEditUserId = null;

    // 获取CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // 初始化
    document.addEventListener('DOMContentLoaded', function() {
        loadPagePermissions();
        loadUsers();
        setupEventListeners();
    });

    // 设置事件监听
    function setupEventListeners() {
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') applyFilters();
        });
    }

    // 加载页面权限选项
    async function loadPagePermissions() {
        try {
            const response = await fetch('/api/user-management/user-permissions/pages/');
            pagePermissions = await response.json();
        } catch (error) {
            console.error('加载页面权限失败:', error);
        }
    }

    // 加载用户列表
    async function loadUsers() {
        try {
            const response = await fetch('/api/user-management/user-permissions/');
            const data = await response.json();
            usersData = Array.isArray(data) ? data : [];
            renderTable(usersData);
        } catch (error) {
            console.error('加载用户列表失败:', error);
            document.getElementById('userTableBody').innerHTML = 
                '<tr><td colspan="7" class="text-center text-danger">加载失败</td></tr>';
        }
    }

    // 渲染表格
    function renderTable(users) {
        const tbody = document.getElementById('userTableBody');
        if (!users || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(user => {
            const permBadges = (user.page_permissions || []).map(code => {
                const perm = pagePermissions.find(p => p.code === code);
                return `<span class="perm-badge">${perm ? perm.name : code}</span>`;
            }).join('');

            return `
                <tr>
                    <td><strong>${escapeHtml(user.username)}</strong></td>
                    <td>${escapeHtml(user.name || '-')}</td>
                    <td><span class="role-badge role-${user.role}">${user.role_display}</span></td>
                    <td>${escapeHtml(user.department || '-')}</td>
                    <td>
                        <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                            ${user.is_active ? '激活' : '未激活'}
                        </span>
                        ${user.is_superuser ? '<span class="super-badge">超管</span>' : ''}
                    </td>
                    <td class="perm-cell">${permBadges || '<span class="text-muted">无权限</span>'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="editPermissions(${user.id})">编辑权限</button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // 应用筛选
    function applyFilters() {
        const search = document.getElementById('searchInput').value.toLowerCase();
        const role = document.getElementById('roleFilter').value;
        const status = document.getElementById('statusFilter').value;

        let filtered = usersData.filter(user => {
            if (search && !user.username.toLowerCase().includes(search) && 
                !(user.name || '').toLowerCase().includes(search)) {
                return false;
            }
            if (role && user.role !== role) {
                return false;
            }
            if (status === 'active' && !user.is_active) {
                return false;
            }
            if (status === 'inactive' && user.is_active) {
                return false;
            }
            return true;
        });

        renderTable(filtered);
    }

    // 重置筛选
    function resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('roleFilter').value = '';
        document.getElementById('statusFilter').value = '';
        renderTable(usersData);
    }

    // 编辑权限
    async function editPermissions(userId) {
        currentEditUserId = userId;
        const user = usersData.find(u => u.id === userId);
        if (!user) return;

        document.getElementById('editUserId').value = userId;
        document.getElementById('editUsername').textContent = user.username;
        document.getElementById('editName').textContent = user.name || '-';
        document.getElementById('editRole').value = user.role || 'staff';
        document.getElementById('editDepartment').textContent = user.department || '-';

        // 生成权限复选框
        const permList = document.getElementById('permissionsList');
        permList.innerHTML = pagePermissions.map(perm => `
            <label class="perm-checkbox">
                <input type="checkbox" value="${perm.code}" 
                       ${(user.page_permissions || []).includes(perm.code) ? 'checked' : ''}
                       ${user.is_superuser ? 'disabled checked' : ''} />
                <span>${perm.name}</span>
            </label>
        `).join('');

        if (user.is_superuser) {
            permList.innerHTML = '<p class="text-muted">超级管理员拥有所有权限</p>' + permList.innerHTML;
        }

        document.getElementById('permissionModal').classList.add('show');
    }

    // 保存权限
    async function savePermissions() {
        const userId = document.getElementById('editUserId').value;
        const role = document.getElementById('editRole').value;

        // 收集选中的权限
        const checkboxes = document.querySelectorAll('#permissionsList input[type="checkbox"]:checked');
        const permissions = Array.from(checkboxes).map(cb => cb.value);

        try {
            const response = await fetch(`/api/user-management/user-permissions/${userId}/set_permissions/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    role,
                    page_permissions: permissions
                })
            });

            const result = await response.json();

            if (result.success) {
                alert('保存成功');
                closeModal();
                loadUsers();
            } else {
                alert('保存失败: ' + (result.error || '未知错误'));
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败');
        }
    }

    // 关闭模态框
    function closeModal() {
        document.getElementById('permissionModal').classList.remove('show');
        currentEditUserId = null;
    }

    // HTML转义
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 暴露函数到全局
    window.applyFilters = applyFilters;
    window.resetFilters = resetFilters;
    window.editPermissions = editPermissions;
    window.savePermissions = savePermissions;
    window.closeModal = closeModal;
})();
