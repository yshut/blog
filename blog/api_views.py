"""
API接口 - 供AI发布文章的API

支持的接口:
- POST /api/articles/ - 创建文章
- PUT /api/articles/<slug>/ - 更新文章
- DELETE /api/articles/<slug>/ - 删除文章
- GET /api/articles/ - 获取文章列表
- GET /api/articles/<slug>/ - 获取文章详情
- GET /api/categories/ - 获取分类列表
- GET /api/tags/ - 获取标签列表

认证方式: API Key (Header: Authorization: Bearer <api_key>)
"""

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404

from .models import Article, Category, Tag, ApiKey


class APIKeyPermission(BasePermission):
    """API Key认证权限"""
    def has_permission(self, request, view):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not api_key:
            api_key = request.query_params.get('api_key', '')

        if not api_key:
            return False

        try:
            key_obj = ApiKey.objects.get(key=api_key, is_active=True)

            # 检查是否过期
            if key_obj.expires_at and key_obj.expires_at < timezone.now():
                return False

            # 保存用户信息到request
            request.api_user = key_obj.user
            request.api_key = key_obj

            # 更新最后使用时间
            key_obj.last_used_at = timezone.now()
            key_obj.save(update_fields=['last_used_at'])

            return True
        except ApiKey.DoesNotExist:
            return False


class CanCreateArticlePermission(BasePermission):
    """创建文章权限"""
    def has_permission(self, request, view):
        if not hasattr(request, 'api_key'):
            return False
        return request.api_key.can_create_article


class CanUpdateArticlePermission(BasePermission):
    """更新文章权限"""
    def has_permission(self, request, view):
        if not hasattr(request, 'api_key'):
            return False
        return request.api_key.can_update_article


class CanDeleteArticlePermission(BasePermission):
    """删除文章权限"""
    def has_permission(self, request, view):
        if not hasattr(request, 'api_key'):
            return False
        return request.api_key.can_delete_article


# Serializers
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at']


class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    tags_list = serializers.StringRelatedField(source='tags', many=True, read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'author', 'content', 'excerpt',
            'category', 'category_name', 'tags', 'tags_list',
            'cover_image', 'status', 'views', 'likes', 'is_top',
            'allow_comment', 'is_ai_generated', 'ai_source',
            'source_url', 'source_name', 'summary', 'published_time',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['id', 'slug', 'author', 'views', 'likes', 'created_at', 'updated_at']


class ArticleCreateSerializer(serializers.ModelSerializer):
    """创建文章的序列化器"""
    category_name = serializers.CharField(write_only=True, required=False)
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Article
        fields = [
            'title', 'content', 'category_name', 'tag_names',
            'excerpt', 'cover_image', 'status', 'is_top',
            'allow_comment', 'is_ai_generated', 'ai_source',
            'source_url', 'source_name', 'summary', 'published_time'
        ]

    def create(self, validated_data):
        category_name = validated_data.pop('category_name', None)
        tag_names = validated_data.pop('tag_names', [])

        # 处理分类
        if category_name:
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'slug': category_name.lower().replace(' ', '-')}
            )
            validated_data['category'] = category

        # 创建文章
        article = Article.objects.create(**validated_data)

        # 处理标签
        if tag_names:
            for tag_name in tag_names:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': tag_name.lower().replace(' ', '-')}
                )
                article.tags.add(tag)

        return article


# API Views
@method_decorator(csrf_exempt, name='dispatch')
class ArticleAPIView(APIView):
    """文章API"""
    permission_classes = [APIKeyPermission]

    def get(self, request, slug=None):
        """获取文章列表或详情"""
        if slug:
            article = get_object_or_404(Article, slug=slug)
            serializer = ArticleSerializer(article)
            return Response(serializer.data)
        else:
            articles = Article.objects.all()

            # 筛选参数
            status_filter = request.query_params.get('status')
            if status_filter:
                articles = articles.filter(status=status_filter)

            category = request.query_params.get('category')
            if category:
                articles = articles.filter(category__slug=category)

            tag = request.query_params.get('tag')
            if tag:
                articles = articles.filter(tags__slug=tag)

            is_ai = request.query_params.get('is_ai')
            if is_ai:
                articles = articles.filter(is_ai_generated=is_ai.lower() == 'true')

            # 资讯筛选参数
            source_name = request.query_params.get('source')
            if source_name:
                articles = articles.filter(source_name__icontains=source_name)

            date_from = request.query_params.get('date_from')
            if date_from:
                articles = articles.filter(published_time__gte=date_from)

            date_to = request.query_params.get('date_to')
            if date_to:
                articles = articles.filter(published_time__lte=date_to)

            # 分页（参数校验防止异常）
            try:
                page = max(1, int(request.query_params.get('page', 1)))
                page_size = min(100, max(1, int(request.query_params.get('page_size', 20))))
            except (ValueError, TypeError):
                page = 1
                page_size = 20
            start = (page - 1) * page_size
            end = start + page_size

            serializer = ArticleSerializer(articles[start:end], many=True)
            return Response({
                'total': articles.count(),
                'page': page,
                'page_size': page_size,
                'results': serializer.data
            })

    def post(self, request):
        """创建文章"""
        if not request.api_key.can_create_article:
            return Response(
                {'error': '该API Key没有创建文章的权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArticleCreateSerializer(data=request.data)
        if serializer.is_valid():
            article = serializer.save(
                author=request.api_user,
                is_ai_generated=True,
                ai_source=request.data.get('ai_source', ''),
            )

            # 发布时间
            if article.status == 'published' and not article.published_at:
                article.published_at = timezone.now()
                article.save(update_fields=['published_at'])

            return Response(
                ArticleSerializer(article).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slug):
        """更新文章"""
        if not request.api_key.can_update_article:
            return Response(
                {'error': '该API Key没有更新文章的权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        article = get_object_or_404(Article, slug=slug)

        # 只有作者或API Key拥有者可以更新
        if article.author != request.api_user:
            return Response(
                {'error': '没有权限更新此文章'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ArticleCreateSerializer(
            article,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            article = serializer.save()
            return Response(ArticleSerializer(article).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        """删除文章"""
        if not request.api_key.can_delete_article:
            return Response(
                {'error': '该API Key没有删除文章的权限'},
                status=status.HTTP_403_FORBIDDEN
            )

        article = get_object_or_404(Article, slug=slug)

        # 只有作者或API Key拥有者可以删除
        if article.author != request.api_user:
            return Response(
                {'error': '没有权限删除此文章'},
                status=status.HTTP_403_FORBIDDEN
            )

        article.delete()
        return Response({'message': '文章已删除'}, status=status.HTTP_204_NO_CONTENT)


class CategoryAPIView(APIView):
    """分类API"""
    permission_classes = [APIKeyPermission]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class TagAPIView(APIView):
    """标签API"""
    permission_classes = [APIKeyPermission]

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)


class APIStatusView(APIView):
    """API状态检查（无需认证）"""
    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'Blog API is running',
            'version': '1.0'
        })
