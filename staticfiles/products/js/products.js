/* 产品管理JavaScript */
(function() {
    'use strict';

    let currentData = [];
    let currentPage = 1;
    let pageSize = 10;
    let currentSort = { field: 'id', order: 'asc' };

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
        loadProducts();
        loadSeries();
        setupEventListeners();
    });

    // 设置事件监听
    function setupEventListeners() {
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') applyFilters();
        });
    }

    // 加载产品列表
    async function loadProducts() {
        try {
            let url = '/api/quotes/products/?';

            // 添加筛选参数
            const search = document.getElementById('searchInput').value.trim();
            if (search) url += `search=${search}&`;

            const seriesId = document.getElementById('seriesFilter').value;
            if (seriesId) url += `series_id=${seriesId}&`;

            const minPrice = document.getElementById('minPrice').value;
            if (minPrice) url += `min_price=${minPrice}&`;

            const maxPrice = document.getElementById('maxPrice').value;
            if (maxPrice) url += `max_price=${maxPrice}&`;

            const minLabor = document.getElementById('minLabor').value;
            if (minLabor) url += `min_labor=${minLabor}&`;

            const maxLabor = document.getElementById('maxLabor').value;
            if (maxLabor) url += `max_labor=${maxLabor}&`;

            const status = document.getElementById('statusFilter').value;
            if (status) url += `status=${status}&`;

            const response = await fetch(url);
            const data = await response.json();
            currentData = Array.isArray(data) ? data : (data.results || data || []);
            renderTable(currentData);
        } catch (error) {
            console.error('加载失败:', error);
            renderTable([]);
        }
    }

    // 加载系列列表
    async function loadSeries() {
        try {
            const response = await fetch('/api/quotes/series/');
            const data = await response.json();
            const series = Array.isArray(data) ? data : (data.results || data || []);

            const select = document.getElementById('productSeries');
            const filterSelect = document.getElementById('seriesFilter');

            select.innerHTML = '<option value="">请选择系列</option>';
            filterSelect.innerHTML = '<option value="">全部系列</option>';

            series.forEach(s => {
                const option = `<option value="${s.id}">${s.name}</option>`;
                select.innerHTML += option;
                filterSelect.innerHTML += option;
            });
        } catch (error) {
            console.error('加载系列失败:', error);
        }
    }

    // 渲染表格
    function renderTable(products) {
        const tbody = document.getElementById('productTableBody');
        if (!products || products.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = products.map(product => `
            <tr>
                <td>${product.id}</td>
                <td><strong>${escapeHtml(product.name)}</strong></td>
                <td>${escapeHtml(product.series_name || '-')}</td>
                <td>¥${parseFloat(product.repair_price).toFixed(2)}</td>
                <td>¥${parseFloat(product.labor_fee).toFixed(2)}</td>
                <td><span class="status-badge status-${product.status}">${getStatusText(product.status)}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editProduct(${product.id})">编辑</button>
                    <button class="btn btn-sm btn-info" onclick="viewProduct(${product.id})">查看</button>
                </td>
            </tr>
        `).join('');
    }

    // 应用筛选
    function applyFilters() {
        loadProducts();
    }

    // 重置筛选
    function resetFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('seriesFilter').value = '';
        document.getElementById('minPrice').value = '';
        document.getElementById('maxPrice').value = '';
        document.getElementById('minLabor').value = '';
        document.getElementById('maxLabor').value = '';
        document.getElementById('statusFilter').value = '';
        loadProducts();
    }

    // 排序表格
    function sortTable(field) {
        if (currentSort.field === field) {
            currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.order = 'asc';
        }

        currentData.sort((a, b) => {
            let aVal = a[field] || '';
            let bVal = b[field] || '';

            if (field === 'repair_price' || field === 'labor_fee') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            }

            if (aVal < bVal) return currentSort.order === 'asc' ? -1 : 1;
            if (aVal > bVal) return currentSort.order === 'asc' ? 1 : -1;
            return 0;
        });

        renderTable(currentData);
    }

    // 显示新增产品模态框
    function showAddProductModal() {
        document.getElementById('modalTitle').textContent = '新增产品';
        document.getElementById('productId').value = '';
        document.getElementById('productName').value = '';
        document.getElementById('productSeries').value = '';
        document.getElementById('repairPrice').value = '';
        document.getElementById('laborFee').value = '';
        document.getElementById('productStatus').value = 'active';
        document.getElementById('productDesc').value = '';
        document.getElementById('errorMessages').innerHTML = '';
        document.getElementById('productModal').classList.add('show');
    }

    // 编辑产品
    async function editProduct(id) {
        try {
            const response = await fetch(`/api/quotes/products/${id}/`);
            const product = await response.json();

            document.getElementById('modalTitle').textContent = '编辑产品';
            document.getElementById('productId').value = product.id;
            document.getElementById('productName').value = product.name || '';
            document.getElementById('productSeries').value = product.series || '';
            document.getElementById('repairPrice').value = product.repair_price || '';
            document.getElementById('laborFee').value = product.labor_fee || '';
            document.getElementById('productStatus').value = product.status || 'active';
            document.getElementById('productDesc').value = product.description || '';
            document.getElementById('errorMessages').innerHTML = '';
            document.getElementById('productModal').classList.add('show');
        } catch (error) {
            console.error('加载产品失败:', error);
            alert('加载产品失败');
        }
    }

    // 查看产品详情
    function viewProduct(id) {
        window.open(`/admin/quotes/quoteproduct/${id}/change/`, '_blank');
    }

    // 保存产品
    async function saveProduct() {
        const id = document.getElementById('productId').value;
        const name = document.getElementById('productName').value.trim();
        const series = document.getElementById('productSeries').value;
        const repairPrice = parseFloat(document.getElementById('repairPrice').value);
        const laborFee = parseFloat(document.getElementById('laborFee').value);
        const status = document.getElementById('productStatus').value;
        const description = document.getElementById('productDesc').value.trim();

        // 校验
        const errors = [];
        if (!name) errors.push('请输入产品名称');
        if (name.length < 1 || name.length > 50) errors.push('产品名称长度必须在1-50字符之间');
        if (!repairPrice || repairPrice <= 0) errors.push('维修价格必须大于0');
        if (!laborFee || laborFee <= 0) errors.push('维修工时费必须大于0');
        if (laborFee > repairPrice) errors.push('维修工时费不能大于维修价格');

        if (errors.length > 0) {
            document.getElementById('errorMessages').innerHTML = errors.map(e => `<div class="error-item">• ${e}</div>`).join('');
            return;
        }

        const data = {
            name,
            series: series || null,
            repair_price: repairPrice,
            labor_fee: laborFee,
            status,
            description
        };

        try {
            const url = id ? `/api/quotes/products/${id}/` : '/api/quotes/products/';
            const method = id ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                alert('保存成功');
                closeModal();
                loadProducts();
            } else {
                const error = await response.json();
                let errorMsg = '保存失败';
                if (error.name) errorMsg += `: ${error.name}`;
                if (error.detail) errorMsg += `: ${error.detail}`;
                if (error.non_field_errors) {
                    errorMsg += ': ' + Object.values(error.non_field_errors).join(', ');
                }
                alert(errorMsg);
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败');
        }
    }

    // 关闭模态框
    function closeModal() {
        document.getElementById('productModal').classList.remove('show');
    }

    // 获取状态文本
    function getStatusText(status) {
        if (status === 'active') return '上架';
        if (status === 'inactive') return '下架';
        return status;
    }

    // HTML转义
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 暴露函数到全局
    window.showAddProductModal = showAddProductModal;
    window.editProduct = editProduct;
    window.viewProduct = viewProduct;
    window.saveProduct = saveProduct;
    window.closeModal = closeModal;
    window.applyFilters = applyFilters;
    window.resetFilters = resetFilters;

    // ==================== 产品系列管理 ====================

    // 显示系列管理模态框
    function showSeriesModal() {
        document.getElementById('seriesModal').classList.add('show');
        loadAllSeries();
    }

    // 显示新增系列模态框
    function showAddSeriesModal() {
        // 先打开系列管理模态框
        showSeriesModal();
        // 聚焦到新系列名称输入框
        setTimeout(() => {
            document.getElementById('newSeriesName').focus();
        }, 100);
    }

    // 关闭系列模态框
    function closeSeriesModal() {
        document.getElementById('seriesModal').classList.remove('show');
    }

    // 加载所有系列（包括未启用的）
    async function loadAllSeries() {
        try {
            const response = await fetch('/api/quotes/series/?include_inactive=true');
            const data = await response.json();
            const series = Array.isArray(data) ? data : (data.results || data || []);
            renderSeriesList(series);
        } catch (error) {
            console.error('加载系列失败:', error);
            document.getElementById('seriesList').innerHTML = '<div class="text-center text-danger">加载失败</div>';
        }
    }

    // 渲染系列列表
    function renderSeriesList(series) {
        const container = document.getElementById('seriesList');
        if (!series || series.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">暂无系列，请添加</div>';
            return;
        }

        container.innerHTML = series.map(s => `
            <div class="d-flex justify-content-between align-items-center p-2 border-bottom">
                <div>
                    <strong>${escapeHtml(s.name)}</strong>
                    ${s.description ? `<br><small class="text-muted">${escapeHtml(s.description)}</small>` : ''}
                    <br><small class="text-muted">创建者: ${escapeHtml(s.created_by_name || '系统')}</small>
                </div>
                <div>
                    <span class="badge bg-${s.is_active ? 'success' : 'secondary'} me-2">
                        ${s.is_active ? '启用' : '禁用'}
                    </span>
                    <button class="btn btn-sm btn-${s.is_active ? 'warning' : 'success'}" onclick="toggleSeries(${s.id}, ${!s.is_active})">
                        ${s.is_active ? '禁用' : '启用'}
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSeries(${s.id})">删除</button>
                </div>
            </div>
        `).join('');
    }

    // 保存系列
    async function saveSeries() {
        const name = document.getElementById('newSeriesName').value.trim();
        const description = document.getElementById('newSeriesDesc').value.trim();

        if (!name) {
            alert('请输入系列名称');
            return;
        }

        try {
            const response = await fetch('/api/quotes/series/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    name,
                    description,
                    is_active: true
                })
            });

            if (response.ok) {
                // 清空表单
                document.getElementById('newSeriesName').value = '';
                document.getElementById('newSeriesDesc').value = '';
                // 刷新列表
                loadAllSeries();
                // 刷新产品表单中的系列下拉框
                loadSeries();
                alert('系列添加成功');
            } else {
                const error = await response.json();
                let errorMsg = '添加失败';
                if (error.name) errorMsg += `: ${error.name[0]}`;
                alert(errorMsg);
            }
        } catch (error) {
            console.error('添加系列失败:', error);
            alert('添加系列失败');
        }
    }

    // 切换系列状态
    async function toggleSeries(id, isActive) {
        if (!confirm(`确定要${isActive ? '启用' : '禁用'}该系列吗？`)) return;

        try {
            const response = await fetch(`/api/quotes/series/${id}/`, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ is_active: isActive })
            });

            if (response.ok) {
                loadAllSeries();
            } else {
                alert('操作失败');
            }
        } catch (error) {
            console.error('操作失败:', error);
            alert('操作失败');
        }
    }

    // 删除系列
    async function deleteSeries(id) {
        if (!confirm('确定要删除该系列吗？')) return;

        try {
            const response = await fetch(`/api/quotes/series/${id}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken }
            });

            if (response.ok) {
                loadAllSeries();
                loadSeries(); // 刷新产品表单中的系列下拉框
            } else {
                const error = await response.json();
                alert(error.detail || '删除失败');
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败');
        }
    }

    // 暴露系列管理函数到全局
    window.showSeriesModal = showSeriesModal;
    window.showAddSeriesModal = showAddSeriesModal;
    window.closeSeriesModal = closeSeriesModal;
    window.saveSeries = saveSeries;
    window.toggleSeries = toggleSeries;
    window.deleteSeries = deleteSeries;
})();
