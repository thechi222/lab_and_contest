from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt 
import traceback
from typing import Dict, Any

# 導入 AI 服務 (必須確保 ai_service.py 已經是修正後的版本)
from .ai_service import AIRecommendationService 

# ====================================================================
# 輔助函式 (Helper Functions)
# ====================================================================

def _get_uploaded_files(request) -> list:
    """從 request.FILES 收集所有圖片檔案 (支援多個欄位名稱)"""
    image_files = request.FILES.getlist('image_files')
    
    # 支援 box1, box2 等單獨上傳的欄位
    for key in ['box1', 'box2']:
        if request.FILES.get(key):
            image_files.append(request.FILES[key])
            
    return image_files

# ====================================================================
# 視圖函式 (View Functions)
# ====================================================================

def index(request):
    """首頁渲染：顯示風格選項和表單"""
    style_options = ['現代風', '北歐風', '工業風', '日式風', '美式風']
    styles = [
        {'name': s, 'description': f'這是 {s} 的簡短描述。'} 
        for s in style_options
    ]
    initial_data = {
        'styles': styles, 
        'room_area': '', 
        'dimensions': '', 
        'total_budget': '', 
        'style_name': ''
    }
    return render(request, 'index.html', {'initial_data': initial_data, 'styles': styles})

@csrf_exempt
@require_POST
def ai_recommend(request):
    """
    AI 推薦 API：處理 POST 請求，提取用戶輸入和圖片，並返回跳轉 URL。
    """
    try:
        # 1. 提取文字資料
        data = request.POST.copy()
        room_area = data.get('room_area', '').strip()
        dimensions = data.get('dimensions', '').strip()
        total_budget = data.get('total_budget', '').strip()
        style_name = data.get('style_name', '').strip()
        image_files = _get_uploaded_files(request) # 這裡只收集檔案，實際處理在 AI 服務內部

        # 2. 驗證必要欄位
        if not total_budget:
            return JsonResponse({'success': False, 'error': '缺少必要欄位: 總預算'}, status=400)
        if not (room_area or dimensions or image_files):
            return JsonResponse({'success': False, 'error': '請提供房間坪數、長寬高或上傳圖片'}, status=400)

        # 3. 準備傳給 AI 的資料結構
        ai_data: Dict[str, Any] = {
            'room_area': room_area,
            'dimensions': dimensions,
            'total_budget': total_budget,
            'style_name': style_name,
            'image_files': image_files,
            'separate_budget': data.get('separate_budget', '').strip(),
            'special_requirements': data.get('special_requirements', '').strip(),
        }

        print(f"收到推薦請求: 文字數據={{'room_area': '{room_area}', 'total_budget': '{total_budget}'}}，圖片數量={len(image_files)}")

        # 4. 呼叫實際 AI 服務 (替換掉模擬數據區塊)
        service = AIRecommendationService()
        recommendation_result = service.process_recommendation_request(ai_data)
        
        # 5. 處理結果並跳轉
        if recommendation_result.get('status') in ['completed', 'fallback']:
            # 即使是 'fallback' (AI分析失敗但返回預設數據)，也視為成功的 HTTP 200 響應並跳轉
            request.session['recommendation_result'] = recommendation_result
            request.session.save()
            return JsonResponse({'status': 'success', 'redirect_url': '/recommand/'})
        else:
            # AI 服務內部處理失敗時的回傳 (來自 ai_service.py 的 except 區塊)
            error_msg = recommendation_result.get('error', 'AI 服務處理失敗')
            print(f"⚠️ AI推薦失敗: {error_msg}")
            # 返回 HTTP 500 讓前端知道這是伺服器內部問題
            return JsonResponse({'success': False, 'error': error_msg}, status=500)

    except Exception as e:
        # 捕獲所有意外錯誤
        error_trace = traceback.format_exc()
        print("="*60)
        print(f"FATAL: AI推薦請求發生未預期錯誤: {e}")
        print(error_trace)
        print("="*60)
        
        # 【修正：針對圖片處理錯誤給予 HTTP 400 錯誤】
        # 檢查常見的圖片處理錯誤關鍵字 (來自 ai_service.py 的 _uploaded_file_to_image_payload)
        if "file is not a recognized image file" in str(e) or "CorruptImageError" in str(e) or 'image_files' in error_trace:
             friendly_error = '圖片檔案無效或已損壞，請檢查圖片格式和完整性後重新上傳。'
             return JsonResponse({'success': False, 'error': friendly_error}, status=400)
        
        # 【修正：處理其他所有嚴重的伺服器錯誤】
        return JsonResponse({
            'success': False,
            'error': 'AI 服務內部錯誤，請稍後再試。', # 用戶看到的通用錯誤
            'detail': f'系統錯誤: {str(e)}', # 供開發者除錯
            'traceback': error_trace
        }, status=500)

# --------------------------------------------------------------------
# 推薦結果頁面
# --------------------------------------------------------------------
def recommand(request):
    """推薦結果頁面渲染 (從 session 讀取數據)"""
    result = request.session.get('recommendation_result', {})
    if not result:
        return redirect('index')

    ai_analysis = result.get('ai_recommendation', {})
    estimated_dims = ai_analysis.get('estimated_dimensions', {})

    # 顯示數據處理
    display_area = str(estimated_dims.get('area_ping', result.get('room_area', 'N/A')))
    display_basis = estimated_dims.get('analysis_basis', 'N/A')

    # 格式化總預算
    total_budget_raw = result.get('total_budget')
    # 處理 total_budget 可能是 float 0 或數字字串的情況
    if total_budget_raw is not None and (isinstance(total_budget_raw, (int, float)) or (isinstance(total_budget_raw, str) and total_budget_raw.isdigit())):
        total_budget_formatted = f"NT$ {float(total_budget_raw):,.0f}"
    else:
        total_budget_formatted = str(total_budget_raw) or 'N/A'

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
        # 【修正：新增 ai_status 傳給模板，用於前端顯示 Fallback 提示】
        'ai_status': ai_analysis.get('ai_status', 'completed') 
    }
    return render(request, 'recommand.html', context)

# --------------------------------------------------------------------
# 推薦詳情頁（暫時功能）
# --------------------------------------------------------------------
def recommendation_detail(request, recommendation_id):
    """查看推薦詳情（暫時功能，無資料庫連結）"""
    return render(request, 'recommendation_detail.html', {'title': '推薦詳情', 'message': '推薦詳情功能暫時不可用'})