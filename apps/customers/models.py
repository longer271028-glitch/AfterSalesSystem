from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    """客户管理模型"""

    CUSTOMER_TYPE_CHOICES = [
        ('dealer', '经销商'),
        ('terminal', '终端用户'),
        ('partner', '合作伙伴'),
    ]

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '不活跃'),
        ('blocked', '已封禁'),
    ]

    name = models.CharField('客户名称', max_length=200)
    customer_type = models.CharField('客户类型', max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='terminal')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')

    # 联系信息
    contact_person = models.CharField('联系人', max_length=100, blank=True)
    contact_phone = models.CharField('联系电话', max_length=20, blank=True)
    contact_email = models.EmailField('联系邮箱', blank=True)
    address = models.TextField('地址', blank=True)

    # 市场经理和服务经理
    market_manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_customers', verbose_name='市场经理'
    )
    service_manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='serviced_customers', verbose_name='服务经理'
    )

    # 备注
    remark = models.TextField('备注', blank=True)

    # 创建信息
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_customers')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'customers'
        verbose_name = '客户'
        verbose_name_plural = '客户'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CustomerTag(models.Model):
    """客户标签"""
    
    name = models.CharField('标签名称', max_length=50, unique=True)
    color = models.CharField('颜色', max_length=20, default='#007bff')
    description = models.TextField('描述', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'customer_tags'
        verbose_name = '客户标签'
        verbose_name_plural = '客户标签'
    
    def __str__(self):
        return self.name


class ServiceHistory(models.Model):
    """服务历史"""
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='service_histories')
    service_type = models.CharField('服务类型', max_length=50)
    description = models.TextField('服务描述')
    service_date = models.DateTimeField('服务日期')
    engineer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='service_records')
    result = models.CharField('服务结果', max_length=100, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'service_histories'
        verbose_name = '服务历史'
        verbose_name_plural = '服务历史'
        ordering = ['-service_date']
    
    def __str__(self):
        return f"{self.customer.name} - {self.service_type}"
