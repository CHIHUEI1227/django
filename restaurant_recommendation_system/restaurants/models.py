from django.db import models
from django.utils import timezone

# ==============================
#  餐廳資料
# ==============================

BUSINESS_STATUS_CHOICES = (
    ("OPERATIONAL", "營業中（官方狀態）"),
    ("CLOSED_TEMPORARILY", "暫時停業（官方狀態）"),
    ("CLOSED_PERMANENTLY", "永久停業（官方狀態）"),
)

OPEN_STATUS_CHOICES = (
    ("open", "營業中"),
    ("closed", "已打烊"),
    ("unknown", "未知"),
)

PRICE_LEVEL_CHOICES = (
    (0, "免費 / 未定價"),
    (1, "$"),
    (2, "$$"),
    (3, "$$$"),
    (4, "$$$$"),
)

SOURCE_CHOICES = (
    ("places_details", "Google Places Details"),
    ("places_textsearch", "Google Places Text Search"),
    ("gmaps_scrape", "Google Maps 抓取"),
    ("ifoodie", "愛食記"),
    ("gmap_photo", "Google Photo API"),
    ("manual", "手動"),
)

# 餐廳資料
class Restaurant(models.Model):
    """餐廳主檔（以 place_id 去重；地址簡化）"""
    # 識別/基本
    place_id = models.CharField(max_length=300, unique=True, verbose_name="Place ID", help_text="來源唯一識別碼")
    name = models.CharField(max_length=200, verbose_name="餐廳名稱")
    formatted_address = models.CharField(max_length=400, blank=True, verbose_name="完整地址")
    # 座標
    lat = models.FloatField(null=True, blank=True, verbose_name="緯度")
    lng = models.FloatField(null=True, blank=True, verbose_name="經度")
    # 狀態/評分
    business_status = models.CharField(max_length=30, choices=BUSINESS_STATUS_CHOICES, default="OPERATIONAL", verbose_name="官方營運狀態")
    open_status = models.CharField(max_length=10, choices=OPEN_STATUS_CHOICES, default="unknown", verbose_name="當前營業狀態", help_text="open=營業中 / closed=已打烊 / unknown=未知")
    price_level = models.PositiveSmallIntegerField(choices=PRICE_LEVEL_CHOICES, null=True, blank=True, verbose_name="價位等級")
    rating = models.FloatField(null=True, blank=True, verbose_name="平均評分")
    user_ratings_total = models.IntegerField(null=True, blank=True, verbose_name="評分數量")
    types = models.JSONField(blank=True, null=True, verbose_name="類別清單")
    # 聯絡/連結
    website = models.URLField(blank=True, verbose_name="官方網站")
    google_maps_url = models.URLField(blank=True, verbose_name="Google 地圖連結")
    # 營業時間（文字）
    weekday_text = models.JSONField(blank=True, null=True, verbose_name="每週營業時間（文字）")
    # 內容
    description = models.TextField(blank=True, verbose_name="描述")
    # 更新欄位
    first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name="首次寫入時間")
    last_fetched_at = models.DateTimeField(default=timezone.now, verbose_name="最近抓取時間")

    class Meta:
        verbose_name = "餐廳"
        verbose_name_plural = "餐廳"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["lat", "lng"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.place_id})"

    def is_open_now(self) -> bool:
        if self.open_status == 'open':
            return True
        if self.open_status == 'closed':
            return False
        return bool(self.current_open_now)

# 營業時間（天）
class RestaurantOpeningHour(models.Model):
    """每週一般營業時間（週期性；支援跨日）。"""
    WEEKDAY_CHOICES = (
        (0, "週一"), (1, "週二"), (2, "週三"), (3, "週四"), (4, "週五"), (5, "週六"), (6, "週日"),
    )
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="opening_hours", verbose_name="餐廳")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES, verbose_name="星期")
    open_time = models.TimeField(verbose_name="開門時間")
    close_time = models.TimeField(verbose_name="打烊時間")
    crosses_midnight = models.BooleanField(default=False, verbose_name="是否跨日")

    class Meta:
        verbose_name = "營業時間（每週）"
        verbose_name_plural = "營業時間（每週）"
        indexes = [models.Index(fields=["restaurant", "weekday"])]


