# 咨询博客系统

一个基于 Django 的博客系统，支持用户注册登录、富文本编辑、评论功能，以及 **AI通过API自动发布文章**。

## 功能特性

- 📝 **文章管理** - 创建、编辑、删除文章
- 🏷️ **分类和标签** - 文章分类和标签管理
- 💬 **评论系统** - 支持登录用户和访客评论
- 🔐 **用户认证** - 注册、登录、个人中心
- 🎨 **富文本编辑器** - TinyMCE 编辑器
- 🤖 **AI发布接口** - API接口支持AI自动发布文章

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install djangorestframework django-tinymce Pillow
```

### 2. 配置数据库

编辑 `blog_project/settings.py`，修改MySQL配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'blog_db',
        'USER': 'root',
        'PASSWORD': 'your_password',  # 修改为你的密码
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

或者使用SQLite（开发环境）：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 3. 初始化数据库

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级管理员

```bash
python manage.py createsuperuser
```

### 5. 运行服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 查看博客

## API接口文档

### 认证方式

所有API请求需要在Header中携带API Key：

```
Authorization: Bearer <your_api_key>
```

或者在URL参数中传递：

```
?api_key=<your_api_key>
```

### 创建API Key

1. 登录管理员后台：http://127.0.0.1:8000/admin/
2. 进入 "API密钥" 管理
3. 创建新的API Key，设置权限

### API端点

#### 1. 检查API状态

```
GET /api/status/
```

无需认证，返回API运行状态。

#### 2. 获取文章列表

```
GET /api/articles/
```

参数：
- `status`: 筛选状态 (published/draft)
- `category`: 按分类slug筛选
- `tag`: 按标签slug筛选
- `is_ai`: 筛选AI生成的文章 (true/false)
- `page`: 页码
- `page_size`: 每页数量

#### 3. 获取文章详情

```
GET /api/articles/<slug>/
```

#### 4. 创建文章

```
POST /api/articles/
```

请求体：
```json
{
    "title": "文章标题",
    "content": "文章内容（支持HTML）",
    "category_name": "技术",        // 可选，分类名称
    "tag_names": ["Python", "Django"],  // 可选，标签名称数组
    "excerpt": "文章摘要",          // 可选
    "status": "published",          // published 或 draft
    "is_ai_generated": true,        // 默认true
    "ai_source": "Claude"           // AI来源标识
}
```

#### 5. 更新文章

```
PUT /api/articles/<slug>/
```

请求体同创建文章，所有字段可选。

#### 6. 删除文章

```
DELETE /api/articles/<slug>/
```

#### 7. 获取分类列表

```
GET /api/categories/
```

#### 8. 获取标签列表

```
GET /api/tags/
```

## 使用示例

### Python示例（AI发布文章）

```python
import requests

API_URL = "http://localhost:8000/api/articles/"
API_KEY = "your-api-key-here"

# 创建文章
article_data = {
    "title": "AI生成的文章示例",
    "content": "<h1>这是一篇由AI生成的文章</h1><p>内容可以包含HTML标签...</p>",
    "category_name": "AI技术",
    "tag_names": ["AI", "Python"],
    "status": "published",
    "ai_source": "Claude"
}

response = requests.post(
    API_URL,
    json=article_data,
    headers={"Authorization": f"Bearer {API_KEY}"}
)

print(response.json())
```

### cURL示例

```bash
# 创建文章
curl -X POST http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "content": "这是文章内容",
    "status": "published"
  }'

# 获取文章列表
curl -X GET "http://localhost:8000/api/articles/" \
  -H "Authorization: Bearer your-api-key"
```

## 项目结构

```
blog/
├── blog/                  # 博客应用
│   ├── __init__.py
│   ├── admin.py          # 管理后台配置
│   ├── api_urls.py       # API路由
│   ├── api_views.py      # API视图
│   ├── forms.py          # 表单
│   ├── models.py         # 数据模型
│   ├── urls.py           # 前端路由
│   └── views.py          # 前端视图
├── blog_project/         # 项目配置
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py       # 设置
│   ├── urls.py           # 主路由
│   └── wsgi.py
├── templates/            # 模板文件
│   ├── base.html        # 基础模板
│   └── blog/
│       ├── index.html
│       ├── article_detail.html
│       ├── article_form.html
│       ├── login.html
│       ├── register.html
│       └── profile.html
├── static/               # 静态文件
├── media/                # 上传文件
├── manage.py
├── requirements.txt
└── README.md
```

## 许可证

MIT License
