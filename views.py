import os
import traceback
import requests
from typing import Dict, Any
from dotenv import load_dotenv 

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# 導入 AI 服務
from .ai_service import AIRecommendationService

# ======================================================
# 輔助函式
# ======================================================
def _get_uploaded_files(request) -> list:
    """收集所有上傳圖片檔案"""
    image_files = request.FILES.getlist('image_files')
    for key in ['box1', 'box2']:
        if request.FILES.get(key):
            image_files.append(request.FILES[key])
    # 確保檔案清單是唯一的
    return list(set(image_files))

# ======================================================
# 首頁
# ======================================================
def index(request):
    """首頁渲染 (維持不變)"""
    style_options = ['現代風', '北歐風', '工業風', '日式風', '美式風']
    styles = [{'name': s, 'description': f'這是 {s} 的簡短描述。'} for s in style_options]
    initial_data = {
        'styles': styles,
        'room_area': '',
        'dimensions': '',
        'total_budget': '',
        'style_name': ''
    }
    print("首頁 index 被呼叫")
    return render(request, 'index.html', {'initial_data': initial_data, 'styles': styles})

# ======================================================
# API: AI 推薦
# ======================================================
@csrf_exempt
@require_POST
def ai_recommend(request):
    """接收用戶表單與圖片，呼叫 AI 服務返回推薦結果"""
    try:
        data = request.POST.copy()
        room_area = data.get('room_area', '').strip()
        dimensions = data.get('dimensions', '').strip()
        total_budget = data.get('total_budget', '').strip()
        style_name = data.get('style_name', '').strip()
        image_files = _get_uploaded_files(request)

        print(f"收到推薦請求: room_area={room_area}, total_budget={total_budget}, 圖片數量={len(image_files)}")

        if not total_budget:
            return JsonResponse({'success': False, 'error': '缺少必要欄位: 總預算'}, status=400)
        
        # 組裝 AI 服務所需數據
        ai_data: Dict[str, Any] = {
            'room_area': room_area,
            'dimensions': dimensions,
            'total_budget': total_budget,
            'style_name': style_name,
            'image_files': image_files,
            'separate_budget': data.get('separate_budget', '').strip(),
            'special_requirements': data.get('special_requirements', '').strip(),
        }

        # 呼叫 AI 推薦服務
        service = AIRecommendationService()
        recommendation_result = service.process_recommendation_request(ai_data)

        # 儲存結果到 session
        if recommendation_result.get('status') in ['completed', 'fallback']:
            request.session['recommendation_result'] = recommendation_result
            request.session.save()
            print("✅ AI推薦完成，存入 session")
            return JsonResponse({'success': True, 'redirect_url': '/recommend/'})
        else:
            error_msg = recommendation_result.get('error', 'AI 服務處理失敗')
            print(f"⚠️ AI推薦失敗: {error_msg}")
            return JsonResponse({'success': False, 'error': error_msg}, status=500)

    except Exception as e:
        error_trace = traceback.format_exc()
        print("=" * 60)
        print(f"FATAL: AI推薦請求發生未預期錯誤: {e}")
        print(error_trace)
        print("=" * 60)

        if "file is not a recognized image file" in str(e) or "CorruptImageError" in str(e):
            return JsonResponse({'success': False, 'error': '圖片檔案無效或已損壞，請檢查圖片格式後重新上傳。'}, status=400)

        return JsonResponse({
            'success': False,
            'error': 'AI 服務內部錯誤，請稍後再試。',
            'detail': str(e)
        }, status=500)

