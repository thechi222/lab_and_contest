import os
import json
import io
import base64
import random
import time
import concurrent.futures
from typing import List, Dict, Any, Union

from PIL import Image # 【關鍵】: 導入 Pillow 庫
from django.core.files.uploadedfile import UploadedFile
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError 
from django.conf import settings
from .product_data import PRODUCT_DATABASE 


def _uploaded_file_to_image_payload(uploaded_file: UploadedFile) -> Dict[str, Any]:
    """將 Django UploadedFile 轉為圖片 payload，並進行壓縮和縮放。"""
    MAX_SIZE = (1280, 1280) # 限制圖片最大邊長為 1280 像素
    QUALITY = 85 # 壓縮品質
    
    try:
        uploaded_file.seek(0)
        file_stream = io.BytesIO(uploaded_file.read())
        img = Image.open(file_stream)
        
        # 紀錄原始大小
        original_size_kb = len(file_stream.getvalue()) / 1024

        # 1. 調整大小 (Resize): 使用縮略圖功能，保持長寬比
        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        
        # 2. 轉換為 JPEG 格式並壓縮
        output_stream = io.BytesIO()
        # 判斷格式：如果原始是 JPEG 或 PNG，就用原格式，否則用 JPEG
        mime_type = getattr(uploaded_file, "content_type", None) or Image.MIME.get(img.format, "image/jpeg")
        output_format = 'JPEG'
        
        # 僅對 JPEG 格式圖片應用質量參數
        if 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
             img.save(output_stream, format=output_format, quality=QUALITY)
        else:
             # 對 PNG 等格式進行一般保存
             img.save(output_stream, format=img.format)
        
        # 獲取壓縮後的數據
        compressed_data = output_stream.getvalue()
        
        # 紀錄壓縮後大小
        compressed_size_kb = len(compressed_data) / 1024

        width, height = img.size
        # 使用壓縮後的數據生成 data_uri
        data_uri = f"data:{mime_type};base64,{base64.b64encode(compressed_data).decode('utf-8')}"
        
        print(f"✅ 圖片壓縮完成: 原始大小約 {original_size_kb:.2f} KB -> 壓縮後約 {compressed_size_kb:.2f} KB")

        return {
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "data_uri": data_uri,
            "filename": getattr(uploaded_file, "name", "uploaded_image")
        }
    except Exception as e:
        print(f"處理圖片檔案 {getattr(uploaded_file, 'name', 'unknown')} 時發生錯誤: {e}")
        raise


