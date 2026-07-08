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
    const productInput = document.getElementById('inProductModal').value;
    // 从"id|name"格式中提取ID
    const productId = productInput.includes('|') ? productInput.split('|')[0] : productInput;
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

// Submit Outbound / Transfer
function submitOutbound() {
    const outWarehouseEl = document.getElementById('outWarehouseModal');
    const inWarehouseEl = document.getElementById('inWarehouseTransferModal');
    const productEl = document.getElementById('outProductModal');
    const quantityEl = document.getElementById('outQuantityModal');
    
    const outWarehouse = outWarehouseEl ? outWarehouseEl.value : '';
    const inWarehouse = inWarehouseEl ? inWarehouseEl.value : '';
    const productInput = productEl ? productEl.value : '';
    // 从"id|name"格式中提取ID
    const productId = productInput.includes('|') ? productInput.split('|')[0] : productInput;
    const quantity = quantityEl ? quantityEl.value : '';
    const orderNo = document.getElementById('outOrderNoModal').value;
    const remark = document.getElementById('outRemarkModal').value;

    console.log('=== 调拨表单数据 ===');
    console.log('出库仓库:', outWarehouse, '- 长度:', outWarehouse.length);
    console.log('入库仓库:', inWarehouse, '- 长度:', inWarehouse.length);
    
    // 检查入库仓库选择器的详细信息
    if (inWarehouseEl) {
        const selectedOption = inWarehouseEl.options[inWarehouseEl.selectedIndex];
        console.log('入库仓库选择器:');
        console.log('  - value属性:', inWarehouseEl.value);
        console.log('  - selectedIndex:', inWarehouseEl.selectedIndex);
        console.log('  - 选中选项text:', selectedOption ? selectedOption.text : '无');
        console.log('  - 选中选项value:', selectedOption ? selectedOption.value : '无');
        console.log('  - options数量:', inWarehouseEl.options.length);
        // 列出所有选项
        for (let i = 0; i < inWarehouseEl.options.length; i++) {
            console.log(`    选项${i}: value="${inWarehouseEl.options[i].value}", text="${inWarehouseEl.options[i].text}"`);
        }
    } else {
        console.log('入库仓库选择器DOM元素不存在!');
    }
    
    console.log('产品ID:', productId, '- 长度:', productId.length);
    console.log('调拨数量:', quantity, '- 长度:', quantity.length);

    if (!outWarehouse || !inWarehouse || !productId || !quantity) {
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
            out_warehouse: outWarehouse,
            in_warehouse: inWarehouse,
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
            alert('调拨成功!');
            closeOutboundModal();
            location.reload();
        }
    })
    .catch(err => {
        alert('操作失败: ' + err);
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
