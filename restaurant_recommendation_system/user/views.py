from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Profile, Follow, BusinessVerification, Notification, Report, Announcement, FavoriteRestaurant
from post.models import Post, FavoritePost, Comment, PostReaction
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm,
    BusinessProfileUpdateForm, BusinessVerificationForm,
    BusinessRegisterForm, ReportForm, AnnouncementForm
)
from post.forms import PostCreateForm, CommentForm
from django.conf import settings

# 登入 / 註冊 / 個人資料 / 編輯個人資料 / 公開個人頁面
# 貼文 / 收藏 / 追蹤 / 動態牆 / 探索 / 貼文詳情 + 留言 + 表情反應
# 貼文管理（用戶 / 管理員） / 置頂貼文 / 刪除貼文
# 收藏清單 / 關注清單 / 我的關注
# 系統公告（管理員新增 / 編輯 / 刪除 / 用戶查看）
# 貼文回報（用戶回報貼文 / 管理員查看回報 / 處理回報）
# 商家認證申請 / 管理員審核商家認證 / 管理員查看所有待審核商家
# 管理儀表板（管理員專用）


# ----------(用戶)登入/註冊/個人資料/編輯個人資料/公開個人頁面----------
# 用戶註冊
def register(request):
    user_type = request.POST.get('user_type') if request.method == 'POST' else None
    show_business_form = user_type == 'business' if user_type else False
    
    if request.method == 'POST':
        if show_business_form:
            # 商家註冊使用普通表單，後續再完成驗證資料
            form = UserRegisterForm(request.POST)
        else:
            form = UserRegisterForm(request.POST)
            
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            if show_business_form:
                # 處理商家註冊
                user_type = 'business'
                
                # 創建用戶個人資料並設置用戶類型
                profile = Profile.objects.get(user=user)
                profile.user_type = user_type
                profile.verification_status = 'unverified'  # 初始設置為未驗證，等待提交資料
                profile.save()
                
                messages.success(request, f'商家帳號已建立，請立即完成商家資訊驗證！')
                
                # 自動登入新用戶
                user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
                login(request, user)
                
                # 導向到商家驗證頁面
                return redirect('apply_for_verification')
            else:
                # 處理一般用戶註冊
                user_type = form.cleaned_data.get('user_type')
                
                # 創建用戶個人資料並設置用戶類型
                profile = Profile.objects.get(user=user)
                profile.user_type = user_type
                profile.save()
                
                messages.success(request, f'帳號已建立，現在可以登入！')
                return redirect('login')
    else:
        # GET請求，創建空表單
        form = UserRegisterForm()
        
    return render(request, 'user/register.html', {
        'form': form,
        'show_business_form': show_business_form
    })

# 用戶登入
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 根據用戶權限導向不同頁面
            if user.is_staff or user.is_superuser:
                # 管理員導向管理儀表板
                messages.success(request, f'歡迎回來，{user.username}！')
                return redirect('admin_dashboard')
            else:
                # 一般用戶導向聊天室頁面
                return redirect('chat_room')
        else:
            messages.error(request, '帳號或密碼不正確！')
    
    return render(request, 'user/login.html')

# 用戶登出
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# 用戶個人資料頁面/編輯
@login_required
def profile(request):
    user_profile = request.user.profile
    posts = Post.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=user_profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '您的個人資料已更新！')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=user_profile)
    
    # 獲取用戶發布的貼文，按置頂和時間排序
    posts = Post.objects.filter(user=request.user).order_by('-is_pinned', '-created_at')
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'posts': posts
    }
    
    return render(request, 'user/profile.html', {
        'user_profile': user_profile,
        'posts': posts,
    })

# 公開用戶個人頁面
def public_profile(request, username):
    """顯示指定用戶的公開個人頁面"""
    target_user = get_object_or_404(User, username=username)
    profile = target_user.profile
    posts = Post.objects.filter(user=target_user).order_by('-created_at')  # 查詢該用戶所有貼文

    # 檢查是否為管理員頁面且訪問者不是管理員
    if profile.user_type == 'admin' and not request.user.is_staff:
        messages.error(request, "您沒有權限查看管理員的個人頁面")
        return redirect('explore')
    
    # 檢查是否為本人查看
    is_self = (request.user.is_authenticated and request.user == target_user)
    
    # 檢查當前用戶是否已關注目標用戶
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, followed=target_user).exists()
    
    # 檢查當前用戶是否已收藏各貼文
    if request.user.is_authenticated:
        favorited_posts = FavoritePost.objects.filter(user=request.user).values_list('post_id', flat=True)
    else:
        favorited_posts = []
    
    # 添加是否已收藏標記
    for post in posts:
        post.is_favorited = post.id in favorited_posts
    
    # 獲取關注者和正在關注的數量
    followers_count = Follow.objects.filter(followed=target_user).count()
    following_count = Follow.objects.filter(follower=target_user).count()
    
    context = {
        'profile_user': target_user,  # 改名，不要用 'user'
        'profile': profile,
        'posts': posts,
        'is_self': is_self,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count
    }
    
    return render(request, 'user/public_profile.html', context)
