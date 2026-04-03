from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import Category, Tag, Article, Comment, ApiKey


# Customize Admin Site
admin.site.site_header = 'NewsFlow 管理后台'
admin.site.site_title = 'NewsFlow Admin'
admin.site.index_title = '资讯管理中心'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'article_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 20

    def article_count(self, obj):
        count = obj.articles.filter(status='published').count()
        return format_html(
            '<span style="background: #e0e7ff; color: #4338ca; padding: 2px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: 600;">{}</span>',
            count
        )
    article_count.short_description = '文章数'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'article_count', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_per_page = 20

    def article_count(self, obj):
        count = obj.articles.filter(status='published').count()
        return format_html(
            '<span style="background: #dbeafe; color: #1d4ed8; padding: 2px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: 600;">{}</span>',
            count
        )
    article_count.short_description = '文章数'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title_display', 'author', 'category', 'status_display',
        'is_top_display', 'views_display', 'ai_display', 'source_display', 'created_at'
    ]
    list_filter = ['status', 'category', 'is_top', 'is_ai_generated', 'created_at']
    search_fields = ['title', 'content', 'author__username', 'source_name']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 20
    list_editable = []
    actions = ['make_published', 'make_draft', 'toggle_top']

    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'author', 'category', 'tags'),
            'description': '文章的基本信息设置'
        }),
        ('内容', {
            'fields': ('content', 'excerpt', 'cover_image'),
            'description': '文章正文和摘要'
        }),
        ('发布设置', {
            'fields': ('status', 'is_top', 'allow_comment', 'published_at'),
            'description': '控制文章的发布状态'
        }),
        ('AI & 资讯来源', {
            'fields': ('is_ai_generated', 'ai_source', 'source_url', 'source_name', 'summary', 'published_time'),
            'classes': ('collapse',),
            'description': 'AI生成和资讯来源相关信息'
        }),
    )

    def title_display(self, obj):
        title = obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
        return format_html(
            '<strong style="color: #1e293b;">{}</strong>',
            title
        )
    title_display.short_description = '标题'
    title_display.admin_order_field = 'title'

    def status_display(self, obj):
        if obj.status == 'published':
            return format_html(
                '<span style="background: #dcfce7; color: #166534; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">已发布</span>'
            )
        return format_html(
            '<span style="background: #fef3c7; color: #92400e; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">草稿</span>'
        )
    status_display.short_description = '状态'
    status_display.admin_order_field = 'status'

    def is_top_display(self, obj):
        if obj.is_top:
            return format_html(
                '<span style="background: #fef3c7; color: #d97706; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">'
                '<i class="fas fa-thumbtack"></i> 置顶</span>'
            )
        return '-'
    is_top_display.short_description = '置顶'

    def views_display(self, obj):
        return format_html(
            '<span style="color: #6366f1; font-weight: 600;">{}</span>',
            obj.views
        )
    views_display.short_description = '阅读'
    views_display.admin_order_field = 'views'

    def ai_display(self, obj):
        if obj.is_ai_generated:
            return format_html(
                '<span style="background: #ede9fe; color: #7c3aed; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">'
                'AI {}</span>',
                obj.ai_source or ''
            )
        return '-'
    ai_display.short_description = 'AI'

    def source_display(self, obj):
        if obj.source_name:
            return format_html(
                '<span style="background: #d1fae5; color: #065f46; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
                obj.source_name
            )
        return '-'
    source_display.short_description = '来源'

    def make_published(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'成功发布 {updated} 篇文章')
    make_published.short_description = '发布选中的文章'

    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'已将 {updated} 篇文章设为草稿')
    make_draft.short_description = '设为草稿'

    def toggle_top(self, request, queryset):
        for article in queryset:
            article.is_top = not article.is_top
            article.save(update_fields=['is_top'])
        self.message_user(request, f'已切换 {queryset.count()} 篇文章的置顶状态')
    toggle_top.short_description = '切换置顶状态'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['comment_preview', 'author_display', 'article_link', 'is_approved_display', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'nickname', 'article__title']
    actions = ['approve_comments', 'disapprove_comments']
    list_per_page = 20

    def comment_preview(self, obj):
        content = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return format_html('<span style="color: #475569;">{}</span>', content)
    comment_preview.short_description = '评论内容'

    def author_display(self, obj):
        name = obj.author.username if obj.author else obj.nickname
        return format_html(
            '<span style="font-weight: 600; color: #1e293b;">{}</span>',
            name
        )
    author_display.short_description = '评论者'

    def article_link(self, obj):
        return format_html(
            '<a href="/admin/blog/article/{}/change/" style="color: #6366f1; text-decoration: none;">{}</a>',
            obj.article.id,
            obj.article.title[:30]
        )
    article_link.short_description = '所属文章'

    def is_approved_display(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="background: #dcfce7; color: #166534; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">已审核</span>'
            )
        return format_html(
            '<span style="background: #fee2e2; color: #991b1b; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">待审核</span>'
        )
    is_approved_display.short_description = '审核状态'

    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'已审核通过 {updated} 条评论')
    approve_comments.short_description = '审核通过所选评论'

    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'已取消审核 {updated} 条评论')
    disapprove_comments.short_description = '取消审核所选评论'


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status_display', 'permissions_display', 'created_at', 'last_used_display']
    list_filter = ['is_active', 'can_create_article', 'can_update_article', 'can_delete_article']
    search_fields = ['name', 'user__username', 'key']
    readonly_fields = ['key', 'created_at', 'last_used_at']
    list_per_page = 20

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'key', 'user', 'description'),
            'description': 'API密钥基本信息'
        }),
        ('权限设置', {
            'fields': ('can_create_article', 'can_update_article', 'can_delete_article'),
            'description': '控制此API密钥可以执行的操作'
        }),
        ('状态', {
            'fields': ('is_active', 'expires_at', 'created_at', 'last_used_at'),
            'description': '密钥的有效状态'
        }),
    )

    def status_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background: #dcfce7; color: #166534; padding: 3px 10px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">有效</span>'
            )
        return format_html(
            '<span style="background: #fee2e2; color: #991b1b; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">已禁用</span>'
        )
    status_display.short_description = '状态'

    def permissions_display(self, obj):
        perms = []
        if obj.can_create_article:
            perms.append('创建')
        if obj.can_update_article:
            perms.append('更新')
        if obj.can_delete_article:
            perms.append('删除')
        if not perms:
            return format_html('<span style="color: #94a3b8;">无权限</span>')
        return format_html(
            '<span style="background: #e0e7ff; color: #4338ca; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            ' / '.join(perms)
        )
    permissions_display.short_description = '权限'

    def last_used_display(self, obj):
        if obj.last_used_at:
            return format_html(
                '<span style="color: #6366f1;">{}</span>',
                obj.last_used_at.strftime('%Y-%m-%d %H:%M')
            )
        return format_html('<span style="color: #94a3b8;">从未使用</span>')
    last_used_display.short_description = '最后使用'
