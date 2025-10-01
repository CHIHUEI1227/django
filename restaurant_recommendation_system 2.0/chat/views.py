from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
import time
from datetime import datetime
from .models import Message, QueryHistory, ChatHistory
from .restaurant_controller import RestaurantRecommendationController
from .preference_service import PreferenceService
from .tools import GooglePlacesAPI
import magic
import os

# 首頁視圖
def home(request):
    return render(request, 'chat/home.html')

# 聊天室視圖
@login_required
def chat_room(request):
    # 獲取用戶的聊天記錄
    chat_history = ChatHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'chat/chat_room.html', {'chat_history': chat_history})

# 聊天記錄列表視圖
@login_required
def chat_history_list(request):
    """獲取用戶的聊天記錄列表"""
    chat_history = ChatHistory.objects.filter(user=request.user).order_by('-created_at')
    
    # 格式化日期時間
    history_list = []
    for chat in chat_history:
        history_list.append({
            'id': chat.id,
            'title': chat.title,
            'date': chat.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return JsonResponse({'chat_history': history_list})

# 保存聊天記錄視圖
@login_required
@require_POST
def save_chat_history(request):
    """保存聊天記錄"""
    try:
        data = json.loads(request.body)
        title = data.get('title', '未命名對話')
        content = data.get('content', '')
        
        # 檢查是否已存在同標題的記錄
        existing_chat = ChatHistory.objects.filter(user=request.user, title=title).first()
        
        if existing_chat:
            # 更新現有記錄
            existing_chat.content = content
            existing_chat.updated_at = datetime.now()
            existing_chat.save()
            chat_id = existing_chat.id
        else:
            # 創建新記錄
            new_chat = ChatHistory.objects.create(
                user=request.user,
                title=title,
                content=content
            )
            chat_id = new_chat.id
        
        return JsonResponse({
            'status': 'success',
            'message': '聊天記錄已儲存',
            'chat_id': chat_id
        })
        
    except Exception as e:
        print(f"儲存聊天記錄時發生錯誤: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# 載入特定聊天記錄視圖
@login_required
def load_chat_history(request, chat_id):
    """載入特定聊天記錄"""
    try:
        chat = ChatHistory.objects.get(id=chat_id, user=request.user)
        return JsonResponse({
            'status': 'success',
            'content': chat.content,
            'title': chat.title,
            'date': chat.created_at.strftime('%Y-%m-%d %H:%M')
        })
    except ChatHistory.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '找不到指定的聊天記錄'
        }, status=404)
    except Exception as e:
        print(f"載入聊天記錄時發生錯誤: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# 刪除聊天記錄視圖
@login_required
@require_POST
def delete_chat_history(request, chat_id):
    """刪除特定聊天記錄"""
    try:
        chat = ChatHistory.objects.get(id=chat_id, user=request.user)
        chat.delete()
        return JsonResponse({
            'status': 'success',
            'message': '聊天記錄已刪除'
        })
    except ChatHistory.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': '找不到指定的聊天記錄'
        }, status=404)
    except Exception as e:
        print(f"刪除聊天記錄時發生錯誤: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# 聊天助手視圖
def chat_assistant(request):
    return render(request, 'chat/assistant.html')

# 探索頁面視圖
def explore(request):
    return render(request, 'chat/explore.html')

# 關於頁面視圖
def about(request):
    return render(request, 'chat/about.html')

# 處理照片代理請求
def proxy_photo(request):
    photo_reference = request.GET.get('reference')
    max_width = request.GET.get('maxwidth', 800)
    
    if not photo_reference:
        return HttpResponse('Missing photo reference', status=400)
    
    # 設置默認圖片路徑
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_img_path = os.path.join(BASE_DIR, 'static', 'images', 'default_restaurant.jpg')
    
    try:
        api = GooglePlacesAPI()
        photo_data = api.get_photo_data(photo_reference, max_width)
        
        if photo_data:
            # 檢查返回的數據是否為有效的圖片
            try:
                mime = magic.Magic(mime=True)
                content_type = mime.from_buffer(photo_data)
                
                if content_type.startswith('image/'):
                    print(f"成功取得圖片，類型: {content_type}, 大小: {len(photo_data)} 字節")
                    
                    # 將成功獲取的圖片緩存到本地（可選）
                    # cache_dir = os.path.join(BASE_DIR, 'static', 'cache')
                    # os.makedirs(cache_dir, exist_ok=True)
                    # cache_path = os.path.join(cache_dir, f"{photo_reference}.jpg")
                    # with open(cache_path, 'wb') as f:
                    #     f.write(photo_data)
                    
                    return HttpResponse(photo_data, content_type=content_type)
                else:
                    print(f"無效的圖片格式: {content_type}")
                    raise Exception("Invalid image format")
            except ImportError:
                # 如果magic庫不可用，假設內容是有效的圖片
                print("magic庫不可用，假設內容是有效的圖片")
                return HttpResponse(photo_data, content_type='image/jpeg')
            except Exception as e:
                print(f"檢查圖片格式時出錯: {str(e)}")
                raise
        
        # 如果未能獲取照片或檢查格式失敗，返回默認圖片
        print("無法從API獲取有效圖片，返回默認圖片")
        with open(default_img_path, 'rb') as f:
            default_photo = f.read()
        return HttpResponse(default_photo, content_type='image/jpeg')
        
    except Exception as e:
        print(f"處理圖片代理時發生錯誤: {str(e)}")
        
        # 出錯時返回默認圖片
        try:
            with open(default_img_path, 'rb') as f:
                default_photo = f.read()
            return HttpResponse(default_photo, content_type='image/jpeg')
        except:
            return HttpResponse('Failed to fetch photo', status=500)

# 處理發送訊息的視圖函數
@login_required
@require_POST
def send_message(request):
    try:
        # 解析JSON數據
        data = json.loads(request.body)
        user_message = data.get('message', '')
        user_preferences = data.get('preferences', {})
        user_location = data.get('location', {})
        
        # 儲存用戶訊息到數據庫
        user_msg = Message.objects.create(
            user=request.user,
            content=user_message,
            is_bot_response=False
        )
        
        # 初始化控制器
        controller = RestaurantRecommendationController()
        
        # 處理查詢，傳入用戶對象以支持偏好處理
        start_time = time.time()
        response = controller.process_query(user_message, user_location, user=request.user)
        processing_time = time.time() - start_time
        
        # 儲存機器人回應到數據庫
        bot_msg = Message.objects.create(
            user=request.user,
            content=response["response_text"],
            is_bot_response=True
        )
        
        # 儲存查詢歷史
        tools_used = []
        if 'places' in response.get('tool_results', {}):
            tools_used.append('places_api')
        if 'search' in response.get('tool_results', {}):
            tools_used.append('search_api')
        if 'menu_data' in response.get('tool_results', {}):
            tools_used.append('menu_scraper')
            
        QueryHistory.objects.create(
            user=request.user,
            query_text=user_message,
            response_text=response["response_text"],
            tools_used=','.join(tools_used)
        )
        
        # 記錄處理時間
        print(f"查詢處理耗時: {processing_time:.2f} 秒")
        
        # 返回響應，包含特定菜品匹配資訊
        restaurant_cards = []
        
        if response.get("tool_results", {}).get("places"):
            for place in response["tool_results"]["places"]:
                card = {
                    'name': place.get('name', ''),
                    'address': place.get('formatted_address', ''),
                    'rating': place.get('rating', 0),
                    'price_level': place.get('price_level_text', '$'),
                    'photo': place.get('photo', ''),
                    'is_open': place.get('opening_hours', {}).get('open_now', False),
                    'website': place.get('website', ''),
                    'map_url': place.get('url', ''),
                    'phone': place.get('formatted_phone_number', '無資訊'),
                    'hours': place.get('formatted_opening_hours', '無資訊'),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'place_id': place.get('place_id', ''),
                    'vicinity': place.get('vicinity', place.get('formatted_address', '')),
                    'types': place.get('types', []),
                    'business_status': place.get('business_status', ''),
                    'opening_hours': {
                        'open_now': place.get('opening_hours', {}).get('open_now', False),
                        'weekday_text': place.get('opening_hours', {}).get('weekday_text', [])
                    },
                    'geometry': {
                        'location': {
                            'lat': place.get('geometry', {}).get('location', {}).get('lat', 0),
                            'lng': place.get('geometry', {}).get('location', {}).get('lng', 0)
                        }
                    }
                }
                
                # 添加菜單匹配資訊
                if place.get('menu_matches'):
                    card['has_target_dishes'] = True
                    card['matched_dishes'] = [match['dish'] for match in place.get('menu_matches', [])]
                else:
                    card['has_target_dishes'] = False
                
                restaurant_cards.append(card)
                
        # 返回響應
        return JsonResponse({
            'status': 'success',
            'bot_response': {
                'content': response["response_text"],
                'place_cards': restaurant_cards
            }
        })
        
    except Exception as e:
        print(f"處理訊息時發生錯誤: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# 用戶偏好頁面視圖
@login_required
def user_preferences(request):
    # 初始化偏好服務
    preference_service = PreferenceService()
    
    if request.method == 'POST':
        # 處理手動更新偏好的請求
        data = json.loads(request.body)
        
        preference_type = data.get('type')
        preference_value = data.get('value')
        score = data.get('score')
        
        if preference_type and preference_value and score is not None:
            preference = [{'type': preference_type, 'value': preference_value, 'score': score}]
            preference_service.save_preferences(request.user, preference, 'manual')
            return JsonResponse({
                'status': 'success',
                'message': '偏好已更新'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': '缺少必要參數'
            }, status=400)
    
    # 獲取用戶偏好
    preferences = preference_service.get_user_preferences(request.user)
    
    return render(request, 'chat/user_preferences.html', {'preferences': preferences}) 