# ----------(用戶)登入/註冊/個人資料/編輯個人資料/公開個人頁面----------！！



# ----------(用戶)貼文/收藏/追蹤/動態牆/探索/貼文詳情 + 留言 + 表情反應----------


# 追蹤/取消追蹤用戶
@login_required
def toggle_follow(request, user_id):
    """追蹤或取消追蹤用戶"""
    user_to_follow = get_object_or_404(User, id=user_id)
    
    # 不能追蹤自己
    if request.user.id == user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': '不能追蹤自己'})
        messages.error(request, '不能追蹤自己')
        return redirect(request.META.get('HTTP_REFERER', 'profile'))
    
    follow, created = Follow.objects.get_or_create(follower=request.user, followed=user_to_follow)
    
    if not created:
        # 如果已存在，說明用戶要取消追蹤
        follow.delete()
        is_following = False
        message = f"已取消追蹤 {user_to_follow.username}"
    else:
        is_following = True
        message = f"已開始追蹤 {user_to_follow.username}"
        
        # 創建追蹤通知
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type='follow',
            message=f"{request.user.username} 開始追蹤了您"
        )
    
    # 如果是AJAX請求，返回JSON響應
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'is_following': is_following,
            'message': message
        })
    
    # 否則重定向回上一頁
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'profile'))


# 我的關注/粉絲清單
@login_required
def followers(request):
    """顯示關注用戶的人"""
    followers = Follow.objects.filter(followed=request.user).select_related('follower')
    following = Follow.objects.filter(follower=request.user).select_related('followed')
    return render(request, 'social/followers.html', {
        'followers': followers,
        'following': following
    })

# 動態牆頁面 - 只顯示關注用戶的貼文
@login_required
def feed(request):
    """顯示當前用戶關注的用戶發布的貼文（動態牆）"""
    # 獲取當前用戶關注的用戶列表
    following_users = Follow.objects.filter(follower=request.user).values_list('followed', flat=True)
    
    # 排除管理員用戶（除非當前用戶是管理員）
    if not request.user.is_staff:
        # 獲取所有管理員用戶的ID
        admin_users = User.objects.filter(
            Q(profile__user_type='admin') | Q(is_staff=True)
        ).values_list('id', flat=True)
        # 從關注列表中排除管理員
        following_users = list(set(following_users) - set(admin_users))
    
    # 獲取這些用戶的貼文
    posts = Post.objects.filter(
        user_id__in=following_users
    ).select_related('user').prefetch_related(
        Prefetch('favorited_by', queryset=FavoritePost.objects.filter(user=request.user), to_attr='user_favorites')
    ).order_by('-created_at')
    
    # 標記用戶是否已收藏各貼文
    for post in posts:
        post.is_favorited = len(post.user_favorites) > 0
    
    # 獲取一些推薦用戶（非當前用戶關注的用戶，按關注者數量排序）
    already_following = list(following_users) + [request.user.id]  # 包含當前用戶自己
    
    # 排除管理員用戶（除非當前用戶是管理員）
    if not request.user.is_staff:
        admin_users = User.objects.filter(
            Q(profile__user_type='admin') | Q(is_staff=True)
        ).values_list('id', flat=True)
        exclude_users = list(set(already_following) | set(admin_users))
    else:
        exclude_users = already_following
    
    recommended_users = User.objects.exclude(id__in=exclude_users).annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count')[:5]
    
    context = {
        'posts': posts,
        'recommended_users': recommended_users,
        'page_type': 'feed'
    }
    
    return render(request, 'social/feed.html', context)

