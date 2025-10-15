import os
import json
import io
import base64
import random
import time
import concurrent.futures
from typing import List, Dict, Any, Union

from PIL import Image
from django.core.files.uploadedfile import UploadedFile
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError 
from django.conf import settings
from .product_data import PRODUCT_DATABASE 


def _uploaded_file_to_image_payload(uploaded_file: UploadedFile) -> Dict[str, Any]:
    """將 Django UploadedFile 轉為圖片 payload，並進行壓縮與縮放"""
    MAX_SIZE = (1280, 1280)
    QUALITY = 85
    
    try:
        uploaded_file.seek(0)
        file_stream = io.BytesIO(uploaded_file.read())
        img = Image.open(file_stream)
        original_size_kb = len(file_stream.getvalue()) / 1024

        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        output_stream = io.BytesIO()

        mime_type = getattr(uploaded_file, "content_type", None) or Image.MIME.get(img.format, "image/jpeg")
        output_format = 'JPEG'

        if 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
            img.save(output_stream, format=output_format, quality=QUALITY)
        else:
            img.save(output_stream, format=img.format)

        compressed_data = output_stream.getvalue()
        compressed_size_kb = len(compressed_data) / 1024
        width, height = img.size

        data_uri = f"data:{mime_type};base64,{base64.b64encode(compressed_data).decode('utf-8')}"
        print(f"[{time.strftime('%H:%M:%S')}] 圖片壓縮完成: 原始 {original_size_kb:.2f} KB → 壓縮 {compressed_size_kb:.2f} KB")

        return {
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "data_uri": data_uri,
            "filename": getattr(uploaded_file, "name", "uploaded_image")
        }
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ 處理圖片檔案 {getattr(uploaded_file,'name','unknown')} 時發生錯誤: {e}")
        raise


