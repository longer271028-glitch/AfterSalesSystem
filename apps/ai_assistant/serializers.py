from rest_framework import serializers
from .models import KnowledgeBase, KnowledgeDocument, Conversation, Message, AIConfig, IntentPattern


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    """知识文档序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KnowledgeDocument
        fields = '__all__'


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """知识库序列化器"""
    
    documents = KnowledgeDocumentSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KnowledgeBase
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    """对话消息序列化器"""
    
    class Meta:
        model = Message
        fields = '__all__'


class ConversationSerializer(serializers.ModelSerializer):
    """AI对话序列化器"""
    
    messages = MessageSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Conversation
        fields = '__all__'


class AIConfigSerializer(serializers.ModelSerializer):
    """AI配置序列化器"""
    
    class Meta:
        model = AIConfig
        fields = '__all__'


class IntentPatternSerializer(serializers.ModelSerializer):
    """意图模式序列化器"""
    
    class Meta:
        model = IntentPattern
        fields = '__all__'
