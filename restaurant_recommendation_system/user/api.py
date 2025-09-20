from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Profile
from .serializers import UserSerializer, ProfileSerializer, PostSerializer, CommentSerializer
from post.models import  Post, Comment

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # 删除用户的token
        request.user.auth_token.delete()
        return Response({"message": "成功登出"}, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """获取当前用户的个人资料"""
        user = request.user
        profile = user.profile
        user_serializer = UserSerializer(user)
        profile_serializer = ProfileSerializer(profile)
        
        return Response({
            'user': user_serializer.data,
            'profile': profile_serializer.data
        })

class PostViewSet(viewsets.ModelViewSet):
    """帖子的API视图集，提供CRUD操作"""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取贴文列表，根据请求参数过滤"""
        queryset = Post.objects.all().order_by('-created_at')
        
        # 获取指定用户的贴文
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset
    
    def perform_create(self, serializer):
        """创建新贴文时设置用户为当前用户"""
        serializer.save(user=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    """评论的API视图集"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取特定帖子的评论"""
        post_id = self.request.query_params.get('post_id')
        if post_id:
            return Comment.objects.filter(post_id=post_id).order_by('-created_at')
        return Comment.objects.none()
    
    def perform_create(self, serializer):
        """创建评论时设置用户和帖子"""
        post_id = self.request.data.get('post_id')
        post = Post.objects.get(id=post_id)
        serializer.save(user=self.request.user, post=post) 