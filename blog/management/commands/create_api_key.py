"""
创建API Key的管理命令

使用方法:
    python manage.py create_api_key <username> [--name="API Key名称"]

示例:
    python manage.py create_api_key admin --name="AI Publisher"
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from blog.models import ApiKey
import secrets


class Command(BaseCommand):
    help = '为指定用户创建API Key'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='用户名')
        parser.add_argument('--name', type=str, default='API Key', help='API Key名称')
        parser.add_argument('--create-article', action='store_true', default=True, help='可创建文章权限')
        parser.add_argument('--update-article', action='store_true', default=False, help='可更新文章权限')
        parser.add_argument('--delete-article', action='store_true', default=False, help='可删除文章权限')

    def handle(self, *args, **options):
        username = options['username']
        name = options['name']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'用户 "{username}" 不存在')

        # 生成安全的API Key
        api_key = secrets.token_urlsafe(32)

        # 创建API Key记录
        key_obj = ApiKey.objects.create(
            name=name,
            key=api_key,
            user=user,
            can_create_article=options['create_article'],
            can_update_article=options['update_article'],
            can_delete_article=options['delete_article'],
        )

        self.stdout.write(self.style.SUCCESS(f'''
API Key 创建成功！

名称: {key_obj.name}
用户: {key_obj.user.username}
API Key: {api_key}

权限:
  - 创建文章: {'是' if key_obj.can_create_article else '否'}
  - 更新文章: {'是' if key_obj.can_update_article else '否'}
  - 删除文章: {'是' if key_obj.can_delete_article else '否'}

请妥善保存API Key，它只会显示一次！

使用示例:
---------
Python:
    import requests
    response = requests.post(
        'http://localhost:8000/api/articles/',
        headers={'Authorization': f'Bearer {api_key}'},
        json={{
            'title': '测试文章',
            'content': '这是内容',
            'status': 'published'
        }}
    )

cURL:
    curl -X POST http://localhost:8000/api/articles/ \\
      -H "Authorization: Bearer {api_key}" \\
      -H "Content-Type: application/json" \\
      -d '{{"title": "测试文章", "content": "内容", "status": "published"}}'
'''))
