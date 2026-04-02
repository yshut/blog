# 咨询博客系统 - AI资讯聚合

一个基于 Django 的博客系统，支持用户注册登录、富文本编辑、评论功能，以及 **AI通过API自动发布资讯文章**。

主要用途：AI自动搜索实时资讯、新闻文章，生成摘要后自动发布到博客。

## 功能特性

- 🤖 **AI资讯聚合** - AI自动搜索并总结实时资讯、新闻文章
- 📝 **文章管理** - 创建、编辑、删除文章
- 🏷️ **分类和标签** - 文章分类和标签管理（科技、财经、新闻、行业等）
- 💬 **评论系统** - 支持登录用户和访客评论
- 🔐 **用户认证** - 注册、登录、个人中心
- 🎨 **富文本编辑器** - TinyMCE 编辑器
- 🤖 **AI发布接口** - API接口支持AI自动发布文章（含来源链接、AI摘要）

## 新增：AI资讯字段

- `source_url` - 原始资讯链接
- `source_name` - 来源网站名称（如"新浪财经"、"36氪"）
- `summary` - AI生成的资讯摘要
- `published_time` - 原始发布时间

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
pip install djangorestframework django-tinymce Pillow bleach markdown
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
- `source`: 按来源名称筛选（如 `source=36氪`）
- `date_from`: 筛选原始发布时间（格式：YYYY-MM-DD）
- `date_to`: 筛选原始发布时间截止（格式：YYYY-MM-DD）
- `page`: 页码
- `page_size`: 每页数量

#### 3. 获取文章详情

```
GET /api/articles/<slug>/
```

#### 4. 创建文章（支持AI资讯）

```
POST /api/articles/
```

请求体：
```json
{
    "title": "AI重塑新闻行业：传统媒体加速转型",
    "content": "<p>文章正文内容...</p>",
    "source_url": "https://www.36kr.com/p/123456789",
    "source_name": "36氪",
    "summary": "AI正在深刻改变新闻行业格局，传统媒体加速数字化转型，AI写稿、智能编辑成为新趋势。",
    "published_time": "2026-04-02T10:30:00",
    "category_name": "科技动态",
    "tag_names": ["AI", "新闻", "数字化转型"],
    "excerpt": "文章摘要",
    "status": "published",
    "ai_source": "Claude"
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

### Python示例（AI发布资讯）

```python
import requests
from datetime import datetime

API_URL = "http://localhost:8000/api/articles/"
API_KEY = "your-api-key-here"

# 创建AI资讯文章
article_data = {
    "title": "AI重塑新闻行业：传统媒体加速转型",
    "content": "<h2>行业现状</h2><p>随着AI技术的快速发展...</p>",
    "source_url": "https://www.36kr.com/p/123456789",
    "source_name": "36氪",
    "summary": "AI正在深刻改变新闻行业格局，传统媒体加速数字化转型，AI写稿、智能编辑成为新趋势。",
    "published_time": "2026-04-02T10:30:00",
    "category_name": "科技动态",
    "tag_names": ["AI", "新闻", "数字化转型"],
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
# 创建AI资讯文章
curl -X POST http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI重塑新闻行业",
    "content": "<p>文章内容...</p>",
    "source_url": "https://www.36kr.com/p/123456789",
    "source_name": "36氪",
    "summary": "AI正在改变新闻行业...",
    "status": "published",
    "ai_source": "Claude"
  }'

# 筛选AI生成的资讯
curl -X GET "http://localhost:8000/api/articles/?is_ai=true" \
  -H "Authorization: Bearer your-api-key"

# 筛选特定来源的资讯
curl -X GET "http://localhost:8000/api/articles/?source=36氪" \
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