# 探索頁面 - 顯示熱門貼文和推薦內容
def explore(request):
    post_type = request.GET.get('type')
    sort = request.GET.get('sort')  # 'hot' or None

    if sort == 'hot':
        posts = Post.objects.annotate(
            favorite_count=Count('favorited_by'),
            comment_count=Count('comments'),
            reaction_count=Count('reactions')
        ).order_by('-favorite_count', '-comment_count', '-reaction_count', '-created_at')
    elif post_type:
        posts = Post.objects.filter(type=post_type).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    recommended_businesses = User.objects.filter(
        profile__user_type='business',
        profile__verification_status='verified'
    ).annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count')[:5]

    recommended_foodies = User.objects.filter(
        profile__user_type='regular'
    ).annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count')[:5]

    context = {
        'posts': posts,
        'recommended_businesses': recommended_businesses,
        'recommended_foodies': recommended_foodies,
    }
    return render(request, 'social/explore.html', context)


# 我的追蹤清單
def following(request, user_id=None):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user
    
    following = user.following.all()
    
    return render(request, 'social/following.html', {
        'user': user,
        'following': following
    })

# 收藏或取消收藏餐廳
@login_required
def toggle_favorite_restaurant(request):
    """收藏或取消收藏餐廳"""
    if request.method == 'POST':
        # 從POST數據中獲取餐廳信息
        restaurant_name = request.POST.get('restaurant_name')
        restaurant_place_id = request.POST.get('restaurant_place_id')
        restaurant_address = request.POST.get('restaurant_address', '')
        restaurant_image_url = request.POST.get('restaurant_image_url', '')
        restaurant_rating = request.POST.get('restaurant_rating')
        restaurant_price_level = request.POST.get('restaurant_price_level')
        restaurant_lat = request.POST.get('restaurant_lat')
        restaurant_lng = request.POST.get('restaurant_lng')
        
        # 檢查必要的參數
        if not restaurant_name or not restaurant_place_id:
            return JsonResponse({'status': 'error', 'message': '缺少必要的餐廳信息'})
        
        # 轉換數值型字段
        try:
            if restaurant_rating:
                restaurant_rating = float(restaurant_rating)
            else:
                restaurant_rating = None
                
            if restaurant_price_level:
                restaurant_price_level = int(restaurant_price_level)
            else:
                restaurant_price_level = None
                
            if restaurant_lat:
                restaurant_lat = float(restaurant_lat)
            else:
                restaurant_lat = None
                
            if restaurant_lng:
                restaurant_lng = float(restaurant_lng)
            else:
                restaurant_lng = None
        except (ValueError, TypeError):
            return JsonResponse({'status': 'error', 'message': '餐廳資料格式錯誤'})
        
        # 檢查用戶是否已收藏該餐廳
        try:
            favorite = FavoriteRestaurant.objects.get(
                user=request.user, 
                restaurant_place_id=restaurant_place_id
            )
            # 如果已存在，說明用戶要取消收藏
            favorite.delete()
            is_favorite = False
            message = "已取消收藏餐廳"
        except FavoriteRestaurant.DoesNotExist:
            # 如果不存在，創建新的收藏
            favorite = FavoriteRestaurant(
                user=request.user,
                restaurant_name=restaurant_name,
                restaurant_place_id=restaurant_place_id,
                restaurant_address=restaurant_address,
                restaurant_image_url=restaurant_image_url,
                restaurant_rating=restaurant_rating,
                restaurant_price_level=restaurant_price_level,
                restaurant_lat=restaurant_lat,
                restaurant_lng=restaurant_lng
            )
            favorite.save()
            is_favorite = True
            message = "已收藏餐廳"
        
        # 如果是AJAX請求，返回JSON響應
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'is_favorite': is_favorite,
                'message': message
            })
        
        # 否則重定向回上一頁
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # 如果不是POST請求，返回錯誤
    return JsonResponse({'status': 'error', 'message': '僅支持POST請求'})

# 查看用戶收藏的餐廳列表
@login_required
def favorite_restaurants(request):
    """顯示用戶收藏的餐廳"""
    favorite_restaurants = FavoriteRestaurant.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'restaurant/favorite_restaurants.html', {'favorite_restaurants': favorite_restaurants})

# 刪除收藏的餐廳
@login_required
def delete_favorite_restaurant(request, favorite_id):
    """刪除收藏的餐廳"""
    favorite = get_object_or_404(FavoriteRestaurant, id=favorite_id, user=request.user)
    
    if request.method == 'POST':
        favorite.delete()
        messages.success(request, '已從收藏中移除餐廳')
        return redirect('favorite_restaurants')
    
    return render(request, 'restaurant/confirm_delete_restaurant.html', {
        'favorite': favorite
    })

