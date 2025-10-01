"""
此文件包含Google Places API照片抓取與處理流程的示例結果
僅用於展示目的
"""

# 1. Google Places API 原始搜索結果示例
SEARCH_RESULT_EXAMPLE = {
    "html_attributions": [],
    "results": [
        {
            "business_status": "OPERATIONAL",
            "geometry": {
                "location": {"lat": 25.0380131, "lng": 121.5679593},
                "viewport": {
                    "northeast": {"lat": 25.0393620802915, "lng": 121.5693082802915},
                    "southwest": {"lat": 25.0366641197085, "lng": 121.5666103197085}
                }
            },
            "icon": "https://maps.gstatic.com/mapfiles/place_api/icons/v1/png_71/restaurant-71.png",
            "icon_background_color": "#FF9E67",
            "icon_mask_base_uri": "https://maps.gstatic.com/mapfiles/place_api/icons/v2/restaurant_pinlet",
            "name": "鮨野村日式料理",
            "opening_hours": {"open_now":True},
            "photos": [
                {
                    "height": 3024,
                    "html_attributions": ["<a href=\"https://maps.google.com/maps/contrib/102184336186328262302\">A Google User</a>"],
                    "photo_reference": "AWU5eFg82Eyrq3v2UMF1n-tPc9J2JJ4UH9FVBvKf9RBxMo8fYJ5EK8v9f6CcO1_7o1pjA_D3osPxcO-Un9MZqoO9ZM0ChgBRs18XTSm1H-fEp7QL8ZhpMBlJgQuX_JLTA_63QQxcT9VoWGE8BAiQPdVvK3yZPeSWHdETbV0DV3iM1FPOkpAD",
                    "width": 4032
                }
            ],
            "place_id": "ChIJxxusNr2rQjQRa-DT_b9Q5MU",
            "plus_code": {
                "compound_code": "2HXM+6X 台灣台北市信義區",
                "global_code": "7QQ32HXM+6X"
            },
            "price_level": 3,
            "rating": 4.6,
            "reference": "ChIJxxusNr2rQjQRa-DT_b9Q5MU",
            "scope": "GOOGLE",
            "types": ["restaurant", "food", "point_of_interest", "establishment"],
            "user_ratings_total": 252,
            "vicinity": "台北市信義區松仁路97號2樓"
        }
    ],
    "status": "OK"
}

# 2. 獲取地點詳情的原始結果示例（包含照片引用）
PLACE_DETAILS_EXAMPLE = {
    "html_attributions": [],
    "result": {
        "formatted_address": "台灣台北市信義區松仁路97號2樓",
        "formatted_phone_number": "02 2345 6789",
        "name": "鮨野村日式料理",
        "opening_hours": {
            "open_now": True,
            "periods": [
                {
                    "close": {"day": 0, "time": "2200"},
                    "open": {"day": 0, "time": "1130"}
                },
                # ...其他營業時間
            ],
            "weekday_text": [
                "星期一: 11:30 – 22:00",
                "星期二: 11:30 – 22:00",
                "星期三: 11:30 – 22:00",
                "星期四: 11:30 – 22:00",
                "星期五: 11:30 – 22:00",
                "星期六: 11:30 – 22:00",
                "星期日: 11:30 – 22:00"
            ]
        },
        "photos": [
            {
                "height": 3024,
                "html_attributions": ["<a href=\"https://maps.google.com/maps/contrib/102184336186328262302\">A Google User</a>"],
                "photo_reference": "AWU5eFg82Eyrq3v2UMF1n-tPc9J2JJ4UH9FVBvKf9RBxMo8fYJ5EK8v9f6CcO1_7o1pjA_D3osPxcO-Un9MZqoO9ZM0ChgBRs18XTSm1H-fEp7QL8ZhpMBlJgQuX_JLTA_63QQxcT9VoWGE8BAiQPdVvK3yZPeSWHdETbV0DV3iM1FPOkpAD",
                "width": 4032
            },
            # ...其他照片
        ],
        "price_level": 3,
        "rating": 4.6,
        "reviews": [
            {
                "author_name": "王小明",
                "rating": 5,
                "text": "非常美味的日式料理，魚生新鮮、醋飯溫潤，真是一次難忘的用餐體驗！",
                "time": 1692345678
            },
            # ...其他評論
        ],
        "user_ratings_total": 252,
        "website": "https://example-sushi.com",
        "photo_url": "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFg82Eyrq3v2UMF1n-tPc9J2JJ4UH9FVBvKf9RBxMo8fYJ5EK8v9f6CcO1_7o1pjA_D3osPxcO-Un9MZqoO9ZM0ChgBRs18XTSm1H-fEp7QL8ZhpMBlJgQuX_JLTA_63QQxcT9VoWGE8BAiQPdVvK3yZPeSWHdETbV0DV3iM1FPOkpAD&key=YOUR_API_KEY"
    },
    "status": "OK"
}

