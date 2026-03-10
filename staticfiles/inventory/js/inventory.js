/**
 * Inventory Module - Main JavaScript
 * Tab switching and core functionality
 */

// Tab Switching
function switchTab(tabName) {
    // Remove active state from all buttons
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
    });

    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(function(content) {
        content.style.display = 'none';
    });

    // Activate corresponding button
    var btn = document.querySelector('.tab-btn[data-tab="' + tabName + '"]');
    if (btn) btn.classList.add('active');

    // Show corresponding content
    var content = document.getElementById('tab-' + tabName);
    if (content) content.style.display = 'block';
}

// Get CSRF Token
function getCSRFToken() {
    return document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
}

// Common Fetch Wrapper
function fetchAPI(url, options = {}) {
    const defaultOptions = {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            ...options.headers
        }
    };
    return fetch(url, { ...defaultOptions, ...options });
}

// Common Alert Helper
function showAlert(message, isError = false) {
    alert(message);
}

// Stock Query Function
function queryStock() {
    const warehouseId = document.getElementById('queryWarehouse').value;
    const productKeyword = document.getElementById('queryProduct').value;

    let url = '/inventory/api/stock/query/?';
    if (warehouseId) url += 'warehouse=' + warehouseId + '&';
    if (productKeyword) url += 'product=' + encodeURIComponent(productKeyword);

    fetch(url, {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById('stockQueryResult');
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">未找到数据</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(item => `
            <tr>
                <td>${item.product_code}</td>
                <td>${item.product_name}</td>
                <td>${item.warehouse_name || '-'}</td>
                <td>${item.quantity}</td>
                <td><span class="stock-badge ${item.quantity > 10 ? 'stock-normal' : (item.quantity > 0 ? 'stock-low' : 'stock-out')}">${item.status}</span></td>
            </tr>
        `).join('');
    })
    .catch(err => {
        alert('查询失败: ' + err);
    });
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any auto-loading components here
});
