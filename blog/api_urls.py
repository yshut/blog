"""
API URL配置

使用方式:

1. 创建文章:
   POST /api/articles/
   Headers: Authorization: Bearer <your_api_key>
   Body: {
       "title": "文章标题",
       "content": "文章内容（支持Markdown或HTML）",
       "category_name": "分类名称",  # 可选
       "tag_names": ["标签1", "标签2"],  # 可选
       "excerpt": "文章摘要",  # 可选
       "status": "published",  # published 或 draft
       "is_ai_generated": true,  # 默认为true
       "ai_source": "Claude"  # AI来源标识
   }

2. 获取文章列表:
   GET /api/articles/
   Headers: Authorization: Bearer <your_api_key>
   Query参数: status, category, tag, is_ai, page, page_size

3. 获取文章详情:
   GET /api/articles/<slug>/
   Headers: Authorization: Bearer <your_api_key>

4. 更新文章:
   PUT /api/articles/<slug>/
   Headers: Authorization: Bearer <your_api_key>

5. 删除文章:
   DELETE /api/articles/<slug>/
   Headers: Authorization: Bearer <your_api_key>
"""

from django.urls import path
from .api_views import ArticleAPIView, CategoryAPIView, TagAPIView, APIStatusView

urlpatterns = [
    path('status/', APIStatusView.as_view(), name='api_status'),
    path('articles/', ArticleAPIView.as_view(), name='article_list'),
    path('articles/<slug:slug>/', ArticleAPIView.as_view(), name='article_detail'),
    path('categories/', CategoryAPIView.as_view(), name='category_list'),
    path('tags/', TagAPIView.as_view(), name='tag_list'),
]
