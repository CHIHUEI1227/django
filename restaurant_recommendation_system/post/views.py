from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, Http404
from django.conf import settings
from django.db.models import Count, Q, Prefetch
from post.models import Post, FavoritePost, Comment, PostReaction
from user.models import Notification
from post.forms import PostCreateForm, CommentForm

# 發布新貼文
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, '貼文已成功建立！')
            return redirect('post_history')
    else:
        form = PostCreateForm()
    context = {
        'form': form,
        'google_api_key': settings.GOOGLE_PLACES_API_KEY
    }
    return render(request, 'post/create_post.html', context)

# 用戶貼文清單
@login_required
def post_history(request):
    posts = Post.objects.filter(user=request.user).order_by('-is_pinned', '-created_at')
    return render(request, 'post/post_history.html', {'posts': posts})

# 用戶編輯貼文
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        messages.error(request, '您沒有權限編輯此貼文')
        return redirect('post_history')
    if request.method == 'POST':
        form = PostCreateForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, '貼文已成功更新！')
            return redirect('view_post', post_id=post.id)
    else:
        form = PostCreateForm(instance=post)
    context = {
        'form': form,
        'post': post,
        'google_api_key': settings.GOOGLE_PLACES_API_KEY,
        'is_edit': True
    }
    return render(request, 'post/create_post.html', context)

# 用戶切換貼文置頂狀態
@login_required
def toggle_post_pin(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '您沒有權限修改此貼文'})
        messages.error(request, '您沒有權限修改此貼文')
        return redirect('post_history')
    post.is_pinned = not post.is_pinned
    post.save()
    action = "置頂" if post.is_pinned else "取消置頂"
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'is_pinned': post.is_pinned,
            'message': f'已{action}貼文'
        })
    messages.success(request, f'已{action}貼文')
    return redirect('post_history')

# 管理員刪除貼文
@staff_member_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, '貼文已被刪除')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    return render(request, 'user/confirm_delete.html', {
        'item_type': '貼文',
        'item': post,
        'cancel_url': request.META.get('HTTP_REFERER', 'home')
    })

