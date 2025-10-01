from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import CustomAuthToken, LogoutView, UserProfileView, PostViewSet, CommentViewSet

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # Token认证
    path('token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    
    # 用户资料
    path('profile/', UserProfileView.as_view(), name='api_profile'),
    
    # 视图集API
    path('', include(router.urls)),
] 