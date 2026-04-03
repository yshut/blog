"""
自定义后台管理视图
替代Django自带admin，提供更友好的管理界面
"""
import secrets
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta

from .models import Article, Category, Tag, Comment, ApiKey


def staff_required(view_func):
    """要求用户是staff"""
    decorated = user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='/dashboard/login/'
    )(view_func)
    return login_required(decorated, login_url='/dashboard/login/')


def admin_login(request):
    """后台登录"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard:index')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.GET.get('next', '')
            from django.utils.http import url_has_allowed_host_and_scheme
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, '用户名或密码错误，或您没有管理权限')

    return render(request, 'admin_custom/login.html')


@require_POST
def admin_logout(request):
    """后台登出"""
    logout(request)
    return redirect('dashboard:login')


@staff_required
def dashboard_index(request):
    """仪表盘首页"""
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    yesterday = now - timedelta(days=1)

    # 统计数据
    total_articles = Article.objects.count()
    published_articles = Article.objects.filter(status='published').count()
    draft_articles = Article.objects.filter(status='draft').count()
    total_views = Article.objects.aggregate(total=Sum('views'))['total'] or 0
    total_comments = Comment.objects.count()
    pending_comments = Comment.objects.filter(is_approved=False).count()
    total_categories = Category.objects.count()
    total_tags = Tag.objects.count()
    ai_articles = Article.objects.filter(is_ai_generated=True).count()

    # 本周新增
    week_articles = Article.objects.filter(created_at__gte=week_ago).count()
    week_comments = Comment.objects.filter(created_at__gte=week_ago).count()
    week_views = Article.objects.filter(created_at__gte=week_ago).aggregate(total=Sum('views'))['total'] or 0

    # 今日数据
    today_articles = Article.objects.filter(created_at__date=today).count()
    today_comments = Comment.objects.filter(created_at__date=today).count()
    today_views = Article.objects.filter(created_at__date=today).aggregate(total=Sum('views'))['total'] or 0

    # 最近文章
    recent_articles = Article.objects.select_related('author', 'category').order_by('-created_at')[:8]

    # 最近评论
    recent_comments = Comment.objects.select_related('article', 'author').order_by('-created_at')[:5]

    # 热门文章（含最大阅读量用于计算百分比）
    popular_articles = Article.objects.filter(status='published').order_by('-views')[:5]
    max_views = popular_articles[0].views if popular_articles else 1

    # 每日文章数（最近7天）
    daily_data = []
    max_daily = 1
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Article.objects.filter(created_at__date=day).count()
        if count > max_daily:
            max_daily = count
        daily_data.append({'date': day.strftime('%m-%d'), 'count': count})

    # 为每日数据计算百分比高度
    for d in daily_data:
        d['percent'] = int((d['count'] / max_daily) * 100) if max_daily > 0 else 0

    # 为热门文章计算百分比
    popular_with_percent = []
    for a in popular_articles:
        popular_with_percent.append({
            'title': a.title,
            'views': a.views,
            'slug': a.slug,
            'percent': int((a.views / max_views) * 100) if max_views > 0 else 0,
        })

    # 时间问候语
    hour = now.hour
    if 5 <= hour < 12:
        greeting = '早上好'
    elif 12 <= hour < 18:
        greeting = '下午好'
    else:
        greeting = '晚上好'

    # API密钥数
    total_apikeys = ApiKey.objects.filter(is_active=True).count()

    context = {
        'total_articles': total_articles,
        'published_articles': published_articles,
        'draft_articles': draft_articles,
        'total_views': total_views,
        'total_comments': total_comments,
        'pending_comments': pending_comments,
        'total_categories': total_categories,
        'total_tags': total_tags,
        'ai_articles': ai_articles,
        'week_articles': week_articles,
        'week_comments': week_comments,
        'week_views': week_views,
        'today_articles': today_articles,
        'today_comments': today_comments,
        'today_views': today_views,
        'recent_articles': recent_articles,
        'recent_comments': recent_comments,
        'popular_articles': popular_with_percent,
        'daily_data': daily_data,
        'greeting': greeting,
        'total_apikeys': total_apikeys,
        'current_time': now,
    }
    return render(request, 'admin_custom/dashboard.html', context)


@staff_required
def article_list(request):
    """文章管理列表"""
    articles = Article.objects.select_related('author', 'category').prefetch_related('tags')

    # 筛选
    status = request.GET.get('status', '')
    if status:
        articles = articles.filter(status=status)

    category_id = request.GET.get('category', '')
    if category_id:
        articles = articles.filter(category_id=category_id)

    is_ai = request.GET.get('is_ai', '')
    if is_ai == '1':
        articles = articles.filter(is_ai_generated=True)
    elif is_ai == '0':
        articles = articles.filter(is_ai_generated=False)

    search = request.GET.get('q', '')
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | Q(content__icontains=search) | Q(author__username__icontains=search)
        )

    articles = articles.order_by('-created_at')

    paginator = Paginator(articles, 15)
    page = request.GET.get('page', 1)
    articles = paginator.get_page(page)

    categories = Category.objects.all()

    context = {
        'articles': articles,
        'categories': categories,
        'current_status': status,
        'current_category': category_id,
        'current_is_ai': is_ai,
        'search_query': search,
    }
    return render(request, 'admin_custom/articles.html', context)


@staff_required
@require_POST
def article_action(request):
    """文章批量操作"""
    action = request.POST.get('action', '')
    ids = request.POST.getlist('ids')

    if not ids:
        return JsonResponse({'error': '请选择文章'}, status=400)

    articles = Article.objects.filter(id__in=ids)

    if action == 'publish':
        articles.update(status='published', published_at=timezone.now())
        return JsonResponse({'message': f'已发布 {articles.count()} 篇文章'})
    elif action == 'draft':
        articles.update(status='draft')
        return JsonResponse({'message': f'已设为草稿 {articles.count()} 篇文章'})
    elif action == 'delete':
        count = articles.count()
        articles.delete()
        return JsonResponse({'message': f'已删除 {count} 篇文章'})
    elif action == 'toggle_top':
        for a in articles:
            a.is_top = not a.is_top
            a.save(update_fields=['is_top'])
        return JsonResponse({'message': f'已切换 {articles.count()} 篇文章的置顶状态'})

    return JsonResponse({'error': '未知操作'}, status=400)


@staff_required
@require_POST
def article_quick_action(request, article_id):
    """单篇文章快捷操作"""
    article = get_object_or_404(Article, id=article_id)
    action = request.POST.get('action', '')

    if action == 'toggle_status':
        if article.status == 'published':
            article.status = 'draft'
        else:
            article.status = 'published'
            if not article.published_at:
                article.published_at = timezone.now()
        article.save(update_fields=['status', 'published_at'])
        return JsonResponse({'status': article.status})
    elif action == 'toggle_top':
        article.is_top = not article.is_top
        article.save(update_fields=['is_top'])
        return JsonResponse({'is_top': article.is_top})
    elif action == 'delete':
        article.delete()
        return JsonResponse({'message': '已删除'})

    return JsonResponse({'error': '未知操作'}, status=400)


@staff_required
def comment_list(request):
    """评论管理"""
    comments = Comment.objects.select_related('article', 'author').order_by('-created_at')

    status = request.GET.get('status', '')
    if status == 'pending':
        comments = comments.filter(is_approved=False)
    elif status == 'approved':
        comments = comments.filter(is_approved=True)

    search = request.GET.get('q', '')
    if search:
        comments = comments.filter(
            Q(content__icontains=search) | Q(nickname__icontains=search) | Q(article__title__icontains=search)
        )

    paginator = Paginator(comments, 20)
    page = request.GET.get('page', 1)
    comments = paginator.get_page(page)

    pending_count = Comment.objects.filter(is_approved=False).count()

    context = {
        'comments': comments,
        'current_status': status,
        'search_query': search,
        'pending_count': pending_count,
    }
    return render(request, 'admin_custom/comments.html', context)


@staff_required
@require_POST
def comment_action(request):
    """评论批量操作"""
    action = request.POST.get('action', '')
    ids = request.POST.getlist('ids')

    if not ids:
        return JsonResponse({'error': '请选择评论'}, status=400)

    comments = Comment.objects.filter(id__in=ids)

    if action == 'approve':
        comments.update(is_approved=True)
        return JsonResponse({'message': f'已审核通过 {comments.count()} 条评论'})
    elif action == 'reject':
        comments.update(is_approved=False)
        return JsonResponse({'message': f'已驳回 {comments.count()} 条评论'})
    elif action == 'delete':
        count = comments.count()
        comments.delete()
        return JsonResponse({'message': f'已删除 {count} 条评论'})

    return JsonResponse({'error': '未知操作'}, status=400)


@staff_required
@require_POST
def comment_quick_action(request, comment_id):
    """单条评论快捷操作"""
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action', '')

    if action == 'toggle_approve':
        comment.is_approved = not comment.is_approved
        comment.save(update_fields=['is_approved'])
        return JsonResponse({'is_approved': comment.is_approved})
    elif action == 'delete':
        comment.delete()
        return JsonResponse({'message': '已删除'})

    return JsonResponse({'error': '未知操作'}, status=400)


@staff_required
def category_tag_manage(request):
    """分类和标签管理"""
    categories = Category.objects.annotate(
        article_count=Count('articles', filter=Q(articles__status='published'))
    ).order_by('name')

    tags = Tag.objects.annotate(
        article_count=Count('articles', filter=Q(articles__status='published'))
    ).order_by('name')

    context = {
        'categories': categories,
        'tags': tags,
    }
    return render(request, 'admin_custom/categories_tags.html', context)


@staff_required
@require_POST
def category_create(request):
    """创建分类"""
    name = request.POST.get('name', '').strip()
    slug = request.POST.get('slug', '').strip()
    description = request.POST.get('description', '').strip()

    if not name or not slug:
        return JsonResponse({'error': '名称和别名不能为空'}, status=400)

    if Category.objects.filter(slug=slug).exists():
        return JsonResponse({'error': '该别名已存在'}, status=400)

    cat = Category.objects.create(name=name, slug=slug, description=description)
    return JsonResponse({'message': f'分类「{cat.name}」创建成功', 'id': cat.id})


@staff_required
@require_POST
def category_delete(request, category_id):
    """删除分类"""
    cat = get_object_or_404(Category, id=category_id)
    name = cat.name
    cat.delete()
    return JsonResponse({'message': f'分类「{name}」已删除'})


@staff_required
@require_POST
def tag_create(request):
    """创建标签"""
    name = request.POST.get('name', '').strip()
    slug = request.POST.get('slug', '').strip()

    if not name or not slug:
        return JsonResponse({'error': '名称和别名不能为空'}, status=400)

    if Tag.objects.filter(slug=slug).exists():
        return JsonResponse({'error': '该别名已存在'}, status=400)

    tag = Tag.objects.create(name=name, slug=slug)
    return JsonResponse({'message': f'标签「{tag.name}」创建成功', 'id': tag.id})


@staff_required
@require_POST
def tag_delete(request, tag_id):
    """删除标签"""
    tag = get_object_or_404(Tag, id=tag_id)
    name = tag.name
    tag.delete()
    return JsonResponse({'message': f'标签「{name}」已删除'})


@staff_required
def apikey_manage(request):
    """API密钥管理"""
    keys = ApiKey.objects.select_related('user').order_by('-created_at')

    context = {
        'keys': keys,
    }
    return render(request, 'admin_custom/apikeys.html', context)


@staff_required
@require_POST
def apikey_create(request):
    """创建API密钥"""
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    can_create = request.POST.get('can_create') == '1'
    can_update = request.POST.get('can_update') == '1'
    can_delete = request.POST.get('can_delete') == '1'

    if not name:
        return JsonResponse({'error': '密钥名称不能为空'}, status=400)

    key_str = secrets.token_hex(32)
    key = ApiKey.objects.create(
        name=name,
        key=key_str,
        user=request.user,
        description=description,
        can_create_article=can_create,
        can_update_article=can_update,
        can_delete_article=can_delete,
    )
    return JsonResponse({'message': f'密钥「{name}」创建成功', 'key': key_str, 'id': key.id})


@staff_required
@require_POST
def apikey_toggle(request, key_id):
    """启用/禁用API密钥"""
    key = get_object_or_404(ApiKey, id=key_id)
    key.is_active = not key.is_active
    key.save(update_fields=['is_active'])
    return JsonResponse({'is_active': key.is_active})


@staff_required
@require_POST
def apikey_delete(request, key_id):
    """删除API密钥"""
    key = get_object_or_404(ApiKey, id=key_id)
    key.delete()
    return JsonResponse({'message': '密钥已删除'})
