# set/urls.py

from django.contrib import admin
from django.urls import path, include # 🌟 必須引入 include 🌟

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 🌟 將所有根路徑 (URL '') 的請求導向 app/urls.py 🌟
    path('', include('app.urls')), 
]