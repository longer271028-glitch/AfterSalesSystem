from django.db import models


class DatabaseConfig(models.Model):
    """数据库配置"""

    name = models.CharField('配置名称', max_length=50, default='default')
    db_type = models.CharField(
        '数据库类型',
        max_length=20,
        choices=[('sqlite', 'SQLite'), ('mysql', 'MySQL')],
        default='sqlite'
    )
    mysql_host = models.CharField('MySQL主机', max_length=100, blank=True, default='localhost')
    mysql_port = models.IntegerField('MySQL端口', default=3306)
    mysql_user = models.CharField('MySQL用户名', max_length=50, blank=True)
    mysql_password = models.CharField('MySQL密码', max_length=100, blank=True)
    mysql_database = models.CharField('MySQL数据库名', max_length=50, blank=True)
    is_active = models.BooleanField('是否启用', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'system_database_config'
        verbose_name = '数据库配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} - {self.db_type}"

    def get_connection_dict(self):
        """获取连接字典"""
        if self.db_type == 'sqlite':
            return {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'db.sqlite3',
            }
        else:
            return {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': self.mysql_database,
                'USER': self.mysql_user,
                'PASSWORD': self.mysql_password,
                'HOST': self.mysql_host,
                'PORT': self.mysql_port,
                'OPTIONS': {
                    'charset': 'utf8mb4',
                }
            }


class SystemConfig(models.Model):
    """系统配置"""

    key = models.CharField('配置键', max_length=50, unique=True)
    value = models.TextField('配置值', blank=True)
    description = models.CharField('描述', max_length=200, blank=True)
    is_public = models.BooleanField('公开配置', default=False, help_text='前端是否可读')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'system_config'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.key
