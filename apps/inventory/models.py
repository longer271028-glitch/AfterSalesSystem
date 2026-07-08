from django.db import models
from django.contrib.auth.models import User
from apps.rbac.models import UserProfile
from apps.quotes.models import QuoteProduct as Product


class StockRecord(models.Model):
    """库存记录 - 使用QuoteProduct作为产品"""

    RECORD_TYPE_CHOICES = [
        ('in', '入库'),
        ('out', '出库'),
        ('adjust', '调整'),
        ('check', '盘点'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_records')
    warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_records')
    record_type = models.CharField('记录类型', max_length=20, choices=RECORD_TYPE_CHOICES)
    quantity = models.IntegerField('数量')
    balance = models.IntegerField('库存余额')
    
    # 关联单据
    related_order_no = models.CharField('关联单号', max_length=50, blank=True)
    
    # 备注
    remark = models.TextField('备注', blank=True)
    
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_operations')
    operate_time = models.DateTimeField('操作时间', auto_now_add=True)
    
    is_deleted = models.BooleanField('是否删除', default=False)
    
    class Meta:
        db_table = 'stock_records'
        verbose_name = '库存记录'
        verbose_name_plural = '库存记录'
        ordering = ['-operate_time']
    
    def __str__(self):
        return f"{self.product.name} - {self.record_type} - {self.quantity}"


class StockCheck(models.Model):
    """库存盘点 - 使用QuoteProduct作为产品"""
    
    CHECK_STATUS_CHOICES = [
        ('draft', '草稿'),
        ('checking', '盘点中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    check_no = models.CharField('盘点单号', max_length=50, unique=True)
    warehouse = models.CharField('仓库', max_length=100, default='主仓库')
    status = models.CharField('状态', max_length=20, choices=CHECK_STATUS_CHOICES, default='draft')
    
    start_date = models.DateField('开始日期')
    end_date = models.DateField('结束日期', null=True, blank=True)
    
    remark = models.TextField('备注', blank=True)
    
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'stock_checks'
        verbose_name = '库存盘点'
        verbose_name_plural = '库存盘点'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.check_no
    
    def save(self, *args, **kwargs):
        if not self.check_no:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            count = StockCheck.objects.filter(check_no__startswith=f'SC{date_str}').count() + 1
            self.check_no = f'SC{date_str}{count:04d}'
        super().save(*args, **kwargs)


class StockCheckDetail(models.Model):
    """盘点明细"""

    check_record = models.ForeignKey(StockCheck, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    book_quantity = models.IntegerField('账面数量')
    actual_quantity = models.IntegerField('实际数量')
    difference = models.IntegerField('差异数量')
    
    remark = models.CharField('备注', max_length=200, blank=True)
    
    class Meta:
        db_table = 'stock_check_details'
        verbose_name = '盘点明细'
        verbose_name_plural = '盘点明细'


class WarehouseCategory(models.Model):
    """仓库类别"""

    name = models.CharField('类别名称', max_length=50)
    code = models.CharField('类别代码', max_length=20, unique=True)
    color = models.CharField('颜色标识', max_length=20, default='#6c757d', help_text='Bootstrap颜色类名或十六进制颜色值')
    icon = models.CharField('图标', max_length=50, default='bi-building', help_text='Bootstrap Icons图标类名')
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'warehouse_categories'
        verbose_name = '仓库类别'
        verbose_name_plural = '仓库类别'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """仓库"""

    name = models.CharField('仓库名称', max_length=100)
    code = models.CharField('仓库编码', max_length=20, unique=True)
    category = models.ForeignKey(WarehouseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouses', verbose_name='仓库类别')
    address = models.CharField('地址', max_length=200, blank=True)
    manager = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses', verbose_name='管理员')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'warehouses'
        verbose_name = '仓库'
        verbose_name_plural = '仓库'

    def __str__(self):
        return self.name


class InventoryTabConfig(models.Model):
    """库存管理Tab配置"""

    TAB_CHOICES = [
        ('overview', '库存概览'),
        ('inbound', '入库'),
        ('outbound', '出库'),
        ('check', '盘点'),
        ('report', '库存报表'),
        ('warehouse', '仓库管理'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_tab_configs')
    tab_key = models.CharField('Tab标识', max_length=20, choices=TAB_CHOICES)
    is_visible = models.BooleanField('是否显示', default=True)
    sort_order = models.IntegerField('排序', default=0)

    class Meta:
        db_table = 'inventory_tab_configs'
        verbose_name = '库存Tab配置'
        verbose_name_plural = '库存Tab配置'
        unique_together = ['user', 'tab_key']
        ordering = ['sort_order', 'id']

    def __str__(self):
        return "{} - {}".format(self.user.username, self.get_tab_key_display())
