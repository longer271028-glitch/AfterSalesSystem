from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import WorkflowType, WorkflowNode, WorkflowInstance, WorkflowTask, Organization, Role, UserProfile
from .serializers import (
    WorkflowTypeSerializer, WorkflowInstanceSerializer, 
    WorkflowTaskSerializer, OrganizationSerializer, RoleSerializer, UserProfileSerializer
)


class WorkflowTypeViewSet(viewsets.ModelViewSet):
    """流程类型视图集"""
    
    queryset = WorkflowType.objects.filter(is_active=True)
    serializer_class = WorkflowTypeSerializer


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    """流程实例视图集"""
    
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 当前用户的任务
        my_tasks = self.request.query_params.get('my_tasks', None)
        if my_tasks:
            queryset = queryset.filter(
                Q(initiator=self.request.user) |
                Q(tasks__assignee=self.request.user)
            ).distinct()
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动流程"""
        workflow = self.get_object()
        
        # 创建流程实例
        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            title=request.data.get('title', workflow.name),
            business_type=request.data.get('business_type', ''),
            business_id=request.data.get('business_id', ''),
            initiator=request.user,
            form_data=request.data.get('form_data', {}),
            current_node=workflow.nodes.filter(order=1).first()
        )
        
        # 创建第一个任务
        first_node = workflow.nodes.filter(order=1).first()
        if first_node:
            WorkflowTask.objects.create(
                instance=instance,
                node=first_node,
                assignee=first_node.assignee_value
            )
        
        return Response(WorkflowInstanceSerializer(instance).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消流程"""
        instance = self.get_object()
        instance.status = 'cancelled'
        instance.save()
        return Response(WorkflowInstanceSerializer(instance).data)


class WorkflowTaskViewSet(viewsets.ModelViewSet):
    """流程任务视图集"""
    
    serializer_class = WorkflowTaskSerializer
    
    def get_queryset(self):
        queryset = WorkflowTask.objects.all()
        
        # 待处理任务
        pending = self.request.query_params.get('pending', None)
        if pending:
            queryset = queryset.filter(assignee=self.request.user, status='pending')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """批准任务"""
        task = self.get_object()
        task.status = 'approved'
        task.comment = request.data.get('comment', '')
        task.handled_at = timezone.now()
        task.save()
        
        # 查找下一个节点
        instance = task.instance
        next_node = instance.workflow.nodes.filter(order__gt=task.node.order).first()
        
        if next_node:
            instance.current_node = next_node
            instance.save()
            
            # 创建下一个任务
            WorkflowTask.objects.create(
                instance=instance,
                node=next_node,
                assignee=next_node.assignee_value
            )
        else:
            instance.status = 'completed'
            instance.completed_at = timezone.now()
            instance.save()
        
        return Response(WorkflowTaskSerializer(task).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝任务"""
        task = self.get_object()
        task.status = 'rejected'
        task.comment = request.data.get('comment', '')
        task.handled_at = timezone.now()
        task.save()
        
        # 终止流程
        instance = task.instance
        instance.status = 'rejected'
        instance.save()
        
        return Response(WorkflowTaskSerializer(task).data)


class OrganizationViewSet(viewsets.ModelViewSet):
    """组织视图集"""
    
    queryset = Organization.objects.filter(is_active=True, parent__isnull=True)
    serializer_class = OrganizationSerializer


class RoleViewSet(viewsets.ModelViewSet):
    """角色视图集"""
    
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    """用户扩展信息视图集"""
    
    queryset = UserProfile.objects.filter(is_active=True)
    serializer_class = UserProfileSerializer
