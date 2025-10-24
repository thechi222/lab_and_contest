
# app/models.py
from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    """產品分類（地板、天花板、壁紙等）"""
    name = models.CharField(max_length=50, verbose_name="分類名稱")
    description = models.TextField(blank=True, verbose_name="分類描述")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "產品分類"
        verbose_name_plural = "產品分類"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """產品模型"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="分類")
    name = models.CharField(max_length=200, verbose_name="產品名稱")
    brand = models.CharField(max_length=100, blank=True, verbose_name="品牌")
    model_number = models.CharField(max_length=100, blank=True, verbose_name="型號")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="價格")
    unit = models.CharField(max_length=20, default="件", verbose_name="單位")  # 件、坪、公尺等
    
    # 產品特性
    material = models.CharField(max_length=100, blank=True, verbose_name="材質")
    color = models.CharField(max_length=50, blank=True, verbose_name="顏色")
    style = models.CharField(max_length=50, blank=True, verbose_name="風格")
    size = models.CharField(max_length=100, blank=True, verbose_name="尺寸")
    
    # 圖片和描述
    image_url = models.URLField(blank=True, verbose_name="圖片網址")
    description = models.TextField(blank=True, verbose_name="產品描述")
    
    # 爬蟲相關
    source_url = models.URLField(verbose_name="來源網址")
    crawled_at = models.DateTimeField(auto_now_add=True, verbose_name="爬取時間")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    
    class Meta:
        verbose_name = "產品"
        verbose_name_plural = "產品"
        ordering = ['-crawled_at']
    
    def __str__(self):
        return f"{self.name} - {self.brand}"

class Style(models.Model):
    """設計風格"""
    name = models.CharField(max_length=50, verbose_name="風格名稱")
    description = models.TextField(verbose_name="風格描述")
    characteristics = models.JSONField(default=list, verbose_name="風格特徵")  # 存儲特徵列表
    suitable_spaces = models.JSONField(default=list, verbose_name="適合空間")  # 存儲適合的空間類型
    
    class Meta:
        verbose_name = "設計風格"
        verbose_name_plural = "設計風格"
    
    def __str__(self):
        return self.name

class RecommendationRequest(models.Model):
    """推薦請求記錄"""
    STATUS_CHOICES = [
        ('pending', '處理中'),
        ('completed', '已完成'),
        ('failed', '失敗'),
    ]
    
    # 用戶輸入的資料
    room_area = models.FloatField(verbose_name="房間總坪數")
    dimensions = models.CharField(max_length=100, verbose_name="長寬高")
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="總預算")
    separate_budget = models.CharField(max_length=200, blank=True, verbose_name="分別預算")
    special_requirements = models.TextField(blank=True, verbose_name="特殊需求")
    selected_style = models.ForeignKey(Style, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="選擇風格")
    
    # 圖片（Base64編碼存儲）
    real_photo = models.TextField(blank=True, verbose_name="實體圖")
    floor_plan = models.TextField(blank=True, verbose_name="平面圖")
    
    # 推薦結果
    ai_recommendation = models.JSONField(default=dict, verbose_name="AI推薦結果")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="狀態")
    
    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "推薦請求"
        verbose_name_plural = "推薦請求"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"推薦請求 - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class RecommendationItem(models.Model):
    """推薦項目"""
    request = models.ForeignKey(RecommendationRequest, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="產品分類")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="推薦產品")
    quantity = models.FloatField(verbose_name="數量")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="總價")
    ai_score = models.FloatField(verbose_name="AI推薦分數", help_text="0-1之間的分數")
    reason = models.TextField(verbose_name="推薦理由")
    
    class Meta:
        verbose_name = "推薦項目"
        verbose_name_plural = "推薦項目"
    
    def __str__(self):
        return f"{self.product.name} - 分數: {self.ai_score}"


# app/models.py
from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    """產品分類（地板、天花板、壁紙等）"""
    name = models.CharField(max_length=50, verbose_name="分類名稱")
    description = models.TextField(blank=True, verbose_name="分類描述")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "產品分類"
        verbose_name_plural = "產品分類"
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """產品模型"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="分類")
    name = models.CharField(max_length=200, verbose_name="產品名稱")
    brand = models.CharField(max_length=100, blank=True, verbose_name="品牌")
    model_number = models.CharField(max_length=100, blank=True, verbose_name="型號")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="價格")
    unit = models.CharField(max_length=20, default="件", verbose_name="單位")  # 件、坪、公尺等
    
    # 產品特性
    material = models.CharField(max_length=100, blank=True, verbose_name="材質")
    color = models.CharField(max_length=50, blank=True, verbose_name="顏色")
    style = models.CharField(max_length=50, blank=True, verbose_name="風格")
    size = models.CharField(max_length=100, blank=True, verbose_name="尺寸")
    
    # 圖片和描述
    image_url = models.URLField(blank=True, verbose_name="圖片網址")
    description = models.TextField(blank=True, verbose_name="產品描述")
    
    # 爬蟲相關
    source_url = models.URLField(verbose_name="來源網址")
    crawled_at = models.DateTimeField(auto_now_add=True, verbose_name="爬取時間")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    
    class Meta:
        verbose_name = "產品"
        verbose_name_plural = "產品"
        ordering = ['-crawled_at']
    
    def __str__(self):
        return f"{self.name} - {self.brand}"

class Style(models.Model):
    """設計風格"""
    name = models.CharField(max_length=50, verbose_name="風格名稱")
    description = models.TextField(verbose_name="風格描述")
    characteristics = models.JSONField(default=list, verbose_name="風格特徵")  # 存儲特徵列表
    suitable_spaces = models.JSONField(default=list, verbose_name="適合空間")  # 存儲適合的空間類型
    
    class Meta:
        verbose_name = "設計風格"
        verbose_name_plural = "設計風格"
    
    def __str__(self):
        return self.name

class RecommendationRequest(models.Model):
    """推薦請求記錄"""
    STATUS_CHOICES = [
        ('pending', '處理中'),
        ('completed', '已完成'),
        ('failed', '失敗'),
    ]
    
    # 用戶輸入的資料
    room_area = models.FloatField(verbose_name="房間總坪數")
    dimensions = models.CharField(max_length=100, verbose_name="長寬高")
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="總預算")
    separate_budget = models.CharField(max_length=200, blank=True, verbose_name="分別預算")
    special_requirements = models.TextField(blank=True, verbose_name="特殊需求")
    selected_style = models.ForeignKey(Style, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="選擇風格")
    
    # 圖片（Base64編碼存儲）
    real_photo = models.TextField(blank=True, verbose_name="實體圖")
    floor_plan = models.TextField(blank=True, verbose_name="平面圖")
    
    # 推薦結果
    ai_recommendation = models.JSONField(default=dict, verbose_name="AI推薦結果")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="狀態")
    
    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "推薦請求"
        verbose_name_plural = "推薦請求"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"推薦請求 - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class RecommendationItem(models.Model):
    """推薦項目"""
    request = models.ForeignKey(RecommendationRequest, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="產品分類")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="推薦產品")
    quantity = models.FloatField(verbose_name="數量")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="總價")
    ai_score = models.FloatField(verbose_name="AI推薦分數", help_text="0-1之間的分數")
    reason = models.TextField(verbose_name="推薦理由")
    
    class Meta:
        verbose_name = "推薦項目"
        verbose_name_plural = "推薦項目"
    
    def __str__(self):
        return f"{self.product.name} - 分數: {self.ai_score}"
