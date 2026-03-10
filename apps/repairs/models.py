from django.db import models
from django.contrib.auth.models import User
from apps.customers.models import Customer
from apps.faults.models import FaultReport
from apps.inventory.models import Warehouse


class RepairOrder(models.Model):
    """返修工单"""
    
    STATUS_CHOICES = [
        ('received', '已接收'),
        ('inbound', '已入库'),
        ('detecting', '检测中'),
        ('quoting', '报价中'),
        ('repairing', '维修中'),
        ('testing', '质检中'),
        ('outbound', '已出库'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    repair_no = models.CharField('返修单号', max_length=50, unique=True)
    
    # 关联信息
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='repair_orders')
    fault_report = models.ForeignKey(FaultReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='repair_orders')
    
    # 设备信息
    equipment_sn = models.CharField('设备序列号', max_length=100)
    equipment_name = models.CharField('设备名称', max_length=100)
    fault_description = models.TextField('故障描述')
    receive_quantity = models.IntegerField('接收数量', default=1)

    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='received')
    
    # 检测信息
    detect_result = models.TextField('检测结果', blank=True)
    detect_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='detected_repairs')
    detect_time = models.DateTimeField('检测时间', null=True, blank=True)
    
    # 报价信息
    quote_amount = models.DecimalField('报价金额', max_digits=10, decimal_places=2, default=0)
    quote_approved = models.BooleanField('报价已审批', default=False)
    quote_approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_repair_quotes')
    quote_time = models.DateTimeField('报价时间', null=True, blank=True)
    
    # 维修信息
    repair_result = models.TextField('维修结果', blank=True)
    repair_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='repaired_devices')
    repair_time = models.DateTimeField('维修时间', null=True, blank=True)
    repair_remark = models.TextField('维修备注', blank=True)
    
    # 质检信息
    test_result = models.CharField('质检结果', max_length=50, blank=True)
    test_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tested_repairs')
    test_time = models.DateTimeField('质检时间', null=True, blank=True)
    
    # 物流信息
    inbound_logistics = models.CharField('入库物流', max_length=100, blank=True)
    outbound_logistics = models.CharField('出库物流', max_length=100, blank=True)

    # 仓库信息
    inbound_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='inbound_repairs', verbose_name='入库仓库')
    outbound_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='outbound_repairs', verbose_name='出库仓库')

    # 产品关联（用于库存管理）
    product = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='repair_orders', verbose_name='关联产品')

    # 备注
    remark = models.TextField('备注', blank=True)
    
    # 创建信息
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_repairs')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'repair_orders'
        verbose_name = '返修工单'
        verbose_name_plural = '返修工单'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.repair_no} - {self.equipment_name}"
    
    def save(self, *args, **kwargs):
        if not self.repair_no:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            count = RepairOrder.objects.filter(repair_no__startswith=f'RO{date_str}').count() + 1
            self.repair_no = f'RO{date_str}{count:04d}'
        super().save(*args, **kwargs)


class RepairRecord(models.Model):
    """维修记录"""
    
    ACTION_CHOICES = [
        ('receive', '接收'),
        ('inbound', '入库'),
        ('detect', '检测'),
        ('quote', '报价'),
        ('repair', '维修'),
        ('test', '质检'),
        ('outbound', '出库'),
    ]
    
    repair = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='records')
    action = models.CharField('操作', max_length=20, choices=ACTION_CHOICES)
    description = models.TextField('描述', blank=True)
    
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    operate_time = models.DateTimeField('操作时间', auto_now_add=True)
    
    class Meta:
        db_table = 'repair_records'
        verbose_name = '维修记录'
        verbose_name_plural = '维修记录'
        ordering = ['operate_time']
    
    def __str__(self):
        return f"{self.repair.repair_no} - {self.get_action_display()}"


class RepairPart(models.Model):
    """维修配件"""
    
    repair = models.ForeignKey(RepairOrder, on_delete=models.CASCADE, related_name='parts')
    part_name = models.CharField('配件名称', max_length=100)
    part_code = models.CharField('配件编码', max_length=50)
    quantity = models.IntegerField('数量', default=1)
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    total_price = models.DecimalField('总价', max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'repair_parts'
        verbose_name = '维修配件'
        verbose_name_plural = '维修配件'
    
    def __str__(self):
        return f"{self.repair.repair_no} - {self.part_name}"
