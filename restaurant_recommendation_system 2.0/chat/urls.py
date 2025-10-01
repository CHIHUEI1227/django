from django.urls import path
from . import views
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', views.home, name='home'),
    path('chat_room/', views.chat_room, name='chat_room'),
    path('assistant/', views.chat_assistant, name='chat_assistant'),
    path('explore/', views.explore, name='explore'),
    path('about/', views.about, name='about'),
    path('send_message/', views.send_message, name='send_message'),
    path('proxy_photo/', views.proxy_photo, name='proxy_photo'),
    path('preferences/', views.user_preferences, name='user_preferences'),
    
    # 聊天記錄相關路由
    path('history/', views.chat_history_list, name='chat_history_list'),
    path('save_chat/', views.save_chat_history, name='save_chat_history'),
    path('history/<int:chat_id>/', views.load_chat_history, name='load_chat_history'),
    path('history/<int:chat_id>/delete/', views.delete_chat_history, name='delete_chat_history'),
] 