# 3. 处理餐厅信息的过程
PROCESSING_STEPS = [
    "1. 獲取附近餐廳列表及基本信息",
    "2. 根據place_id獲取餐廳詳細資訊，包含照片引用",
    "3. 使用photo_reference獲取照片URL",
    "4. 將照片URL添加到餐廳詳細資訊中",
    "5. 將餐廳資訊傳遞給LLM進行處理"
]

# 4. LLM处理后的餐厅推荐格式示例
LLM_PROCESSED_RESULT = """以下是我為您推薦的日式料理餐廳：

1. 鮨野村日式料理 - 精緻的日本料理，提供新鮮的魚生和壽司。
   地址: 台灣台北市信義區松仁路97號2樓
   評分: 4.6
   價格: ¥¥¥
   狀態: 營業中
   照片: https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFg82Eyrq3v2UMF1n-tPc9J2JJ4UH9FVBvKf9RBxMo8fYJ5EK8v9f6CcO1_7o1pjA_D3osPxcO-Un9MZqoO9ZM0ChgBRs18XTSm1H-fEp7QL8ZhpMBlJgQuX_JLTA_63QQxcT9VoWGE8BAiQPdVvK3yZPeSWHdETbV0DV3iM1FPOkpAD&key=YOUR_API_KEY

2. 禾豐壽司 - 平價美味的日式料理，適合商務午餐。
   地址: 台灣台北市信義區松高路12號4樓
   評分: 4.3
   價格: ¥¥
   狀態: 營業中
   照片: https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFhpd2HG9qOiLlLksVOlbQnOTDKjhUGKJl_pmZkIyHwOdt0CzQECpX3RWLkXfg6HUDVtVaSUUnj0QRH5EnSoP_RZ75WVs47j1&key=YOUR_API_KEY

3. 大和壽司 - 傳統日式料理，正宗的京都風味。
   地址: 台灣台北市信義區忠孝東路五段68號
   評分: 4.5
   價格: ¥¥¥¥
   狀態: 營業中
   照片: https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFgRG7hU30iUm0EFBs8VDQMj9lvl2TtG2_Qwm4xvxEU4QDPEZ2K7g5a_F5L_l0DFhjG9SYcC3qm4-VhkOWAVfS0z39QrQeKYlg&key=YOUR_API_KEY

這些餐廳均提供高品質的日式料理，您可以根據自己的預算和口味偏好選擇。需要更多餐廳推薦或是其他風格的美食嗎？
"""

# 5. 最終在用戶界面顯示的餐廳卡片數據
RESTAURANT_CARDS_DATA = [
    {
        "name": "鮨野村日式料理",
        "description": "精緻的日本料理，提供新鮮的魚生和壽司。",
        "tags": ["日本料理", "壽司", "評分 4.6", "¥¥¥"],
        "location": "台灣台北市信義區松仁路97號2樓",
        "photo_url": "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFg82Eyrq3v2UMF1n-tPc9J2JJ4UH9FVBvKf9RBxMo8fYJ5EK8v9f6CcO1_7o1pjA_D3osPxcO-Un9MZqoO9ZM0ChgBRs18XTSm1H-fEp7QL8ZhpMBlJgQuX_JLTA_63QQxcT9VoWGE8BAiQPdVvK3yZPeSWHdETbV0DV3iM1FPOkpAD&key=YOUR_API_KEY"
    },
    {
        "name": "禾豐壽司",
        "description": "平價美味的日式料理，適合商務午餐。",
        "tags": ["日本料理", "壽司", "評分 4.3", "¥¥"],
        "location": "台灣台北市信義區松高路12號4樓",
        "photo_url": "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFhpd2HG9qOiLlLksVOlbQnOTDKjhUGKJl_pmZkIyHwOdt0CzQECpX3RWLkXfg6HUDVtVaSUUnj0QRH5EnSoP_RZ75WVs47j1&key=YOUR_API_KEY"
    },
    {
        "name": "大和壽司",
        "description": "傳統日式料理，正宗的京都風味。",
        "tags": ["日本料理", "壽司", "評分 4.5", "¥¥¥¥"],
        "location": "台灣台北市信義區忠孝東路五段68號",
        "photo_url": "https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFgRG7hU30iUm0EFBs8VDQMj9lvl2TtG2_Qwm4xvxEU4QDPEZ2K7g5a_F5L_l0DFhjG9SYcC3qm4-VhkOWAVfS0z39QrQeKYlg&key=YOUR_API_KEY"
    }
]