# 檢查餐廳是否已被收藏（AJAX用）（前端按鈕狀態用）
@login_required
def check_favorite_restaurant(request):
    """檢查餐廳是否已被收藏"""
    if request.method == 'GET':
        place_id = request.GET.get('place_id')
        
        if not place_id:
            return JsonResponse({'status': 'error', 'message': '缺少必要的參數'})
        
        # 檢查是否已收藏
        is_favorited = FavoriteRestaurant.objects.filter(
            user=request.user, 
            restaurant_place_id=place_id
        ).exists()
        
        return JsonResponse({
            'status': 'success',
            'is_favorited': is_favorited
        })
    
    return JsonResponse({'status': 'error', 'message': '僅支持GET請求'})
# ----------(用戶)貼文/收藏/追蹤/動態牆/探索/貼文詳情 + 留言 + 表情反應----------！！



# ----------(用戶/管理員)商家認證申請/管理員審核商家認證/管理員查看所有待審核商家----------
# 商家認證申請
@login_required
def apply_for_verification(request):
    # 檢查用戶資料
    profile = request.user.profile
    is_new_application = True
    
    # 檢查是否已有申請記錄
    existing_verification = BusinessVerification.objects.filter(
        user=request.user
    ).order_by('-submitted_at').first()
    
    # 如果已經是已驗證的商家，顯示提示並跳轉
    if profile.user_type == 'business' and profile.verification_status == 'verified':
        messages.info(request, '您的商家帳號已經通過驗證，無需再次申請！')
        return redirect('profile')
    
    if request.method == 'POST':
        form = BusinessVerificationForm(request.POST, request.FILES, instance=existing_verification)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.status = 'pending'
            verification.save()
            
            # 更新用戶狀態為審核中
            profile.user_type = 'business'  # 確保用戶類型是商家
            profile.verification_status = 'pending'
            profile.save()
            
            # 向管理員發送通知
            admin_users = User.objects.filter(is_staff=True)
            notification_message = f"有新的商家申請需要審核: {verification.business_name}" if is_new_application else f"商家 {verification.business_name} 更新了申請資料"
            
            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    notification_type='system',
                    message=notification_message
                )
            
            if is_new_application:
                messages.success(request, '商家認證申請已提交，請等待審核！')
            else:
                messages.success(request, '商家認證資料已更新，請等待審核！')
            return redirect('profile')
    else:
        if existing_verification:
            # 如果有現有申請，使用其資料預填表單
            is_new_application = False
            form = BusinessVerificationForm(instance=existing_verification)
            
            # 顯示不同提示訊息，依據狀態
            if existing_verification.status == 'pending':
                messages.info(request, '您的申請正在審核中。如需更新資料，請修改後重新提交。')
            elif existing_verification.status == 'rejected':
                messages.warning(request, '您之前的申請已被拒絕。您可以修改資料後重新提交。')
                if existing_verification.review_notes:
                    messages.info(request, f'拒絕理由: {existing_verification.review_notes}')
        else:
            # 預填用戶已有的商家資訊
            initial_data = {
                'business_name': profile.business_name if profile.business_name else '',
                'business_address': profile.business_address if profile.business_address else '',
                'business_phone': profile.business_phone if profile.business_phone else '',
                'business_email': request.user.email
            }
            form = BusinessVerificationForm(initial=initial_data)
            
            # 如果用戶是新註冊的商家，但還未提交驗證資料
            if profile.user_type == 'business' and profile.verification_status == 'unverified':
                messages.info(request, '請完成商家資訊驗證以啟用商家功能。')
    
    return render(request, 'business/apply_verification.html', {
        'form': form,
        'is_new_application': is_new_application
    })

# 管理員審核商家認證 通過/拒絕
@staff_member_required
def review_verification(request, verification_id):
    verification = get_object_or_404(BusinessVerification, id=verification_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '')
        
        verification.review_notes = notes
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        
        if action == 'approve':
            verification.status = 'verified'
            
            # 更新用戶資料
            profile = verification.user.profile
            profile.verification_status = 'verified'
            profile.business_name = verification.business_name
            profile.business_address = verification.business_address
            profile.business_phone = verification.business_phone
            profile.save()
            
            messages.success(request, f'已批准 {verification.business_name} 的商家認證申請')
        elif action == 'reject':
            verification.status = 'rejected'
            
            # 更新用戶狀態
            profile = verification.user.profile
            profile.verification_status = 'rejected'
            profile.save()
            
            messages.success(request, f'已拒絕 {verification.business_name} 的商家認證申請')
        
        verification.save()
        return redirect('admin_verification_list')
    
    return render(request, 'business/review_verification.html', {'verification': verification})

