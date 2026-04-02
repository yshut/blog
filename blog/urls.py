from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 首页和文章
    path('', views.index, name='index'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('article/new/', views.create_article, name='create_article'),
    path('article/<slug:slug>/edit/', views.update_article, name='update_article'),
    path('article/<slug:slug>/delete/', views.delete_article, name='delete_article'),

    # 分类和标签
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('tag/<slug:slug>/', views.tag_view, name='tag'),

    # 评论
    path('article/<int:article_id>/comment/', views.add_comment, name='add_comment'),

    # 用户认证
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
]
