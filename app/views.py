# app/views.py

from django.shortcuts import render
from django.http import HttpRequest

# 🌟 這個函數必須存在，以匹配 app/urls.py 中的 path('', views.index) 🌟
def index(request: HttpRequest):
    """處理首頁請求並渲染 index.html 模板"""
    context = {
        'title': '首頁',
        'intro': '您的 Django 專案已成功啟動！',
    }
    # render() 會自動在 app/templates/ 目錄下尋找 index.html
    return render(request, 'index.html', context)