# 管理員查看所有待審核的商家認證
@staff_member_required
def admin_verification_list(request):
    pending_verifications = BusinessVerification.objects.filter(status='pending').order_by('submitted_at')
    verified_verifications = BusinessVerification.objects.filter(status='verified').order_by('-reviewed_at')
    rejected_verifications = BusinessVerification.objects.filter(status='rejected').order_by('-reviewed_at')
    
    context = {
        'pending_verifications': pending_verifications,
        'verified_verifications': verified_verifications,
        'rejected_verifications': rejected_verifications
    }
    
    return render(request, 'admin/admin_verification_list.html', context)
# ----------(用戶/管理員)商家認證申請/管理員審核商家認證/管理員查看所有待審核商家----------！！


# ----------(用戶)通知系統 / 回報系統----------
# 通知列表 載入時順便把未讀 → 已讀
@login_required
def notifications(request):
    """顯示用戶的通知列表"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # 標記所有未讀通知為已讀
    unread_notifications = notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.is_read = True
        notification.save()
    
    return render(request, 'notification/notifications.html', {'notifications': notifications})

# 標記單一通知已讀
@login_required
def mark_notification_read(request, notification_id):
    """標記單個通知為已讀"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'status': 'success', 'message': '通知已標記為已讀'})

# 刪除單一通知
@login_required
def delete_notification(request, notification_id):
    """刪除通知"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': '通知已刪除'})
    
    return redirect('notifications')

# 全部通知標記已讀
@login_required
def mark_all_notifications_read(request):
    """標記所有通知為已讀"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success', 'message': '所有通知已標記為已讀'})
    return JsonResponse({'status': 'error', 'message': '方法不允許'}, status=405)

# 刪除所有通知
@login_required
def delete_all_notifications(request):
    """刪除所有通知"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user).delete()
        return JsonResponse({'status': 'success', 'message': '所有通知已刪除'})
    return JsonResponse({'status': 'error', 'message': '方法不允許'}, status=405)

# 回報貼文 / 評論 / 用戶（不可回報自己/自己的貼文或評論）
@login_required
def report_post(request, post_id):
    """回報貼文"""
    post = get_object_or_404(Post, id=post_id)
    
    # 不能回報自己的貼文
    if post.user == request.user:
        messages.error(request, '您不能回報自己的貼文')
        return redirect('post:post:view_post', post_id=post.id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.report_type = 'post'
            report.post = post
            report.reported_user = post.user
            report.save()
            
            # 通知管理員
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    notification_type='system',
                    post=post,
                    message=f"用戶 {request.user.username} 回報了一篇貼文，請查看"
                )
            
            messages.success(request, '您的回報已提交，管理員將會審核')
            return redirect('post:post:view_post', post_id=post.id)
    else:
        form = ReportForm()
    
    return render(request, 'report/report_form.html', {
        'form': form,
        'report_type': '貼文',
        'reported_item': post
    })

# 回報評論
@login_required
def report_comment(request, comment_id):
    """回報評論"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # 不能回報自己的評論
    if comment.user == request.user:
        messages.error(request, '您不能回報自己的評論')
        return redirect('post:post:view_post', post_id=comment.post.id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.report_type = 'comment'
            report.comment = comment
            report.reported_user = comment.user
            report.save()
            
            # 通知管理員
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    notification_type='system',
                    comment=comment,
                    post=comment.post,
                    message=f"用戶 {request.user.username} 回報了一則評論，請查看"
                )
            
            messages.success(request, '您的回報已提交，管理員將會審核')
            return redirect('post:post:view_post', post_id=comment.post.id)
    else:
        form = ReportForm()
    
    return render(request, 'report/report_form.html', {
        'form': form,
        'report_type': '評論',
        'reported_item': comment
    })

