from django.db import models
from django.contrib.auth.models import User


class Phone(models.Model):
    """手机管理记录"""

    name = models.CharField('手机名称', max_length=100)
    model = models.CharField('手机型号', max_length=100, blank=True)
    user = models.CharField('使用者', max_length=50, blank=True)
    phone_number = models.CharField('手机号码', max_length=20, unique=True)
    remark = models.TextField('备注', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_phones',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'sms_phones'
        verbose_name = '手机管理'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone_number}"


class SmsRecord(models.Model):
    """短信接收记录"""

    phone = models.ForeignKey(
        Phone,
        on_delete=models.CASCADE,
        related_name='sms_records',
        verbose_name='关联手机'
    )
    phone_number = models.CharField('手机号码', max_length=20)
    content = models.TextField('短信内容')
    received_date = models.DateField('接收日期')
    received_time = models.TimeField('接收时间')
    sender = models.CharField('发送方', max_length=50, blank=True)
    is_read = models.BooleanField('是否已读', default=False)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sms_records'
        verbose_name = '短信记录'
        verbose_name_plural = verbose_name
        ordering = ['-received_date', '-received_time']

    def __str__(self):
        return f"{self.phone_number} - {self.received_date}"
