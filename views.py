from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import traceback
import requests
from typing import Dict, Any

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
    return image_files


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
    """
    接收用戶表單與圖片，呼叫 AI 服務返回推薦結果
    """
    try:
        data = request.POST.copy()
        room_area = data.get('room_area', '').strip()
        dimensions = data.get('dimensions', '').strip()
        total_budget = data.get('total_budget', '').strip()
        style_name = data.get('style_name', '').strip()
        image_files = _get_uploaded_files(request)

        print(f"收到推薦請求: 文字數據={{'room_area': '{room_area}', 'total_budget': '{total_budget}'}}，圖片數量={len(image_files)}")

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

        service = AIRecommendationService()
        recommendation_result = service.process_recommendation_request(ai_data)

        # === Gemini 坪數分析開始 ===
        try:
            GOOGLE_API_KEY = "AIzaSyCEFHtAG98fLQ8oSPMAGWiqc7b_Wao00wg"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
            
            prompt = f"根據以下資料，估算房間坪數並提供推論依據：\n房間坪數: {room_area}\n長寬高: {dimensions}\n預算: {total_budget}\n請用繁體中文回覆。"
            payload = {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            }

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
            print(f"✅ Gemini 坪數分析成功: {gemini_text[:100]}...")

            recommendation_result["gemini_analysis"] = gemini_text

        except Exception as gemini_error:
            print(f"⚠️ Gemini 坪數分析失敗: {gemini_error}")
            recommendation_result["gemini_analysis"] = "AI 坪數分析失敗，請稍後再試。"
        # === Gemini 坪數分析結束 ===

        if recommendation_result.get('status') in ['completed', 'fallback']:
            request.session['recommendation_result'] = recommendation_result
            request.session.save()
            print("✅ AI推薦完成，存入 session")
            # ✅ 修正這裡：返回 success 讓前端自動跳轉
            return JsonResponse({'success': True, 'redirect_url': '/recommand/'})
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
            friendly_error = '圖片檔案無效或已損壞，請檢查圖片格式和完整性後重新上傳。'
            return JsonResponse({'success': False, 'error': friendly_error}, status=400)

        return JsonResponse({
            'success': False,
            'error': 'AI 服務內部錯誤，請稍後再試。',
            'detail': str(e),
            'traceback': error_trace
        }, status=500)


# ======================================================
# 推薦結果頁面
# ======================================================
def recommand(request):
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

    # === 顯示 Gemini 分析結果 ===
    gemini_text = result.get("gemini_analysis", "無分析結果")

    context = {
        'recommendation_id': result.get('id'),
        'room_area': display_area,
        'dimensions': result.get('dimensions'),
        'total_budget': total_budget_formatted,
        'style_name': result.get('style_name'),
        'ai_recommendation': ai_analysis,
        'display_analysis_basis': display_basis,
        'recommendations': result.get('recommendations', {}),
        'total_cost': f"NT$ {result.get('total_cost', 0):,.0f}",
        'ai_status': ai_analysis.get('ai_status', 'completed'),
        'budget_breakdown': ai_analysis.get('budget_allocation', {
            'flooring': 'TWD 0',
            'ceiling': 'TWD 0',
            'wallpaper': 'TWD 0'
        }),
        'gemini_analysis': gemini_text,  # ✅ 新增給前端顯示
    }
    print(f"渲染 recommand.html，推薦結果: {context}")
    return render(request, 'recommand_style.html', context)


# ======================================================
# 推薦詳情頁
# ======================================================
def recommendation_detail(request, recommendation_id):
    """暫時功能，顯示選擇方案"""
    print(f"recommendation_detail 被呼叫, recommendation_id={recommendation_id}")
    return render(request, 'recommendation_detail.html', {
        'title': '推薦詳情',
        'message': f'您選擇的 recommendation_id: {recommendation_id}'
    })


# ======================================================
# Google Gemini API 測試
# ======================================================
@csrf_exempt
def gemini_test(request):
    """
    測試呼叫 Google Gemini API (相當於你提供的 curl 指令)
    """
    try:
        GOOGLE_API_KEY = ""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Explain how AI works in a few words"}
                    ]
                }
            ]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        return JsonResponse({"success": True, "response": result}, status=200)

    except Exception as e:
        print("Gemini API 呼叫失敗:", e)
        return JsonResponse({"success": False, "error": str(e)}, status=500)
