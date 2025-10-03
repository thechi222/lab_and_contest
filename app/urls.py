# app/urls.py (這個檔案通常需要您手動建立)

from django.urls import path
from . import views  # 從同一個 App 中引入 views.py 

# 定義應用程式內的 URL 模式
urlpatterns = [
    # 🌟 當路徑為根目錄 ('') 時，執行 views.py 裡的 index 函數 🌟
    path('', views.index, name='index'), 
]