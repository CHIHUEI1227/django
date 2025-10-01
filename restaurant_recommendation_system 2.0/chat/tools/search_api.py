"""
Google Search API 工具類，用於搜尋網絡內容和餐廳評價
"""

import requests
from typing import Dict, Any
from .api_keys import GOOGLE_SEARCH_API_KEY, GOOGLE_CX_ID

class GoogleSearchAPI:
    """Google Search API 工具類"""
    
    def __init__(self, api_key: str = GOOGLE_SEARCH_API_KEY, cx_id: str = GOOGLE_CX_ID):
        self.api_key = api_key
        self.cx_id = cx_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, num: int = 5) -> Dict[str, Any]:
        """
        執行 Google 搜尋
        
        參數:
            query: 搜尋查詢字串
            num: 返回結果數量
            
        返回:
            搜尋結果字典
        """
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cx_id,
            "num": num,
            "lr": "lang_zh-TW",  # 限制搜尋繁體中文結果
            "hl": "zh-TW"        # 設置界面語言為繁體中文
        }
        
        response = requests.get(self.base_url, params=params)
        return response.json()
        
    def search_restaurant_reviews(self, restaurant_name: str, location: str = None, specific_dish: str = None) -> Dict[str, Any]:
        """
        針對特定餐廳或特定菜品搜尋評論
        
        參數:
            restaurant_name: 餐廳名稱
            location: 地點 (可選)
            specific_dish: 特定菜品名稱 (可選)
            
        返回:
            評論搜尋結果
        """
        query = restaurant_name
        if location:
            query += f" {location}"
        if specific_dish:
            query += f" {specific_dish} 評價 評論"
        else:
            query += " 評價 評論 推薦"
            
        return self.search(query, num=5) 