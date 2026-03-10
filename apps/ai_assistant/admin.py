from django.contrib import admin
from django.contrib.auth.models import User
from .models import KnowledgeBase, KnowledgeDocument, Conversation, Message, AIConfig, IntentPattern


def get_user_name(user):
    """获取用户的姓名，优先使用 first_name + last_name，否则使用 username"""
    if user is None:
        return '-'
    if user.first_name or user.last_name:
        name = f"{user.last_name}{user.first_name}".strip()
        if not name:
            name = f"{user.first_name} {user.last_name}".strip()
        return name
    return user.username


class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'kb_type', 'is_active', 'formatted_created_by', 'created_at']
    list_filter = ['kb_type', 'is_active']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'
    formatted_created_by.admin_order_field = 'created_by'


class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'knowledge_base', 'embedding_status', 'view_count', 'created_at']
    list_filter = ['knowledge_base', 'embedding_status']
    search_fields = ['title', 'content']


class ConversationAdmin(admin.ModelAdmin):
    list_display = ['formatted_user', 'title', 'conversation_type', 'created_at', 'updated_at']
    list_filter = ['conversation_type', 'created_at']
    date_hierarchy = 'created_at'

    def formatted_user(self, obj):
        return get_user_name(obj.user)
    formatted_user.short_description = '用户'
    formatted_user.admin_order_field = 'user'


class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'intent', 'created_at']
    list_filter = ['role', 'intent']
    date_hierarchy = 'created_at'


class AIConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_name', 'is_active', 'is_default']
    list_filter = ['provider', 'is_active', 'is_default']


class IntentPatternAdmin(admin.ModelAdmin):
    list_display = ['name', 'intent', 'is_active']
    list_filter = ['is_active']


# 手动注册所有模型到admin.site
admin.site.register(KnowledgeBase, KnowledgeBaseAdmin)
admin.site.register(KnowledgeDocument, KnowledgeDocumentAdmin)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(AIConfig, AIConfigAdmin)
admin.site.register(IntentPattern, IntentPatternAdmin)
