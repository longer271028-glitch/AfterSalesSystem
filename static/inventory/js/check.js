/**
 * Inventory Module - Stock Check Operations
 * Handle stock check operations
 */

// Global variable for current check
let currentCheckId = null;

// API base URL
const API_BASE = '/api/checks';

// Start New Stock Check - 简化版：先创建盘点单
function startCheck() {
    const warehouse = document.getElementById('checkWarehouse').value;
    const remark = document.getElementById('checkRemark').value;

    if (!warehouse) {
        alert('请选择盘点仓库');
        return;
    }

    fetch('/api/products/stock/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            warehouse: warehouse,
            remark: remark
        })
    })
    .then(res => {
        if (!res.ok) {
            return res.text().then(text => { throw new Error(text); });
        }
        return res.json();
    })
    .then(data => {
        alert('盘点单创建成功!');
        location.reload();
    })
    .catch(err => {
        alert('创建失败: ' + err.message);
    });
}

// Start Existing Stock Check
function startStockCheck(checkId) {
    if (!confirm('确认开始盘点吗？系统将自动导入该仓库的所有产品库存数据。')) return;

    fetch(`${API_BASE}${checkId}/start/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => {
        if (!res.ok) {
            return res.text().then(text => { throw new Error(text); });
        }
        return res.json();
    })
    .then(data => {
        if (data.error) {
            alert('操作失败: ' + data.error);
        } else {
            alert(data.message || '盘点已开始!');
            location.reload();
        }
    })
    .catch(err => {
        alert('操作失败: ' + err.message);
    });
}

// View Check Detail - 查看盘点明细并进行数据校对
function viewCheckDetail(checkId) {
    currentCheckId = checkId;

    // 显示弹窗
    document.getElementById('checkDetailModal').style.display = 'flex';
    document.getElementById('checkDetailTitle').textContent = `盘点明细 - #${checkId}`;

    // 加载盘点明细
    loadCheckDetail(checkId);
}

// Load Check Detail Data
async function loadCheckDetail(checkId) {
    try {
        const response = await fetch(`${API_BASE}${checkId}/`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Load detail error:', errorText);
            alert('加载失败: HTTP ' + response.status);
            return;
        }
        const data = await response.json();

        const details = data.details || [];

        // 更新统计
        let totalBook = 0, totalActual = 0, totalDiff = 0;
        details.forEach(d => {
            totalBook += d.book_quantity;
            totalActual += d.actual_quantity;
            totalDiff += d.difference;
        });

        document.getElementById('statProducts').textContent = details.length;
        document.getElementById('statBook').textContent = totalBook;
        document.getElementById('statActual').textContent = totalActual;
        document.getElementById('statDiff').textContent = totalDiff;

        // 渲染明细表格
        const tbody = document.getElementById('checkDetailBody');
        if (details.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无盘点明细</td></tr>';
            return;
        }

        tbody.innerHTML = details.map(d => {
            const diff = d.actual_quantity - d.book_quantity;
            const diffClass = diff > 0 ? 'text-success' : diff < 0 ? 'text-danger' : '';
            const diffSign = diff > 0 ? '+' : '';

            return `
                <tr>
                    <td>${d.product_name}</td>
                    <td>${d.book_quantity}</td>
                    <td>
                        <input type="number" class="form-control form-control-sm"
                               style="width: 80px; display: inline-block;"
                               value="${d.actual_quantity}"
                               onchange="updateCheckDetail(${d.id}, this.value)">
                    </td>
                    <td class="${diffClass}">${diffSign}${diff}</td>
                    <td>${d.remark || '-'}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('Load error:', err);
        alert('加载失败: ' + err.message);
    }
}

// Update Check Detail - 修正实盘数量
async function updateCheckDetail(detailId, actualQuantity) {
    try {
        const response = await fetch(`${API_BASE}${currentCheckId}/update_detail/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                detail_id: detailId,
                actual_quantity: parseInt(actualQuantity)
            })
        });

        // Check if response is OK
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            alert('更新失败: HTTP ' + response.status);
            return;
        }

        const data = await response.json();

        // 重新加载明细
        loadCheckDetail(currentCheckId);
    } catch (err) {
        console.error('Update error:', err);
        alert('更新失败: ' + err.message);
    }
}

// Close Check Detail Modal
function closeCheckDetail() {
    document.getElementById('checkDetailModal').style.display = 'none';
    currentCheckId = null;
}

// Complete Stock Check
function completeStockCheck(checkId) {
    if (!confirm('确认完成盘点吗？')) return;

    fetch(`${API_BASE}${checkId}/complete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => {
        if (!res.ok) {
            return res.text().then(text => { throw new Error(text); });
        }
        return res.json();
    })
    .then(data => {
        alert('盘点完成!');
        location.reload();
    })
    .catch(err => {
        alert('操作失败: ' + err.message);
    });
}

// View Check Report
function viewCheckReport(checkId) {
    fetch(`${API_BASE}${checkId}/report/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => {
        if (!res.ok) {
            return res.text().then(text => { throw new Error(text); });
        }
        return res.json();
    })
    .then(data => {
        let reportText = `盘点报告\n`;
        reportText += `================\n`;
        reportText += `盘点单号: ${data.check_no}\n`;
        reportText += `仓库: ${data.warehouse}\n`;
        reportText += `状态: ${data.status_display}\n`;
        reportText += `----------------\n`;
        reportText += `产品数: ${data.summary.total_products}\n`;
        reportText += `账面数量: ${data.summary.total_book}\n`;
        reportText += `实盘数量: ${data.summary.total_actual}\n`;
        reportText += `差异数量: ${data.summary.total_difference}\n`;

        alert(reportText);
    })
    .catch(err => {
        alert('获取报告失败: ' + err.message);
    });
}