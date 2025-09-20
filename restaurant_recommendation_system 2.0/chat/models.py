from django.db import models
from django.contrib.auth.models import User

# 使用者與機器人訊息流
class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    content = models.TextField(verbose_name='訊息內容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='時間戳')
    is_bot_response = models.BooleanField(default=False, verbose_name='是否為機器人回覆')
    
    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = '訊息'
        verbose_name_plural = '訊息'

# 聊天歷史記錄
class ChatHistory(models.Model):
    """用戶的聊天歷史記錄"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_histories', verbose_name='使用者')
    title = models.CharField(max_length=255, help_text="聊天標題", verbose_name='聊天標題')
    content = models.TextField(help_text="完整的聊天內容HTML", verbose_name='聊天內容（HTML）')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = '聊天歷史'
        verbose_name_plural = '聊天歷史'
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"

# 推薦結果（食物名、圖、時間）
class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    food_name = models.CharField(max_length=100, verbose_name='食物名稱')
    description = models.TextField(verbose_name='描述')
    image = models.ImageField(upload_to='recommendation_images', blank=True, null=True, verbose_name='圖片')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    
    class Meta:
        verbose_name = '推薦結果'
        verbose_name_plural = '推薦結果'

    def __str__(self):
        return self.food_name

# 用戶總偏好
class UserPreference(models.Model):
    """用戶美食偏好"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='food_preferences', verbose_name='使用者')
    favorite_foods = models.TextField(blank=True, help_text="用户偏好的食物，以逗號分隔", verbose_name='偏好食物')
    food_restrictions = models.TextField(blank=True, help_text="飲食限制（如過敏、素食等）", verbose_name='飲食限制')
    preferred_price_level = models.IntegerField(null=True, blank=True, help_text="偏好的價格等級(0-4)", verbose_name='偏好價格等級')
    cuisine_preferences = models.TextField(blank=True, help_text="偏好的菜系，以逗號分隔", verbose_name='偏好菜系')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '使用者偏好'
        verbose_name_plural = '使用者偏好'

    def __str__(self):
        return f"{self.user.username}的飲食偏好"

# 用戶保存的地點
class SavedPlace(models.Model):
    """用戶保存的地點（指向 restaurants.Restaurant）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='saved_places', verbose_name='使用者')
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE,related_name='saved_by', verbose_name='餐廳')
    notes = models.TextField(blank=True, help_text="用戶對此地點的筆記", verbose_name='備註')
    saved_at = models.DateTimeField(auto_now_add=True, verbose_name='儲存時間')
    
    class Meta:
        unique_together = (('user', 'restaurant'),)
        verbose_name = '已儲存地點'
        verbose_name_plural = '已儲存地點'
    
    def __str__(self):
        return f"{self.user.username} - {self.restaurant.name}"

# 查詢歷史
class QueryHistory(models.Model):
    """用戶查詢歷史"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='query_history', verbose_name='使用者')
    query_text = models.TextField(verbose_name='查詢內容')
    response_text = models.TextField(verbose_name='回覆內容')
    tools_used = models.CharField(max_length=255, blank=True, help_text="使用的工具，以逗號分隔", verbose_name='使用工具')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '查詢歷史'
        verbose_name_plural = '查詢歷史'
    
    def __str__(self):
        return f"{self.user.username}: {self.query_text[:50]}"

# 細項偏好加分數
class UserPreferenceDetail(models.Model):
    """使用者偏好詳細資料表"""
    id = models.AutoField(primary_key=True, verbose_name='編號')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preference_details', verbose_name='使用者')
    preference_type = models.CharField(max_length=20, help_text="偏好類型（口味/菜系/地區/禁忌）", verbose_name='偏好類型')
    preference_value = models.CharField(max_length=255, help_text="偏好值（如：不辣/日式料理/台北市）", verbose_name='偏好值')
    score = models.FloatField(help_text="對該偏好的強度（+代表喜好，-代表排斥）", verbose_name='偏好分數')
    source = models.CharField(max_length=20, help_text="來源（dialog/post/collection）", verbose_name='來源')
    source_id = models.IntegerField(null=True, blank=True, help_text="對應該來源的id，例如貼文編號", verbose_name='來源ID')
    created_at = models.DateTimeField(auto_now_add=True, help_text="記錄建立時間", verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, help_text="最後更新時間", verbose_name='更新時間') 
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'preference_type']),
            models.Index(fields=['user', 'score']),
        ]
        verbose_name = '偏好明細'
        verbose_name_plural = '偏好明細'
    
    def __str__(self):
        return f"{self.user.username} - {self.preference_type}: {self.preference_value} ({self.score})"
