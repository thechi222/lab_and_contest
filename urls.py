# app/urls.py

from django.urls import path
from . import views

# 定義應用程式內的 URL 模式
urlpatterns = [
    # --- 頁面路由 ---
    path('', views.index, name='index'), 
    path('recommand/', views.recommand, name='recommand'),
    path('recommendation/<int:recommendation_id>/', views.recommendation_detail, name='recommendation_detail'),
    
    # --- AI 推薦 API ---
    path('api/ai_recommend/', views.ai_recommend, name='api_ai_recommend_submission'),

    # --- ✅ 新增 Gemini 測試 API (對應 curl 指令) ---
    path('api/gemini_test/', views.gemini_test, name='api_gemini_test'),
]