# 管理員設置推薦貼文
@staff_member_required
def toggle_post_feature(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_platform_featured = not post.is_platform_featured
    post.save()
    action = "設為平台推薦" if post.is_platform_featured else "取消平台推薦"
    messages.success(request, f'已{action}貼文')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# 貼文詳情 + 留言 + 表情反應統計
def view_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    is_favorited = False
    comments = Comment.objects.filter(post=post, parent=None).order_by('created_at')
    reactions_count = {
        reaction_type: PostReaction.objects.filter(post=post, reaction_type=reaction_type).count()
        for reaction_type, _ in PostReaction.REACTION_CHOICES
    }
    total_reactions = sum(reactions_count.values())
    user_reaction = None
    if request.user.is_authenticated:
        is_favorited = FavoritePost.objects.filter(user=request.user, post=post).exists()
        comment_form = CommentForm()
        try:
            user_reaction = PostReaction.objects.get(user=request.user, post=post).reaction_type
        except PostReaction.DoesNotExist:
            pass
    else:
        comment_form = None
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            parent_comment_id = request.POST.get('parent_comment_id')
            if parent_comment_id:
                parent_comment = get_object_or_404(Comment, id=parent_comment_id)
                new_comment.parent = parent_comment
            new_comment.save()
            if parent_comment_id:
                if new_comment.parent.user != request.user:
                    Notification.objects.create(
                        recipient=new_comment.parent.user,
                        sender=request.user,
                        notification_type='reply',
                        post=post,
                        comment=new_comment,
                        message=f"{request.user.username} 回覆了您的評論: {new_comment.content[:50]}..."
                    )
            else:
                if post.user != request.user:
                    Notification.objects.create(
                        recipient=post.user,
                        sender=request.user,
                        notification_type='comment',
                        post=post,
                        comment=new_comment,
                        message=f"{request.user.username} 評論了您的貼文: {new_comment.content[:50]}..."
                    )
            messages.success(request, '評論已發布！')
            return redirect('view_post', post_id=post.id)
        else:
            messages.error(request, '發布評論失敗，請檢查您的輸入。')
    other_posts = Post.objects.filter(
        user=post.user
    ).exclude(id=post.id).order_by('-created_at')[:5]  # 取最新5篇
    context = {
        'post': post,
        'is_favorited': is_favorited,
        'google_api_key': settings.GOOGLE_PLACES_API_KEY,
        'comments': comments,
        'comment_form': comment_form,
        'reactions_count': reactions_count,
        'total_reactions': total_reactions,
        'user_reaction': user_reaction,
        'other_posts': other_posts,
    }
    return render(request, 'post/view_post.html', context)

# 新增/變更對貼文的表情反應
@login_required
def add_reaction(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        reaction_type = request.POST.get('reaction_type')
        print("reaction_type:", reaction_type)
        print("post:", post)
        print("request.user:", request.user)
        valid_reactions = dict(PostReaction.REACTION_CHOICES).keys()
        if reaction_type not in valid_reactions:
            return JsonResponse({'status': 'error', 'message': '無效的表情符號類型'})
        reaction, created = PostReaction.objects.update_or_create(
            user=request.user, 
            post=post,
            defaults={'reaction_type': reaction_type}
        )
        reactions_count = {
            r_type: PostReaction.objects.filter(post=post, reaction_type=r_type).count()
            for r_type, _ in PostReaction.REACTION_CHOICES
        }
        total_reactions = sum(reactions_count.values())
        if post.user != request.user:
            reaction_display = dict(PostReaction.REACTION_CHOICES)[reaction_type]
            Notification.objects.create(
                recipient=post.user,
                sender=request.user,
                notification_type='reaction',
                post=post,
                message=f"{request.user.username} 對您的貼文添加了 {reaction_display}"
            )
        return JsonResponse({
            'status': 'success',
            'created': created,
            'message': '已新增反應' if created else '已更新反應',
            'reactions_count': reactions_count,
            'total_reactions': total_reactions
        })
    return JsonResponse({'status': 'error', 'message': '僅支持POST請求'})

# 移除自己對貼文的表情反應
@login_required
def remove_reaction(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        try:
            reaction = PostReaction.objects.get(user=request.user, post=post)
            reaction.delete()
            reactions_count = {
                r_type: PostReaction.objects.filter(post=post, reaction_type=r_type).count()
                for r_type, _ in PostReaction.REACTION_CHOICES
            }
            total_reactions = sum(reactions_count.values())
            return JsonResponse({
                'status': 'success',
                'message': '已移除反應',
                'reactions_count': reactions_count,
                'total_reactions': total_reactions
            })
        except PostReaction.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '沒有找到反應'})
    return JsonResponse({'status': 'error', 'message': '僅支持POST請求'})

# 收藏/取消收藏貼文
@login_required
def toggle_favorite(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    favorite, created = FavoritePost.objects.get_or_create(user=request.user, post=post)
    if not created:
        favorite.delete()
        is_favorite = False
        message = "已取消收藏"
    else:
        is_favorite = True
        message = "已加入收藏"
        if post.user != request.user:
            Notification.objects.create(
                recipient=post.user,
                sender=request.user,
                notification_type='favorite',
                post=post,
                message=f"{request.user.username} 收藏了您的貼文: {post.title}"
            )
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'is_favorite': is_favorite,
            'message': message
        })
    return redirect(request.META.get('HTTP_REFERER', 'post_history'))

# 我的收藏貼文清單
@login_required
def favorites(request):
    """顯示用戶收藏的貼文"""
    favorites = FavoritePost.objects.filter(user=request.user).select_related('post', 'post__user')
    return render(request, 'social/favorites.html', {'favorites': favorites})



@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user == request.user or request.user.is_staff:
        comment.delete()
        messages.success(request, "評論已刪除。")
    else:
        messages.error(request, "您沒有權限刪除此評論。")
    return redirect(request.META.get('HTTP_REFERER', '/'))

def add_favorite(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    FavoritePost.objects.get_or_create(user=request.user, post=post)
    return JsonResponse({'status': 'success', 'message': '已收藏'})

@login_required
def remove_favorite(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    FavoritePost.objects.filter(user=request.user, post=post).delete()
    return JsonResponse({'status': 'success', 'message': '已取消收藏'})
