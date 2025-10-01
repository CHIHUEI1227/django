from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .api import CustomAuthToken, LogoutView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
    path('followers/', views.followers, name='followers'),
    path('following/', views.following, name='following'),
    path('following/<int:user_id>/', views.following, name='user_following'),
    path('meal_dashboard/', views.user_meal_dashboard, name='user_meal_dashboard'),

    # 商家認證相關
    path('verification/apply/', views.apply_for_verification, name='apply_for_verification'),
    path('verification/review/<int:verification_id>/', views.review_verification, name='review_verification'),
    path('admin/verifications/', views.admin_verification_list, name='admin_verification_list'),
    # 管理員功能
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # 系統公告相關
    path('announcements/', views.view_announcements, name='view_announcements'),
    path('announcement/<int:announcement_id>/', views.view_announcement, name='view_announcement'),
    path('admin/announcements/', views.announcement_list, name='announcement_list'),
    path('admin/announcement/new/', views.create_announcement, name='create_announcement'),
    path('admin/announcement/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('admin/announcement/<int:announcement_id>/delete/', views.delete_announcement, name='delete_announcement'),
    path('admin/announcement/<int:announcement_id>/toggle/', views.toggle_announcement, name='toggle_announcement'),
    # 動態牆與探索頁面功能
    path('feed/', views.feed, name='feed'),
    path('explore/', views.explore, name='explore'),
    # 單一貼文頁面與編輯功能（已移除貼文相關）
    # 通知系統
    path('notifications/', views.notifications, name='notifications'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notification/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    # 回報系統
    path('report/post/<int:post_id>/', views.report_post, name='report_post'),
    path('report/comment/<int:comment_id>/', views.report_comment, name='report_comment'),
    path('report/user/<int:user_id>/', views.report_user, name='report_user'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/report/<int:report_id>/handle/', views.handle_report, name='handle_report'),
    # 公開用戶主頁
    path('user/<str:username>/', views.public_profile, name='public_profile'),
    # API端点 - Token认证
    path('api/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('api/logout/', LogoutView.as_view(), name='api_logout'),
    # 餐廳收藏相關
    path('restaurant/favorite/', views.toggle_favorite_restaurant, name='toggle_favorite_restaurant'),
    path('restaurant/favorites/', views.favorite_restaurants, name='favorite_restaurants'),
    path('restaurant/favorite/delete/<int:favorite_id>/', views.delete_favorite_restaurant, name='delete_favorite_restaurant'),
    path('restaurant/check_favorite/', views.check_favorite_restaurant, name='check_favorite_restaurant'),
]