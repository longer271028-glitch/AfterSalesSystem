/**
 * Inventory Module - Inbound/Outbound Operations
 * Handle stock in/out operations
 */

// ===== Inbound Operations =====

// Show Inbound Modal
function showInboundModal() {
    document.getElementById('inboundModal').style.display = 'block';
}

// Close Inbound Modal
function closeInboundModal() {
    document.getElementById('inboundModal').style.display = 'none';
}

// Submit Inbound
function submitInbound() {
    const warehouse = document.getElementById('inWarehouseModal').value;
    const productId = document.getElementById('inProductModal').value;
    const quantity = document.getElementById('inQuantityModal').value;
    const orderNo = document.getElementById('inOrderNoModal').value;
    const remark = document.getElementById('inRemarkModal').value;

    if (!productId || !quantity) {
        alert('请填写完整信息');
        return;
    }

    fetch('/inventory/api/stock/in_stock/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            warehouse: warehouse,
            product_id: productId,
            quantity: parseInt(quantity),
            order_no: orderNo,
            remark: remark
        })
    })
    .then(res => res.json())
    .then(data => {
        alert('入库成功!');
        closeInboundModal();
        location.reload();
    })
    .catch(err => {
        alert('入库失败: ' + err);
    });
}

// Query Inbound Records
function queryInboundRecords(page) {
    const startDate = document.getElementById('inStartDate').value;
    const endDate = document.getElementById('inEndDate').value;
    const warehouse = document.getElementById('inQueryWarehouse').value;
    const product = document.getElementById('inQueryProduct').value;

    let url = `/inventory/api/stock/?record_type=in&page=${page}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (warehouse) url += `&warehouse=${warehouse}`;
    if (product) url += `&product=${encodeURIComponent(product)}`;

    fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById('inboundRecordsTable');
        if (!data.results || data.results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">未找到数据</td></tr>';
            return;
        }
        tbody.innerHTML = data.results.map(item => `
            <tr>
                <td>${item.operate_time}</td>
                <td>${item.product_name}</td>
                <td>${item.warehouse_name || '-'}</td>
                <td class="text-success">+${item.quantity}</td>
                <td>${item.balance}</td>
                <td>${item.related_order_no || '-'}</td>
                <td>${item.operator_name || '-'}</td>
            </tr>
        `).join('');
        // Simple pagination
        const totalPages = Math.ceil(data.count / 20);
        if (totalPages > 1) {
            let html = '';
            for (let i = 1; i <= totalPages && i <= 5; i++) {
                html += `<li class="page-item ${i === page ? 'active' : ''}"><a class="page-link" href="javascript:queryInboundRecords(${i})">${i}</a></li>`;
            }
            document.getElementById('inboundPagination').innerHTML = html;
        }
    })
    .catch(err => {
        alert('查询失败: ' + err);
    });
}

// ===== Outbound Operations =====

// Show Outbound Modal
function showOutboundModal() {
    document.getElementById('outboundModal').style.display = 'block';
}

// Close Outbound Modal
function closeOutboundModal() {
    document.getElementById('outboundModal').style.display = 'none';
}

// Submit Outbound
function submitOutbound() {
    const warehouse = document.getElementById('outWarehouseModal').value;
    const productId = document.getElementById('outProductModal').value;
    const quantity = document.getElementById('outQuantityModal').value;
    const orderNo = document.getElementById('outOrderNoModal').value;
    const remark = document.getElementById('outRemarkModal').value;

    if (!productId || !quantity) {
        alert('请填写完整信息');
        return;
    }

    fetch('/inventory/api/stock/out_stock/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            warehouse: warehouse,
            product_id: productId,
            quantity: parseInt(quantity),
            order_no: orderNo,
            remark: remark
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert('出库成功!');
            closeOutboundModal();
            location.reload();
        }
    })
    .catch(err => {
        alert('出库失败: ' + err);
    });
}

// Query Outbound Records
function queryOutboundRecords(page) {
    const startDate = document.getElementById('outStartDate').value;
    const endDate = document.getElementById('outEndDate').value;
    const warehouse = document.getElementById('outQueryWarehouse').value;
    const product = document.getElementById('outQueryProduct').value;

    let url = `/inventory/api/stock/?record_type=out&page=${page}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (warehouse) url += `&warehouse=${warehouse}`;
    if (product) url += `&product=${encodeURIComponent(product)}`;

    fetch(url, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById('outboundRecordsTable');
        if (!data.results || data.results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">未找到数据</td></tr>';
            return;
        }
        tbody.innerHTML = data.results.map(item => `
            <tr>
                <td>${item.operate_time}</td>
                <td>${item.product_name}</td>
                <td>${item.warehouse_name || '-'}</td>
                <td class="text-danger">-${item.quantity}</td>
                <td>${item.balance}</td>
                <td>${item.related_order_no || '-'}</td>
                <td>${item.operator_name || '-'}</td>
            </tr>
        `).join('');
        const totalPages = Math.ceil(data.count / 20);
        if (totalPages > 1) {
            let html = '';
            for (let i = 1; i <= totalPages && i <= 5; i++) {
                html += `<li class="page-item ${i === page ? 'active' : ''}"><a class="page-link" href="javascript:queryOutboundRecords(${i})">${i}</a></li>`;
            }
            document.getElementById('outboundPagination').innerHTML = html;
        }
    })
    .catch(err => {
        alert('查询失败: ' + err);
    });
}
