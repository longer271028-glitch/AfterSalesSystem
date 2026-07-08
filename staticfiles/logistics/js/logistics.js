/* 物流管理统一页面JavaScript */
(function() {
    'use strict';

    // 当前激活的标签
    let currentTab = 'records';

    // 初始化页面
    function init() {
        loadChannels();
        loadRecords();
        setupEventListeners();
    }

    // 设置事件监听
    function setupEventListeners() {
        // 标签切换
        document.querySelectorAll('.logistics-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.dataset.tab;
                switchTab(tabName);
            });
        });

        // 搜索
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', loadRecords);
        }

        // 模态框关闭
        document.querySelectorAll('.logistics-modal-close, .logistics-modal-cancel').forEach(btn => {
            btn.addEventListener('click', closeModal);
        });

        // 点击模态框外部关闭
        document.querySelectorAll('.logistics-modal').forEach(modal => {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal();
                }
            });
        });
    }

    // 切换标签
    function switchTab(tabName) {
        currentTab = tabName;

        // 更新标签样式
        document.querySelectorAll('.logistics-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // 更新内容显示
        document.getElementById('recordsTab').style.display = tabName === 'records' ? 'block' : 'none';
        document.getElementById('channelsTab').style.display = tabName === 'channels' ? 'block' : 'none';

        // 加载数据
        if (tabName === 'records') {
            loadRecords();
        } else {
            loadChannels();
        }
    }

    // ========== 物流记录相关函数 ==========

    // 加载物流记录
    async function loadRecords() {
        const trackNo = document.getElementById('searchInput')?.value || '';
        const trackType = document.getElementById('typeFilter')?.value || '';

        let url = '/logistics/api/records/?';
        if (trackNo) url += `track_no=${trackNo}&`;
        if (trackType) url += `track_type=${trackType}&`;

        try {
            const response = await fetch(url);
            const data = await response.json();
            const records = data.results || data || [];
            renderRecords(records);
        } catch (error) {
            console.error('加载失败:', error);
            renderRecords([]);
        }
    }

    // 渲染物流记录
    function renderRecords(records) {
        const tbody = document.getElementById('recordsTable');
        if (!tbody) return;

        if (!records || records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="logistics-empty">暂无数据</td></tr>';
            return;
        }

        tbody.innerHTML = records.map(record => {
            const canQuery = record.can_query_today && !record.is_completed;
            const queryBtn = canQuery
                ? `<a class="logistics-action-link query" onclick="queryLogistics(${record.id})">查询</a>`
                : `<span style="color: #999;">已查询</span>`;
            const tracesBtn = record.traces && record.traces.length > 0
                ? `<a class="logistics-action-link trace" onclick="viewTraces(${record.id})">查看轨迹</a>`
                : '';
            return `
            <tr>
                <td>${record.track_no || '-'}</td>
                <td>${record.order_no || '-'}</td>
                <td>${record.track_type === 'inbound' ? '收件' : '发件'}</td>
                <td>${record.channel?.name || '-'}</td>
                <td><span class="logistics-status-badge ${getStatusClass(record.status)}">${record.status || '-'}</span></td>
                <td>${renderTraces(record.traces)}</td>
                <td>${record.current_location || '-'}</td>
                <td>${formatDate(record.created_at)}</td>
                <td>
                    ${queryBtn}
                    ${tracesBtn}
                    <a class="logistics-action-link" href="/admin/logistics/logisticsrecord/${record.id}/change/">编辑</a>
                    <a class="logistics-action-link delete" onclick="deleteLogisticsRecord(${record.id})">删除</a>
                </td>
            </tr>
        `}).join('');
    }

    // 查询物流信息
    window.queryLogistics = async function(id) {
        if (!confirm('确定查询该物流信息吗？每天只能查询一次。')) return;

        try {
            const response = await fetch(`/logistics/api/records/${id}/query/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') }
            });
            const data = await response.json();

            if (response.ok) {
                alert('查询成功');
                loadRecords(); // 刷新列表
            } else {
                alert('查询失败: ' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('查询失败:', error);
            alert('查询失败');
        }
    };

    // 查看物流轨迹
    window.viewTraces = async function(id) {
        try {
            const response = await fetch(`/logistics/api/records/${id}/`);
            const record = await response.json();

            // 构建轨迹HTML
            let tracesHtml = '';
            if (record.traces && record.traces.length > 0) {
                tracesHtml = record.traces.slice().reverse().map(trace => `
                    <tr>
                        <td>${formatDate(trace.trace_time)}</td>
                        <td>${trace.status || '-'}</td>
                        <td>${trace.location || trace.description || '-'}</td>
                    </tr>
                `).join('');
            } else {
                tracesHtml = '<tr><td colspan="3" style="text-align: center; color: #999;">暂无物流轨迹信息</td></tr>';
            }

            // 构建弹窗内容
            const modalHtml = `
                <div class="logistics-trace-modal" id="traceModal">
                    <div class="logistics-trace-modal-content">
                        <div class="logistics-trace-modal-header">
                            <h3>物流轨迹详情</h3>
                            <button class="logistics-trace-modal-close" onclick="closeTraceModal()">×</button>
                        </div>
                        <div class="logistics-trace-modal-body">
                            <div class="trace-info-section">
                                <h4>物流基本信息</h4>
                                <table class="trace-info-table">
                                    <tr><th>物流单号:</th><td>${record.track_no || '-'}</td></tr>
                                    <tr><th>关联单号:</th><td>${record.order_no || '-'}</td></tr>
                                    <tr><th>物流类型:</th><td>${record.track_type === 'inbound' ? '收件' : '发件'}</td></tr>
                                    <tr><th>物流渠道:</th><td>${record.channel_name || '-'}</td></tr>
                                    <tr><th>当前状态:</th><td><span class="status-badge ${getStatusClass(record.status)}">${record.status || '-'}</span></td></tr>
                                    <tr><th>当前位置:</th><td>${record.current_location || '-'}</td></tr>
                                </table>
                            </div>
                            <div class="trace-list-section">
                                <h4>物流轨迹</h4>
                                <table class="trace-table">
                                    <thead>
                                        <tr>
                                            <th>时间</th>
                                            <th>状态</th>
                                            <th>地点/描述</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${tracesHtml}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 添加到页面
            const existingModal = document.getElementById('traceModal');
            if (existingModal) {
                existingModal.remove();
            }
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        } catch (error) {
            console.error('加载轨迹失败:', error);
            alert('加载轨迹失败');
        }
    };

    // 关闭轨迹弹窗
    window.closeTraceModal = function() {
        const modal = document.getElementById('traceModal');
        if (modal) {
            modal.remove();
        }
    };

    // 删除物流记录
    window.deleteLogisticsRecord = async function(id) {
        if (!confirm('确定要删除此物流记录吗？此操作不可恢复！')) return;

        try {
            const response = await fetch(`/api/logistics/records/${id}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (response.ok) {
                alert('删除成功！');
                loadRecords(); // 刷新列表
            } else {
                const data = await response.json();
                alert('删除失败: ' + (data.detail || '未知错误'));
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败');
        }
    };

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

    // 渲染物流轨迹
    function renderTraces(traces) {
        if (!traces || traces.length === 0) {
            return '<span style="color: #999;">暂无轨迹</span>';
        }
        // 显示最新的3条轨迹
        const recentTraces = traces.slice(-3).reverse();
        return recentTraces.map(trace => `
            <div style="font-size: 12px; margin-bottom: 2px;">
                <span style="color: #64748b;">${formatTraceDate(trace.trace_time)}</span>
                <span>${trace.status}</span>
            </div>
        `).join('');
    }

    // 格式化轨迹时间
    function formatTraceDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    }

    // 获取状态样式类
    function getStatusClass(status) {
        if (!status) return 'logistics-status-transit';
        if (status.includes('已签收') || status.includes('签收')) return 'logistics-status-delivered';
        if (status.includes('已完成')) return 'logistics-status-completed';
        return 'logistics-status-transit';
    }

    // ========== 物流渠道相关函数 ==========

    // 加载渠道列表
    async function loadChannels() {
        try {
            const response = await fetch('/logistics/api/channels/');
            const data = await response.json();
            const channels = data.results || data || [];
            renderChannels(channels);
        } catch (error) {
            console.error('加载失败:', error);
            renderChannels([]);
        }
    }

    // 渲染渠道列表
    function renderChannels(channels) {
        const tbody = document.getElementById('channelsTable');
        if (!tbody) return;

        if (!channels || channels.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="logistics-empty">暂无数据，点击"添加渠道"新增</td></tr>';
            return;
        }

        tbody.innerHTML = channels.map(channel => `
            <tr>
                <td>${channel.name || '-'}</td>
                <td>${channel.secret_id ? channel.secret_id.substring(0, 20) + '...' : '-'}</td>
                <td>${formatDate(channel.created_at)}</td>
                <td>
                    <a class="logistics-action-link" onclick="editChannel(${channel.id})">编辑</a>
                    <a class="logistics-action-link delete" onclick="deleteChannel(${channel.id})">删除</a>
                </td>
            </tr>
        `).join('');
    }

    // 显示添加渠道模态框
    window.showAddChannelModal = function() {
        document.getElementById('modalTitle').textContent = '添加物流渠道';
        document.getElementById('channelId').value = '';
        document.getElementById('channelName').value = '';
        document.getElementById('secretId').value = '';
        document.getElementById('secretKey').value = '';
        document.getElementById('apiUrl').value = 'https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list';
        document.getElementById('channelModal').classList.add('show');
    };

    // 编辑渠道
    window.editChannel = async function(id) {
        try {
            const response = await fetch(`/logistics/api/channels/${id}/`);
            const channel = await response.json();

            document.getElementById('modalTitle').textContent = '编辑物流渠道';
            document.getElementById('channelId').value = channel.id;
            document.getElementById('channelName').value = channel.name || '';
            document.getElementById('secretId').value = channel.secret_id || '';
            document.getElementById('secretKey').value = channel.secret_key_market || '';
            document.getElementById('apiUrl').value = channel.market_api_url || 'https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list';
            document.getElementById('channelModal').classList.add('show');
        } catch (error) {
            console.error('加载失败:', error);
            alert('加载渠道信息失败');
        }
    };

    // 删除渠道
    window.deleteChannel = async function(id) {
        if (!confirm('确定要删除该渠道吗？')) return;

        try {
            const response = await fetch(`/api/logistics/channels/${id}/`, {
                method: 'DELETE'
            });

            if (response.ok) {
                alert('删除成功');
                loadChannels();
            } else {
                alert('删除失败');
            }
        } catch (error) {
            console.error('删除失败:', error);
            alert('删除失败');
        }
    };

    // 保存渠道
    window.saveChannel = async function() {
        const id = document.getElementById('channelId').value;
        const name = document.getElementById('channelName').value.trim();
        const secretId = document.getElementById('secretId').value.trim();
        const secretKey = document.getElementById('secretKey').value.trim();
        const apiUrl = document.getElementById('apiUrl').value.trim();

        if (!name) { alert('请填写渠道名称'); return; }
        if (!secretId) { alert('请填写Secret ID'); return; }
        if (!secretKey) { alert('请填写Secret Key'); return; }

        const data = {
            name,
            code: name.toLowerCase().replace(/\s+/g, '_'),
            api_type: 'tencent_market',
            secret_id: secretId,
            secret_key_market: secretKey,
            market_api_url: apiUrl || 'https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list',
            is_active: true,
        };

        try {
            const url = id ? `/logistics/api/channels/${id}/` : '/logistics/api/channels/';
            const method = id ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                alert('保存成功');
                closeModal();
                loadChannels();
            } else {
                const error = await response.json();
                alert('保存失败: ' + JSON.stringify(error));
            }
        } catch (error) {
            console.error('保存失败:', error);
            alert('保存失败');
        }
    };

    // ========== 通用函数 ==========

    // 关闭模态框
    function closeModal() {
        document.getElementById('channelModal')?.classList.remove('show');
    }
    window.closeModal = closeModal;

    // 格式化日期
    function formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN');
    }
    window.formatDate = formatDate;

    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
