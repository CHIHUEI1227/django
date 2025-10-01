"""
OpenAI GPT API 工具類，用於處理自然語言生成任務
"""

import requests
import json
from typing import List, Dict, Any
from .api_keys import GPT_API_KEY

class GPTAPI:
    """OpenAI GPT API 工具類"""
    
    def __init__(self, api_key: str = GPT_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """
        獲取 GPT 回應
        
        參數:
            messages: 訊息列表，格式為 [{"role": "user", "content": "你好"}]
            model: 使用的模型名稱
            
        返回:
            GPT 回應字典
        """
        try:
            # 檢查 API 密鑰是否已設置
            if not self.api_key or self.api_key == "":
                print("API 密鑰未設置，使用模擬回應")
                return self._get_mock_response(messages)
            
            data = {
                "model": model,
                "messages": messages
            }
            
            # 嘗試發送請求到 OpenAI API
            try:
                response = requests.post(self.base_url, headers=self.headers, json=data, timeout=30)
                response.raise_for_status()  # 如果狀態碼不是 200，會拋出異常
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"API 請求失敗: {str(e)}")
                return self._get_mock_response(messages)
            
        except Exception as e:
            print(f"獲取 GPT 回應時發生異常: {str(e)}")
            return self._get_mock_response(messages)
        
    def _get_mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        當 API 調用失敗時生成模擬回應
        
        參數:
            messages: 訊息列表
            
        返回:
            模擬的 GPT 回應
        """
        # 檢查是否是用戶查詢
        user_message = ""
        system_message = ""
        for message in messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
            elif message.get("role") == "system":
                system_message = message.get("content", "")
        
        # 檢查是否是查詢分析請求
        if "分析用戶的查詢" in system_message and "JSON" in system_message:
            # 模擬分析查詢的回應
            location = ""
            food_type = ""
            price_level = None
            
            # 簡單提取地點
            locations = ["台北", "台中", "高雄", "信義區", "西門町", "東區", "北投", "士林"]
            for loc in locations:
                if loc in user_message:
                    location = loc
                    break
            
            # 簡單提取食物類型
            food_types = ["日本料理", "韓式", "火鍋", "燒烤", "日式", "義式", "泰式", "法式", "美式", "中式", "西式", "素食"]
            for food in food_types:
                if food in user_message:
                    food_type = food
                    break
            
            # 簡單提取價格等級
            if any(term in user_message for term in ["超便宜", "非常便宜", "便宜到爆", "銅板價"]):
                price_level = 0
            elif any(term in user_message for term in ["便宜", "實惠", "學生價"]):
                price_level = 1
            elif any(term in user_message for term in ["中等", "適中", "普通價位"]):
                price_level = 2
            elif any(term in user_message for term in ["高檔", "昂貴", "高級", "高價"]):
                price_level = 3
            elif any(term in user_message for term in ["頂級", "奢華", "非常高級", "豪華"]):
                price_level = 4
            
            # 特殊處理"平價"
            if "平價" in user_message or "經濟" in user_message:
                price_level = 2
            
            # 生成分析結果
            analysis_result = {
                "tools": ["places_api"],
                "location": location,
                "food_type": food_type,
                "price_level": price_level,
                "query_for_search": "",
                "radius": 2000,
                "keywords": ""
            }
            
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(analysis_result, ensure_ascii=False)
                        }
                    }
                ]
            }
        
        # 根據用戶訊息生成模擬回應
        mock_content = ""
        if "餐廳" in user_message or "推薦" in user_message:
            # 檢查特定類型
            if "燒烤" in user_message:
                if "平價" in user_message or "便宜" in user_message:
                    mock_content = """以下是我推薦的平價燒烤餐廳：

1. 燒肉王 - 平價燒烤店，提供新鮮食材和多種醬料選擇
   地址: 台北市中山區林森北路123號
   評分: 4.3
   價格: $
   狀態: 營業中

2. 烤肉天堂 - 自助式平價燒烤，多種肉品和蔬菜可選
   地址: 台北市信義區松高路45號
   評分: 4.1
   價格: $
   狀態: 營業中

