from django.urls import path
from . import views

urlpatterns = [
    path('new/', views.create_post, name='create_post'),
    path('history/', views.post_history, name='post_history'),
    path('<int:post_id>/', views.view_post, name='view_post'),
    path('<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('<int:post_id>/pin/', views.toggle_post_pin, name='toggle_post_pin'),
    path('<int:post_id>/feature/', views.toggle_post_feature, name='toggle_post_feature'),
    path('<int:post_id>/reaction/add/', views.add_reaction, name='add_reaction'),
    path('<int:post_id>/reaction/remove/', views.remove_reaction, name='remove_reaction'),
    path('favorite/<int:post_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.favorites, name='favorites'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('<int:post_id>/favorite/add/', views.add_favorite, name='add_favorite'),
    path('<int:post_id>/favorite/remove/', views.remove_favorite, name='remove_favorite'),

]