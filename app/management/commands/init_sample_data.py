# app/management/commands/init_sample_data.py
from django.core.management.base import BaseCommand
from app.models import Category, Product, Style

class Command(BaseCommand):
    help = '初始化範例資料'

    def handle(self, *args, **options):
        self.stdout.write('開始初始化範例資料...')
        
        # 創建分類
        categories_data = [
            {'name': '地板', 'description': '各種地板材料'},
            {'name': '天花板', 'description': '天花板材料和設計'},
            {'name': '壁紙', 'description': '壁紙和牆面材料'},
            {'name': '家具', 'description': '室內家具'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'創建分類: {category.name}')
        
        # 創建風格
        styles_data = [
            {
                'name': '北歐風',
                'description': '簡約、自然、功能性強的設計風格',
                'characteristics': ['簡約', '自然', '功能性', '明亮'],
                'suitable_spaces': ['小戶型', '採光良好', '現代住宅']
            },
            {
                'name': '工業風',
                'description': '原始、粗獷、金屬質感的設計風格',
                'characteristics': ['金屬', '原始', '粗獷', '復古'],
                'suitable_spaces': ['挑高空間', '開放式', '商業空間']
            },
            {
                'name': '現代風',
                'description': '簡潔、科技感、線條感強的設計風格',
                'characteristics': ['簡潔', '科技感', '線條感', '時尚'],
                'suitable_spaces': ['現代住宅', '辦公空間', '方正空間']
            },
            {
                'name': '極簡風',
                'description': '極度簡化、禪意、空靈的設計風格',
                'characteristics': ['極簡', '禪意', '空靈', '純淨'],
                'suitable_spaces': ['安靜空間', '冥想空間', '私密空間']
            }
        ]
        
        for style_data in styles_data:
            style, created = Style.objects.get_or_create(
                name=style_data['name'],
                defaults={
                    'description': style_data['description'],
                    'characteristics': style_data['characteristics'],
                    'suitable_spaces': style_data['suitable_spaces']
                }
            )
            if created:
                self.stdout.write(f'創建風格: {style.name}')
        
        # 創建範例產品
        products_data = [
            # 地板產品
            {
                'category': '地板',
                'name': '北歐風實木地板',
                'brand': 'Nordic Wood',
                'model_number': 'NW001',
                'price': 8000,
                'unit': '坪',
                'material': '橡木',
                'color': '原木色',
                'style': '北歐風',
                'size': '120cm x 20cm',
                'description': '天然橡木製成，環保無毒，適合北歐風格裝修',
                'source_url': 'https://example.com/floor1'
            },
            {
                'category': '地板',
                'name': '工業風水泥地磚',
                'brand': 'Industrial Style',
                'model_number': 'IS001',
                'price': 3500,
                'unit': '坪',
                'material': '水泥',
                'color': '灰色',
                'style': '工業風',
                'size': '60cm x 60cm',
                'description': '仿水泥質感地磚，適合工業風格空間',
                'source_url': 'https://example.com/floor2'
            },
            {
                'category': '地板',
                'name': '現代風大理石地磚',
                'brand': 'Modern Stone',
                'model_number': 'MS001',
                'price': 12000,
                'unit': '坪',
                'material': '大理石',
                'color': '白色',
                'style': '現代風',
                'size': '80cm x 80cm',
                'description': '高品質大理石地磚，奢華現代',
                'source_url': 'https://example.com/floor3'
            },
            
            # 天花板產品
            {
                'category': '天花板',
                'name': '北歐簡約吊燈',
                'brand': 'Nordic Light',
                'model_number': 'NL001',
                'price': 15000,
                'unit': '組',
                'material': '木質+金屬',
                'color': '白色',
                'style': '北歐風',
                'size': '直徑60cm',
                'description': '簡約設計吊燈，營造溫馨北歐氛圍',
                'source_url': 'https://example.com/ceiling1'
            },
            {
                'category': '天花板',
                'name': '工業風鐵藝吊燈',
                'brand': 'Industrial Metal',
                'model_number': 'IM001',
                'price': 25000,
                'unit': '組',
                'material': '鐵藝',
                'color': '黑色',
                'style': '工業風',
                'size': '長100cm',
                'description': '復古鐵藝吊燈，營造工業風氛圍',
                'source_url': 'https://example.com/ceiling2'
            },
            {
                'category': '天花板',
                'name': '現代科技感吸頂燈',
                'brand': 'Modern Tech',
                'model_number': 'MT001',
                'price': 20000,
                'unit': '組',
                'material': '鋁合金',
                'color': '銀色',
                'style': '現代風',
                'size': '直徑80cm',
                'description': '智能調光吸頂燈，科技感十足',
                'source_url': 'https://example.com/ceiling3'
            },
            
            # 壁紙產品
            {
                'category': '壁紙',
                'name': '北歐風植物壁紙',
                'brand': 'Nordic Nature',
                'model_number': 'NN001',
                'price': 1200,
                'unit': '捲',
                'material': '無紡布',
                'color': '綠色系',
                'style': '北歐風',
                'size': '53cm x 10m',
                'description': '植物圖案壁紙，自然清新',
                'source_url': 'https://example.com/wallpaper1'
            },
            {
                'category': '壁紙',
                'name': '工業風磚牆壁紙',
                'brand': 'Industrial Brick',
                'model_number': 'IB001',
                'price': 1500,
                'unit': '捲',
                'material': 'PVC',
                'color': '紅磚色',
                'style': '工業風',
                'size': '53cm x 10m',
                'description': '仿磚牆效果壁紙，工業風必備',
                'source_url': 'https://example.com/wallpaper2'
            },
            {
                'category': '壁紙',
                'name': '現代幾何壁紙',
                'brand': 'Modern Geo',
                'model_number': 'MG001',
                'price': 1800,
                'unit': '捲',
                'material': '純紙',
                'color': '黑白灰',
                'style': '現代風',
                'size': '53cm x 10m',
                'description': '幾何圖案壁紙，現代簡約',
                'source_url': 'https://example.com/wallpaper3'
            },
            
            # 家具產品
            {
                'category': '家具',
                'name': '北歐風沙發',
                'brand': 'Nordic Comfort',
                'model_number': 'NC001',
                'price': 45000,
                'unit': '組',
                'material': '布藝',
                'color': '米白色',
                'style': '北歐風',
                'size': '200cm x 90cm x 75cm',
                'description': '舒適布藝沙發，北歐風格',
                'source_url': 'https://example.com/furniture1'
            },
            {
                'category': '家具',
                'name': '工業風鐵櫃',
                'brand': 'Industrial Storage',
                'model_number': 'IS002',
                'price': 35000,
                'unit': '組',
                'material': '鐵藝',
                'color': '黑色',
                'style': '工業風',
                'size': '120cm x 60cm x 180cm',
                'description': '復古鐵藝儲物櫃，工業風格',
                'source_url': 'https://example.com/furniture2'
            },
            {
                'category': '家具',
                'name': '現代風茶几',
                'brand': 'Modern Table',
                'model_number': 'MT002',
                'price': 25000,
                'unit': '組',
                'material': '玻璃+金屬',
                'color': '透明',
                'style': '現代風',
                'size': '120cm x 60cm x 45cm',
                'description': '簡約玻璃茶几，現代設計',
                'source_url': 'https://example.com/furniture3'
            }
        ]
        
        for product_data in products_data:
            category = categories[product_data['category']]
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'category': category,
                    'brand': product_data['brand'],
                    'model_number': product_data['model_number'],
                    'price': product_data['price'],
                    'unit': product_data['unit'],
                    'material': product_data['material'],
                    'color': product_data['color'],
                    'style': product_data['style'],
                    'size': product_data['size'],
                    'description': product_data['description'],
                    'source_url': product_data['source_url']
                }
            )
            if created:
                self.stdout.write(f'創建產品: {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS('範例資料初始化完成！')
        )

