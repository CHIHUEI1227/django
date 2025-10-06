from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_restaurants, name='search_restaurants'),
    path('detail/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    # 其他路由...
]