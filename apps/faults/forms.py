from django import forms
from .models import FaultCategory, FaultReport, FaultImage, FaultComment, Solution


class FaultReportForm(forms.ModelForm):
    """故障上报表单 - 简化版"""

    class Meta:
        model = FaultReport
        fields = ['fault_no', 'title', 'description', 'customer', 'equipment_sn', 'equipment_name',
                  'fault_category', 'reporter_name', 'reporter_phone', 'status', 'priority', 'solution']
        widgets = {
            'fault_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入故障问题'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': '请描述故障情况'}),
            'equipment_sn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入设备序列号'}),
            'equipment_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入设备名称'}),
            'reporter_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入上报人姓名'}),
            'reporter_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入联系电话'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'fault_category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'solution': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': '请输入处理方案描述'}),
        }


class FaultCategoryForm(forms.ModelForm):
    """故障分类表单"""

    class Meta:
        model = FaultCategory
        fields = ['code', 'name', 'description', 'parent']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入故障代码'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入故障分类名称'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '请输入描述'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }


class FaultImageForm(forms.ModelForm):
    """故障图片表单"""

    class Meta:
        model = FaultImage
        fields = ['fault', 'image', 'description']
        widgets = {
            'fault': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入图片描述'}),
        }


class FaultCommentForm(forms.ModelForm):
    """故障备注表单"""

    class Meta:
        model = FaultComment
        fields = ['fault', 'content']
        widgets = {
            'fault': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': '请输入备注内容'}),
        }


class SolutionForm(forms.ModelForm):
    """解决方案表单"""

    class Meta:
        model = Solution
        fields = ['title', 'fault_category', 'description', 'steps', 'applicable_models',
                  'use_count', 'success_rate', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入解决方案标题'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': '请输入解决方案描述'}),
            'steps': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': '步骤用换行分隔'}),
            'applicable_models': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '多个型号用逗号分隔'}),
            'fault_category': forms.Select(attrs={'class': 'form-select'}),
            'use_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'success_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