# 回報用戶
@login_required
def report_user(request, user_id):
    """回報用戶"""
    reported_user = get_object_or_404(User, id=user_id)
    
    # 不能回報自己
    if reported_user == request.user:
        messages.error(request, '您不能回報自己')
        return redirect('public_profile', username=reported_user.username)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.report_type = 'user'
            report.reported_user = reported_user
            report.save()
            
            # 通知管理員
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    notification_type='system',
                    message=f"用戶 {request.user.username} 回報了用戶 {reported_user.username}，請查看"
                )
            
            messages.success(request, '您的回報已提交，管理員將會審核')
            return redirect('public_profile', username=reported_user.username)
    else:
        form = ReportForm()
    
    return render(request, 'report/report_form.html', {
        'form': form,
        'report_type': '用戶',
        'reported_item': reported_user
    })
# ----------(用戶)通知系統 / 回報系統----------！！



# ----------(管理員)管理員查看和處理所有回報 / 管理員儀表板 / 管理員查看所有系統公告----------
# 管理員查看和處理所有回報
@staff_member_required
def admin_reports(request):
    """管理員查看所有回報"""
    pending_reports = Report.objects.filter(status='pending').order_by('-created_at')
    processing_reports = Report.objects.filter(status='processing').order_by('-created_at')
    resolved_reports = Report.objects.filter(status__in=['resolved', 'rejected']).order_by('-created_at')
    
    return render(request, 'report/admin_reports.html', {
        'pending_reports': pending_reports,
        'processing_reports': processing_reports,
        'resolved_reports': resolved_reports
    })

