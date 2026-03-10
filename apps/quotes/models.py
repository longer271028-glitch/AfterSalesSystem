from django.db import models
from django.contrib.auth.models import User


class QuoteTemplate(models.Model):
    """报价模板"""

    name = models.CharField('模板名称', max_length=100)
    description = models.TextField('描述', blank=True)
    content = models.JSONField('模板内容', default=dict)

    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quote_templates')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'quote_templates'
        verbose_name = '报价模板'
        verbose_name_plural = '报价模板'

    def __str__(self):
        return self.name


class ProductSeries(models.Model):
    """产品系列"""

    name = models.CharField('系列名称', max_length=100, unique=True)
    description = models.TextField('系列描述', blank=True)

    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_product_series')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'product_series'
        verbose_name = '产品系列'
        verbose_name_plural = '产品系列'
        ordering = ['name']

    def __str__(self):
        return self.name


class QuoteProduct(models.Model):
    """产品（报价用）"""

    STATUS_CHOICES = [
        ('active', '上架'),
        ('inactive', '下架'),
    ]

    name = models.CharField('产品名称', max_length=50, unique=True)
    series = models.ForeignKey(ProductSeries, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_products')

    # 价格和工时费
    repair_price = models.DecimalField('维修价格', max_digits=10, decimal_places=2)
    labor_fee = models.DecimalField('维修工时费', max_digits=10, decimal_places=2)

    description = models.TextField('产品描述', blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quote_products')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'quote_products'
        verbose_name = '产品'
        verbose_name_plural = '产品'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.labor_fee <= 0:
            raise ValidationError({'labor_fee': '维修工时费必须大于0'})
        if self.labor_fee > self.repair_price:
            raise ValidationError({'labor_fee': '维修工时费不能大于维修价格'})


class Quote(models.Model):
    """报价单 - 针对成品、配件、工费"""

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('active', '生效中'),
        ('archived', '已归档'),
    ]

    quote_no = models.CharField('报价单号', max_length=50, unique=True)

    # 报价名称/标题
    name = models.CharField('报价名称', max_length=200, blank=True, default='')

    # 金额明细 - 只保留配件和工时
    parts_amount = models.DecimalField('配件费用', max_digits=10, decimal_places=2, default=0)
    labor_amount = models.DecimalField('工时费用', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('合计金额', max_digits=10, decimal_places=2, default=0)

    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')

    # 有效期
    valid_from = models.DateField('生效日期', null=True, blank=True)
    valid_until = models.DateField('有效期至', null=True, blank=True)

    # 备注
    remark = models.TextField('备注', blank=True)

    # 创建信息
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_quotes')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'quotes'
        verbose_name = '报价单'
        verbose_name_plural = '报价单'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quote_no} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.quote_no:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            count = Quote.objects.filter(quote_no__startswith=f'QP{date_str}').count() + 1
            self.quote_no = f'QP{date_str}{count:04d}'
        self.total_amount = self.parts_amount + self.labor_amount
        super().save(*args, **kwargs)


class QuoteItem(models.Model):
    """报价明细 - 只针对成品配件和工时"""

    ITEM_TYPE_CHOICES = [
        ('part', '成品配件'),
        ('labor', '工时'),
    ]

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField('类型', max_length=20, choices=ITEM_TYPE_CHOICES)

    # 成品配件关联
    product = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name='quote_items')

    item_name = models.CharField('项目名称', max_length=200)
    specification = models.CharField('规格', max_length=100, blank=True)
    quantity = models.IntegerField('数量', default=1)
    unit = models.CharField('单位', max_length=20, default='个')
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    total_price = models.DecimalField('总价', max_digits=10, decimal_places=2)

    remark = models.CharField('备注', max_length=200, blank=True)

    class Meta:
        db_table = 'quote_items'
        verbose_name = '报价明细'
        verbose_name_plural = '报价明细'

    def __str__(self):
        return f"{self.quote.quote_no} - {self.item_name}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class PriceConfig(models.Model):
    """价格配置 - 只针对成品配件和工时费"""

    CONFIG_TYPE_CHOICES = [
        ('part', '成品配件'),
        ('labor', '工时费'),
    ]

    config_type = models.CharField('配置类型', max_length=20, choices=CONFIG_TYPE_CHOICES)
    name = models.CharField('名称', max_length=100)
    code = models.CharField('编码', max_length=50)

    # 关联产品（配件类型时使用）
    product = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name='price_configs')

    price = models.DecimalField('价格', max_digits=10, decimal_places=2)

    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'price_configs'
        verbose_name = '价格配置'
        verbose_name_plural = '价格配置'

    def __str__(self):
        return f"{self.get_config_type_display()} - {self.name}"

