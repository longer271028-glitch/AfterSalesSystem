/* 手机短信管理JavaScript */
(function() {
    'use strict';

    let phonesData = [];
    let smsData = [];
    let currentTab = 'phones';

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
        loadPhones();
        loadPhonesForSelect();
        setupEventListeners();
    });

    // 设置事件监听
    function setupEventListeners() {
        // 手机搜索回车
        document.getElementById('phoneSearchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') loadPhones();
        });
        // 短信搜索回车
        document.getElementById('smsSearchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') loadSmsRecords();
        });
        // 手机选择联动号码
        document.getElementById('smsPhone').addEventListener('change', function() {
            const selected = this.options[this.selectedIndex];
            document.getElementById('smsPhoneNumber').value = selected.dataset.number || '';
        });
    }

    // 切换标签
    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        
        if (tab === 'phones') {
            document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
            document.getElementById('phonesPanel').classList.add('active');
        } else {
            document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
            document.getElementById('recordsPanel').classList.add('active');
            loadSmsRecords();
        }
    }

    // ==================== 手机管理 ====================

    // 加载手机列表
    async function loadPhones() {
        try {
            let url = '/api/sms/phones/?';
            
            const search = document.getElementById('phoneSearchInput').value.trim();
            if (search) url += `search=${encodeURIComponent(search)}&`;
            
            const status = document.getElementById('phoneStatusFilter').value;
            if (status) url += `is_active=${status}&`;

            const response = await fetch(url);
            const data = await response.json();
            phonesData = Array.isArray(data) ? data : (data.results || data || []);
            renderPhoneTable(phonesData);
        } catch (error) {
            console.error('加载手机列表失败:', error);
            document.getElementById('phoneTableBody').innerHTML = 
                '<tr><td colspan="9" class="text-center text-danger">加载失败</td></tr>';
        }
    }

    // 渲染手机表格
    function renderPhoneTable(phones) {
        const tbody = document.getElementById('phoneTableBody');
        if (!phones || phones.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = phones.map(phone => `
            <tr>
                <td>${phone.id}</td>
                <td><strong>${escapeHtml(phone.name)}</strong></td>
                <td>${escapeHtml(phone.model || '-')}</td>
                <td>${escapeHtml(phone.user || '-')}</td>
                <td>${escapeHtml(phone.phone_number)}</td>
                <td>${phone.sms_count || 0}</td>
                <td><span class="status-badge status-${phone.is_active ? 'active' : 'inactive'}">${phone.is_active ? '启用' : '禁用'}</span></td>
                <td>${escapeHtml(phone.created_by_name || '系统')}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editPhone(${phone.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deletePhone(${phone.id})">删除</button>
                </td>
            </tr>
        `).join('');
    }

    // 重置手机筛选
    function resetPhoneFilters() {
        document.getElementById('phoneSearchInput').value = '';
        document.getElementById('phoneStatusFilter').value = '';
        loadPhones();
    }

    // 显示新增手机模态框
    function showAddPhoneModal() {
        document.getElementById('phoneModalTitle').textContent = '新增手机';
        document.getElementById('phoneId').value = '';
        document.getElementById('phoneName').value = '';
        document.getElementById('phoneModel').value = '';
        document.getElementById('phoneUser').value = '';
        document.getElementById('phoneNumber').value = '';
        document.getElementById('phoneActive').value = 'true';
        document.getElementById('phoneRemark').value = '';
        document.getElementById('phoneErrorMessages').innerHTML = '';
        document.getElementById('phoneModal').classList.add('show');
    }

    // 编辑手机
    async function editPhone(id) {
        try {
            const response = await fetch(`/api/sms/phones/${id}/`);
            const phone = await response.json();

            document.getElementById('phoneModalTitle').textContent = '编辑手机';
            document.getElementById('phoneId').value = phone.id;
            document.getElementById('phoneName').value = phone.name || '';
            document.getElementById('phoneModel').value = phone.model || '';
            document.getElementById('phoneUser').value = phone.user || '';
            document.getElementById('phoneNumber').value = phone.phone_number || '';
            document.getElementById('phoneActive').value = phone.is_active ? 'true' : 'false';
            document.getElementById('phoneRemark').value = phone.remark || '';
            document.getElementById('phoneErrorMessages').innerHTML = '';
            document.getElementById('phoneModal').classList.add('show');
        } catch (error) {
            console.error('加载手机信息失败:', error);
            alert('加载手机信息失败');
        }
    }

    // 保存手机
    async function savePhone() {
        const id = document.getElementById('phoneId').value;
        const name = document.getElementById('phoneName').value.trim();
        const model = document.getElementById('phoneModel').value.trim();
        const user = document.getElementById('phoneUser').value.trim();
        const phone_number = document.getElementById('phoneNumber').value.trim();
        const is_active = document.getElementById('phoneActive').value === 'true';
        const remark = document.getElementById('phoneRemark').value.trim();

        // 校验
        const errors = [];
        if (!name) errors.push('请输入手机名称');
        if (!phone_number) errors.push('请输入手机号码');

        if (errors.length > 0) {
            document.getElementById('phoneErrorMessages').innerHTML = 
                errors.map(e => `<div class="error-item">• ${e}</div>`).join('');
            return;
        }

        const data = { name, model, user, phone_number, is_active, remark };

        try {
            const url = id ? `/api/sms/phones/${id}/` : '/api/sms/phones/';
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
                closePhoneModal();
                loadPhones();
                loadPhonesForSelect();
            } else {
                const error = await response.json();
                let errorMsg = '保存失败';
                if (error.phone_number) errorMsg += `: ${error.phone_number[0]}`;
                else if (error.detail) errorMsg += `: ${error.detail}`;
                alert(errorMsg);
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败');
        }
    }

    // 删除手机
    async function deletePhone(id) {
        if (!confirm('确定要删除该手机吗？相关的短信记录也会被删除！')) return;

        try {
            const response = await fetch(`/api/sms/phones/${id}/`, { 
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken }
            });
            if (response.ok) {
                alert('删除成功');
                loadPhones();
                loadPhonesForSelect();
            } else {
                const error = await response.json();
                alert(error.detail || '删除失败');
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败');
        }
    }

    // 关闭手机模态框
    function closePhoneModal() {
        document.getElementById('phoneModal').classList.remove('show');
    }

    // 加载手机选项（用于短信关联）
    async function loadPhonesForSelect() {
        try {
            const response = await fetch('/api/sms/phones/?is_active=true');
            const data = await response.json();
            const phones = Array.isArray(data) ? data : (data.results || data || []);

            const select = document.getElementById('smsPhone');
            const filterSelect = document.getElementById('smsPhoneFilter');

            select.innerHTML = '<option value="">请选择手机</option>';
            filterSelect.innerHTML = '<option value="">全部手机</option>';

            phones.forEach(phone => {
                const option = `<option value="${phone.id}" data-number="${phone.phone_number}">${phone.name} (${phone.phone_number})</option>`;
                select.innerHTML += option;
                filterSelect.innerHTML += `<option value="${phone.id}">${phone.name} (${phone.phone_number})</option>`;
            });
        } catch (error) {
            console.error('加载手机选项失败:', error);
        }
    }

    // ==================== 短信管理 ====================

    // 加载短信记录
    async function loadSmsRecords() {
        try {
            let url = '/api/sms/records/?';
            
            const search = document.getElementById('smsSearchInput').value.trim();
            if (search) url += `search=${encodeURIComponent(search)}&`;
            
            const phoneId = document.getElementById('smsPhoneFilter').value;
            if (phoneId) url += `phone_id=${phoneId}&`;
            
            const startDate = document.getElementById('smsStartDate').value;
            if (startDate) url += `start_date=${startDate}&`;
            
            const endDate = document.getElementById('smsEndDate').value;
            if (endDate) url += `end_date=${endDate}&`;
            
            const isRead = document.getElementById('smsReadFilter').value;
            if (isRead) url += `is_read=${isRead}&`;

            const response = await fetch(url);
            const data = await response.json();
            smsData = Array.isArray(data) ? data : (data.results || data || []);
            renderSmsTable(smsData);
        } catch (error) {
            console.error('加载短信记录失败:', error);
            document.getElementById('smsTableBody').innerHTML = 
                '<tr><td colspan="8" class="text-center text-danger">加载失败</td></tr>';
        }
    }

    // 渲染短信表格
    function renderSmsTable(records) {
        const tbody = document.getElementById('smsTableBody');
        if (!records || records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = records.map(sms => `
            <tr class="${sms.is_read ? '' : 'unread'}">
                <td>${sms.id}</td>
                <td>${escapeHtml(sms.phone_number)}</td>
                <td class="sms-content-preview">${escapeHtml(sms.content.substring(0, 30))}${sms.content.length > 30 ? '...' : ''}</td>
                <td>${escapeHtml(sms.sender || '-')}</td>
                <td>${sms.received_date}</td>
                <td>${sms.received_time}</td>
                <td><span class="status-badge status-${sms.is_read ? 'read' : 'unread'}">${sms.is_read ? '已读' : '未读'}</span></td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="viewSms(${sms.id})">查看</button>
                    <button class="btn btn-sm btn-primary" onclick="editSms(${sms.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSms(${sms.id})">删除</button>
                </td>
            </tr>
        `).join('');
    }

    // 重置短信筛选
    function resetSmsFilters() {
        document.getElementById('smsSearchInput').value = '';
        document.getElementById('smsPhoneFilter').value = '';
        document.getElementById('smsStartDate').value = '';
        document.getElementById('smsEndDate').value = '';
        document.getElementById('smsReadFilter').value = '';
        loadSmsRecords();
    }

    // 显示新增短信模态框
    function showAddSmsModal() {
        document.getElementById('smsModalTitle').textContent = '新增短信';
        document.getElementById('smsId').value = '';
        document.getElementById('smsPhone').value = '';
        document.getElementById('smsPhoneNumber').value = '';
        document.getElementById('smsContent').value = '';
        document.getElementById('smsSender').value = '';
        
        // 默认今天
        const today = new Date().toISOString().split('T')[0];
        const now = new Date().toTimeString().split(' ')[0].substring(0, 5);
        document.getElementById('smsDate').value = today;
        document.getElementById('smsTime').value = now;
        
        document.getElementById('smsRead').value = 'false';
        document.getElementById('smsRemark').value = '';
        document.getElementById('smsErrorMessages').innerHTML = '';
        document.getElementById('smsModal').classList.add('show');
    }

    // 编辑短信
    async function editSms(id) {
        try {
            const response = await fetch(`/api/sms/records/${id}/`);
            const sms = await response.json();

            document.getElementById('smsModalTitle').textContent = '编辑短信';
            document.getElementById('smsId').value = sms.id;
            document.getElementById('smsPhone').value = sms.phone || '';
            document.getElementById('smsPhoneNumber').value = sms.phone_number || '';
            document.getElementById('smsContent').value = sms.content || '';
            document.getElementById('smsSender').value = sms.sender || '';
            document.getElementById('smsDate').value = sms.received_date || '';
            document.getElementById('smsTime').value = sms.received_time || '';
            document.getElementById('smsRead').value = sms.is_read ? 'true' : 'false';
            document.getElementById('smsRemark').value = sms.remark || '';
            document.getElementById('smsErrorMessages').innerHTML = '';
            document.getElementById('smsModal').classList.add('show');
        } catch (error) {
            console.error('加载短信信息失败:', error);
            alert('加载短信信息失败');
        }
    }

    // 查看短信详情
    async function viewSms(id) {
        const sms = smsData.find(s => s.id === id);
        if (!sms) return;

        document.getElementById('detailPhoneNumber').textContent = sms.phone_number;
        document.getElementById('detailSender').textContent = sms.sender || '-';
        document.getElementById('detailDateTime').textContent = `${sms.received_date} ${sms.received_time}`;
        document.getElementById('detailContent').textContent = sms.content;
        document.getElementById('detailRemark').textContent = sms.remark || '-';
        document.getElementById('smsDetailModal').classList.add('show');

        // 标记为已读
        if (!sms.is_read) {
            await fetch(`/api/sms/records/${id}/`, {
                method: 'PATCH',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ is_read: true })
            });
            loadSmsRecords();
        }
    }

    // 保存短信
    async function saveSms() {
        const id = document.getElementById('smsId').value;
        const phone = document.getElementById('smsPhone').value;
        const phone_number = document.getElementById('smsPhoneNumber').value;
        const content = document.getElementById('smsContent').value.trim();
        const sender = document.getElementById('smsSender').value.trim();
        const received_date = document.getElementById('smsDate').value;
        const received_time = document.getElementById('smsTime').value;
        const is_read = document.getElementById('smsRead').value === 'true';
        const remark = document.getElementById('smsRemark').value.trim();

        // 校验
        const errors = [];
        if (!phone) errors.push('请选择关联手机');
        if (!content) errors.push('请输入短信内容');
        if (!received_date) errors.push('请选择接收日期');
        if (!received_time) errors.push('请选择接收时间');

        if (errors.length > 0) {
            document.getElementById('smsErrorMessages').innerHTML = 
                errors.map(e => `<div class="error-item">• ${e}</div>`).join('');
            return;
        }

        const data = { phone, phone_number, content, sender, received_date, received_time, is_read, remark };

        try {
            const url = id ? `/api/sms/records/${id}/` : '/api/sms/records/';
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
                closeSmsModal();
                loadSmsRecords();
                loadPhones(); // 刷新短信计数
            } else {
                const error = await response.json();
                alert('保存失败: ' + JSON.stringify(error));
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败');
        }
    }

    // 删除短信
    async function deleteSms(id) {
        if (!confirm('确定要删除该短信吗？')) return;

        try {
            const response = await fetch(`/api/sms/records/${id}/`, { 
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken }
            });
            if (response.ok) {
                alert('删除成功');
                loadSmsRecords();
                loadPhones();
            } else {
                alert('删除失败');
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败');
        }
    }

    // 关闭短信模态框
    function closeSmsModal() {
        document.getElementById('smsModal').classList.remove('show');
    }

    // 关闭短信详情模态框
    function closeSmsDetailModal() {
        document.getElementById('smsDetailModal').classList.remove('show');
    }

    // HTML转义
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 暴露函数到全局
    window.switchTab = switchTab;
    window.loadPhones = loadPhones;
    window.resetPhoneFilters = resetPhoneFilters;
    window.showAddPhoneModal = showAddPhoneModal;
    window.editPhone = editPhone;
    window.savePhone = savePhone;
    window.deletePhone = deletePhone;
    window.closePhoneModal = closePhoneModal;
    window.loadSmsRecords = loadSmsRecords;
    window.resetSmsFilters = resetSmsFilters;
    window.showAddSmsModal = showAddSmsModal;
    window.editSms = editSms;
    window.viewSms = viewSms;
    window.saveSms = saveSms;
    window.deleteSms = deleteSms;
    window.closeSmsModal = closeSmsModal;
    window.closeSmsDetailModal = closeSmsDetailModal;
})();
