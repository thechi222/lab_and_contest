import os
import json
import io
import base64
import random
import time
import concurrent.futures
import re
from typing import List, Dict, Any, Union

from PIL import Image
from django.core.files.uploadedfile import UploadedFile
import google.generativeai as genai
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
        img.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
        output_stream = io.BytesIO()
        mime_type = getattr(uploaded_file, "content_type", None) or Image.MIME.get(img.format, "image/jpeg")
        output_format = 'JPEG'
        if 'jpeg' in mime_type.lower() or 'jpg' in mime_type.lower():
            img.save(output_stream, format=output_format, quality=QUALITY)
        else:
            img.save(output_stream, format=img.format)
        compressed_data = output_stream.getvalue()
        width, height = img.size
        data_uri = f"data:{mime_type};base64,{base64.b64encode(compressed_data).decode('utf-8')}"
        return {
            "mime_type": mime_type,
            "width": width,
            "height": height,
            "data_uri": data_uri,
            "filename": getattr(uploaded_file, "name", "uploaded_image")
        }
    except Exception as e:
        raise RuntimeError(f"處理圖片檔案 {getattr(uploaded_file,'name','unknown')} 錯誤: {e}")


class AIRecommendationService:
    """AI推薦服務，支援圖片分析、文字分析與產品推薦"""

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        if not api_key:
            raise ValueError("⚠️ GEMINI_API_KEY 未設定")
        genai.configure(api_key=api_key)
        available_models = [
            m.name for m in genai.list_models()
            if "generateContent" in getattr(m, 'supported_generation_methods', [])
        ]
        preferred_models = [
            "gemini-2.5-pro-preview-03-25",
            "gemini-2.5-pro",
            "gemini-flash-latest"
        ]
        selected_model_name = next((m for m in preferred_models if m in available_models), None)
        if not selected_model_name and available_models:
            selected_model_name = available_models[0]
        elif not selected_model_name:
            raise RuntimeError("⚠️ 找不到可用 Gemini 模型")
        self.model = genai.GenerativeModel(selected_model_name)
        self.core_categories = ["flooring", "ceiling", "wallpaper_塗料"]

    def _get_default_analysis(self, request_data):
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
                "wallpaper_塗料": "建議分配25%預算於壁紙"
            },
            "style_suggestions": "依空間與預算選擇合適風格",
        }

    def _extract_json_from_text(self, text: str):
        if not text:
            return None
        cleaned = re.sub(r'```(?:json)?', '', text, flags=re.IGNORECASE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        match = re.search(r'(\{(?:.|\s)*\})', cleaned, re.DOTALL)
        if match:
            candidate = match.group(1).strip().strip('` \n\t')
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                candidate_fixed = re.sub(r',\s*([}\]])', r'\1', candidate)
                try:
                    return json.loads(candidate_fixed)
                except json.JSONDecodeError:
                    return None
        return None

    def analyze_user_requirements(self, request_data: Dict[str, Any], image_payloads: List[Dict[str, Any]], retries=2, timeout_sec=150):
        """分析房間坪數與尺寸"""
        def call_generate_content(contents):
            return self.model.generate_content(contents=contents)

        for attempt in range(1, retries + 2):
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
你是一位專業室內設計師，提供精準設計分析。
{instruction}

用戶資料：
- 風格: {request_data.get('style_name', '未指定')}
- 總坪數: {room_area or '待分析'}
- 長寬高: {dimensions or '待分析'}
- 預算: {request_data.get('total_budget')}
- 特殊需求: {request_data.get('special_requirements', '無')}

請輸出 JSON，包含：
- estimated_dimensions: area_ping, LxWxH, analysis_basis
- style_suggestions: 四至六種風格建議，每個風格給一段簡介
"""
                contents.append(prompt_text)
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(call_generate_content, contents)
                    response = future.result(timeout=timeout_sec)

                raw_text = response.text if hasattr(response, 'text') else str(response)
                parsed = self._extract_json_from_text(raw_text)
                if not parsed:
                    raise ValueError("AI 回傳內容無法解析成 JSON。")
                parsed['ai_status'] = 'completed'
                return parsed
            except Exception as e:
                if attempt <= retries:
                    time.sleep(10)
                else:
                    return self._get_default_analysis(request_data)

    def recommend_products(self, request_data: Dict[str, Any], analysis_result: Dict[str, Any]):
        """直接從資料庫選風格及商品，產生三種方案"""
        budget = float(request_data.get('total_budget', 0)) if str(request_data.get('total_budget','')).isdigit() else 0
        recommendations = {}
        
        # 從資料庫選出 4~6 個不同風格
        db_styles = list({p['style'] for p in PRODUCT_DATABASE})
        random.shuffle(db_styles)
        selected_styles = db_styles[:6]

        for style_name in selected_styles:
            style_products = [p for p in PRODUCT_DATABASE if p['style'] == style_name]
            recommendations[style_name] = {
                "style_summary": f"{style_name} 風格",
                "plans": []
            }
            for plan_name, factor in [("便宜方案", 0.6), ("中等方案", 1.0), ("奢華方案", 1.5)]:
                plan_items = {}
                total_cost = 0.0
                for category in self.core_categories:
                    filtered = [p for p in style_products if p['category'] == category] or [p for p in PRODUCT_DATABASE if p['category'] == category]
                    if filtered:
                        filtered_sorted = sorted(filtered, key=lambda x: x['price_per_unit'])
                        if plan_name == "便宜方案":
                            selected = filtered_sorted[:1]
                        elif plan_name == "中等方案":
                            selected = filtered_sorted[1:2] if len(filtered_sorted) > 1 else filtered_sorted[:1]
                        else:
                            selected = filtered_sorted[-1:]
                        item = selected[0]
                        cost = item['price_per_unit'] * 1
                        total_cost += cost
                        plan_items[category] = {
                            "name": item['name'],
                            "quantity": 1,
                            "unit": item['unit'],
                            "description": item['description'],
                            "price_per_unit": item['price_per_unit'],
                            "product_id": item['id']
                        }
                    else:
                        plan_items[category] = {
                            "name": "無推薦商品",
                            "quantity": 0,
                            "unit": "件",
                            "description": "",
                            "price_per_unit": 0,
                            "product_id": 0
                        }
                recommendations[style_name]["plans"].append({
                    "plan": plan_name,
                    "total_cost": total_cost,
                    "items": plan_items
                })
            # 計算最便宜方案標記
            min_total = min([p["total_cost"] for p in recommendations[style_name]["plans"]])
            recommendations[style_name]["min_total_cost"] = min_total

        # 標記所有風格中最便宜的方案
        all_min = min([v["min_total_cost"] for v in recommendations.values()])
        for style_data in recommendations.values():
            style_data["cheapest_flag"] = style_data["min_total_cost"] == all_min

        return recommendations

    def process_recommendation_request(self, request_data: Dict[str, Any]):
        """整合圖片分析與資料庫推薦，回傳完整結果"""
        try:
            image_files: List[UploadedFile] = request_data.pop('image_files', [])
            image_payloads = [_uploaded_file_to_image_payload(f) for f in image_files]
            analysis = self.analyze_user_requirements(request_data, image_payloads)
            product_recommendations = self.recommend_products(request_data, analysis)

            return {
                'id': 1,
                'room_area': analysis.get('estimated_dimensions', {}).get('area_ping', request_data.get('room_area', 'N/A')),
                'dimensions': analysis.get('estimated_dimensions', {}).get('LxWxH', request_data.get('dimensions', 'N/A')),
                'total_budget': float(request_data.get('total_budget', 0)) if str(request_data.get('total_budget','')).isdigit() else 0,
                'style_name': request_data.get('style_name', '未指定'),
                'ai_recommendation': analysis,
                'status': 'completed',
                'recommendations': product_recommendations
            }
        except Exception as e:
            return {
                'id': 1,
                'status': 'failed', 
                'error': str(e),
                'recommendations': {}
            }
