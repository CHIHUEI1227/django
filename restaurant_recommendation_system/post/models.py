from django.db import models
from django.contrib.auth.models import User

# 貼文與留言
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False, help_text="是否將貼文置頂於個人頁面")
    is_platform_featured = models.BooleanField(default=False, help_text="是否為平台推薦貼文")
    location_name = models.CharField(max_length=200, blank=True, null=True, help_text="餐廳名稱或地點名稱")
    location_address = models.CharField(max_length=300, blank=True, null=True, help_text="餐廳地址")
    location_lat = models.FloatField(null=True, blank=True, help_text="地點緯度")
    location_lng = models.FloatField(null=True, blank=True, help_text="地點經度")
    location_place_id = models.CharField(max_length=300, blank=True, null=True, help_text="Google Places ID")
    
    POST_TYPE_CHOICES = [
        ('promotion', '優惠'),
        ('experience', '用餐體驗'),
    ]
    type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='experience')

    def __str__(self):
        return self.title

# 貼文圖片
class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/')
    
# 用戶對貼文的評論
class Comment(models.Model):
    """用戶對貼文的評論"""
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']  # 按時間順序排列評論
        
    def __str__(self):
        return f'{self.user.username}的評論 on {self.post.title}'
        
    def get_replies(self):
        """獲取評論的回覆"""
        return Comment.objects.filter(parent=self).order_by('created_at')
        
    def is_reply(self):
        """判斷是否為回覆評論"""
        return self.parent is not None

# 用戶對貼文的表情符號反應
class PostReaction(models.Model):
    """用戶對貼文的表情符號反應"""
    REACTION_CHOICES = (
        ('like', '👍 讚'),
        ('love', '❤️ 愛心'),
        ('haha', '😄 哈哈'),
        ('wow', '😲 哇'),
        ('sad', '😢 傷心'),
        ('angry', '😠 怒')
    )
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # 確保每個用戶只能對同一貼文有一種反應
        unique_together = ('user', 'post')
        
    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()} - {self.post.title}"

# 用戶收藏的貼文
class FavoritePost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

