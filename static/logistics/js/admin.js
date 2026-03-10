// 物流管理后台 JavaScript

// 根据API类型显示/隐藏相应的配置字段
function toggleApiFields() {
    const apiTypeSelect = document.getElementById('id_api_type');
    if (!apiTypeSelect) return;

    const apiType = apiTypeSelect.value;

    // 获取字段组
    const tencentFieldset = document.querySelector('.collapse');
    if (tencentFieldset) {
        if (apiType === 'tencent') {
            tencentFieldset.style.display = 'block';
        } else {
            tencentFieldset.style.display = 'none';
        }
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    const apiTypeSelect = document.getElementById('id_api_type');
    if (apiTypeSelect) {
        apiTypeSelect.addEventListener('change', toggleApiFields);
        toggleApiFields(); // 初始化显示
    }

    // 添加查询按钮到物流记录列表
    addQueryButtonsToList();
});

// 添加查询按钮到物流记录列表
function addQueryButtonsToList() {
    // 检查是否在物流记录列表页面
    const listTable = document.querySelector('#result_list');
    if (!listTable) return;

    // 为每一行添加查询按钮
    const rows = listTable.querySelectorAll('tbody tr');
    rows.forEach(function(row, index) {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            // 获取物流单号
            const trackNo = cells[1].textContent.trim();

            // 在最后一列添加操作按钮
            const actionCell = cells[cells.length - 1];
            const queryButton = document.createElement('button');
            queryButton.type = 'button';
            queryButton.className = 'btn btn-sm btn-primary';
            queryButton.style.marginRight = '5px';
            queryButton.textContent = '查询';
            queryButton.onclick = function() {
                queryLogistics(trackNo, row);
            };

            actionCell.appendChild(queryButton);
        }
    });
}

// 查询物流信息
async function queryLogistics(trackNo, row) {
    if (!confirm(`确定要查询物流单号 ${trackNo} 吗？\n注意：每个物流单每天只能查询一次。`)) {
        return;
    }

    try {
        // 获取记录ID
        const recordUrl = row.querySelector('a').href;
        const recordId = recordUrl.split('/').filter(Boolean).pop();

        // 发送查询请求
        const response = await fetch(`/api/logistics/records/${recordId}/query/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({})
        });

        const result = await response.json();

        if (response.ok) {
            alert('查询成功！物流信息已更新。');
            // 重新加载页面
            location.reload();
        } else {
            alert('查询失败：' + (result.error || result.detail || '未知错误'));
        }
    } catch (error) {
        alert('查询失败：' + error.message);
    }
}