# 餐廳圖片
class RestaurantPhoto(models.Model):
    """餐廳圖片。"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="photos", verbose_name="餐廳")
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default="gmap_photo", verbose_name="來源")
    photo_reference = models.CharField(max_length=500, blank=True, verbose_name="Photo Reference")
    remote_url = models.URLField(blank=True, verbose_name="遠端圖片 URL")
    file = models.ImageField(upload_to="restaurant_photos", blank=True, verbose_name="本地圖片檔")
    width = models.IntegerField(null=True, blank=True, verbose_name="寬度")
    height = models.IntegerField(null=True, blank=True, verbose_name="高度")
    attribution = models.TextField(blank=True, verbose_name="版權/出處標示")
    collected_at = models.DateTimeField(auto_now_add=True, verbose_name="蒐集時間")

    class Meta:
        verbose_name = "餐廳圖片"
        verbose_name_plural = "餐廳圖片"
        indexes = [models.Index(fields=["restaurant"])]

# 餐廳評論
class RestaurantReview(models.Model):
    """評論快照。"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="reviews", verbose_name="餐廳")
    author_name = models.CharField(max_length=120, blank=True, verbose_name="作者名稱")
    author_url = models.URLField(blank=True, verbose_name="作者連結")
    rating = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="評分（1-5）")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="評論時間")
    text = models.TextField(blank=True, verbose_name="評論內容")
    category_scores = models.JSONField(blank=True, null=True, verbose_name="類別及細項評分")  # 餐點/服務/氣氛等
    # 你可視需求保留 source 欄位（如需追蹤評論來源）
    # 你可視需求保留 raw_json 欄位（如需存原始資料）

    class Meta:
        verbose_name = "餐廳評論"
        verbose_name_plural = "餐廳評論"
        indexes = [
            models.Index(fields=["restaurant", "rating"]),
            models.Index(fields=["restaurant", "published_at"]),
        ]

# 餐廳彈性屬性
class RestaurantAttribute(models.Model):
    """彈性屬性（可訂位、外送、素食、寵物友善、插座、Wi-Fi 等）。"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="attributes", verbose_name="餐廳")
    key = models.CharField(max_length=60, verbose_name="屬性鍵")
    value = models.CharField(max_length=120, blank=True, verbose_name="屬性值")
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, default="manual", verbose_name="來源")

    class Meta:
        verbose_name = "餐廳屬性"
        verbose_name_plural = "餐廳屬性"
        unique_together = ("restaurant", "key")

# 來源追蹤
class RestaurantSourceMeta(models.Model):
    """來源抓取/配額/版本資訊（除錯與稽核）。"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="source_meta", verbose_name="餐廳")
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES, verbose_name="來源")
    fetched_at = models.DateTimeField(default=timezone.now, verbose_name="抓取時間")
    status_code = models.CharField(max_length=20, blank=True, verbose_name="來源回應碼")
    etag = models.CharField(max_length=80, blank=True, verbose_name="ETag/版本")
    quota_cost = models.IntegerField(null=True, blank=True, verbose_name="配額消耗")
    raw_json = models.JSONField(blank=True, null=True, verbose_name="原始 JSON")

    class Meta:
        verbose_name = "來源追蹤"
        verbose_name_plural = "來源追蹤"
        indexes = [models.Index(fields=["restaurant", "source", "fetched_at"]) ]

# 餐廳指標細項表
class RestaurantIndicatorDetail(models.Model):
    """餐廳指標細項（如食物、服務、環境、價錢等，來源可追蹤）。"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='indicator_details', verbose_name="餐廳")
    indicator_type = models.CharField(max_length=20, help_text="指標類型（食物/服務/環境/價錢等）", verbose_name="指標類型")
    score = models.FloatField(help_text="該指標的分數（如情感分數）", verbose_name="分數")
    source = models.CharField(max_length=20, help_text="來源（post/review等）", verbose_name="來源")
    source_id = models.IntegerField(null=True, blank=True, help_text="來源的ID，例如貼文ID", verbose_name="來源ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "餐廳指標細項"
        verbose_name_plural = "餐廳指標細項"
        indexes = [
            models.Index(fields=['restaurant', 'indicator_type']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.indicator_type}: {self.score}"

# 餐廳指標總表
class RestaurantIndicatorSummary(models.Model):
    """餐廳指標總表（彙總各細項分數，方便查詢與排序）。"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='indicator_summaries', verbose_name="餐廳")
    indicator_type = models.CharField(max_length=20, verbose_name="指標類型")
    total_score = models.FloatField(verbose_name="總分數")
    count = models.IntegerField(default=0, verbose_name="統計次數")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "餐廳指標總表"
        verbose_name_plural = "餐廳指標總表"
        unique_together = ("restaurant", "indicator_type")
        indexes = [
            models.Index(fields=['restaurant', 'indicator_type']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.indicator_type}: {self.total_score} (n={self.count})"
