import os
import traceback
import requests
from typing import Dict, Any
from dotenv import load_dotenv  # 雖然 settings.py 已經載入，但保留以防萬一

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
    # 去重確保不重複
    return list(set(image_files))


# ======================================================
# 首頁
# ======================================================
def index(request):
    """首頁渲染"""
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
        GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

        if not GOOGLE_API_KEY:
            raise ValueError("❌ 缺少 GEMINI_API_KEY，請確認 .env 檔案已正確設置")

        data = request.POST.copy()
        room_area = data.get('room_area', '').strip()
        dimensions = data.get('dimensions', '').strip()
        total_budget = data.get('total_budget', '').strip()
        style_name = data.get('style_name', '').strip()
        image_files = _get_uploaded_files(request)

        print(f"收到推薦請求: room_area={room_area}, total_budget={total_budget}, 圖片數量={len(image_files)}")

        if not total_budget:
            return JsonResponse({'success': False, 'error': '缺少必要欄位: 總預算'}, status=400)
        if not (room_area or dimensions or image_files):
            return JsonResponse({'success': False, 'error': '請提供房間坪數、長寬高或上傳圖片'}, status=400)

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

        # === Gemini 坪數分析 ===
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
            prompt = (
                f"根據以下資料，估算房間坪數並提供推論依據：\n"
                f"房間坪數: {room_area}\n長寬高: {dimensions}\n預算: {total_budget}\n請用繁體中文回覆。"
            )

            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            headers = {"Content-Type": "application/json"}

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            gemini_data = response.json()
            gemini_text = (
                gemini_data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            ) or "無法取得分析結果"

            print(f"✅ Gemini 坪數分析成功: {gemini_text[:80]}...")
            recommendation_result["gemini_analysis"] = gemini_text

        except Exception as gemini_error:
            print(f"⚠️ Gemini 坪數分析失敗: {gemini_error}")
            recommendation_result["gemini_analysis"] = "AI 坪數分析失敗，請稍後再試。"

        # === 儲存結果到 session ===
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


# 推薦結果頁面 (最終穩定版：處理結構不一致問題)
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

    gemini_text = result.get("gemini_analysis", "無分析結果")

    # 必須顯示的產品類別（用於總價和卡片展開區）
    REQUIRED_PRODUCT_CATEGORIES = ['flooring', 'wallpaper', 'ceiling']

    # --- 關鍵修正：處理 recommendations 結構，支援多個風格 ---
    # 預期 AI service 返回的 'recommendations' 是一個 {style_name: {category: [product]}} 的結構
    raw_recommendations_by_style = result.get('recommendations', {})
    processed_recommendations_by_style = {}

    # 1. 確保 raw_recommendations_by_style 是一個字典，否則使用一個 fallback 結構
    if not isinstance(raw_recommendations_by_style, dict):
        # 如果不是字典（例如它是一個列表），我們將它視為一個包含所有產品數據的單一風格 (回退模式)
        fallback_style_name = result.get('style_name', 'AI 推薦風格')
        
        # ⚠️ 這裡假設如果有問題，整個 recommendations 是一個產品字典 {category: [product]}
        # 如果它真的是一個列表，下面的處理會讓程式碼跳過。
        style_data_fallback = raw_recommendations_by_style
        
        # 嘗試將其轉換為一個可迭代的單風格字典
        if isinstance(style_data_fallback, dict):
            raw_recommendations_by_style = {fallback_style_name: style_data_fallback}
        else:
            raw_recommendations_by_style = {}
            print(f"⚠️ recommendations 結構異常 ({type(style_data_fallback)})，無法轉換為字典，將顯示空推薦。")
            

    # 2. 遍歷所有風格
    for style_name, style_data in raw_recommendations_by_style.items():
        
        # 2a. 再次檢查 style_data 是否為字典，這是防止 'list' object has no attribute 'get' 的關鍵
        if not isinstance(style_data, dict):
            print(f"⚠️ 風格 '{style_name}' 的數據不是字典 ({type(style_data)})，已跳過。")
            continue

        style_items = {
            'style_summary': style_data.get('style_summary', ai_analysis.get('style_suggestions', '無建議')),
        }
        total_cost_for_style = 0.0

        # 3. 處理該風格下的產品數據
        for category, products_list in style_data.items():
            
            if category == 'style_summary':
                continue
                
            category_key = category.lower()
            
            # 確保 product_list 是有效的列表
            if products_list and isinstance(products_list, list):
                first_product = products_list[0] 
                
                # 確保 first_product 是字典，防止 product.get 再次出錯
                if not isinstance(first_product, dict):
                     print(f"⚠️ 產品清單中元素不是字典，已跳過。")
                     continue
                
                price_per_unit = first_product.get('price_per_unit', 0)
                quantity = first_product.get('quantity', 1.0)
                
                try:
                    product_price = float(price_per_unit) * float(quantity)
                except (ValueError, TypeError):
                    product_price = 0.0
                
                product_data = {
                    'price': product_price,
                    'name': first_product.get('name', 'N/A'),
                }
                
                style_items[category_key] = product_data
                
                # 關鍵：只對指定的三個類別進行總價累計
                if category_key in REQUIRED_PRODUCT_CATEGORIES:
                    total_cost_for_style += product_price 

            else:
                style_items[category_key] = {'price': 0.0, 'name': '無推薦商品'}


        # 4. 檢查並強制補齊模板中需要的但結果中缺失的三個硬裝類別
        for required_cat in REQUIRED_PRODUCT_CATEGORIES:
            if required_cat not in style_items:
                style_items[required_cat] = {'price': 0.0, 'name': 'AI 無此類別推薦'}
        
        style_items['total_cost'] = total_cost_for_style

        # 組合最終的 context 字典：{風格名稱: {產品數據...}}
        processed_recommendations_by_style[style_name] = style_items
    # --- 修正結束 ---

    context = {
        'recommendation_id': result.get('id'),
        'room_area': display_area,
        'dimensions': result.get('dimensions'),
        'total_budget': total_budget_formatted,
        'style_name': result.get('style_name'),
        'ai_recommendation': ai_analysis,
        'display_analysis_basis': display_basis,
        'recommendations': processed_recommendations_by_style, # 傳遞多風格結構
        'total_cost': total_budget_formatted, 
        'ai_status': ai_analysis.get('ai_status', 'completed'),
        'gemini_analysis': gemini_text,
    }

    print(f"渲染 recommend_style.html，推薦結果: {context}")
    return render(request, 'recommend_style.html', context)
# ======================================================
# 單個推薦詳情頁面
# ======================================================
def recommendation_detail(request, recommendation_id):
    """顯示單個推薦的詳細內容"""
    result = request.session.get('recommendation_result', {})

    if not result or result.get('id') != recommendation_id:
        print(f"⚠️ 找不到 recommendation_id={recommendation_id} 的資料，跳轉首頁")
        return redirect('index')

    ai_analysis = result.get('ai_recommendation', {})
    context = {
        'recommendation_id': recommendation_id,
        'ai_recommendation': ai_analysis,
        'recommendations': result.get('recommendations', {}),
        'total_budget': result.get('total_budget', 'N/A'),
        'room_area': result.get('room_area', 'N/A'),
        'style_name': result.get('style_name', ''),
    }

    print(f"渲染 recommendation_detail.html，推薦詳情: {context}")
    return render(request, 'recommendation_detail.html', context)


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

        payload = {
            "contents": [{"parts": [{"text": "Explain how AI works in a few words"}]}]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return JsonResponse({"success": True, "response": result}, status=200)

    except Exception as e:
        print("Gemini API 呼叫失敗:", e)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
