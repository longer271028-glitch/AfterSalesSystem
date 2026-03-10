# 武汉禾大科技售后服务系统

## 项目简介

构建智能协同的售后服务新生态——武汉禾大科技售后服务系统设计与实现

## 技术栈

- **后端**: Python 3.10+ / Django 4.2+ / Django REST Framework
- **数据库**: SQLite (开发) / MySQL (生产)
- **前端**: Bootstrap 5 + jQuery + Vue.js 3
- **AI能力**: OpenAI API / 本地LLM集成

## 项目结构

```
AfterSalesSystem/
├── apps/                      # 应用模块
│   ├── customers/            # 客户管理
│   ├── faults/               # 故障管理
│   ├── repairs/              # 返修流程
│   ├── inventory/            # 库存管理
│   ├── logistics/            # 物流管理
│   ├── quotes/               # 报价管理
│   ├── workflows/            # 流程引擎
│   ├── analytics/             # 数据分析
│   └── ai_assistant/         # AI智能助手
├── core/                     # 核心模块
│   ├── settings.py           # Django配置
│   ├── urls.py               # 路由配置
│   └── wsgi.py               # WSGI入口
├── static/                   # 静态文件
├── templates/                # 模板文件
└── manage.py                 # 管理脚本
```

## 核心功能

### 1. 故障问题管理
- 多渠道故障上报
- 状态跟踪与闭环管理
- 关联解决方案库

### 2. 故障产品返修流程
- 接收→入库→检测→报价→维修→质检→出库
- 过程留痕与可追溯

### 3. 产品出入库管理
- 零配件/半成品/成品三类物资
- 库存盘点与动态管控

### 4. 物流信息管理
- 快递API对接
- 物流状态自动更新

### 5. 维修报价管理
- 多维度报价模型
- 报价审批流程

### 6. 客户管理
- 客户档案与分类
- 标签管理与服务历史

### 7. AI智能能力
- 自然语言对话交互
- 智能故障预判
- 知识库自学习
- 异常数据识别

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
```bash
cp .env.example .env
# 编辑 .env 配置数据库等
```

### 3. 初始化数据库
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. 启动服务
```bash
python manage.py runserver
```

## API文档

启动服务后访问: `http://localhost:8000/api/docs/`

## 许可证

MIT License