# ======================================================
# 推薦結果頁面
# ======================================================
def recommend(request):
    """渲染推薦結果頁面"""
    result = request.session.get('recommendation_result', {})
    if not result:
        print("⚠️ 沒有推薦結果，跳轉首頁")
        return redirect('index')

    ai_analysis = result.get('ai_recommendation', {})
    estimated_dims = ai_analysis.get('estimated_dimensions', {})

    display_area = str(estimated_dims.get('area_ping', result.get('room_area', 'N/A')))
    display_basis = estimated_dims.get('analysis_basis', 'N/A')

    total_budget_raw = result.get('total_budget')
    if total_budget_raw is not None and (isinstance(total_budget_raw, (int, float)) or str(total_budget_raw).isdigit()):
        total_budget_formatted = f"NT$ {float(total_budget_raw):,.0f}"
    else:
        total_budget_formatted = str(total_budget_raw) or 'N/A'

    gemini_text = ai_analysis.get('style_suggestions', "無詳細 AI 分析結果") 

    # --- ✅ 修正風格名稱未知問題 ---
    raw_recommendations = result.get('recommendations', {})
    if isinstance(raw_recommendations, list):
        processed_recommendations = {
            item.get("style_name", f"unknown_{idx+1}"): item
            for idx, item in enumerate(raw_recommendations)
        }
    elif isinstance(raw_recommendations, dict):
        processed_recommendations = raw_recommendations
    else:
        processed_recommendations = {}

    # 計算每個風格每個方案總價
    for style_name, style_data in processed_recommendations.items():
        if not isinstance(style_data, dict):
            processed_recommendations[style_name] = {}
            continue

        plans = style_data.get('plans', [])
        for i, plan in enumerate(plans):
            plan_total_cost = 0
            items_dict = plan.get('items', {})
            for category in ['flooring', 'wallpaper_塗料', 'ceiling']:
                product_info = items_dict.get(category, {})
                price_per_unit = product_info.get('price_per_unit', 0)
                quantity = product_info.get('quantity', 1)
                try:
                    product_price = float(price_per_unit) * float(quantity)
                except (ValueError, TypeError):
                    product_price = 0
                # 將每個分類資料存回 plan
                plan[category] = {
                    'price': product_price,
                    'name': product_info.get('name', '無推薦商品'),
                    'unit': product_info.get('unit', '件'),
                    'description': product_info.get('description', '')
                }
                plan_total_cost += product_price
            # 將方案總價存回 plan
            plan['total_cost'] = plan_total_cost

        # 計算風格總價 (取最便宜方案)
        style_data['total_cost'] = min([p.get('total_cost', float('inf')) for p in plans]) if plans else 0
        style_data['style_summary'] = style_data.get('style_summary', ai_analysis.get('style_suggestions', '無建議'))

    # --- ✅ 選擇最便宜風格當推薦 ---
    recommended_style_name = None
    min_price = float('inf')
    for style_name, style_data in processed_recommendations.items():
        plans = style_data.get('plans', [])
        for plan in plans:
            plan_cost = plan.get('total_cost', float('inf'))
            if plan_cost < min_price:
                min_price = plan_cost
                recommended_style_name = style_name

    context = {
        'recommendation_id': result.get('id'),
        'room_area': display_area,
        'dimensions': result.get('dimensions'),
        'total_budget': total_budget_formatted,
        'style_name': result.get('style_name'),
        'ai_recommendation': ai_analysis,
        'display_analysis_basis': display_basis,
        'recommendations': processed_recommendations,
        'total_cost': total_budget_formatted,
        'ai_status': ai_analysis.get('ai_status', 'completed'),
        'gemini_analysis': gemini_text,
        'recommended_style_name': recommended_style_name,  
    }

    print(f"渲染 recommend_style.html，推薦結果: {context}")
    return render(request, 'recommend_style.html', context)

# ======================================================
# Google Gemini API 測試
# ======================================================
@csrf_exempt
def gemini_test(request):
    """測試呼叫 Google Gemini API"""
    try:
        GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GOOGLE_API_KEY:
            raise ValueError("API KEY 未設定於環境變數中")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
        payload = {"contents": [{"parts": [{"text": "Explain how AI works in a few words"}]}]}
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return JsonResponse({"success": True, "response": result}, status=200)

    except Exception as e:
        print("Gemini API 呼叫失敗:", e)
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# ======================================================
# 單個推薦詳情頁面
# ======================================================
def recommendation_detail(request, recommendation_id):
    """顯示單個推薦的詳細內容"""
    result = request.session.get('recommendation_result', {})

    recommendation_id_str = str(recommendation_id)
    if not result or str(result.get('id')) != recommendation_id_str:
        print(f"⚠️ 找不到 recommendation_id={recommendation_id} 的資料，跳轉首頁")
        return redirect('index')

    ai_analysis = result.get('ai_recommendation', {})
    context = {
        'recommendation_id': recommendation_id_str,
        'ai_recommendation': ai_analysis,
        'recommendations': result.get('recommendations', {}),
        'total_budget': result.get('total_budget', 'N/A'),
        'room_area': result.get('room_area', 'N/A'),
        'style_name': result.get('style_name', ''),
    }

    print(f"渲染 recommendation_detail.html，推薦詳情: {context}")
    return render(request, 'recommendation_detail.html', context)
