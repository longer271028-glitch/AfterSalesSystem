from django.db import models
from django.contrib.auth.models import User


class KnowledgeBase(models.Model):
    """知识库"""
    
    name = models.CharField('知识库名称', max_length=100)
    description = models.TextField('描述', blank=True)
    
    # 知识库类型
    KB_TYPE_CHOICES = [
        ('document', '文档'),
        ('faq', 'FAQ'),
        ('case', '维修案例'),
        ('manual', '手册'),
    ]
    
    kb_type = models.CharField('知识库类型', max_length=20, choices=KB_TYPE_CHOICES, default='document')
    
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_knowledge_bases')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'knowledge_bases'
        verbose_name = '知识库'
        verbose_name_plural = '知识库'
    
    def __str__(self):
        return self.name


class KnowledgeDocument(models.Model):
    """知识文档"""
    
    knowledge_base = models.ForeignKey(KnowledgeBase, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField('文档标题', max_length=200)
    
    # 内容
    content = models.TextField('文档内容')
    summary = models.TextField('摘要', blank=True)
    
    # 标签
    tags = models.CharField('标签', max_length=500, blank=True)
    
    # 关联信息
    related_equipment_models = models.CharField('关联设备型号', max_length=500, blank=True)
    related_fault_codes = models.CharField('关联故障代码', max_length=200, blank=True)
    
    # AI处理状态
    embedding_status = models.CharField('向量化状态', max_length=20, default='pending',
        choices=[
            ('pending', '待处理'),
            ('processing', '处理中'),
            ('completed', '已完成'),
            ('failed', '失败'),
        ])
    embedding_error = models.TextField('向量化错误信息', blank=True)
    
    # 统计
    view_count = models.IntegerField('查看次数', default=0)
    useful_count = models.IntegerField('点赞次数', default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_knowledge_docs')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'knowledge_documents'
        verbose_name = '知识文档'
        verbose_name_plural = '知识文档'
    
    def __str__(self):
        return self.title


class Conversation(models.Model):
    """AI对话"""
    
    USER_TYPE_CHOICES = [
        ('user', '用户'),
        ('assistant', 'AI助手'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField('对话标题', max_length=200, blank=True)
    
    # 对话类型
    CONVERSATION_TYPE_CHOICES = [
        ('chat', '智能问答'),
        ('fault_predict', '故障预判'),
        ('data_query', '数据查询'),
        ('work_order', '工单创建'),
    ]
    
    conversation_type = models.CharField('对话类型', max_length=20, choices=CONVERSATION_TYPE_CHOICES, default='chat')
    
    # 上下文
    context_data = models.JSONField('上下文数据', default=dict, blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'ai_conversations'
        verbose_name = 'AI对话'
        verbose_name_plural = 'AI对话'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title or '新对话'}"


class Message(models.Model):
    """对话消息"""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    
    # 消息内容
    role = models.CharField('角色', max_length=20, choices=Conversation.USER_TYPE_CHOICES)
    content = models.TextField('消息内容')
    
    # 附加数据
    extra_data = models.JSONField('附加数据', default=dict, blank=True)
    
    # 意图识别结果
    intent = models.CharField('意图', max_length=50, blank=True)
    entities = models.JSONField('实体', default=dict, blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'ai_messages'
        verbose_name = '对话消息'
        verbose_name_plural = '对话消息'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIConfig(models.Model):
    """AI配置"""
    
    name = models.CharField('配置名称', max_length=100)
    
    # 提供商
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('azure', 'Azure OpenAI'),
        ('local', '本地模型'),
        ('custom', '自定义'),
    ]
    
    provider = models.CharField('AI提供商', max_length=20, choices=PROVIDER_CHOICES, default='openai')
    
    # 配置
    api_key = models.CharField('API Key', max_length=200, blank=True)
    api_base = models.CharField('API Base URL', max_length=200, blank=True)
    model_name = models.CharField('模型名称', max_length=100, blank=True)
    
    # 参数配置
    temperature = models.FloatField('温度参数', default=0.7)
    max_tokens = models.IntegerField('最大令牌数', default=2000)
    
    # 向量库配置
    embedding_provider = models.CharField('Embedding提供商', max_length=50, blank=True)
    embedding_model = models.CharField('Embedding模型', max_length=50, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    is_default = models.BooleanField('设为默认', default=False)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'ai_configs'
        verbose_name = 'AI配置'
        verbose_name_plural = 'AI配置'
    
    def __str__(self):
        return f"{self.name} - {self.get_provider_display()}"


class IntentPattern(models.Model):
    """意图模式"""
    
    name = models.CharField('意图名称', max_length=100)
    intent = models.CharField('意图标识', max_length=50)
    
    # 匹配模式
    patterns = models.JSONField('匹配模式', default=list)
    
    # 响应模板
    response_template = models.TextField('响应模板', blank=True)
    
    # 关联动作
    action_type = models.CharField('动作类型', max_length=50, blank=True)
    action_config = models.JSONField('动作配置', default=dict, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'intent_patterns'
        verbose_name = '意图模式'
        verbose_name_plural = '意图模式'
    
    def __str__(self):
        return f"{self.name} ({self.intent})"
