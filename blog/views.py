from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
import json

from .models import Article, Category, Tag, Comment
from .forms import (
    UserRegisterForm, UserLoginForm, ArticleForm,
    CommentForm, GuestCommentForm
)


def index(request):
    """首页 - 文章列表"""
    articles = Article.objects.filter(status='published')

    # 搜索功能
    search_query = request.GET.get('q', '')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # 分类筛选
    category_slug = request.GET.get('category', '')
    if category_slug:
        articles = articles.filter(category__slug=category_slug)

    # 标签筛选
    tag_slug = request.GET.get('tag', '')
    if tag_slug:
        articles = articles.filter(tags__slug=tag_slug)

    # 分页
    paginator = Paginator(articles, 10)
    page = request.GET.get('page', 1)
    articles = paginator.get_page(page)

    categories = Category.objects.all()
    tags = Tag.objects.all()

    context = {
        'articles': articles,
        'categories': categories,
        'tags': tags,
        'search_query': search_query,
        'current_category': category_slug,
        'current_tag': tag_slug,
    }
    return render(request, 'blog/index.html', context)


def article_detail(request, slug):
    """文章详情页"""
    article = get_object_or_404(Article, slug=slug, status='published')
    article.increase_views()

    # 获取评论
    comments = article.comments.filter(is_approved=True, parent__isnull=True)

    # 评论表单
    if request.user.is_authenticated:
        comment_form = CommentForm()
    else:
        comment_form = GuestCommentForm()

    context = {
        'article': article,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'blog/article_detail.html', context)


def category_view(request, slug):
    """分类页面"""
    category = get_object_or_404(Category, slug=slug)
    articles = Article.objects.filter(category=category, status='published')

    paginator = Paginator(articles, 10)
    page = request.GET.get('page', 1)
    articles = paginator.get_page(page)

    context = {
        'category': category,
        'articles': articles,
    }
    return render(request, 'blog/category.html', context)


def tag_view(request, slug):
    """标签页面"""
    tag = get_object_or_404(Tag, slug=slug)
    articles = Article.objects.filter(tags=tag, status='published')

    paginator = Paginator(articles, 10)
    page = request.GET.get('page', 1)
    articles = paginator.get_page(page)

    context = {
        'tag': tag,
        'articles': articles,
    }
    return render(request, 'blog/tag.html', context)


@login_required
def create_article(request):
    """创建文章"""
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            form.save_m2m()  # 保存多对多关系（标签）
            messages.success(request, '文章创建成功！')
            return redirect('blog:article_detail', slug=article.slug)
    else:
        form = ArticleForm()

    return render(request, 'blog/article_form.html', {'form': form, 'title': '创建文章'})


@login_required
def update_article(request, slug):
    """更新文章"""
    article = get_object_or_404(Article, slug=slug, author=request.user)

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, '文章更新成功！')
            return redirect('blog:article_detail', slug=article.slug)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'blog/article_form.html', {'form': form, 'title': '编辑文章', 'article': article})


@login_required
def delete_article(request, slug):
    """删除文章"""
    article = get_object_or_404(Article, slug=slug, author=request.user)

    if request.method == 'POST':
        article.delete()
        messages.success(request, '文章已删除！')
        return redirect('blog:index')

    return render(request, 'blog/article_confirm_delete.html', {'article': article})


@require_POST
def add_comment(request, article_id):
    """添加评论"""
    article = get_object_or_404(Article, id=article_id)

    if not article.allow_comment:
        return JsonResponse({'error': '该文章已关闭评论'}, status=403)

    parent_id = request.POST.get('parent_id')

    if request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            comment.author = request.user
            if parent_id:
                comment.parent_id = parent_id
            comment.save()
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                }
            })
    else:
        form = GuestCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = article
            if parent_id:
                comment.parent_id = parent_id
            comment.ip_address = request.META.get('REMOTE_ADDR')
            comment.save()
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author': comment.nickname,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                }
            })

    return JsonResponse({'error': form.errors}, status=400)


def register(request):
    """用户注册"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！欢迎加入我们！')
            return redirect('blog:index')
    else:
        form = UserRegisterForm()

    return render(request, 'blog/register.html', {'form': form})


def user_login(request):
    """用户登录"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            from django.contrib.auth import authenticate
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{user.username}！')
                next_url = request.GET.get('next', 'blog:index')
                return redirect(next_url)
            else:
                messages.error(request, '用户名或密码错误！')
    else:
        form = UserLoginForm()

    return render(request, 'blog/login.html', {'form': form})


def user_logout(request):
    """用户登出"""
    logout(request)
    messages.success(request, '已退出登录！')
    return redirect('blog:index')


@login_required
def user_profile(request):
    """用户个人中心"""
    user_articles = Article.objects.filter(author=request.user)
    user_comments = Comment.objects.filter(author=request.user)

    context = {
        'user_articles': user_articles,
        'user_comments': user_comments,
    }
    return render(request, 'blog/profile.html', context)
