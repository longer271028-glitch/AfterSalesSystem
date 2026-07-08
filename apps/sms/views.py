from rest_framework import viewsets, permissions
from django.shortcuts import render
from django.db import models
from django.contrib.auth.decorators import login_required
from .models import Phone, SmsRecord
from .serializers import PhoneSerializer, SmsRecordSerializer


@login_required
def sms_management_view(request):
    """手机短信管理页面"""
    return render(request, 'sms/index.html')


class PhoneViewSet(viewsets.ModelViewSet):
    """手机管理视图集"""
    serializer_class = PhoneSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Phone.objects.all()
        
        # 搜索
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(phone_number__icontains=search) |
                models.Q(user__icontains=search)
            )
        
        # 状态筛选
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)


class SmsRecordViewSet(viewsets.ModelViewSet):
    """短信记录视图集"""
    serializer_class = SmsRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = SmsRecord.objects.all()
        
        # 手机号码筛选
        phone_number = self.request.query_params.get('phone_number', None)
        if phone_number:
            queryset = queryset.filter(phone_number__icontains=phone_number)
        
        # 手机ID筛选
        phone_id = self.request.query_params.get('phone_id', None)
        if phone_id:
            queryset = queryset.filter(phone_id=phone_id)
        
        # 日期范围筛选
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(received_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(received_date__lte=end_date)
        
        # 已读状态筛选
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read == 'true')
        
        # 内容搜索
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(content__icontains=search)
        
        return queryset.order_by('-received_date', '-received_time')
