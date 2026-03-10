/**
 * Inventory Module - Stock Check Operations
 * Handle stock check operations
 */

// Start New Stock Check
function startCheck() {
    const warehouse = document.getElementById('checkWarehouse').value;
    const remark = document.getElementById('checkRemark').value;

    if (!warehouse) {
        alert('请选择盘点仓库');
        return;
    }

    fetch('/inventory/api/checks/', {
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
    .then(res => res.json())
    .then(data => {
        alert('盘点单创建成功!');
        location.reload();
    })
    .catch(err => {
        alert('创建失败: ' + err);
    });
}

// Start Existing Stock Check
function startStockCheck(checkId) {
    if (!confirm('确认开始盘点吗？')) return;

    fetch(`/inventory/api/checks/${checkId}/start/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => res.json())
    .then(data => {
        alert('盘点已开始!');
        location.reload();
    })
    .catch(err => {
        alert('操作失败: ' + err);
    });
}

// Complete Stock Check
function completeStockCheck(checkId) {
    if (!confirm('确认完成盘点吗？')) return;

    fetch(`/inventory/api/checks/${checkId}/complete/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(res => res.json())
    .then(data => {
        alert('盘点已完成!');
        location.reload();
    })
    .catch(err => {
        alert('操作失败: ' + err);
    });
}
