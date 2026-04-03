from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import markdown
from bleach import clean


class Category(models.Model):
    """文章分类"""
    name = models.CharField('分类名称', max_length=100, unique=True)
    slug = models.SlugField('URL别名', max_length=100, unique=True)
    description = models.TextField('分类描述', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', args=[self.slug])


class Tag(models.Model):
    """文章标签"""
    name = models.CharField('标签名称', max_length=50, unique=True)
    slug = models.SlugField('URL别名', max_length=50, unique=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag', args=[self.slug])


class Article(models.Model):
    """文章模型"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
    )

    title = models.CharField('标题', max_length=200)
    slug = models.SlugField('URL别名', max_length=200, unique=True, blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='作者'
    )
    content = models.TextField('文章内容')
    content_html = models.TextField('HTML内容', blank=True)
    excerpt = models.TextField('摘要', max_length=500, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='articles',
        verbose_name='分类'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles', verbose_name='标签')

    cover_image = models.ImageField('封面图片', upload_to='articles/%Y/%m/', blank=True, null=True)

    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)
    views = models.PositiveIntegerField('阅读量', default=0)
    likes = models.PositiveIntegerField('点赞数', default=0)

    is_top = models.BooleanField('置顶', default=False, db_index=True)
    allow_comment = models.BooleanField('允许评论', default=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    published_at = models.DateTimeField('发布时间', null=True, blank=True)

    # AI发布标记
    is_ai_generated = models.BooleanField('AI生成', default=False)
    ai_source = models.CharField('AI来源', max_length=100, blank=True)

    # 资讯相关字段
    source_url = models.URLField('原始链接', max_length=500, blank=True, null=True, help_text='原始资讯URL')
    source_name = models.CharField('来源名称', max_length=100, blank=True, help_text='如：新浪财经、36氪')
    summary = models.TextField('AI摘要', blank=True, help_text='AI生成的资讯摘要')
    published_time = models.DateTimeField('原始发布时间', null=True, blank=True, help_text='原文发布时间')

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'
        ordering = ['-is_top', '-created_at']
        indexes = [
            models.Index(fields=['-is_top', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 自动生成slug
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)[:200]
            # 确保唯一性
            counter = 1
            while Article.objects.filter(slug=self.slug).exists():
                self.slug = f"{slugify(self.title)[:190]}-{counter}"
                counter += 1

        # 生成摘要
        if not self.excerpt and self.content:
            self.excerpt = self.content[:200] + '...' if len(self.content) > 200 else self.content

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:article_detail', args=[self.slug])

    def increase_views(self):
        """增加阅读量，使用 F 表达式避免竞态条件"""
        from django.db.models import F
        Article.objects.filter(pk=self.pk).update(views=F('views') + 1)
        self.refresh_from_db(fields=['views'])


class Comment(models.Model):
    """评论模型"""
    article = models.ForeignKey(
        Article, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='文章'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies',
        verbose_name='父评论'
    )

    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者',
        null=True, blank=True
    )
    nickname = models.CharField('昵称', max_length=50, blank=True)
    email = models.EmailField('邮箱', blank=True)

    content = models.TextField('评论内容')
    content_html = models.TextField('HTML内容', blank=True)

    is_approved = models.BooleanField('已审核', default=True)
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.nickname or self.author.username}: {self.content[:30]}...'

    def save(self, *args, **kwargs):
        # 处理评论内容（简单处理，防止XSS）
        allowed_tags = ['p', 'br', 'strong', 'em', 'a', 'code', 'pre']
        self.content_html = clean(self.content, tags=allowed_tags, strip=True)
        super().save(*args, **kwargs)


class ApiKey(models.Model):
    """API密钥管理"""
    name = models.CharField('密钥名称', max_length=100)
    key = models.CharField('API Key', max_length=64, unique=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name='所属用户'
    )

    is_active = models.BooleanField('是否有效', default=True)
    description = models.TextField('描述', blank=True)

    # 权限设置
    can_create_article = models.BooleanField('可创建文章', default=True)
    can_update_article = models.BooleanField('可更新文章', default=False)
    can_delete_article = models.BooleanField('可删除文章', default=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    last_used_at = models.DateTimeField('最后使用时间', null=True, blank=True)
    expires_at = models.DateTimeField('过期时间', null=True, blank=True)

    class Meta:
        verbose_name = 'API密钥'
        verbose_name_plural = 'API密钥'

    def __str__(self):
        return f'{self.name} ({self.user.username})'
