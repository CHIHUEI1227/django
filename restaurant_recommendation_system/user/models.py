from django.db import models
from django.contrib.auth.models import User

# 使用者個人資料擴展
class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('general', '一般使用者'),
        ('business', '商家'),
        ('admin', '管理員'),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('unverified', '未驗證'),
        ('pending', '審核中'),
        ('verified', '已驗證'),
        ('rejected', '已拒絕'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics', default='default.jpg')
    bio = models.TextField(blank=True)
    favorite_foods = models.CharField(max_length=200, blank=True, help_text="請列出您喜愛的食物，用逗號分隔")
    food_restrictions = models.CharField(max_length=200, blank=True, help_text="請列出您的飲食禁忌，用逗號分隔")
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='general')
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='unverified')
    business_name = models.CharField(max_length=100, blank=True, null=True)
    business_address = models.CharField(max_length=200, blank=True, null=True)
    business_phone = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def is_business(self):
        return self.user_type == 'business'
    
    def is_admin(self):
        return self.user_type == 'admin'

# 系統公告
class Announcement(models.Model):
    """系統公告模型，用於管理員發布重要通知"""
    ANNOUNCEMENT_TYPES = (
        ('system', '系統公告'),
        ('maintenance', '系統維護'),
        ('update', '功能更新'),
        ('promotion', '活動宣傳'),
        ('other', '其他')
    )
    
    title = models.CharField(max_length=200, verbose_name="公告標題")
    content = models.TextField(verbose_name="公告內容")
    announcement_type = models.CharField(max_length=15, choices=ANNOUNCEMENT_TYPES, default='system', verbose_name="公告類型")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="發布者", related_name="announcements")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="發布時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    is_pinned = models.BooleanField(default=False, verbose_name="是否置頂")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="開始日期")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="結束日期")
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = "系統公告"
        verbose_name_plural = "系統公告"
    
    def __str__(self):
        return self.title
    
    def is_valid(self):
        """檢查公告是否在有效期內"""
        from django.utils import timezone
        now = timezone.now()
        
        # 如果沒有設置開始或結束日期，視為一直有效
        if not self.start_date and not self.end_date:
            return self.is_active
        
        # 檢查是否在有效期內
        is_after_start = True if not self.start_date else now >= self.start_date
        is_before_end = True if not self.end_date else now <= self.end_date
        
        return self.is_active and is_after_start and is_before_end




# 用戶收藏餐廳
class FavoriteRestaurant(models.Model):
    """用戶收藏的餐廳"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_restaurants')
    restaurant_name = models.CharField(max_length=200)
    restaurant_address = models.CharField(max_length=300, blank=True, null=True)
    restaurant_image_url = models.URLField(blank=True, null=True)
    restaurant_place_id = models.CharField(max_length=300, blank=True, null=True)
    restaurant_rating = models.FloatField(null=True, blank=True)
    restaurant_price_level = models.IntegerField(null=True, blank=True)
    restaurant_lat = models.FloatField(null=True, blank=True)
    restaurant_lng = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # 確保每個用戶只能收藏同一餐廳一次
        unique_together = ('user', 'restaurant_place_id')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} favorited restaurant: {self.restaurant_name}'

# 追蹤收藏
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # 確保每個用戶只能追蹤另一個用戶一次
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.follower.username} follows {self.followed.username}'


# 商家身份驗證申請
class BusinessVerification(models.Model):
    """商家身份驗證申請"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    business_name = models.CharField(max_length=100)
    business_registration_number = models.CharField(max_length=50)
    business_address = models.CharField(max_length=200)
    business_phone = models.CharField(max_length=20)
    business_email = models.EmailField()
    registration_document = models.FileField(upload_to='verification_documents')
    additional_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Profile.VERIFICATION_STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f'{self.business_name} - {self.get_status_display()}'


# 用戶通知系統
class Notification(models.Model):
    """用戶通知系統"""
    NOTIFICATION_TYPES = (
        ('comment', '評論'),
        ('reply', '回覆'),
        ('follow', '追蹤'),
        ('favorite', '收藏'),
        ('reaction', '表情符號'),
        ('system', '系統通知')
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey('post.Post', on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey('post.Comment', on_delete=models.CASCADE, blank=True, null=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.recipient.username}的通知 - {self.get_notification_type_display()}"
        
    def mark_as_read(self):
        """標記通知為已讀"""
        self.is_read = True
        self.save()

# 用戶回報系統
class Report(models.Model):
    """用戶回報系統"""
    REPORT_TYPES = (
        ('post', '貼文'),
        ('comment', '評論'),
        ('user', '用戶'),
        ('other', '其他')
    )
    
    REPORT_STATUS = (
        ('pending', '待處理'),
        ('processing', '處理中'),
        ('resolved', '已解決'),
        ('rejected', '已拒絕')
    )
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted')
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    post = models.ForeignKey('post.Post', on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.ForeignKey('post.Comment', on_delete=models.SET_NULL, null=True, blank=True)
    reported_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_received')
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=REPORT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_reports')
    handled_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"回報 #{self.id} - {self.get_report_type_display()} - {self.get_status_display()}"


