# app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- 頁面路由 ---
    path('', views.index, name='index'), 
    path('recommend/', views.recommend, name='recommend'),  # 修正這裡
    path('recommendation/<int:recommendation_id>/', views.recommendation_detail, name='recommendation_detail'),
    
    # --- AI 推薦 API ---
    path('api/ai_recommend/', views.ai_recommend, name='api_ai_recommend_submission'),

    # --- ✅ 新增 Gemini 測試 API (對應 curl 指令) ---
    path('api/gemini_test/', views.gemini_test, name='api_gemini_test'),
]
