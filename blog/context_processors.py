"""
自定义后台管理的 context processor
为所有后台模板注入侧边栏所需数据
"""
from .models import Comment


def dashboard_context(request):
    """为后台管理页面注入全局上下文"""
    if not request.path.startswith('/dashboard/') or not request.user.is_authenticated:
        return {}

    pending_comments_count = Comment.objects.filter(is_approved=False).count()

    # 根据 URL 判断当前激活的导航项
    path = request.path
    active_nav = 'dashboard'
    if '/articles' in path:
        active_nav = 'articles'
    elif '/comments' in path:
        active_nav = 'comments'
    elif '/categories-tags' in path:
        active_nav = 'categories_tags'
    elif '/apikeys' in path:
        active_nav = 'apikeys'

    return {
        'pending_comments_count': pending_comments_count,
        'active_nav': active_nav,
    }
