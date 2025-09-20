from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from post.models import Post, Comment
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['user', 'image', 'bio', 'user_type', 'verification_status',
                  'business_name', 'business_address', 'business_phone']
        read_only_fields = ['verification_status']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'user', 'title', 'content', 'created_at', 'updated_at',
                  'location_name', 'location_lat', 'location_lng', 'image',
                  'is_featured', 'is_pinned', 'comments']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_featured'] 