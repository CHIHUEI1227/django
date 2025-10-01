from typing import Dict, List, Any, Optional
import json
from .tools import GooglePlacesAPI, GoogleSearchAPI, LLMFactory, MenuScraperTool
from .preference_service import PreferenceService

class RestaurantRecommendationController:
    """餐廳推薦系統控制器，用於協調不同的API調用"""
    
    def __init__(self):
        """初始化控制器及其工具"""
        self.places_api = GooglePlacesAPI()
        self.search_api = GoogleSearchAPI()
        self.gpt_api = LLMFactory.create_llm()  # 使用工廠方法
        self.preference_service = PreferenceService()
        # 初始化菜單爬蟲工具
        self.menu_scraper = MenuScraperTool()
    
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """分析用戶查詢以決定需要調用的工具"""
        try:
            # 檢查查詢中是否包含具體金額
            import re
            price_pattern = r'(\d+)\s*[塊元]|約\s*(\d+)'
            price_match = re.search(price_pattern, user_query)
            
            price_level_from_amount = None
            if price_match:
                # 提取金額
                amount = price_match.group(1) or price_match.group(2)
                amount = int(amount)
                print(f"檢測到金額: {amount}元")
                
                # 根據金額範圍設定價格等級
                if amount <= 100:
                    price_level_from_amount = 1  # $
                elif amount <= 300:
                    price_level_from_amount = 2  # $$
                elif amount <= 600:
                    price_level_from_amount = 3  # $$$
                else:
                    price_level_from_amount = 4  # $$$$
                    
                print(f"根據金額 {amount}元 設定價格等級: {price_level_from_amount}")
            
            # 檢查是否是查詢熱門/流行/推薦的食物
            trend_keywords = ["熱門", "流行", "最近", "推薦", "人氣", "排行", "排名", "最受歡迎"]
            is_trend_query = any(keyword in user_query for keyword in trend_keywords)
            
            search_query = None
            search_tools = []
            
            if is_trend_query:
                print(f"檢測到熱門/流行查詢: {user_query}")
                # 識別查詢主題(如甜點、餐廳、火鍋等)
                food_categories = ["甜點", "蛋糕", "餐廳", "火鍋", "燒烤", "牛排", "壽司", "拉麵", "漢堡", "咖啡", "奶茶", "飲料", "小吃"]
                
                # 尋找匹配的食物類別
                matched_category = None
                for category in food_categories:
                    if category in user_query:
                        matched_category = category
                        break
                
                # 如果沒有明確類別，嘗試識別查詢中的食物類型
                if not matched_category:
                    # 從查詢中提取可能的食物類型
                    words = re.findall(r'\w+', user_query)
                    for word in words:
                        if len(word) >= 2 and word not in ["最近", "有哪些", "什麼", "推薦", "熱門"]:
                            matched_category = word
                            break
                
                if matched_category:
                    # 構建搜索查詢
                    search_query = f"2025 熱門 {matched_category} 推薦 排行"
                    print(f"構建搜索查詢: {search_query}")
                    search_tools.append("search_api")
                    
                    # 同時使用places_api尋找相關餐廳
                    search_tools.append("places_api")
            
            # 使用 LLM 來分析查詢並決定要調用哪些工具
            system_prompt = """
            你是一個智能美食推薦助理，需要分析用戶的查詢，並決定需要調用哪些工具與解析需求。
            
            可用工具:
            1. places_api - 當查詢包含地點、餐廳類型或直接詢問餐廳推薦時使用
            2. search_api - 當需要獲取網路評價、部落格文章或"10大推薦"等時使用
            3. menu_scraper - 當用戶詢問特定菜品或特定餐點內容時使用
            
            請仔細分析用戶查詢，識別以下關鍵信息:
            - 地點信息: 用戶希望在哪裡吃
            - 餐廳類型: 如日式、韓式、火鍋等
            - 特定菜品: 用戶想吃的具體菜品，如"炙燒鮭魚"、"無骨牛小排"
            - 價格範圍: 用戶提到的價格要求，如"便宜的"、"高級的"或具體金額
            - 味道偏好: 如辣度、口味等特殊要求
            - 評價要求: 如高評價、網友推薦等
            - 排除條件: 用戶明確不想要的條件，如"不要太辣"、"不要海鮮"
            
            請輸出JSON格式:
            {
                "tools": ["工具1", "工具2"],
                "location": "地點名稱",
                "food_type": "食物類型",
                "price_level": 價格等級,
                "specific_dishes": ["具體菜品1", "具體菜品2"], 
                "preferences": ["喜好1", "喜好2"],
                "exclusions": ["排除1", "排除2"],
                "query_for_search": "搜索查詢",
                "keywords": "關鍵字"
            }
            
            價格等級說明:
            1(無或$) - 非常平價 (100元以下)
            2($$) - 平價 (100-300元)
            3($$$) - 高級 (300-600元)
            4($$$$) - 奢華 (600元以上)
            
            範例解析:
            1. "幫我找一間有炙燒鮭魚的壽司店" 
               -> 需要places_api找壽司店 + menu_scraper檢查菜單是否有炙燒鮭魚
               -> specific_dishes: ["炙燒鮭魚"]
               
            2. "附近有沒有不辣又高評價的日式餐廳" 
               -> 需要places_api找日式餐廳 + 關注評價
               -> exclusions: ["辣"]
               
            3. "我今天想吃網路上推薦的10大牛排館之一" 
               -> 需要search_api查詢"10大牛排館"文章 + places_api確認位置和評價
               
            4. "我想吃300元左右的商業午餐"
               -> 需要places_api找餐廳 + 設定價格等級為2($$)
               -> food_type: "商業午餐"
               -> price_level: 2
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
            
            response = self.gpt_api.get_completion(messages)
            
            # 處理回應和錯誤處理代碼
            analysis = self._default_analysis()  # 初始化默認分析結果
            
            if response and "choices" in response and response["choices"]:
                content = response["choices"][0].get("message", {}).get("content", "")
                
                if content:
                    try:
                        # 嘗試解析 JSON 內容
                        import json
                        import re
                        
                        # 檢查是否有 JSON 字符串，使用正則表達式查找大括號內的內容
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            analysis_data = json.loads(json_str)
                            
                            # 更新分析結果
                            for key, value in analysis_data.items():
                                analysis[key] = value
                            
                            # 處理價格等級，確保它是整數或None
                            if "price_level" in analysis_data:
                                price_level = analysis_data["price_level"]
                                if isinstance(price_level, str):
                                    # 轉換文字描述為數值
                                    if "平價" in price_level.lower() or "便宜" in price_level.lower() or "經濟" in price_level.lower():
                                        analysis["price_level"] = 2
                                    elif "高級" in price_level.lower() or "高檔" in price_level.lower():
                                        analysis["price_level"] = 3
                                    elif "奢華" in price_level.lower() or "頂級" in price_level.lower():
                                        analysis["price_level"] = 4
                                    else:
                                        try:
                                            # 嘗試將字符串轉換為整數
                                            analysis["price_level"] = int(price_level)
                                        except ValueError:
                                            # 轉換失敗，使用預設值
                                            analysis["price_level"] = 2
                                            print(f"無法解析價格等級: {price_level}，使用預設值: 2")
                    except Exception as json_error:
                        print(f"解析 JSON 時出錯: {str(json_error)}")
                        print(f"原始內容: {content}")
            
            # 如果LLM未能提取價格等級但我們直接從查詢中找到了金額，使用我們的解析結果
            if price_level_from_amount is not None and analysis.get("price_level") is None:
                analysis["price_level"] = price_level_from_amount
                print(f"使用從查詢直接提取的價格等級: {price_level_from_amount}")
                
                # 添加關鍵字，如果查詢中有"商業午餐"、"定食"等關鍵詞
                food_keywords = ["商業午餐", "定食", "便當", "套餐", "自助餐"]
                for keyword in food_keywords:
                    if keyword in user_query:
                        if not analysis.get("food_type"):
                            analysis["food_type"] = keyword
                        if not analysis.get("keywords"):
                            analysis["keywords"] = keyword
                        print(f"從查詢中提取關鍵字: {keyword}")
                        break
            
            # 增加解析出特定菜品、偏好和排除項
            if "specific_dishes" not in analysis:
                analysis["specific_dishes"] = []
                
            if "preferences" not in analysis:
                analysis["preferences"] = []
                
            if "exclusions" not in analysis:
                analysis["exclusions"] = []
            
            # 確保至少有places_api工具
            if not analysis.get("tools"):
                analysis["tools"] = ["places_api"]
                print("未指定工具，默認使用places_api")
            
            return analysis
        except Exception as e:
            print(f"分析查詢時發生異常: {str(e)}")
            return self._default_analysis()
    
    def _default_analysis(self) -> Dict[str, Any]:
        """返回默認的分析結果"""
        return {
            "tools": ["places_api"],
            "location": "",
            "food_type": "",
            "price_level": None,
            "query_for_search": "",
            "radius": 2000,
            "keywords": ""
        }
    
    def execute_tools(self, analysis: Dict[str, Any], user_location: Dict[str, Any] = None, user_query: str = "") -> Dict[str, Any]:
        """根據分析結果執行所需工具"""
        results = {}
        
        # 執行 Google Places API 調用
        if "places_api" in analysis.get("tools", []):
            # 修复：如果没有指定位置但有食物类型，使用默認位置(台北)
            location = analysis.get("location", "")
            
            # 檢查是否使用用戶地理位置
            use_user_location = False
            if not location and analysis.get("food_type"):
                # 如果有用戶地理位置資訊，優先使用
                if user_location and user_location.get("latitude") and user_location.get("longitude"):
                    use_user_location = True
                    location = ""  # 清空位置，使用經緯度代替
                else:
                    location = "台北"
                    print(f"未指定位置，使用默認位置：{location}")
            
            if location or use_user_location:
                price_level = analysis.get("price_level")
                # 使用更多的搜索参数
                radius = analysis.get("radius", 2000)  # 默认2000米
                # 確保radius不為None
                if radius is None:
                    radius = 2000
                    print(f"設置默認搜索半徑: {radius}米")
                
                keyword = analysis.get("food_type", "")
                
                # 如果有额外关键词，添加到查询中
                if analysis.get("keywords"):
                    if keyword:
                        keyword = f"{keyword} {analysis.get('keywords')}"
                    else:
                        keyword = analysis.get("keywords")
                
                # 檢查是否使用用戶地理位置
                latitude = None
                longitude = None
                if use_user_location:
                    latitude = user_location.get("latitude")
                    longitude = user_location.get("longitude")
                    print(f"使用用戶位置進行搜尋: 緯度={latitude}, 經度={longitude}")
                
                # 確保正確處理價格等級
                if price_level is not None:
                    print(f"使用價格等級進行搜尋: {price_level}")
                    
                    # 確保 price_level 是整數，處理字符串類型的價格
                    if isinstance(price_level, str):
                        # 轉換文字描述
                        if "平價" in price_level or "便宜" in price_level or "經濟" in price_level:
                            price_level = 2
                        elif "高級" in price_level or "高檔" in price_level:
                            price_level = 3
                        elif "奢華" in price_level or "頂級" in price_level:
                            price_level = 4
                        else:
                            # 預設為中等價格
                            price_level = 2
                            print(f"未識別的價格等級文字: {price_level}，使用預設值: 2")
                    
                    # 如果是平價搜索(price_level<=2)，確保使用maxprice參數限制價格
                    if isinstance(price_level, int) and price_level <= 2:
                        print(f"檢測到平價搜索需求($$及以下)，設置最高價格等級為: {price_level}")
                    elif "平價" in keyword or "經濟" in keyword:
                        price_level = 2
                        print(f"從關鍵字檢測到平價需求，設置價格等級為: {price_level}")
                
                places_result = self.places_api.search_nearby(
                    location=location,
                    keyword=keyword,
                    radius=radius,
                    price_level=price_level,
                    latitude=latitude,
                    longitude=longitude
                )
                
                # 獲取前三個結果的詳細信息
                if places_result.get("status") == "OK" and places_result.get("results"):
                    detailed_places = []
                    for place in places_result["results"][:3]:
                        place_id = place["place_id"]
                        details = self.places_api.get_place_details(place_id)
                        if details.get("status") == "OK":
                            # 参考scraper.py处理细节数据
                            result = details["result"]
                            # 确保照片URL使用我们的代理
                            if result.get("photos") and len(result["photos"]) > 0:
                                photo_reference = result["photos"][0].get("photo_reference")
                                if photo_reference:
                                    result["photo"] = f"/chat/proxy_photo/?reference={photo_reference}&maxwidth=800"
                                    
                            # 增强营业时间显示
                            if result.get("opening_hours") and result["opening_hours"].get("weekday_text"):
                                result["formatted_opening_hours"] = "\n".join(result["opening_hours"]["weekday_text"])
                            
                            # 添加额外的处理以适配前端卡片展示
                            result["is_open"] = result.get("opening_hours", {}).get("open_now", False)
                            result["address"] = result.get("formatted_address", "地址未知")
                            result["phone"] = result.get("formatted_phone_number", "")
                            result["website"] = result.get("website", "")
                            result["total_ratings"] = result.get("user_ratings_total", 0)
                            
                            # 提供料理類型數據
                            if not result.get("types"):
                                result["types"] = ["restaurant"]
                                
                            # 確保有評論數據
                            if not result.get("reviews") or len(result.get("reviews", [])) == 0:
                                result["reviews"] = [{"text": "這家餐廳的菜品非常美味，服務也很好，推薦前來品嚐。"}]
                            
                            # 處理評論，截取最多前3條有內容的評論
                            if result.get("reviews"):
                                valid_reviews = [review for review in result["reviews"] if review.get("text") and len(review.get("text", "")) > 10]
                                result["reviews"] = valid_reviews[:3]
                            
                            detailed_places.append(result)
                    
                    # 按评分排序
                    detailed_places.sort(key=lambda x: x.get("rating", 0), reverse=True)
                    results["places"] = detailed_places
                else:
                    results["places"] = []
                    print(f"Google Places API 搜索失败，状态: {places_result.get('status')}")
                    if places_result.get("error_message"):
                        print(f"错误信息: {places_result.get('error_message')}")
            else:
                results["places"] = []
                print("缺少位置信息，无法搜索餐厅")
        
        # 獲取餐廳基本信息後，根據需要進行菜單和評論爬取
        if "places" in results and results["places"] and "menu_scraper" in analysis.get("tools", []):
            # 使用已初始化的菜單爬蟲工具
            menu_results = []
            for place in results["places"]:
                # 檢查是否有網站URL
                website = place.get("website")
                if website and analysis.get("specific_dishes"):
                    # 爬取菜單並檢查特定菜品
                    menu_data = self.menu_scraper.scrape_menu(
                        restaurant_name=place.get("name", ""),
                        website_url=website,
                        target_dishes=analysis.get("specific_dishes", [])
                    )
                    menu_results.append(menu_data)
                    
                    # 如果這家餐廳有匹配的菜品，增加相關性分數
                    if menu_data.get("has_matches"):
                        # 增加餐廳排名分數
                        place["relevance_score"] = place.get("relevance_score", 0) + 5
                        # 添加菜單匹配信息到餐廳數據
                        place["menu_matches"] = menu_data.get("matches", [])
            
            # 保存菜單爬取結果
            results["menu_data"] = menu_results
        
        # 執行高級搜索 API 調用
        if "search_api" in analysis.get("tools", []):
            query = analysis.get("query_for_search", "")
            
            # 如果查詢中提到"10大"、"推薦"、"最佳"等關鍵詞，進行相關搜索
            ranking_keywords = ["10大", "推薦", "最佳", "必吃", "人氣", "排名"]
            # 確保user_query不為空，避免錯誤
            has_ranking_query = False
            if user_query:
                has_ranking_query = any(keyword in user_query for keyword in ranking_keywords)
            
            if has_ranking_query:
                # 搜索排名相關文章
                if analysis.get("food_type") and analysis.get("location"):
                    ranking_query = f"{analysis['location']} {analysis['food_type']} 推薦 排名"
                    search_result = self.search_api.search(ranking_query)
                    results["ranking_search"] = search_result.get("items", [])
            
            # 如果有特定菜品，搜索菜品評價
            if analysis.get("specific_dishes") and "places" in results and results["places"]:
                dish_results = []
                for dish in analysis["specific_dishes"]:
                    # 對每家餐廳的特定菜品進行搜索
                    for place in results["places"][:3]:  # 限制前3家餐廳
                        dish_search = self.search_api.search_restaurant_reviews(
                            restaurant_name=place.get("name", ""),
                            location=analysis.get("location", ""),
                            specific_dish=dish
                        )
                        dish_results.append({
                            "restaurant": place.get("name", ""),
                            "dish": dish,
                            "search_results": dish_search.get("items", [])
                        })
                results["dish_search"] = dish_results
        
        # 根據所有工具的結果重新排序餐廳
        if "places" in results and results["places"]:
            # 計算綜合評分
            for place in results["places"]:
                # 基礎分數 = 評分 * 10
                base_score = (place.get("rating", 0) * 10)
                # 評價數加分
                reviews_score = min(10, place.get("user_ratings_total", 0) / 100)  # 最多10分
                # 相關性加分
                relevance_score = place.get("relevance_score", 0)
                
                # 計算總分
                total_score = base_score + reviews_score + relevance_score
                place["_score"] = total_score
            
            # 根據綜合評分排序
            results["places"].sort(key=lambda x: x.get("_score", 0), reverse=True)
        
        return results
    
    def generate_response(self, user_query: str, tool_results: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """生成最終回應"""
        try:
            # 記錄工具調用結果
            print("==== 工具調用結果 ====")
            print(f"查詢: {user_query}")
            
            if "places" in tool_results:
                print(f"餐廳資料數量: {len(tool_results['places'])}")
                for i, place in enumerate(tool_results["places"], 1):
                    print(f"餐廳 {i}:")
                    print(f"  名稱: {place.get('name', '未知')}")
                    print(f"  地址: {place.get('formatted_address', '未知')}")
                    print(f"  評分: {place.get('rating', '未知')}")
                    print(f"  價格等級: {place.get('price_level', '未知')} ({place.get('price_level_text', '')})")
                    print(f"  營業狀態: {place.get('business_status_text', place.get('business_status', '未知'))}")
                    print(f"  類型: {place.get('cuisine_type', '未知')}")
                    
                    # 处理照片URL
                    photo_reference = None
                    if place.get("photos") and len(place["photos"]) > 0:
                        photo_reference = place["photos"][0].get("photo_reference")
                        if photo_reference:
                            # 使用代理URL替代直接Google API URL
                            proxy_photo_url = f"/chat/proxy_photo/?reference={photo_reference}&maxwidth=800"
                            place["photo"] = proxy_photo_url
                            print(f"  照片URL(代理): {place['photo']}")
                    
            else:
                print("未獲取到餐廳資料")
                
            if "search" in tool_results:
                print(f"搜索結果數量: {len(tool_results['search'])}")
            else:
                print("未獲取到搜索結果")
                
            # 如果沒有工具結果，直接回應無法取得資訊
            if (not tool_results.get("places") and not tool_results.get("search")) and ("餐廳" in user_query or "推薦" in user_query or "美食" in user_query):
                print("無工具結果，回應無法取得資訊")
                return "很抱歉，目前系統無法取得您所需的資訊。請稍後再試或嘗試其他查詢方式。"
            
            system_prompt = """
            你是一個專業的美食推薦助理，需要根據提供的資料生成簡潔且有幫助的回答。
            
            請根據以下資料生成回覆:
            1. 用戶查詢
            2. 查詢分析結果
            3. 餐廳基本信息
            4. 菜單爬取結果 (如有)
            5. 網路評價搜索結果 (如有)
            6. 特定菜品評價 (如有)
            
            回答格式要求:
            - 使用繁體中文
            - 只需提供簡短介紹，例如「為您推薦以下台北平價火鍋店：」
            - 不要在文字中重複餐廳名稱、評分、地址等卡片上已顯示的資訊
            - 如果用戶詢問特定菜品，只需簡短提及「這些餐廳提供您想要的菜品」
            - 如果用戶有特定偏好(如不要辣)，只需簡短提及「這些餐廳符合您的偏好」
            
            注意:
            - 回答必須非常簡短，因為詳細資訊已在卡片上顯示
            - 不要列出餐廳名稱、地址、評分等資訊
            - 不要提及API或爬蟲等技術詞彙
            """
            
            # 格式化工具結果為字串
            places_info = ""
            if tool_results.get("places"):
                places_info = "餐廳資訊:\n"
                for i, place in enumerate(tool_results["places"], 1):
                    name = place.get("name", "未知餐廳")
                    address = place.get("formatted_address", "地址未提供")
                    rating = place.get("rating", "暫無評分")
                    
                    # 使用已格式化的价格等级文本
                    price_str = place.get("price_level_text", "價格未知")
                    if not price_str and place.get("price_level") is not None:
                        price_str = "$" * (place.get("price_level") + 1)
                    
                    # 使用格式化后的营业状态文本
                    status = place.get("business_status_text", "")
                    if not status:
                        business_status = place.get('business_status', '')
                        if business_status == 'OPERATIONAL':
                            status = "營業中"
                        elif business_status == 'CLOSED_TEMPORARILY':
                            status = "暫時休業"
                        elif business_status == 'CLOSED_PERMANENTLY':
                            status = "永久停業"
                        else:
                            # 使用旧方法作为后备
                            opening_hours = place.get("opening_hours", {})
                            status = "營業中" if opening_hours and opening_hours.get("open_now") else "已休息"
                    
                    # 餐厅类型
                    cuisine_type = place.get("cuisine_type", "")
                    cuisine_info = f"類型: {cuisine_type}\n   " if cuisine_type else ""
                    
                    # 获取格式化的营业时间
                    opening_hours_text = place.get("formatted_opening_hours", "")
                    if not opening_hours_text and place.get("opening_hours") and place["opening_hours"].get("weekday_text"):
                        opening_hours_text = "\n".join(place["opening_hours"]["weekday_text"])
                    opening_info = f"營業時間: {opening_hours_text}\n   " if opening_hours_text else ""
                    
                    # 添加照片URL信息
                    photo_url = place.get("photo", "")
                    photo_info = f"照片: {photo_url}\n   " if photo_url else ""
                    
                    # 添加电话和网站信息
                    phone = place.get("formatted_phone_number", "")
                    phone_info = f"電話: {phone}\n   " if phone else ""
                    
                    website = place.get("website", "")
                    website_info = f"網站: {website}\n   " if website else ""
                    
                    places_info += f"{i}. {name}\n   地址: {address}\n   評分: {rating}\n   價格: {price_str}\n   狀態: {status}\n   {cuisine_info}{opening_info}{phone_info}{website_info}{photo_info}\n"
            
            search_info = ""
            if tool_results.get("search"):
                search_info = "網路評價與推薦:\n"
                for i, item in enumerate(tool_results["search"], 1):
                    title = item.get("title", "未知標題")
                    snippet = item.get("snippet", "未提供摘要")
                    link = item.get("link", "#")
                    
                    search_info += f"{i}. {title}\n   {snippet}\n   來源: {link}\n\n"
            
            # 添加菜單和評論的格式化內容
            menu_info = ""
            if "menu_data" in tool_results:
                menu_info = "菜單信息:\n"
                for menu_data in tool_results["menu_data"]:
                    restaurant = menu_data.get("restaurant", "未知餐廳")
                    has_menu = menu_data.get("has_menu", False)
                    matches = menu_data.get("matches", [])
                    
                    menu_info += f"{restaurant}："
                    if has_menu:
                        if matches:
                            menu_info += f"確認有以下菜品: {', '.join([m['dish'] for m in matches])}\n"
                        else:
                            menu_info += "已爬取菜單，但未找到特定菜品。\n"
                    else:
                        menu_info += "無法獲取菜單。\n"
            
            # 組合訊息並調用 GPT
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
                用戶查詢: {user_query}
                
                查詢分析: 
                地點: {analysis.get('location', '未指定')}
                食物類型: {analysis.get('food_type', '未指定')}
                特定菜品: {', '.join(analysis.get('specific_dishes', ['無特定菜品']))}
                偏好: {', '.join(analysis.get('preferences', ['無特定偏好']))}
                排除項: {', '.join(analysis.get('exclusions', ['無排除項']))}
                
                {places_info}
                
                {menu_info}
                
                {search_info}
                """}
            ]
            
            response = self.gpt_api.get_completion(messages)
            
            # 增加更多錯誤處理
            if not response or not isinstance(response, dict):
                print(f"API 回應無效: {response}")
                return "很抱歉，目前系統無法處理您的請求。請稍後再試。"
                
            choices = response.get("choices", [])
            if not choices or len(choices) == 0:
                print(f"API 回應中沒有 choices: {response}")
                return "很抱歉，系統目前無法生成合適的回應。請嘗試重新提問。"
                
            return choices[0].get("message", {}).get("content", "無法生成回應")
            
        except Exception as e:
            print(f"生成回應時發生異常: {str(e)}")
            return f"很抱歉，處理您的請求時發生錯誤: {str(e)}。請稍後再試。"
    
    def process_query(self, user_query: str, user_location: Dict[str, Any] = None, user=None) -> Dict[str, Any]:
        """
        處理用戶查詢
        
        參數:
            user_query: 用戶的查詢字串
            user_location: 用戶地理位置信息（可選）
            user: 用戶對象（可選，用於個性化處理）
            
        返回:
            包含處理結果的字典
        """
        try:
            # 分析查詢
            print(f"處理查詢: {user_query}")
            analysis = self.analyze_query(user_query)
            
            # 如果提供了用戶對象，可以處理用戶偏好
            if user:
                # 先從查詢中提取偏好
                preferences = self.preference_service.extract_preferences_from_dialog(user, user_query)
                if preferences:
                    # 儲存提取到的偏好
                    print(f"從對話中提取到的偏好: {preferences}")
                    self.preference_service.save_preferences(user, preferences, 'dialog')
                    
                # 如果查詢未指定特定條件，可以使用用戶偏好增強查詢
                if not analysis.get('food_type') and not analysis.get('location'):
                    pref_params = self.preference_service.get_preference_based_recommendations(
                        user, location=analysis.get('location'))
                    
                    # 只在用戶沒有明確指定時使用偏好
                    for key, value in pref_params.items():
                        if key not in analysis or not analysis[key]:
                            analysis[key] = value
                            print(f"使用用戶偏好增強查詢: {key}={value}")
            
            # 執行工具調用，傳入user_query參數
            tool_results = self.execute_tools(analysis, user_location, user_query)
            
            # 如果提供了用戶對象，可以根據用戶忌口過濾結果
            if user and 'places' in tool_results:
                places_data = tool_results['places']
                if places_data:
                    # 過濾結果，排除用戶忌口的餐廳
                    original_count = len(places_data)
                    tool_results['places'] = self.preference_service.filter_recommendations_by_preferences(
                        user, places_data)
                    filtered_count = len(tool_results['places'])
                    
                    if original_count > filtered_count:
                        print(f"基於用戶偏好過濾餐廳: 從{original_count}家減少到{filtered_count}家")
            
            # 生成回應
            response_text = self.generate_response(user_query, tool_results, analysis)
            
            return {
                "response_text": response_text,
                "tool_results": tool_results,
                "analysis": analysis
            }
        except Exception as e:
            print(f"處理查詢時出錯: {str(e)}")
            return {
                "response_text": f"很抱歉，處理您的查詢時遇到問題。請再試一次或嘗試不同的查詢。(錯誤: {str(e)})",
                "tool_results": {},
                "analysis": {}
            }
