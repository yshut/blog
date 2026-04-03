from django.urls import path
from . import admin_views

app_name = 'dashboard'

urlpatterns = [
    path('login/', admin_views.admin_login, name='login'),
    path('logout/', admin_views.admin_logout, name='logout'),
    path('', admin_views.dashboard_index, name='index'),

    # 文章管理
    path('articles/', admin_views.article_list, name='articles'),
    path('articles/action/', admin_views.article_action, name='article_action'),
    path('articles/<int:article_id>/action/', admin_views.article_quick_action, name='article_quick_action'),

    # 评论管理
    path('comments/', admin_views.comment_list, name='comments'),
    path('comments/action/', admin_views.comment_action, name='comment_action'),
    path('comments/<int:comment_id>/action/', admin_views.comment_quick_action, name='comment_quick_action'),

    # 分类标签管理
    path('categories-tags/', admin_views.category_tag_manage, name='categories_tags'),
    path('categories/create/', admin_views.category_create, name='category_create'),
    path('categories/<int:category_id>/delete/', admin_views.category_delete, name='category_delete'),
    path('tags/create/', admin_views.tag_create, name='tag_create'),
    path('tags/<int:tag_id>/delete/', admin_views.tag_delete, name='tag_delete'),

    # API密钥管理
    path('apikeys/', admin_views.apikey_manage, name='apikeys'),
    path('apikeys/create/', admin_views.apikey_create, name='apikey_create'),
    path('apikeys/<int:key_id>/toggle/', admin_views.apikey_toggle, name='apikey_toggle'),
    path('apikeys/<int:key_id>/delete/', admin_views.apikey_delete, name='apikey_delete'),
]
