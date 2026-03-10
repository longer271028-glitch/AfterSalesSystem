from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from .models import KnowledgeBase, KnowledgeDocument, Conversation, Message, AIConfig, IntentPattern
from .serializers import (
    KnowledgeBaseSerializer, KnowledgeDocumentSerializer, 
    ConversationSerializer, MessageSerializer, AIConfigSerializer, IntentPatternSerializer
)


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """知识库视图集"""
    
    queryset = KnowledgeBase.objects.filter(is_active=True)
    serializer_class = KnowledgeBaseSerializer


class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    """知识文档视图集"""
    
    queryset = KnowledgeDocument.objects.all()
    serializer_class = KnowledgeDocumentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        knowledge_base_id = self.request.query_params.get('knowledge_base_id', None)
        if knowledge_base_id:
            queryset = queryset.filter(knowledge_base_id=knowledge_base_id)
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def embed(self, request, pk=None):
        """生成文档向量（模拟）"""
        doc = self.get_object()
        doc.embedding_status = 'completed'
        doc.save()
        
        return Response(KnowledgeDocumentSerializer(doc).data)


class ConversationViewSet(viewsets.ModelViewSet):
    """AI对话视图集"""
    
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        return queryset.none()
    
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """AI对话"""
        from django.contrib.auth.models import User
        # 对于匿名用户，创建一个默认用户或使用临时用户
        if not request.user.is_authenticated:
            user, _ = User.objects.get_or_create(username='anonymous', defaults={'is_active': False})
        else:
            user = request.user
            
        message_content = request.data.get('message', '')
        conversation_id = request.data.get('conversation_id')
        
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=user)
            except Conversation.DoesNotExist:
                conversation = Conversation.objects.create(
                    user=user,
                    title=message_content[:50] if message_content else '新对话',
                    conversation_type='chat'
                )
        else:
            conversation = Conversation.objects.create(
                user=user,
                title=message_content[:50] if message_content else '新对话',
                conversation_type='chat'
            )
        
        # 保存用户消息
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )
        
        # 意图识别
        intent, entities = self._recognize_intent(message_content)
        
        # 生成回复（这里使用简单的模拟回复，实际应接入LLM）
        reply_content = self._generate_reply(message_content, intent, entities)
        
        # 保存AI回复
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=reply_content,
            intent=intent,
            entities=entities
        )
        
        conversation.updated_at = timezone.now()
        conversation.save()
        
        return Response({
            'conversation': ConversationSerializer(conversation).data,
            'message': MessageSerializer(assistant_message).data,
        })
    
    def _recognize_intent(self, message):
        """识别意图（简化版）"""
        message_lower = message.lower()
        
        # 简单意图匹配
        if any(kw in message_lower for kw in ['故障', '问题', '报错', '坏']):
            return 'fault_query', {'type': 'fault'}
        elif any(kw in message_lower for kw in ['库存', '还有', '多少']):
            return 'inventory_query', {'type': 'inventory'}
        elif any(kw in message_lower for kw in ['工单', '返修', '维修']):
            return 'repair_query', {'type': 'repair'}
        elif any(kw in message_lower for kw in ['创建', '新建', '上报']):
            return 'create_workorder', {'type': 'create'}
        
        return 'general_query', {}
    
    def _generate_reply(self, message, intent, entities):
        """生成回复（简化版）"""
        replies = {
            'fault_query': '根据您描述的问题，可能是设备故障。建议您先检查设备电源和连接线，如果仍有问题，我可以帮您创建故障工单。',
            'inventory_query': '请问您想查询哪种产品的库存？我可以帮您查询零配件、半成品或成品的库存情况。',
            'repair_query': '我可以帮您查询返修工单的状态，或者创建新的返修工单。请提供设备序列号或工单号。',
            'create_workorder': '好的，我来帮您创建工单。请提供以下信息：设备序列号、故障描述、您的联系方式。',
            'general_query': '您好！我是禾大科技智能助手，我可以帮您查询故障信息、库存情况、创建工单等。请问有什么可以帮您？'
        }
        
        return replies.get(intent, replies['general_query'])


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """对话消息视图集"""
    
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        conversation_id = self.request.query_params.get('conversation_id', None)
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        return queryset


class AIConfigViewSet(viewsets.ModelViewSet):
    """AI配置视图集"""
    
    queryset = AIConfig.objects.filter(is_active=True)
    serializer_class = AIConfigSerializer
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """获取默认配置"""
        config = AIConfig.objects.filter(is_default=True, is_active=True).first()
        if config:
            return Response(AIConfigSerializer(config).data)
        return Response({'error': '未找到默认配置'}, status=status.HTTP_404_NOT_FOUND)


class IntentPatternViewSet(viewsets.ModelViewSet):
    """意图模式视图集"""
    
    queryset = IntentPattern.objects.filter(is_active=True)
    serializer_class = IntentPatternSerializer
