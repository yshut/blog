from django.contrib import admin
from .models import Category, Tag, Article, Comment, ApiKey


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_top', 'views', 'created_at', 'is_ai_generated']
    list_filter = ['status', 'category', 'is_top', 'is_ai_generated', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'author', 'category', 'tags')
        }),
        ('内容', {
            'fields': ('content', 'excerpt', 'cover_image')
        }),
        ('状态设置', {
            'fields': ('status', 'is_top', 'allow_comment')
        }),
        ('AI信息', {
            'fields': ('is_ai_generated', 'ai_source'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'article', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'nickname', 'article__title']
    actions = ['approve_comments', 'disapprove_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = '审核通过所选评论'

    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_comments.short_description = '取消审核所选评论'


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'can_create_article', 'created_at', 'last_used_at']
    list_filter = ['is_active', 'can_create_article', 'can_update_article', 'can_delete_article']
    search_fields = ['name', 'user__username', 'key']
    readonly_fields = ['key', 'created_at', 'last_used_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'key', 'user', 'description')
        }),
        ('权限设置', {
            'fields': ('can_create_article', 'can_update_article', 'can_delete_article')
        }),
        ('状态', {
            'fields': ('is_active', 'expires_at', 'created_at', 'last_used_at')
        }),
    )