class AIRecommendationService:
    """AI推薦服務，支援圖片分析、文字分析與產品推薦"""

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        
        # 載入診斷行
        if api_key and len(api_key) > 10:
            print(f"✅ Key 載入長度檢查通過: {len(api_key)} 字元 (Key 的前五碼: {api_key[:5]}...)")
        else:
            print("❌ 警告：Key 載入失敗或為空！")
            
        if not api_key:
            raise ValueError("⚠️ GEMINI_API_KEY 未設定")
        
        genai.configure(api_key=api_key)

        available_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        preferred_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-pro"]
        selected_model_name = next((m for m in preferred_models if m in available_models), None)
        if not selected_model_name and available_models:
            selected_model_name = available_models[0]
        elif not selected_model_name:
            raise RuntimeError("⚠️ 找不到可用 Gemini 模型")
        self.model = genai.GenerativeModel(selected_model_name)
        print(f"✅ 使用 Gemini 模型: {selected_model_name}")

        self.core_categories = ["flooring", "furniture", "lighting", "wallpaper"]

    def _get_default_analysis(self, request_data):
        """返回 fallback 預設分析結果"""
        return {
            "ai_status": "fallback",
            "estimated_dimensions": {
                "area_ping": request_data.get('room_area', '無法估算'),
                "LxWxH": request_data.get('dimensions', '無法估算'),
                "analysis_basis": "AI 分析失敗，已返回預設數據。請檢查 API Key 或網路連線。"
            },
            "budget_allocation": {
                "flooring": "建議分配30%預算於地板",
                "ceiling": "建議分配20%預算於天花板",
                "wallpaper": "建議分配25%預算於壁紙",
                "furniture": "建議分配25%預算於家具"
            },
            "style_suggestions": "根據空間大小和預算選擇合適風格",
            "space_optimization": "優化空間布局，提升使用效率",
            "product_focus": "注重產品質量和性價比"
        }

    def recommend_products(self, request_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Union[str, float]]]]:
        """根據分析結果推薦產品"""
        style = request_data.get('style_name', 'modern').lower()
        normalized_style = {'現代風': 'modern','北歐風': 'scandinavian','工業風': 'industrial'}.get(style, 'modern')
        recommendations: Dict[str, List[Dict[str, Union[str, float]]]] = {}
        for category in self.core_categories:
            filtered_products = [
                p for p in PRODUCT_DATABASE
                if p['category'] == category and (p['style'] == normalized_style or p['style'] == 'general')
            ]
            if filtered_products:
                num_to_select = min(len(filtered_products), random.randint(1,2))
                selected_products = random.sample(filtered_products, num_to_select)
                recommendations[category] = [
                    {
                        "name": p['name'],
                        "quantity": 1.0,
                        "unit": p['unit'],
                        "description": p['description'],
                        "price_per_unit": p['price_per_unit'],
                        "product_id": p['id']
                    } for p in selected_products
                ]
        return recommendations

    def analyze_user_requirements(self, request_data: Dict[str, Any], image_payloads: List[Dict[str, Any]], retries=2, timeout_sec=150):
        """分析用戶需求，帶重試與超時控制（timeout 150 秒）"""
        def call_generate_content(contents):
            return self.model.generate_content(contents=contents)

        for attempt in range(1, retries+2):
            try:
                room_area = str(request_data.get('room_area', '')).strip()
                dimensions = str(request_data.get('dimensions', '')).strip()
                is_area_missing = not room_area
                is_dimensions_missing = not dimensions

                instruction = (
                    "請分析提供的圖片，估算房間長寬高與總坪數，並說明依據，回傳 JSON。"
                    if image_payloads and (is_area_missing or is_dimensions_missing)
                    else "根據用戶提供資訊進行分析。"
                )

                estimated_area = room_area if room_area else "待分析"
                estimated_dimensions = dimensions if dimensions else "待分析"

                contents = []
                for idx, p in enumerate(image_payloads):
                    image_data = base64.b64decode(p['data_uri'].split(',')[1])
                    contents.append({'mime_type': p['mime_type'], 'data': image_data})
                    contents.append(f"這是第 {idx+1} 張圖片，用於分析。")

                prompt_text = f"""
你是一位頂尖室內設計師，提供客製化設計方案。
{instruction}

## 用戶資訊
- 風格: {request_data.get('style_name', '未指定')}
- 總坪數: {estimated_area}
- 長寬高: {estimated_dimensions}
- 總預算: {request_data.get('total_budget')}
- 特殊需求: {request_data.get('special_requirements', '無')}

## 回傳 JSON
{{
  "estimated_dimensions": {{"area_ping": "AI 估算坪數", "LxWxH": "AI 估算長寬高", "analysis_basis": "依據"}},
  "budget_allocation": {{"flooring": "...", "ceiling": "...", "wallpaper": "...", "furniture": "..."}},
  "style_suggestions": "...",
  "space_optimization": "...",
  "product_focus": "..."
}}
"""
                contents.append(prompt_text)

                # 使用 ThreadPoolExecutor 控制超時
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(call_generate_content, contents)
                    try:
                        response = future.result(timeout=timeout_sec)
                    except concurrent.futures.TimeoutError:
                        raise TimeoutError("AI 服務超時")

                # 優先檢查回應候選者（Candidates）是否存在，以捕獲 Key/連線失敗
                if not response.candidates or not response.text:
                    
                    finish_reason = 'API CALL FAILURE' 
                    if response.candidates and response.candidates[0].finish_reason:
                        finish_reason = response.candidates[0].finish_reason.name
                        
                    if finish_reason == 'SAFETY' or finish_reason == 'RECITATION':
                        raise ValueError(f"AI 回應被內容過濾器攔截 (Reason: {finish_reason})，請調整輸入內容。")
                    
                    raise ValueError(f"AI 服務回傳空內容或無候選者 (Reason: {finish_reason})。請檢查 API Key 或網路連線。")
                
                json_text = response.text.strip()
                
                # 處理常見的 Gemini JSON 格式問題
                if json_text.startswith('```json'):
                    json_text = json_text.lstrip('```json').strip()
                
                if json_text.endswith('```'):
                    json_text = json_text.rstrip('```').strip()
                    
                if json_text.startswith('```'):
                    json_text = json_text.lstrip('```').strip()
                
                result = json.loads(json_text)
                result['ai_status'] = 'completed'
                return result

            except (GoogleAPICallError, Exception) as e: 
                error_message = str(e)
                if isinstance(e, GoogleAPICallError) or "API_KEY_INVALID" in error_message or "PERMISSION_DENIED" in error_message:
                    print(f"AI分析錯誤 (第 {attempt} 次嘗試): API KEY/權限錯誤: {e}")
                    return self._get_default_analysis(request_data) 
                elif "504" in error_message or "timed out" in error_message or isinstance(e, TimeoutError):
                    print(f"AI分析錯誤 (第 {attempt} 次嘗試): 服務超時")
                else:
                    print(f"AI分析錯誤 (第 {attempt} 次嘗試): {error_message}")
                
                
                if attempt <= retries:
                    time.sleep(2)
                else:
                    print("⚠️ 已達最大重試次數，使用 fallback 預設結果。")
                    return self._get_default_analysis(request_data)

    def process_recommendation_request(self, request_data: Dict[str, Any]):
        """處理完整推薦請求"""
        try:
            image_files: List[UploadedFile] = request_data.pop('image_files', [])
            image_payloads = [_uploaded_file_to_image_payload(f) for f in image_files]

            analysis = self.analyze_user_requirements(request_data, image_payloads)
            product_recommendations = self.recommend_products(request_data, analysis)

            estimated_dims = analysis.get('estimated_dimensions', {})
            total_budget_float = float(request_data.get('total_budget', 0)) if str(request_data.get('total_budget','')).isdigit() else 0

            recommendation_result = {
                'id': 1,
                'room_area': estimated_dims.get('area_ping', request_data.get('room_area', 'N/A')),
                'dimensions': estimated_dims.get('LxWxH', request_data.get('dimensions', 'N/A')),
                'total_budget': total_budget_float,
                'style_name': request_data.get('style_name', '未指定'),
                'ai_recommendation': analysis,
                'status': 'completed',
                'recommendations': product_recommendations,
                'total_cost': sum(
                    rec.get('price_per_unit',0) * float(rec.get('quantity',1))
                    for recs in product_recommendations.values()
                    for rec in recs
                )
            }

            return recommendation_result

        except Exception as e:
            print(f"處理推薦請求錯誤: {e}")
            return {
                'id': 1,
                'status': 'failed', 
                'error': str(e),
                'recommendations': {}
            }