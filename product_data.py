# app/product_data.py
from typing import List, Dict, Any

PRODUCT_DATABASE: List[Dict[str, Any]] = [
    # 現代風 (Modern)
    {"id": 101, "category": "flooring", "style": "modern", "name": "極簡灰木紋複合地板", "model": "M-F001", "price_per_unit": 3500, "unit": "坪", "description": "12mm厚，耐磨等級AC4，適合高人流區域。"},
    {"id": 102, "category": "flooring", "style": "modern", "name": "淺胡桃木複合地板", "model": "M-F002", "price_per_unit": 4000, "unit": "坪", "description": "耐磨防滑，溫潤色調。"},
    {"id": 103, "category": "wallpaper_塗料", "style": "modern", "name": "米白色乳膠漆", "model": "M-W001", "price_per_unit": 900, "unit": "加侖", "description": "環保無味，高遮蓋力。"},
    {"id": 104, "category": "wallpaper_塗料", "style": "modern", "name": "淺灰色乳膠漆", "model": "M-W002", "price_per_unit": 950, "unit": "加侖", "description": "清新灰色，適合臥室和書房。"},
    {"id": 105, "category": "ceiling", "style": "modern", "name": "現代風輕鋼龍骨天花板", "model": "M-C001", "price_per_unit": 1800, "unit": "坪", "description": "易施工，適合客廳與臥室。"},
    {"id": 106, "category": "ceiling", "style": "modern", "name": "石膏板天花板", "model": "M-C002", "price_per_unit": 1600, "unit": "坪", "description": "簡單白色天花板，低成本選擇。"},
    
    # 北歐風 (Scandinavian)
    {"id": 201, "category": "flooring", "style": "scandinavian", "name": "漂白橡木實木地板", "model": "S-F001", "price_per_unit": 4800, "unit": "坪", "description": "淺色系，溫暖質感。"},
    {"id": 202, "category": "flooring", "style": "scandinavian", "name": "淺灰色實木地板", "model": "S-F002", "price_per_unit": 5000, "unit": "坪", "description": "柔和色調，簡約北歐風。"},
    {"id": 203, "category": "wallpaper_塗料", "style": "scandinavian", "name": "淺灰色乳膠漆", "model": "S-W001", "price_per_unit": 1000, "unit": "加侖", "description": "柔和北歐色系，適合臥室。"},
    {"id": 204, "category": "wallpaper_塗料", "style": "scandinavian", "name": "莫蘭迪淺綠壁紙", "model": "S-W002", "price_per_unit": 1200, "unit": "卷", "description": "無縫貼合，提升空間柔和度。"},
    {"id": 205, "category": "ceiling", "style": "scandinavian", "name": "白色平板天花板", "model": "S-C001", "price_per_unit": 1700, "unit": "坪", "description": "簡潔設計，搭配木質家具。"},
    {"id": 206, "category": "ceiling", "style": "scandinavian", "name": "木質橫梁天花板", "model": "S-C002", "price_per_unit": 1900, "unit": "坪", "description": "北歐木質格調，適合客廳。"},
    
    # 工業風 (Industrial)
    {"id": 301, "category": "flooring", "style": "industrial", "name": "水泥灰環氧樹脂地坪", "model": "I-F001", "price_per_unit": 2500, "unit": "坪", "description": "耐重耐油污，表面光滑。"},
    {"id": 302, "category": "flooring", "style": "industrial", "name": "深灰水泥磚地板", "model": "I-F002", "price_per_unit": 2700, "unit": "坪", "description": "粗獷工業感，易清潔。"},
    {"id": 303, "category": "wallpaper_塗料", "style": "industrial", "name": "深灰水泥紋壁紙", "model": "I-W001", "price_per_unit": 1400, "unit": "卷", "description": "增加工業風格質感。"},
    {"id": 304, "category": "wallpaper_塗料", "style": "industrial", "name": "黑色金屬感乳膠漆", "model": "I-W002", "price_per_unit": 1500, "unit": "加侖", "description": "現代工業風，適合餐廳或客廳。"},
    {"id": 305, "category": "ceiling", "style": "industrial", "name": "裸露管線天花板", "model": "I-C001", "price_per_unit": 2000, "unit": "坪", "description": "工業風，帶復古感。"},
    {"id": 306, "category": "ceiling", "style": "industrial", "name": "黑色鋼架天花板", "model": "I-C002", "price_per_unit": 2200, "unit": "坪", "description": "現代工業風格，金屬感十足。"},
    
    # 日式風 (Japanese)
    {"id": 401, "category": "flooring", "style": "japanese", "name": "榻榻米地板", "model": "J-F001", "price_per_unit": 3000, "unit": "坪", "description": "天然草編，營造和風氛圍。"},
    {"id": 402, "category": "flooring", "style": "japanese", "name": "淺色橡木地板", "model": "J-F002", "price_per_unit": 3500, "unit": "坪", "description": "和風溫潤質感，適合臥室。"},
    {"id": 403, "category": "wallpaper_塗料", "style": "japanese", "name": "淺米色和紙壁紙", "model": "J-W001", "price_per_unit": 1300, "unit": "卷", "description": "柔和自然光感，典型日式風格。"},
    {"id": 404, "category": "wallpaper_塗料", "style": "japanese", "name": "淡木色乳膠漆", "model": "J-W002", "price_per_unit": 1200, "unit": "加侖", "description": "自然木質色，簡約日式風。"},
    {"id": 405, "category": "ceiling", "style": "japanese", "name": "木質格柵天花板", "model": "J-C001", "price_per_unit": 1800, "unit": "坪", "description": "簡約木質線條，適合茶室或臥室。"},
    {"id": 406, "category": "ceiling", "style": "japanese", "name": "白色平板天花板", "model": "J-C002", "price_per_unit": 1600, "unit": "坪", "description": "簡單白色天花板，低成本選擇。"},
    
    # 美式風 (American)
    {"id": 501, "category": "flooring", "style": "american", "name": "胡桃木實木地板", "model": "A-F001", "price_per_unit": 5200, "unit": "坪", "description": "厚實耐磨，經典美式風格。"},
    {"id": 502, "category": "flooring", "style": "american", "name": "橡木拼花地板", "model": "A-F002", "price_per_unit": 5400, "unit": "坪", "description": "拼花設計，適合客廳與餐廳。"},
    {"id": 503, "category": "wallpaper_塗料", "style": "american", "name": "淺米色乳膠漆", "model": "A-W001", "price_per_unit": 1000, "unit": "加侖", "description": "柔和色系，百搭風格。"},
    {"id": 504, "category": "wallpaper_塗料", "style": "american", "name": "淺咖啡色壁紙", "model": "A-W002", "price_per_unit": 1200, "unit": "卷", "description": "經典美式風格，搭配木質家具。"},
    {"id": 505, "category": "ceiling", "style": "american", "name": "石膏板吊頂", "model": "A-C001", "price_per_unit": 2000, "unit": "坪", "description": "標準美式吊頂，適合客廳與餐廳。"},
    {"id": 506, "category": "ceiling", "style": "american", "name": "白色裝飾線條天花板", "model": "A-C002", "price_per_unit": 2200, "unit": "坪", "description": "帶裝飾線條，經典美式感。"},
    
    # 英式風 (English)
    {"id": 601, "category": "flooring", "style": "english", "name": "橡木深色地板", "model": "E-F001", "price_per_unit": 5000, "unit": "坪", "description": "高質感英式風格地板。"},
    {"id": 602, "category": "flooring", "style": "english", "name": "胡桃木拼花地板", "model": "E-F002", "price_per_unit": 5200, "unit": "坪", "description": "拼花設計，經典英式風格。"},
    {"id": 603, "category": "wallpaper_塗料", "style": "english", "name": "淺米色乳膠漆", "model": "E-W001", "price_per_unit": 1100, "unit": "加侖", "description": "柔和英式色系，百搭牆面。"},
    {"id": 604, "category": "wallpaper_塗料", "style": "english", "name": "碎花壁紙", "model": "E-W002", "price_per_unit": 1300, "unit": "卷", "description": "經典英式碎花，提升溫馨感。"},
    {"id": 605, "category": "ceiling", "style": "english", "name": "白色石膏板天花板", "model": "E-C001", "price_per_unit": 1800, "unit": "坪", "description": "簡單白色天花板，低成本選擇。"},
    {"id": 606, "category": "ceiling", "style": "english", "name": "裝飾線條天花板", "model": "E-C002", "price_per_unit": 2100, "unit": "坪", "description": "帶裝飾線條，英式經典感。"},
    
    # 鄉村風 (Country)
    {"id": 701, "category": "flooring", "style": "country", "name": "松木實木地板", "model": "C-F001", "price_per_unit": 3200, "unit": "坪", "description": "自然木色，溫暖鄉村感。"},
    {"id": 702, "category": "flooring", "style": "country", "name": "橡木淺色地板", "model": "C-F002", "price_per_unit": 3400, "unit": "坪", "description": "簡約鄉村風，適合客廳。"},
    {"id": 703, "category": "wallpaper_塗料", "style": "country", "name": "淺米色乳膠漆", "model": "C-W001", "price_per_unit": 900, "unit": "加侖", "description": "溫暖色系，百搭牆面。"},
    {"id": 704, "category": "wallpaper_塗料", "style": "country", "name": "鄉村碎花壁紙", "model": "C-W002", "price_per_unit": 1100, "unit": "卷", "description": "典型鄉村風碎花設計。"},
    {"id": 705, "category": "ceiling", "style": "country", "name": "木質橫梁天花板", "model": "C-C001", "price_per_unit": 1800, "unit": "坪", "description": "鄉村木質線條，營造自然感。"},
    {"id": 706, "category": "ceiling", "style": "country", "name": "白色平板天花板", "model": "C-C002", "price_per_unit": 1600, "unit": "坪", "description": "簡單白色天花板，低成本選擇。"},
]
