from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Article, Comment


class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(label='邮箱', required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加中文标签
        self.fields['username'].label = '用户名'
        self.fields['password1'].label = '密码'
        self.fields['password2'].label = '确认密码'


class UserLoginForm(forms.Form):
    """用户登录表单"""
    username = forms.CharField(label='用户名', max_length=100)
    password = forms.CharField(label='密码', widget=forms.PasswordInput)


class ArticleForm(forms.ModelForm):
    """文章表单"""
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'tags', 'cover_image', 'status', 'allow_comment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入文章标题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.CheckboxSelectMultiple(),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = '文章标题'
        self.fields['content'].label = '文章内容'
        self.fields['category'].label = '分类'
        self.fields['tags'].label = '标签'
        self.fields['cover_image'].label = '封面图片'
        self.fields['status'].label = '发布状态'
        self.fields['allow_comment'].label = '允许评论'


class CommentForm(forms.ModelForm):
    """评论表单"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '写下你的评论...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = ''


class GuestCommentForm(forms.ModelForm):
    """访客评论表单"""
    class Meta:
        model = Comment
        fields = ['nickname', 'email', 'content']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '昵称'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '邮箱（选填）'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '写下你的评论...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nickname'].label = '昵称'
        self.fields['email'].label = '邮箱'
        self.fields['email'].required = False
        self.fields['content'].label = ''


class CategoryForm(forms.ModelForm):
    """分类表单"""
    class Meta:
        model = Article._meta.get_field('category').related_model
        fields = ['name', 'slug', 'description']


class TagForm(forms.ModelForm):
    """标签表单"""
    class Meta:
        model = Article._meta.get_field('tags').related_model
        fields = ['name', 'slug']
