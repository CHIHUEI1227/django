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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='帳號')
    profile_pic = models.ImageField(upload_to='profile_pics', default='default.jpg', verbose_name='頭像')
    bio = models.TextField(blank=True, verbose_name='自介')
    favorite_foods = models.CharField(max_length=200, blank=True, help_text="請列出您喜愛的食物，用逗號分隔", verbose_name='喜愛食物')
    food_restrictions = models.CharField(max_length=200, blank=True, help_text="請列出您的飲食禁忌，用逗號分隔", verbose_name='飲食禁忌')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='general', verbose_name='使用者類型')
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS_CHOICES, default='unverified', verbose_name='驗證狀態')
    business_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='商家名稱')
    business_address = models.CharField(max_length=200, blank=True, null=True, verbose_name='商家地址')
    business_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='商家電話')
    
    class Meta:
        verbose_name = '個人資料'
        verbose_name_plural = '個人資料'

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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="announcements", verbose_name="發布者")
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

# 貼文與留言
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    title = models.CharField(max_length=100, verbose_name='標題')
    content = models.TextField(verbose_name='內容')
    image = models.ImageField(upload_to='post_images', blank=True, null=True, verbose_name='圖片')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    is_pinned = models.BooleanField(default=False, help_text="是否將貼文置頂於個人頁面", verbose_name='是否置頂')
    is_platform_featured = models.BooleanField(default=False, help_text="是否為平台推薦貼文", verbose_name='平台推薦')
    location_name = models.CharField(max_length=200, blank=True, null=True, help_text="餐廳名稱或地點名稱", verbose_name='地點名稱')
    location_address = models.CharField(max_length=300, blank=True, null=True, help_text="餐廳地址", verbose_name='地點地址')
    location_lat = models.FloatField(null=True, blank=True, help_text="地點緯度", verbose_name='緯度')
    location_lng = models.FloatField(null=True, blank=True, help_text="地點經度", verbose_name='經度')
    location_place_id = models.CharField(max_length=300, blank=True, null=True, help_text="Google Places ID", verbose_name='Place ID')
    restaurant = models.ForeignKey('restaurants.Restaurant',on_delete=models.SET_NULL,null=True, blank=True,verbose_name='關聯餐廳',help_text='可留空；後端會依 Place ID 自動對應/建立')
    
    class Meta:
        verbose_name = '貼文'
        verbose_name_plural = '貼文'

    def __str__(self):
        return self.title

# 用戶收藏的貼文
class FavoritePost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='使用者')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='貼文')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏時間')
    
    class Meta:
        # 確保每個用戶只能收藏同一貼文一次
        unique_together = ('user', 'post')
        ordering = ['-created_at']
        verbose_name = '收藏貼文'
        verbose_name_plural = '收藏貼文'
    
    def __str__(self):
        return f'{self.user.username} favorited {self.post.title}'

# 用戶收藏餐廳
class FavoriteRestaurant(models.Model):
    """用戶收藏的餐廳（指向 restaurants.Restaurant）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='favorite_restaurants', verbose_name='使用者')
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE,related_name='favorited_by', verbose_name='餐廳')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏時間')
    
    class Meta:
        # 確保每個用戶只能收藏同一餐廳一次
        unique_together = ('user', 'restaurant')
        ordering = ['-created_at']
        verbose_name = '收藏餐廳'
        verbose_name_plural = '收藏餐廳'
    
    def __str__(self):
        return f'{self.user.username} 收藏 {self.restaurant.name}'

# 追蹤收藏
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following', verbose_name='追蹤者')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', verbose_name='被追蹤者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    
    class Meta:
        # 確保每個用戶只能追蹤另一個用戶一次
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']
        verbose_name = '追蹤關係'
        verbose_name_plural = '追蹤關係'   
    
    def __str__(self):
        return f'{self.follower.username} follows {self.followed.username}'


# 商家身份驗證申請
class BusinessVerification(models.Model):
    """商家身份驗證申請"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests', verbose_name='申請者')
    business_name = models.CharField(max_length=100, verbose_name='商家名稱')
    business_registration_number = models.CharField(max_length=50, verbose_name='統一編號/營業登記字號')
    business_address = models.CharField(max_length=200, verbose_name='商家地址')
    business_phone = models.CharField(max_length=20, verbose_name='商家電話')
    business_email = models.EmailField(verbose_name='商家 Email')
    registration_document = models.FileField(upload_to='verification_documents', verbose_name='證明文件')
    additional_notes = models.TextField(blank=True, verbose_name='補充說明')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='提交時間')
    status = models.CharField(max_length=10, choices=Profile.VERIFICATION_STATUS_CHOICES, default='pending', verbose_name='審核狀態')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews', verbose_name='審核者')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='審核時間')
    review_notes = models.TextField(blank=True, verbose_name='審核意見')
    
    class Meta:
        verbose_name = '商家驗證申請'
        verbose_name_plural = '商家驗證申請'

    def __str__(self):
        return f'{self.business_name} - {self.get_status_display()}'

# 用戶對貼文的評論
class Comment(models.Model):
    """用戶對貼文的評論"""
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments', verbose_name='貼文')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='留言者')
    content = models.TextField(verbose_name='留言內容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name='回覆對象')
    
    class Meta:
        ordering = ['created_at']  # 按時間順序排列評論
        verbose_name = '留言'
        verbose_name_plural = '留言'
        
    def __str__(self):
        return f'{self.user.username}的評論 on {self.post.title}'
        
    def get_replies(self):
        """獲取評論的回覆"""
        return Comment.objects.filter(parent=self).order_by('created_at')
        
    def is_reply(self):
        """判斷是否為回覆評論"""
        return self.parent is not None

# 用戶對貼文的表情符號反應
class Reaction(models.Model):
    """用戶對貼文的表情符號反應"""
    REACTION_CHOICES = (
        ('like', '👍 讚'),
        ('love', '❤️ 愛心'),
        ('haha', '😄 哈哈'),
        ('wow', '😲 哇'),
        ('sad', '😢 傷心'),
        ('angry', '😠 怒')
    )
    
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='reactions', verbose_name='貼文')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='使用者')
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES, verbose_name='反應類型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    
    class Meta:
        # 確保每個用戶只能對同一貼文有一種反應
        unique_together = ('user', 'post')
        verbose_name = '互動反應'
        verbose_name_plural = '互動反應'
        
    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()} - {self.post.title}"

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
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='接收者')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications', verbose_name='發送者')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, verbose_name='通知類型')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True, verbose_name='關聯貼文')
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, verbose_name='關聯留言')
    message = models.TextField(verbose_name='通知內容')
    is_read = models.BooleanField(default=False, verbose_name='是否已讀')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = '通知'
        
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
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_submitted', verbose_name='檢舉者')
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES, verbose_name='回報類型')
    post = models.ForeignKey('Post', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='被回報貼文')
    comment = models.ForeignKey('Comment', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='被回報留言')
    reported_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_received', verbose_name='被回報用戶')
    reason = models.TextField(verbose_name='回報原因')
    status = models.CharField(max_length=10, choices=REPORT_STATUS, default='pending', verbose_name='處理狀態')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_reports', verbose_name='處理者')
    handled_at = models.DateTimeField(null=True, blank=True, verbose_name='處理時間')
    admin_notes = models.TextField(blank=True, verbose_name='管理備註')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '回報'
        verbose_name_plural = '回報'
        
    def __str__(self):
        return f"回報 #{self.id} - {self.get_report_type_display()} - {self.get_status_display()}"


