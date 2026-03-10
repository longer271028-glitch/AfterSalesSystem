/* 系统设置JavaScript */
(function() {
    'use strict';

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

    // 切换标签
    window.switchTab = function(tab) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        
        if (tab === 'database') {
            document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
            document.getElementById('databasePanel').classList.add('active');
        } else {
            document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
            document.getElementById('initPanel').classList.add('active');
        }
    };

    // 切换数据库字段显示
    window.toggleDbFields = function() {
        const dbType = document.getElementById('dbType').value;
        const mysqlFields = document.getElementById('mysqlFields');
        
        if (dbType === 'mysql') {
            mysqlFields.style.display = 'block';
        } else {
            mysqlFields.style.display = 'none';
        }
    };

    // 测试数据库连接
    window.testConnection = async function() {
        const dbType = document.getElementById('dbType').value;
        const messageBox = document.getElementById('dbMessage');
        
        let data = { db_type: dbType };
        
        if (dbType === 'mysql') {
            data.mysql_host = document.getElementById('mysqlHost').value || 'localhost';
            data.mysql_port = parseInt(document.getElementById('mysqlPort').value) || 3306;
            data.mysql_user = document.getElementById('mysqlUser').value;
            data.mysql_password = document.getElementById('mysqlPassword').value;
            data.mysql_database = document.getElementById('mysqlDatabase').value;
        }

        messageBox.innerHTML = '<div class="alert alert-info">正在测试连接...</div>';
        messageBox.style.display = 'block';

        try {
            const response = await fetch('/api/system/database/test_connection/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                messageBox.innerHTML = '<div class="alert alert-success">' + result.message + '</div>';
            } else {
                messageBox.innerHTML = '<div class="alert alert-danger">' + result.message + '</div>';
            }
        } catch (error) {
            messageBox.innerHTML = '<div class="alert alert-danger">连接测试失败: ' + error.message + '</div>';
        }
    };

    // 保存数据库配置
    window.saveDatabaseConfig = async function() {
        const dbType = document.getElementById('dbType').value;
        const messageBox = document.getElementById('dbMessage');
        
        let data = { 
            name: 'default',
            db_type: dbType,
            is_active: true
        };
        
        if (dbType === 'mysql') {
            data.mysql_host = document.getElementById('mysqlHost').value || 'localhost';
            data.mysql_port = parseInt(document.getElementById('mysqlPort').value) || 3306;
            data.mysql_user = document.getElementById('mysqlUser').value;
            data.mysql_password = document.getElementById('mysqlPassword').value;
            data.mysql_database = document.getElementById('mysqlDatabase').value;
        }

        messageBox.innerHTML = '<div class="alert alert-info">正在保存配置...</div>';
        messageBox.style.display = 'block';

        try {
            // 先保存配置
            const saveResponse = await fetch('/api/system/database/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            });

            const saveResult = await saveResponse.json();

            if (saveResponse.ok || saveResult.id) {
                messageBox.innerHTML = '<div class="alert alert-success">配置保存成功！注意：切换数据库需要重启应用服务才能生效。</div>';
            } else {
                messageBox.innerHTML = '<div class="alert alert-danger">保存失败: ' + JSON.stringify(saveResult) + '</div>';
            }
        } catch (error) {
            messageBox.innerHTML = '<div class="alert alert-danger">保存失败: ' + error.message + '</div>';
        }
    };

    // 初始化数据库
    window.initDatabase = async function() {
        if (!confirm('确定要初始化数据库吗？这将执行所有迁移并创建默认超级管理员。')) {
            return;
        }

        const messageBox = document.getElementById('initMessage');
        const resultBox = document.getElementById('initResult');
        
        messageBox.innerHTML = '<div class="alert alert-info">正在初始化数据库，请稍候...</div>';
        messageBox.style.display = 'block';
        resultBox.style.display = 'none';

        try {
            const response = await fetch('/api/system/database/init_database/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                }
            });

            const result = await response.json();

            // 显示结果
            resultBox.style.display = 'block';
            
            // 迁移结果
            const migrationsEl = document.getElementById('resultMigrations');
            if (result.migrations) {
                migrationsEl.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            } else {
                migrationsEl.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i>';
            }
            
            // 超级管理员结果
            const superuserEl = document.getElementById('resultSuperuser');
            if (result.superuser) {
                superuserEl.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            } else {
                superuserEl.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i>';
            }
            
            // 权限结果
            const permissionsEl = document.getElementById('resultPermissions');
            if (result.permissions) {
                permissionsEl.innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
            } else {
                permissionsEl.innerHTML = '<i class="bi bi-x-circle-fill text-danger"></i>';
            }

            if (result.errors && result.errors.length > 0) {
                messageBox.innerHTML = '<div class="alert alert-warning">初始化完成，但有错误: ' + result.errors.join(', ') + '</div>';
            } else {
                messageBox.innerHTML = '<div class="alert alert-success">数据库初始化成功！默认管理员: admin / 123456</div>';
            }
        } catch (error) {
            messageBox.innerHTML = '<div class="alert alert-danger">初始化失败: ' + error.message + '</div>';
        }
    };
})();
