from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'chathistory', views.ChatHistoryViewSet, basename='chathistory')

urlpatterns = [
    path('process_message/', views.ProcessMessageAPIView.as_view(), name='process_message'),
] + router.urls
