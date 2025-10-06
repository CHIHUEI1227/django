import requests
from django.db import models
from restaurants.models import RestaurantIndicatorDetail, RestaurantIndicatorSummary
from user.models import UserPreferenceDetail, UserPreferenceSummary
from django.db.models import Sum, Count, Q

def call_fastapi_analyze_restaurant(post_id, content, place_id=None):
    url = "http://localhost:8001/analyze/restaurant/"
    data = {
        "post_id": post_id,
        "content": content,
    }
    if place_id:
        data["place_id"] = place_id
    print(f"[送出] call_fastapi_analyze_restaurant: {data}")
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        print(f"[回傳] call_fastapi_analyze_restaurant: {resp.json()}")
        return resp.json()
    except Exception as e:
        print(f"[錯誤] call_fastapi_analyze_restaurant: {e}")
        return {"status": "error", "msg": str(e)}

def call_fastapi_analyze_user(post_id, content, user_id=None):
    url = "http://localhost:8001/analyze/user/"
    data = {
        "post_id": post_id,
        "content": content,
    }
    if user_id:
        data["user_id"] = user_id
    print(f"[送出] call_fastapi_analyze_user: {data}")
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        print(f"[回傳] call_fastapi_analyze_user: {resp.json()}")
        return resp.json()
    except Exception as e:
        print(f"[錯誤] call_fastapi_analyze_user: {e}")
        return {"status": "error", "msg": str(e)}

def analyze_and_save_restaurant_indicator(post, logger=None):
    result = call_fastapi_analyze_restaurant(post.id, post.content, post.location_place_id)
    if logger:
        logger.info(f"已呼叫 FastAPI 分析餐廳指標 ID:{post.id}，結果：{result}")
    if result.get("status") == "success" and "data" in result:
        for indicator in result["data"]:
            detail, created = RestaurantIndicatorDetail.objects.update_or_create(
                source="post",
                source_id=post.id,
                place_id=indicator.get("place_id"),
                indicator_type=indicator.get("indicator_type"),
                defaults={
                    "score": indicator.get("score")
                }
            )
            # 每次細項更新後，同步更新 summary
            update_restaurant_indicator_summary(
                place_id=indicator.get("place_id"),
                indicator_type=indicator.get("indicator_type")
            )
    return result

def analyze_and_save_user_preference(post, logger=None):
    result = call_fastapi_analyze_user(post.id, post.content, post.user.id)
    if logger:
        logger.info(f"已呼叫 FastAPI 分析使用者偏好 ID:{post.id}，結果：{result}")
    if result.get("status") == "success" and "data" in result:
        foods = result["data"].get("foods", [])
        for food in foods:
            UserPreferenceDetail.objects.update_or_create(
                user=post.user,
                keyword=food,
                preference_type="mention",
                source="post",
                source_id=post.id,
                defaults={
                    "weight": 1.0,
                    "frequency": 1,
                }
            )
        # 新增這一行，確保總表即時更新
        update_user_preference_summary(post.user)
    return result

def update_user_preference_summary(user):
    """
    統計該 user 的所有 UserPreferenceDetail，彙總到 UserPreferenceSummary。
    - preference_value: keyword
    - preference_type: 若 like/dislike/restrict 次數最多則為該類型，否則為 try/mention
    - total_score: 可用細項的 weight 總和或平均（依需求）
    - count: like/dislike/restrict 累計次數
    - try_count: try/mention 累計次數
    """
    # 先取得所有 keyword
    keywords = UserPreferenceDetail.objects.filter(user=user).values_list('keyword', flat=True).distinct()
    for keyword in keywords:
        details = UserPreferenceDetail.objects.filter(user=user, keyword=keyword)
        # 統計各類型次數
        type_counts = details.values('preference_type').annotate(c=Count('id'))
        type_count_map = {t['preference_type']: t['c'] for t in type_counts}
        # 決定總表的 preference_type
        main_type = max(type_count_map, key=type_count_map.get) if type_count_map else "mention"
        # 計算分數
        total_score = details.aggregate(total=Sum('weight'))['total'] or 0
        # 正負面出現次數
        count = details.filter(preference_type__in=['like', 'dislike', 'restrict']).count()
        # 嘗試/提及次數
        try_count = details.filter(preference_type__in=['try', 'mention']).count()
        # 更新或建立總表
        UserPreferenceSummary.objects.update_or_create(
            user=user,
            preference_value=keyword,
            defaults={
                "preference_type": main_type,
                "total_score": total_score,
                "count": count,
                "try_count": try_count,
            }
        )

def update_restaurant_indicator_summary(place_id, indicator_type):
    # 彙總所有細項
    details = RestaurantIndicatorDetail.objects.filter(
        place_id=place_id,
        indicator_type=indicator_type
    )
    count = details.count()
    total_score = details.aggregate(total=models.Avg('score'))['total'] or 0
    RestaurantIndicatorSummary.objects.update_or_create(
        place_id=place_id,
        indicator_type=indicator_type,
        defaults={
            "total_score": total_score,
            "count": count,
        }
    )