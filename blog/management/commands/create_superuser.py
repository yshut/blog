from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = '创建超级管理员用户'

    def handle(self, *args, **options):
        # 检查是否已存在 admin 用户
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('用户 "admin" 已存在！'))
            user = User.objects.get(username='admin')
            if user.is_superuser:
                self.stdout.write(self.style.SUCCESS('该用户已是超级管理员。'))
            else:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS('已将 "admin" 升级为超级管理员！'))
            return

        # 创建超级管理员
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123456'
        )
        self.stdout.write(self.style.SUCCESS('超级管理员创建成功！'))
        self.stdout.write(self.style.SUCCESS('用户名: admin'))
        self.stdout.write(self.style.SUCCESS('密码: admin123456'))
        self.stdout.write(self.style.WARNING('请登录后立即修改密码！'))