# 管理員處理回報（解決 / 駁回） 可選擇同步刪除涉案內容
@staff_member_required
def handle_report(request, report_id):
    """處理回報"""
    report = get_object_or_404(Report, id=report_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        report.admin_notes = admin_notes
        report.handled_by = request.user
        report.handled_at = timezone.now()
        
        if action == 'resolve':
            report.status = 'resolved'
            messages.success(request, f'已解決回報 #{report.id}')
        elif action == 'reject':
            report.status = 'rejected'
            messages.success(request, f'已拒絕回報 #{report.id}')
        elif action == 'processing':
            report.status = 'processing'
            messages.success(request, f'已將回報 #{report.id} 設為處理中')
        
        report.save()
        
        # 如果是解決回報並且選擇了刪除內容
        if action == 'resolve' and request.POST.get('delete_content') == 'yes':
            if report.report_type == 'post' and report.post:
                post = report.post
                post.delete()
                messages.success(request, f'已刪除相關貼文')
            elif report.report_type == 'comment' and report.comment:
                comment = report.comment
                comment.delete()
                messages.success(request, f'已刪除相關評論')
        
        return redirect('admin_reports')
    
    return render(request, 'report/handle_report.html', {'report': report})

# 管理員儀表板
@staff_member_required
def admin_dashboard(request):
    """管理員儀表板，集中展示系統關鍵數據與管理功能"""
    # 獲取各類待處理數量
    pending_verifications_count = BusinessVerification.objects.filter(status='pending').count()
    pending_reports_count = Report.objects.filter(status='pending').count()
    processing_reports_count = Report.objects.filter(status='processing').count()
    
    # 用戶統計
    total_users_count = User.objects.count()
    regular_users_count = Profile.objects.filter(user_type='regular').count()
    business_users_count = Profile.objects.filter(user_type='business').count()
    verified_business_count = Profile.objects.filter(user_type='business', verification_status='verified').count()
    unverified_business_count = business_users_count - verified_business_count
    
    # 內容統計
    total_posts_count = Post.objects.count()
    total_comments_count = Comment.objects.count()
    featured_posts_count = Post.objects.filter(is_platform_featured=True).count()
    
    # 互動統計
    total_favorites_count = FavoritePost.objects.count()
    total_follows_count = Follow.objects.count()
    total_reactions_count = PostReaction.objects.count()

    # 最近活動
    recent_reports = Report.objects.order_by('-created_at')[:5]
    recent_verifications = BusinessVerification.objects.order_by('-submitted_at')[:5]
    recent_posts = Post.objects.order_by('-created_at')[:5]
    
    context = {
        # 待處理項目
        'pending_verifications_count': pending_verifications_count,
        'pending_reports_count': pending_reports_count,
        'processing_reports_count': processing_reports_count,
        
        # 用戶統計
        'total_users_count': total_users_count,
        'regular_users_count': regular_users_count,
        'business_users_count': business_users_count,
        'verified_business_count': verified_business_count,
        'unverified_business_count': unverified_business_count,
        
        # 內容統計
        'total_posts_count': total_posts_count,
        'total_comments_count': total_comments_count,
        'featured_posts_count': featured_posts_count,
        
        # 互動統計
        'total_favorites_count': total_favorites_count,
        'total_follows_count': total_follows_count,
        'total_reactions_count': total_reactions_count,
        
        # 最近活動
        'recent_reports': recent_reports,
        'recent_verifications': recent_verifications,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'admin/admin_dashboard.html', context)

# 管理員查看所有系統公告
@staff_member_required
def announcement_list(request):
    """管理員查看所有系統公告"""
    active_announcements = Announcement.objects.filter(is_active=True).order_by('-is_pinned', '-created_at')
    inactive_announcements = Announcement.objects.filter(is_active=False).order_by('-created_at')
    
    context = {
        'active_announcements': active_announcements,
        'inactive_announcements': inactive_announcements
    }
    
    return render(request, 'admin/announcement_list.html', context)

# 管理員創建系統公告
@staff_member_required
def create_announcement(request):
    """管理員創建系統公告"""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()
            
            # 如果勾選了立即啟用，創建系統通知給所有用戶
            if announcement.is_active:
                # 獲取所有用戶
                users = User.objects.all()
                for user in users:
                    if user != request.user:  # 不需要通知發布者自己
                        Notification.objects.create(
                            recipient=user,
                            sender=request.user,
                            notification_type='system',
                            message=f"新系統公告: {announcement.title}"
                        )
            
            messages.success(request, '系統公告已成功創建！')
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()
    
    return render(request, 'admin/create_announcement.html', {'form': form})

# 管理員編輯系統公告
@staff_member_required
def edit_announcement(request, announcement_id):
    """管理員編輯系統公告"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            # 檢查是否從未啟用變為啟用
            was_inactive = not announcement.is_active
            will_be_active = form.cleaned_data.get('is_active')
            
            updated_announcement = form.save(commit=False)
            updated_announcement.updated_at = timezone.now()
            updated_announcement.save()
            
            # 如果公告從未啟用變為啟用，創建系統通知
            if was_inactive and will_be_active:
                users = User.objects.all()
                for user in users:
                    if user != request.user:
                        Notification.objects.create(
                            recipient=user,
                            sender=request.user,
                            notification_type='system',
                            message=f"新系統公告: {updated_announcement.title}"
                        )
            
            messages.success(request, '系統公告已成功更新！')
            return redirect('announcement_list')
    else:
        form = AnnouncementForm(instance=announcement)
    
    return render(request, 'admin/edit_announcement.html', {
        'form': form,
        'announcement': announcement
    })

# 管理員刪除系統公告
@staff_member_required
def delete_announcement(request, announcement_id):
    """管理員刪除系統公告"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, '系統公告已成功刪除！')
        return redirect('announcement_list')
    
    return render(request, 'admin/confirm_delete.html', {
        'item': announcement,
        'item_type': '系統公告',
        'cancel_url': 'announcement_list'
    })

# 管理員切換系統公告的啟用狀態 啟用/停用
@staff_member_required
def toggle_announcement(request, announcement_id):
    """管理員切換系統公告的啟用狀態"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    announcement.is_active = not announcement.is_active
    announcement.save()
    
    status = '啟用' if announcement.is_active else '停用'
    messages.success(request, f'系統公告 "{announcement.title}" 已{status}')
    
    return redirect('announcement_list')
# ----------(管理員)管理員查看和處理所有回報 / 管理員儀表板 / 管理員查看所有系統公告----------！！



# ----------(用戶)查看系統公告 / 查看單個系統公告詳細內容----------
# 用戶查看所有系統公告
def view_announcements(request):
    """用戶查看所有有效的系統公告"""
    from django.utils import timezone
    now = timezone.now()
    
    # 獲取有效的公告
    announcements = Announcement.objects.filter(
        is_active=True
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('-is_pinned', '-created_at')
    
    return render(request, 'announcement/announcement_list.html', {
        'announcements': announcements
    })

# 用戶查看單個系統公告的詳細內容
def view_announcement(request, announcement_id):
    """用戶查看單個系統公告的詳細內容"""
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    # 檢查公告是否有效
    if not announcement.is_active or not announcement.is_valid():
        raise Http404("公告不存在或已過期")
    
    return render(request, 'announcement/announcement_detail.html', {
        'announcement': announcement
    })
# ----------(用戶)查看系統公告 / 查看單個系統公告詳細內容----------！！

