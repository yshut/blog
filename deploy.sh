#!/bin/bash
# Django 博客部署脚本
# 用法: bash deploy.sh

set -e

echo "=========================================="
echo "开始部署 Django 博客..."
echo "=========================================="

# 进入项目目录
cd /var/www/blog

# 拉取最新代码
echo ">>> 拉取最新代码..."
git pull

# 激活虚拟环境
echo ">>> 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ">>> 安装依赖..."
pip install -r requirements.txt

# 收集静态文件
echo ">>> 收集静态文件..."
python manage.py collectstatic --noinput

# 数据库迁移
echo ">>> 执行数据库迁移..."
python manage.py migrate --noinput

# 重启服务
echo ">>> 重启 Gunicorn..."
sudo systemctl restart gunicorn

echo ">>> 重启 Nginx..."
sudo systemctl restart nginx

# 清理缓存
echo ">>> 清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "=========================================="
echo "部署完成！"
echo "=========================================="
