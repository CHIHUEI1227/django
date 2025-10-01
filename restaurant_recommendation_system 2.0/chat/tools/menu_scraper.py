"""
餐廳菜單爬蟲工具，用於獲取特定餐廳的菜單信息
"""

import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

class MenuScraperTool:
    """餐廳菜單爬蟲工具類"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    
    def scrape_menu(self, restaurant_name: str, website_url: str, target_dishes: List[str] = None) -> Dict[str, Any]:
        """
        爬取餐廳菜單
        
        參數:
            restaurant_name: 餐廳名稱
            website_url: 餐廳網站URL
            target_dishes: 目標菜品關鍵詞列表
            
        返回:
            包含菜單和匹配項的字典
        """
        try:
            print(f"正在爬取 {restaurant_name} 的菜單...")
            
            # 實現爬蟲邏輯...
            # 這裡需要根據不同網站結構進行調整
            
            # 模擬菜單項目
            menu_items = [
                "炙燒鮭魚握壽司 - NT$120",
                "鮪魚腹握壽司 - NT$180",
                "鮭魚生魚片 - NT$220",
                "綜合握壽司套餐 - NT$450",
                "特上生魚片 - NT$580"
            ]
            
            # 如果有目標菜品，檢查是否匹配
            matches = []
            if target_dishes and menu_items:
                for dish in target_dishes:
                    dish_matches = [item for item in menu_items if dish.lower() in item.lower()]
                    if dish_matches:
                        matches.append({
                            "dish": dish,
                            "found_in": dish_matches
                        })
            
            return {
                "restaurant": restaurant_name,
                "menu_items": menu_items,
                "matches": matches,
                "has_menu": len(menu_items) > 0,
                "has_matches": len(matches) > 0 if target_dishes else None
            }
            
        except Exception as e:
            print(f"爬取菜單時出錯: {str(e)}")
            return {
                "restaurant": restaurant_name,
                "error": str(e),
                "has_menu": False,
                "has_matches": False
            }
    
    def is_menu_page(self, soup: BeautifulSoup) -> bool:
        """
        判断页面是否包含菜单
        """
        # 检查页面是否包含菜单关键词
        text = soup.get_text().lower()
        menu_keywords = ["菜單", "menu", "餐點", "料理", "套餐", "價格", "price"]
        return any(keyword in text for keyword in menu_keywords)
    
    def extract_price(self, text: str) -> Optional[int]:
        """
        从文本中提取价格
        """
        # 匹配常见价格格式
        price_patterns = [
            r'NT\$\s*(\d+)',  # NT$120
            r'(\d+)\s*元',     # 120元
            r'\$\s*(\d+)',     # $120
            r'¥\s*(\d+)',      # ¥120
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None 