# utils_card_enhancer.py

import random
from .utils_card import (
    generate_map_url,
    format_open_status,
    extract_district,
    generate_price_description,
    generate_recommend_reason
)

def enrich_restaurant_info(restaurant):
    name = restaurant.get('name', '')
    rating = restaurant.get('rating', 0)
    address = restaurant.get('address', '')
    price_level = restaurant.get('price_level', '')
    review_count = restaurant.get('review_count', 0)
    is_open_raw = restaurant.get('is_open', None)
    matched_tags = restaurant.get('matched_tags', [])
    ai_reason = restaurant.get('ai_reason', '')
    highlight = restaurant.get('highlight', '')
    distance_m = restaurant.get('distance_m', random.randint(100, 2000))  
    distance = f"{distance_m} 公尺"

    map_url = generate_map_url(name)
    is_open = format_open_status(is_open_raw)
    district = extract_district(address)
    price_desc = generate_price_description(price_level)

    tags = list(set(matched_tags + ([district] if district else []) + ([price_desc] if price_desc else [])))

    # highlight 補強
    if not highlight:
        if "甜點" in tags or "蛋糕" in name:
            highlight = "甜點評價高"
        elif rating >= 4.5:
            highlight = "評價優良"
        elif district and name not in ["泰式小館"]:
            highlight = "地點便利"

    # 推薦理由
    recommend_reason = generate_recommend_reason(matched_tags, highlight, district, price_desc)

    # 模擬 features
    features = []
    if "素食" in tags:
        features.append("提供素食")
    if price_desc == "價格實惠":
        features.append("高 CP 值")
    if "甜點" in tags or "蛋糕" in name:
        features.append("甜點專門")
    if rating >= 4.5 and review_count >= 300:
        features.append("人氣餐廳")
    if price_level == "$":
        features.append("價格便宜")
    if "異國料理" in tags or "泰式" in name:
        features.append("異國料理")

    # 模擬 style
    style = ""
    if "泰式" in name or "東南亞" in tags:
        style = "東南亞風"
    elif "夜貓族" in tags or "夜貓" in name or "宵夜" in tags or distance_m > 1500:
        style = "夜貓族"
    elif "文青" in name or "咖啡" in name or "甜點" in tags:
        style = "文青"
    elif "燒肉" in name or "烤肉" in tags:
        style = "美式"
    elif "壽司" in name or "日式" in tags or "拉麵" in name:
        style = "日式"

    # 固定欄位
    opening_hours = "11:00 - 21:00"
    has_coupon = False
    image_url = ""

    return {
        "name": name,
        "rating": rating,
        "address": address,
        "tags": tags,
        "highlight": highlight,
        "distance": distance,
        "distance_m": distance_m,
        "review_count": review_count,
        "price_level": price_level,
        "is_open": is_open,
        "map_url": map_url,
        "features": features,
        "style": style,
        "opening_hours": opening_hours,
        "recommend_reason": recommend_reason,
        "has_coupon": has_coupon,
        "image_url": image_url
    }