# 6. 圖示使用者介面上餐廳卡片的HTML示例
RESTAURANT_CARD_HTML = """
<div class="restaurant-card">
    <img src="https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=AWU5eFg82Eyrq3v2UMF1n-tPc9J2JJ4UH9FVBvKf9RBxMo8fYJ5EK8v9f6CcO1_7o1pjA_D3osPxcO-Un9MZqoO9ZM0ChgBRs18XTSm1H-fEp7QL8ZhpMBlJgQuX_JLTA_63QQxcT9VoWGE8BAiQPdVvK3yZPeSWHdETbV0DV3iM1FPOkpAD&key=YOUR_API_KEY" 
        alt="鮨野村日式料理" 
        class="restaurant-photo">
    <div class="restaurant-name">鮨野村日式料理</div>
    <div class="restaurant-tags">
        <span class="restaurant-tag">日本料理</span>
        <span class="restaurant-tag">壽司</span>
        <span class="restaurant-tag">評分 4.6</span>
        <span class="restaurant-tag">¥¥¥</span>
    </div>
    <div class="restaurant-description">精緻的日本料理，提供新鮮的魚生和壽司。</div>
    <div class="restaurant-actions">
        <button class="btn-map" onclick="window.open('https://www.google.com/maps/search/?api=1&query=鮨野村日式料理 台灣台北市信義區松仁路97號2樓', '_blank')">
            <i class="fas fa-map-marker-alt"></i> 查看地圖
        </button>
        <button class="btn-navigation" onclick="window.open('https://www.google.com/maps/dir/?api=1&destination=鮨野村日式料理 台灣台北市信義區松仁路97號2樓', '_blank')">
            <i class="fas fa-directions"></i> 導航前往
        </button>
    </div>
</div>
"""

def display_demo_results():
    """
    打印演示結果，展示整個流程
    """
    print("===== Google Places API照片抓取與處理流程示例 =====\n")
    
    print("一、處理步驟：")
    for i, step in enumerate(PROCESSING_STEPS, 1):
        print(f"   {step}")
    
    print("\n二、API原始搜索結果示例（簡化）：")
    result = SEARCH_RESULT_EXAMPLE["results"][0]
    print(f"   餐廳名稱: {result['name']}")
    print(f"   地址: {result['vicinity']}")
    print(f"   評分: {result['rating']}")
    print(f"   價格等級: {result['price_level']}")
    print(f"   照片引用: {result['photos'][0]['photo_reference'][:50]}...")
    
    print("\n三、照片URL構建：")
    photo_ref = result['photos'][0]['photo_reference']
    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref[:20]}...&key=YOUR_API_KEY"
    print(f"   照片URL: {photo_url}")
    
    print("\n四、經過LLM整理後的餐廳推薦：")
    print("   " + LLM_PROCESSED_RESULT.replace("\n", "\n   ").strip())
    
    print("\n五、最終餐廳卡片數據結構：")
    card_data = RESTAURANT_CARDS_DATA[0]
    for key, value in card_data.items():
        if key == "photo_url":
            print(f"   {key}: {value[:50]}...")
        elif key == "tags":
            print(f"   {key}: {', '.join(value)}")
        else:
            print(f"   {key}: {value}")
            
    print("\n===== 演示結束 =====")

# 如果直接運行此文件，則顯示演示結果
if __name__ == "__main__":
    display_demo_results() 