class AIRecommendationService:
    """AI推薦服務，支援圖片分析、文字分析與產品推薦"""

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if api_key and len(api_key) > 10:
            print(f"[{time.strftime('%H:%M:%S')}]  Key 載入成功 ({len(api_key)} 字元, 前五碼: {api_key[:5]}...)")
        else:
            print("❌ 警告：Key 載入失敗或為空！")

        if not api_key:
            raise ValueError("⚠️ GEMINI_API_KEY 未設定")

        genai.configure(api_key=api_key)
        print(f"[{time.strftime('%H:%M:%S')}] 正在檢查可用模型...")
        start_time = time.time()

        available_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        preferred_models = ["gemini-2.5-pro-preview-03-25", "gemini-2.5-pro", "gemini-flash-latest"]
        selected_model_name = next((m for m in preferred_models if m in available_models), None)
        if not selected_model_name and available_models:
            selected_model_name = available_models[0]
        elif not selected_model_name:
            raise RuntimeError("⚠️ 找不到可用 Gemini 模型")

        self.model = genai.GenerativeModel(selected_model_name)
        print(f"[{time.strftime('%H:%M:%S')}] 使用 Gemini 模型: {selected_model_name} (初始化耗時 {time.time() - start_time:.2f}s)")

        self.core_categories = ["flooring", "furniture", "lighting", "wallpaper"]

    def _get_default_analysis(self, request_data):
        """返回 fallback 預設分析結果"""
        return {
            "ai_status": "fallback",
            "estimated_dimensions": {
                "area_ping": request_data.get('room_area', '無法估算'),
                "LxWxH": request_data.get('dimensions', '無法估算'),
                "analysis_basis": "AI 分析失敗，返回預設數據。"
            },
            "budget_allocation": {
                "flooring": "建議分配30%預算於地板",
                "ceiling": "建議分配20%預算於天花板",
                "wallpaper": "建議分配25%預算於壁紙",
                "furniture": "建議分配25%預算於家具"
            },
            "style_suggestions": "依空間與預算選擇合適風格",
            "space_optimization": "優化空間布局",
            "product_focus": "注重品質與性價比"
        }

    def recommend_products(self, request_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Union[str, float]]]]:
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
        """分析用戶需求，帶重試與超時控制"""
        def call_generate_content(contents):
            return self.model.generate_content(contents=contents)

        for attempt in range(1, retries + 2):
            print(f"[{time.strftime('%H:%M:%S')}]  AI分析開始 (第 {attempt} 次嘗試)...")
            try:
                room_area = str(request_data.get('room_area', '')).strip()
                dimensions = str(request_data.get('dimensions', '')).strip()
                is_area_missing = not room_area
                is_dimensions_missing = not dimensions

                instruction = (
                    "請分析提供的圖片，估算房間長寬高與坪數，回傳 JSON。"
                    if image_payloads and (is_area_missing or is_dimensions_missing)
                    else "根據提供資訊分析。"
                )

                contents = []
                for idx, p in enumerate(image_payloads):
                    image_data = base64.b64decode(p['data_uri'].split(',')[1])
                    contents.append({'mime_type': p['mime_type'], 'data': image_data})
                    contents.append(f"這是第 {idx+1} 張圖片，用於分析。")

                prompt_text = f"""
你是一位專業室內設計師，提供精準的設計分析。
{instruction}

用戶資料：
- 風格: {request_data.get('style_name', '未指定')}
- 總坪數: {room_area or '待分析'}
- 長寬高: {dimensions or '待分析'}
- 預算: {request_data.get('total_budget')}
- 特殊需求: {request_data.get('special_requirements', '無')}

請輸出以下 JSON：
{{
  "estimated_dimensions": {{"area_ping": "AI估算坪數", "LxWxH": "AI估算長寬高", "analysis_basis": "依據"}},
  "budget_allocation": {{"flooring": "...", "ceiling": "...", "wallpaper": "...", "furniture": "..."}},
  "style_suggestions": "...",
  "space_optimization": "...",
  "product_focus": "..."
}}
"""
                contents.append(prompt_text)

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(call_generate_content, contents)
                    response = future.result(timeout=timeout_sec)

                print(f"[{time.strftime('%H:%M:%S')}] AI原始回應內容:")
                print(response.text if hasattr(response, 'text') else "(無回傳內容)")

                if not response.candidates or not response.text:
                    raise ValueError("AI 服務回傳空內容。")

                json_text = response.text.strip().replace('```json', '').replace('```', '').strip()
                result = json.loads(json_text)
                result['ai_status'] = 'completed'
                return result

            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ AI分析錯誤 (第 {attempt} 次): {e}")
                if attempt <= retries:
                    print(f"[{time.strftime('%H:%M:%S')}] 🔁 2 秒後重試...")
                    time.sleep(2)
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] ❌ 已達最大重試次數，回傳 fallback 結果。")
                    return self._get_default_analysis(request_data)

    def process_recommendation_request(self, request_data: Dict[str, Any]):
        start_time = time.time()
        try:
            image_files: List[UploadedFile] = request_data.pop('image_files', [])
            image_payloads = [_uploaded_file_to_image_payload(f) for f in image_files]
            print(f"[{time.strftime('%H:%M:%S')}] 🖼️ 已載入 {len(image_payloads)} 張圖片")

            analysis = self.analyze_user_requirements(request_data, image_payloads)
            product_recommendations = self.recommend_products(request_data, analysis)

            total_cost = sum(
                rec.get('price_per_unit', 0) * float(rec.get('quantity', 1))
                for recs in product_recommendations.values()
                for rec in recs
            )

            print(f"[{time.strftime('%H:%M:%S')}] 💰 成本計算完成，總金額約 {total_cost}")
            print(f"[{time.strftime('%H:%M:%S')}] ✅ 推薦流程完成 (總耗時 {time.time() - start_time:.2f}s)")

            return {
                'id': 1,
                'room_area': analysis.get('estimated_dimensions', {}).get('area_ping', request_data.get('room_area', 'N/A')),
                'dimensions': analysis.get('estimated_dimensions', {}).get('LxWxH', request_data.get('dimensions', 'N/A')),
                'total_budget': float(request_data.get('total_budget', 0)) if str(request_data.get('total_budget','')).isdigit() else 0,
                'style_name': request_data.get('style_name', '未指定'),
                'ai_recommendation': analysis,
                'status': 'completed',
                'recommendations': product_recommendations,
                'total_cost': total_cost
            }

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ 推薦流程錯誤: {e}")
            return {
                'id': 1,
                'status': 'failed', 
                'error': str(e),
                'recommendations': {}
            }
