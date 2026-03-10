from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KnowledgeBaseViewSet, KnowledgeDocumentViewSet, 
    ConversationViewSet, MessageViewSet, AIConfigViewSet, IntentPatternViewSet
)

router = DefaultRouter()
router.register(r'bases', KnowledgeBaseViewSet, basename='knowledge-base')
router.register(r'documents', KnowledgeDocumentViewSet, basename='knowledge-document')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'config', AIConfigViewSet, basename='ai-config')
router.register(r'intents', IntentPatternViewSet, basename='intent-pattern')

urlpatterns = [
    path('', include(router.urls)),
    path('chat/', ConversationViewSet.as_view({'post': 'chat'}), name='ai-chat'),
]
