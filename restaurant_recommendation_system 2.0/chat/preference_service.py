import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.db.models import Avg
from django.utils import timezone
from django.contrib.auth.models import User
from .models import  Message, SavedPlace
from user.models import UserPreferenceDetail
from .tools import LLMFactory
from post.models import Post as UserPost, FavoritePost
# 整理/讀寫使用者偏好

class PreferenceService:
    """用戶偏好服務類，用於處理偏好的提取、存儲和檢索"""
    
    def __init__(self):
        """初始化偏好服務"""
        self.gpt_api = LLMFactory.create_llm()  # 使用工廠方法
        
    def extract_preferences_from_dialog(self, user: User, message_content: str) -> List[Dict]:
        """
        從對話中提取用戶偏好
        
        參數:
            user: 用戶對象
            message_content: 用戶消息內容
            
        返回:
            偏好列表，每個偏好為包含類型、值和分數的字典
        """
        # 使用LLM分析對話內容
        system_prompt = """
        你是一個專精於分析使用者飲食偏好的AI助手。你的任務是從使用者的對話中提取與食物相關的偏好、喜好和忌口。
        
        請從下列文本中識別可能的偏好資訊，並以JSON格式輸出：
        1. 喜好：使用者明確表示喜歡的食物、菜系、口味或特點
        2. 忌口：使用者明確表示不喜歡或不能吃的食物、配料或口味
        3. 地區：使用者提到的地理位置偏好
        
        輸出格式應為：
        {
            "preferences": [
                {
                    "type": "口味/菜系/地區/禁忌",
                    "value": "具體偏好值",
                    "score": 數值（喜好為正值1-5，忌口為負值-1至-5）
                }
            ]
        }
        
        重要規則：
        - 喜好值應根據表達強度給予1-5的分數（非常喜歡=5，喜歡=3，還不錯=1）
        - 忌口值應根據表達強度給予-1至-5的分數（不喜歡=-1，討厭=-3，過敏/絕對不能吃=-5）
        - 只提取明確表達的偏好，不要推測或擴展
        - 如果沒有識別到偏好，返回空preferences列表
        - 具體偏好值請使用簡短關鍵詞（如"辣"、"日式料理"、"台北"），而非長句
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_content}
        ]
        
        response = self.gpt_api.get_completion(messages)
        
        if not response or not isinstance(response, dict):
            return []
            
        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            result = json.loads(content)
            return result.get("preferences", [])
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            print(f"解析對話偏好時出錯: {str(e)}")
            return []
            
    def extract_preferences_from_post(self, user: User, post_id: int, is_user_post=True) -> List[Dict]:
        """
        從貼文中提取用戶偏好
        
        參數:
            user: 用戶對象
            post_id: 貼文ID
            is_user_post: 是否為用戶自己的貼文(True)或收藏的貼文(False)
            
        返回:
            偏好列表，每個偏好為包含類型、值和分數的字典
        """
        try:
            # 獲取貼文內容
            if is_user_post:
                post = UserPost.objects.get(id=post_id, user=user)
                content = f"{post.title}\n{post.content}"
                source = "post"
            else:
                favorite = FavoritePost.objects.get(id=post_id, user=user)
                post = favorite.post
                content = f"{post.title}\n{post.content}"
                source = "collection"
                
            # 使用LLM分析貼文內容
            system_prompt = """
            你是一個專精於分析文章中飲食內容的AI助手。請從下列文章中提取與食物、餐廳、菜系相關的關鍵信息。
            
            請識別:
            1. 提到的特定食物或料理（如壽司、牛排、拉麵）
            2. 菜系或餐廳類型（如日式、義大利菜、火鍋）
            3. 餐點口味特點（如辣、甜、酸、鮮）
            4. 地區位置（如台北市、信義區）
            5. 明確表達的情感（正面或負面評價）
            
            輸出格式應為：
            {
                "preferences": [
                    {
                        "type": "口味/菜系/地區/禁忌",
                        "value": "具體偏好值",
                        "score": 數值（正面評價為1-3，負面評價為-1至-3）
                    }
                ]
            }
            
            規則：
            - 對於文章中明確推薦或正面評價的項目，給予2-3分
            - 對於中性提及的項目，給予1分
            - 對於負面評價的項目，給予-2至-3分
            - 只提取明確提及的項目，不要推測
            - 如果是收藏的文章，假設用戶對內容有興趣，可適當提高分數
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
            
            response = self.gpt_api.get_completion(messages)
            
            if not response or not isinstance(response, dict):
                return []
                
            try:
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                return result.get("preferences", [])
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                print(f"解析貼文偏好時出錯: {str(e)}")
                return []
        except (UserPost.DoesNotExist, FavoritePost.DoesNotExist) as e:
            print(f"獲取貼文數據時出錯: {str(e)}")
            return []
            
    def save_preferences(self, user: User, preferences: List[Dict], source: str, source_id: Optional[int] = None) -> None:
        """
        保存用戶偏好到數據庫
        
        參數:
            user: 用戶對象
            preferences: 偏好列表，每個偏好為包含類型、值和分數的字典
            source: 來源（如 'dialog', 'post', 'collection'）
            source_id: 來源ID（如訊息ID或貼文ID）
        """
        if not preferences:
            return
            
        for pref in preferences:
            pref_type = pref.get('type')
            pref_value = pref.get('value')
            score = pref.get('score', 0)
            
            if not pref_type or not pref_value:
                continue
                
            # 檢查是否已存在相同偏好
            existing_pref = UserPreferenceDetail.objects.filter(
                user=user,
                preference_type=pref_type,
                preference_value=pref_value
            ).first()
            
            if existing_pref:
                # 更新已有偏好的分數，使用加權平均
                # 新分數 = 舊分數 * 0.7 + 新偏好 * 0.3（給予一定的時間衰減）
                new_score = existing_pref.score * 0.7 + score * 0.3
                
                # 如果分數接近0（-0.5到0.5之間），可考慮移除此偏好
                if -0.5 <= new_score <= 0.5:
                    # 可選：刪除變得中性的偏好
                    # existing_pref.delete()
                    # 或保留但記錄低分數
                    existing_pref.score = new_score
                    existing_pref.updated_at = timezone.now()
                    existing_pref.save()
                else:
                    existing_pref.score = new_score
                    existing_pref.updated_at = timezone.now()
                    existing_pref.save()
            else:
                # 創建新的偏好記錄
                UserPreferenceDetail.objects.create(
                    user=user,
                    preference_type=pref_type,
                    preference_value=pref_value,
                    score=score,
                    source=source,
                    source_id=source_id
                )
                
    def get_user_preferences(self, user: User, min_score_abs: float = 1.0, limit: int = 20) -> Dict[str, List[Dict]]:
        """
        獲取用戶偏好，按類型分組
        
        參數:
            user: 用戶對象
            min_score_abs: 最小分數絕對值（過濾低強度偏好）
            limit: 每種類型返回的最大偏好數量
            
        返回:
            按類型分組的偏好字典
        """
        # 獲取用戶所有高於閾值的偏好
        positive_prefs = UserPreferenceDetail.objects.filter(
            user=user, 
            score__gte=min_score_abs
        ).order_by('-score')[:limit]
        
        negative_prefs = UserPreferenceDetail.objects.filter(
            user=user, 
            score__lte=-min_score_abs
        ).order_by('score')[:limit]
        
        # 按類型分組
        grouped_prefs = {}
        
        for pref in list(positive_prefs) + list(negative_prefs):
            pref_type = pref.preference_type
            
            if pref_type not in grouped_prefs:
                grouped_prefs[pref_type] = []
                
            grouped_prefs[pref_type].append({
                'value': pref.preference_value,
                'score': pref.score,
                'updated_at': pref.updated_at
            })
            
        return grouped_prefs
        
    def apply_time_decay(self, days_since: int) -> float:
        """
        計算基於時間的衰減係數
        
        參數:
            days_since: 自上次更新以來的天數
            
        返回:
            衰減係數 (0-1之間)
        """
        # 使用指數衰減模型：每週降低5%
        weekly_decay = 0.95
        weeks = days_since / 7.0
        return math.pow(weekly_decay, weeks)
        
    def refresh_preference_scores(self, user: User = None) -> None:
        """
        為所有用戶或特定用戶的偏好分數應用時間衰減
        
        參數:
            user: 特定用戶（如果為None，則處理所有用戶）
        """
        now = timezone.now()
        
        # 獲取要處理的偏好
        preferences = UserPreferenceDetail.objects.all()
        if user:
            preferences = preferences.filter(user=user)
            
        for pref in preferences:
            # 計算自上次更新以來的天數
            days_since = (now - pref.updated_at).days
            
            # 如果超過30天未更新，應用時間衰減
            if days_since > 30:
                decay_factor = self.apply_time_decay(days_since)
                pref.score *= decay_factor
                
                # 如果分數接近0，考慮刪除
                if abs(pref.score) < 0.5:
                    pref.delete()
                else:
                    pref.updated_at = now  # 更新時間戳
                    pref.save()
                    
    def get_preference_based_recommendations(self, user: User, location: str = None) -> Dict:
        """
        基於用戶偏好生成餐廳推薦
        
        參數:
            user: 用戶對象
            location: 位置限制（可選）
            
        返回:
            推薦參數字典
        """
        # 獲取用戶偏好
        preferences = self.get_user_preferences(user)
        
        # 提取最強烈的喜好和忌口
        liked_cuisines = []
        disliked_flavors = []
        preferred_locations = []
        
        for pref_type, values in preferences.items():
            if pref_type.lower() in ['菜系', '料理']:
                # 提取喜好的菜系
                for item in values:
                    if item['score'] > 2:  # 只選擇強烈喜好
                        liked_cuisines.append(item['value'])
            elif pref_type.lower() in ['口味', '風味']:
                # 提取忌口
                for item in values:
                    if item['score'] < -2:  # 只選擇強烈排斥
                        disliked_flavors.append(item['value'])
            elif pref_type.lower() in ['地區', '地點']:
                # 提取地區偏好
                for item in values:
                    if item['score'] > 0:  # 任何正向的地區偏好
                        preferred_locations.append(item['value'])
        
        # 構建推薦參數
        recommendation_params = {}
        
        # 如果有喜好的菜系，添加到關鍵字中
        if liked_cuisines:
            recommendation_params['food_type'] = liked_cuisines[0]  # 使用最強烈的菜系偏好
            
        # 如果有地區偏好且未指定位置，使用偏好地區
        if not location and preferred_locations:
            recommendation_params['location'] = preferred_locations[0]
        elif location:
            recommendation_params['location'] = location
            
        # 其他可能的參數，如價格等級可以從UserPreference獲取
        try:
            user_general_pref = user.food_preferences
            if user_general_pref.preferred_price_level is not None:
                recommendation_params['price_level'] = user_general_pref.preferred_price_level
        except:
            pass
            
        # 返回構建的參數
        return recommendation_params
        
    def filter_recommendations_by_preferences(self, user: User, restaurants: List[Dict]) -> List[Dict]:
        """
        根據用戶忌口偏好過濾餐廳推薦結果
        
        參數:
            user: 用戶對象
            restaurants: 餐廳列表
            
        返回:
            過濾後的餐廳列表
        """
        if not restaurants:
            return []
            
        # 獲取用戶忌口偏好
        preferences = self.get_user_preferences(user)
        
        # 提取強烈的忌口
        strong_dislikes = []
        for pref_type, values in preferences.items():
            if pref_type.lower() in ['禁忌', '口味', '菜系']:
                for item in values:
                    if item['score'] < -3:  # 只考慮非常強烈的忌口
                        strong_dislikes.append(item['value'].lower())
        
        # 如果沒有強烈忌口，直接返回原始列表
        if not strong_dislikes:
            return restaurants
            
        # 過濾餐廳
        filtered_restaurants = []
        for restaurant in restaurants:
            # 檢查餐廳名稱、類型和描述是否包含忌口關鍵詞
            name = restaurant.get('name', '').lower()
            types = [t.lower() for t in restaurant.get('types', [])]
            vicinity = restaurant.get('vicinity', '').lower()
            
            # 檢查是否包含任何忌口關鍵詞
            should_exclude = any(
                dislike in name or 
                any(dislike in t for t in types) or 
                dislike in vicinity
                for dislike in strong_dislikes
            )
            
            if not should_exclude:
                filtered_restaurants.append(restaurant)
        
        return filtered_restaurants 