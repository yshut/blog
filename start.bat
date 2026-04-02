@echo off
echo ================================
echo 咨询博客系统 - 启动脚本
echo ================================
echo.

REM 检查是否已创建超级用户
echo 正在启动开发服务器...
echo.
echo 访问地址:
echo   博客首页: http://127.0.0.1:8000/
echo   管理后台: http://127.0.0.1:8000/admin/
echo   API状态: http://127.0.0.1:8000/api/status/
echo.
echo 按 Ctrl+C 停止服务器
echo ================================

python manage.py runserver
