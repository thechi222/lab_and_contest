# app/product_data.py
from typing import List, Dict, Any

# 模擬產品資料庫
# 每個產品包含:
# - category: 類別 (flooring, furniture, lighting, etc.)
# - style: 風格 (modern, scandinavian, industrial, etc.)
# - name: 產品名稱
# - price_per_unit: 單位價格 (我們暫時使用 NTD/ unit)
# - description: 產品描述

PRODUCT_DATABASE: List[Dict[str, Any]] = [
    # 現代風 (Modern)
    {"id": 101, "category": "flooring", "style": "modern", "name": "極簡灰木紋複合地板", "price_per_unit": 3500, "unit": "坪", "description": "12mm厚，耐磨等級AC4，適合高人流區域。"},
    {"id": 102, "category": "furniture", "style": "modern", "name": "義式低背皮質沙發", "price_per_unit": 55000, "unit": "張", "description": "線條簡潔，科技皮材質，適合小戶型客廳。"},
    {"id": 103, "category": "lighting", "style": "modern", "name": "線性LED軌道燈", "price_per_unit": 2200, "unit": "盞", "description": "可調整角度，提供均勻照明。"},
    
    # 北歐風 (Scandinavian)
    {"id": 201, "category": "flooring", "style": "scandinavian", "name": "漂白橡木實木地板", "price_per_unit": 4800, "unit": "坪", "description": "淺色系，溫暖質感，營造北歐氛圍。"},
    {"id": 202, "category": "furniture", "style": "scandinavian", "name": "實木白臘木餐桌", "price_per_unit": 28000, "unit": "張", "description": "天然紋理，搭配圓潤邊角。"},
    {"id": 203, "category": "wallpaper", "style": "scandinavian", "name": "莫蘭迪淺綠壁紙", "price_per_unit": 1200, "unit": "卷", "description": "無縫貼合，提升空間柔和度。"},
    
    # 工業風 (Industrial)
    {"id": 301, "category": "flooring", "style": "industrial", "name": "水泥灰環氧樹脂地坪", "price_per_unit": 2500, "unit": "坪", "description": "耐重耐油污，表面光滑。"},
    {"id": 302, "category": "furniture", "style": "industrial", "name": "鐵件原木工作桌", "price_per_unit": 18000, "unit": "張", "description": "粗獷風格，結合金屬和實木。"},
    {"id": 303, "category": "lighting", "style": "industrial", "name": "Edison燈泡吊燈", "price_per_unit": 1500, "unit": "盞", "description": "裸露燈泡，增加復古感。"},
    
    # 通用產品 (General)
    {"id": 901, "category": "wallpaper", "style": "general", "name": "白色百搭乳膠漆", "price_per_unit": 800, "unit": "加侖", "description": "高遮蓋力，環保無味。"},
]