3. 燒烤夜市 - 道地臺式燒烤，價格經濟實惠
   地址: 台北市大安區師大路32號
   評分: 4.2
   價格: $
   狀態: 營業中

這些店家的價格都很平實，食材新鮮，適合朋友聚餐。您有其他特別的需求嗎？"""
                else:
                    mock_content = """以下是我推薦的燒烤餐廳：

1. 炭火燒肉專門店 - 正宗日式燒肉，選用上等肉品
   地址: 台北市信義區松壽路12號
   評分: 4.7
   價格: $$$
   狀態: 營業中

2. 韓式烤肉屋 - 道地韓式烤肉，提供各式小菜
   地址: 台北市中山區林森北路88號
   評分: 4.4
   價格: $$
   狀態: 營業中

3. BBQ花園 - 戶外烤肉體驗，提供精緻食材和專業服務
   地址: 台北市內湖區成功路三段123號
   評分: 4.5
   價格: $$$
   狀態: 營業中

請問這些推薦符合您的需求嗎？或者您有其他特定的偏好？"""
            elif "火鍋" in user_message:
                mock_content = """以下是我推薦的火鍋餐廳：

1. 老四川麻辣鍋 - 正宗川味，麻辣鮮香，食材新鮮多樣。
   地址: 台北市信義區松高路123號
   評分: 4.5
   價格: $$
   狀態: 營業中

2. 涮涮鍋專門店 - 日式風格涮涮鍋，湯頭清淡鮮美。
   地址: 台北市大安區敦化南路245號
   評分: 4.3
   價格: $$
   狀態: 營業中

3. 養生藥膳鍋 - 溫補養生，食材講究，適合全家享用。
   地址: 台北市中山區南京東路56號
   評分: 4.6
   價格: $$$
   狀態: 營業中

請問這些推薦符合您的需求嗎？或者您有其他特定的偏好？"""
            else:
                mock_content = """以下是我推薦的餐廳：

1. 鼎泰豐 - 世界知名的小籠包，皮薄餡多汁。
   地址: 台北市信義區松高路194號
   評分: 4.8
   價格: $$$
   狀態: 營業中

2. 老四川麻辣鍋 - 正宗川味，麻辣鮮香，食材新鮮多樣。
   地址: 台北市信義區松高路123號
   評分: 4.5
   價格: $$
   狀態: 營業中

3. 金蓬萊遵古台菜 - 傳統台灣料理，古早味道，適合家庭聚餐。
   地址: 台北市中山區林森北路
   評分: 4.6
   價格: $$
   狀態: 營業中

請問這些推薦符合您的需求嗎？或者您有其他特定的偏好？"""
        elif "早餐" in user_message:
            mock_content = """早餐推薦：

1. 燒餅油條 - 經典的中式早餐組合
2. 豆漿與蛋餅 - 營養均衡的搭配
3. 飯糰 - 方便攜帶的早餐選擇
4. 蘿蔔糕 - 煎至金黃的外皮特別香脆

這些早餐都很適合忙碌的早晨！"""
        elif "午餐" in user_message or "晚餐" in user_message:
            mock_content = """以下是一些受歡迎的餐點推薦：

1. 紅燒牛肉麵 - 湯頭濃郁，牛肉軟嫩多汁
2. 三杯雞 - 香氣四溢，搭配白飯超下飯
3. 滷肉飯 - 台灣經典小吃，簡單卻美味
4. 清蒸魚 - 鮮美健康的選擇

您喜歡哪種口味的料理？"""
        else:
            mock_content = """感謝您的提問！我是美食推薦小幫手，可以為您推薦各種美食和餐廳。請告訴我您的口味偏好或是您想了解的美食類型，我會給您最適合的推薦。無論是中式、西式、日式料理，或是特定的料理方式，我都很樂意為您提供建議！"""
        
        # 模擬 OpenAI API 回應格式
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": mock_content
                    }
                }
            ]
        } 