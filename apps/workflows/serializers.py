from rest_framework import serializers
from django.contrib.auth.models import User
from .models import WorkflowType, WorkflowNode, WorkflowInstance, WorkflowTask, Organization, Role, UserProfile


class WorkflowNodeSerializer(serializers.ModelSerializer):
    """流程节点序列化器"""
    
    class Meta:
        model = WorkflowNode
        fields = '__all__'


class WorkflowTypeSerializer(serializers.ModelSerializer):
    """流程类型序列化器"""
    
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowType
        fields = '__all__'


class WorkflowTaskSerializer(serializers.ModelSerializer):
    """流程任务序列化器"""
    
    node_name = serializers.CharField(source='node.name', read_only=True)
    assignee_name = serializers.CharField(source='assignee.username', read_only=True)
    
    class Meta:
        model = WorkflowTask
        fields = '__all__'


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    """流程实例序列化器"""
    
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    current_node_name = serializers.CharField(source='current_node.name', read_only=True)
    initiator_name = serializers.CharField(source='initiator.username', read_only=True)
    tasks = WorkflowTaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkflowInstance
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = '__all__'


class OrganizationSerializer(serializers.ModelSerializer):
    """组织序列化器"""
    
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = '__all__'
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return OrganizationSerializer(children, many=True).data


class UserProfileSerializer(serializers.ModelSerializer):
    """用户扩展信息序列化器"""
    
    username = serializers.CharField(source='user.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    roles_names = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = '__all__'
    
    def get_roles_names(self, obj):
        return [role.name for role in obj.roles.all()]
