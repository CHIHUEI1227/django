"""
Google Places API 工具類，用於獲取餐廳信息和照片
"""

import requests
import os
import json
from typing import Dict, Any, Optional
from .api_keys import GOOGLE_PLACES_API_KEY

class GooglePlacesAPI:
    """Google Places API 工具類"""
    
    def __init__(self, api_key: str = GOOGLE_PLACES_API_KEY):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def search_nearby(self, 
                      location: str, 
                      keyword: str = None, 
                      radius: int = 2000, 
                      type: str = "restaurant", 
                      price_level: Optional[int] = None,
                      latitude: float = None,
                      longitude: float = None) -> Dict[str, Any]:
        """
        搜尋指定位置附近的餐廳
        
        參數:
            location: 搜尋地點 (例如: "台中市一中街")，如果提供latitude和longitude則可為空
            keyword: 搜尋關鍵字 (例如: "日式料理")
            radius: 搜尋半徑 (單位: 米)
            type: 地點類型 (預設: "restaurant")
            price_level: 價格等級 (0-4，4最貴，None表示不限)
            latitude: 緯度座標 (如果直接提供座標則優先使用)
            longitude: 經度座標 (如果直接提供座標則優先使用)
        
        返回:
            包含餐廳資料的字典
        """
        try:
            # 確保radius有有效值
            if radius is None:
                radius = 2000
                print(f"設定默認搜索半徑: {radius}米")
                
            # 檢查API密鑰是否設置
            if not self.api_key or self.api_key == "":
                print("Error: Google Places API key not set")
                return {"status": "ERROR", "error_message": "API key not configured", "results": []}
                
            # 如果提供了經緯度座標，直接使用
            if latitude is not None and longitude is not None:
                # 搜尋附近餐廳
                nearby_url = f"{self.base_url}/nearbysearch/json"
                nearby_params = {
                    "location": f"{latitude},{longitude}",
                    "radius": radius,
                    "type": type,
                    "key": self.api_key,
                    "language": "zh-TW"  # 設置返回結果為繁體中文
                }
                
                if keyword:
                    nearby_params["keyword"] = keyword
                
                # 處理價格等級 - 如果是"平價"（2或以下），則設置maxprice
                if price_level is not None:
                    # 確保 price_level 是整數
                    if isinstance(price_level, str):
                        # 將文字描述轉換為數值
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
                    
                    if price_level <= 2:  # 平價範圍 ($$及以下)
                        nearby_params["maxprice"] = price_level
                        print(f"搜尋平價餐廳: 最高價格等級設為 {price_level} ($$及以下)")
                    else:  # 高級範圍
                        nearby_params["minprice"] = price_level - 1
                        nearby_params["maxprice"] = price_level
                        print(f"搜尋高級餐廳: 價格等級範圍設為 {price_level-1}-{price_level}")
                
                response = requests.get(nearby_url, params=nearby_params, timeout=10)
                return response.json()
                
            # 如果未提供經緯度，需要從location中獲取
            # 首先嘗試從靜態JSON文件中查找位置信息
            location_found = False
            lat, lng = None, None
            
            if location:
                # 標準化處理地點名稱 (統一處理「臺」和「台」)
                location_normalized = location.replace('台', '臺') if '台' in location else location
                
                # 嘗試從靜態文件讀取地理位置數據
                try:
                    import os
                    import json
                    
                    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                           'static', 'json', 'town.json')
                    
                    if os.path.exists(json_path):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            towns_data = json.load(f)
                        
                        print(f"正在從位置數據庫中尋找位置: {location}")
                        
                        # 先嘗試精確匹配完整地名
                        for town in towns_data:
                            full_name = f"{town['CountyName']}{town['TownName']}"
                            
                            if location_normalized in full_name or full_name in location_normalized:
                                lat = town['latitude']
                                lng = town['longitude']
                                location_found = True
                                print(f"找到精確位置: {full_name}, 座標: {lat}, {lng}")
                                break
                        
                        # 如果精確匹配失敗，嘗試匹配縣市名稱
                        if not location_found:
                            for town in towns_data:
                                county_name = town['CountyName']
                                town_name = town['TownName']
                                
                                # 檢查縣市名稱是否在查詢中，或查詢是否在縣市名稱中
                                if county_name in location_normalized or location_normalized in county_name:
                                    # 對於縣市匹配，優先使用縣市中心（通常是XXX市或第一個行政區）
                                    if town_name in ['中正區', '中區', '中山區'] or '市' in town_name:
                                        lat = town['latitude']
                                        lng = town['longitude']
                                        location_found = True
                                        print(f"找到縣市中心位置: {county_name}{town_name}, 座標: {lat}, {lng}")
                                        break
                            
                            # 如果仍未找到，使用第一個匹配縣市名的資料
                            if not location_found:
                                for town in towns_data:
                                    county_name = town['CountyName']
                                    
                                    if county_name in location_normalized or location_normalized in county_name:
                                        lat = town['latitude']
                                        lng = town['longitude']
                                        location_found = True
                                        print(f"找到縣市位置: {county_name}, 座標: {lat}, {lng}")
                                        break
                    else:
                        print(f"位置數據文件不存在: {json_path}")
                except Exception as e:
                    print(f"從靜態文件讀取位置數據時出錯: {str(e)}")
            
            # 如果從靜態文件中未找到位置，使用Google地理編碼API
            if not location_found:
                print(f"嘗試使用Google地理編碼API查詢位置: {location}")
                geocode_url = f"{self.base_url}/findplacefromtext/json"
                geocode_params = {
                    "input": location,
                    "inputtype": "textquery",
                    "fields": "geometry",
                    "key": self.api_key,
                    "language": "zh-TW"  # 設置返回結果為繁體中文
                }
                
                response = requests.get(geocode_url, params=geocode_params, timeout=10)
                result = response.json()
                
                if result.get("status") != "OK" or not result.get("candidates"):
                    error_msg = f"無法找到位置: {location}"
                    print(error_msg)
                    return {"status": "ZERO_RESULTS", "error_message": error_msg, "results": []}
                
                # 獲取座標
                location_data = result["candidates"][0]["geometry"]["location"]
                lat = location_data["lat"]
                lng = location_data["lng"]
                print(f"使用Google API找到位置座標: {lat}, {lng}")
            
            # 搜尋附近餐廳
            nearby_url = f"{self.base_url}/nearbysearch/json"
            nearby_params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": type,
                "key": self.api_key,
                "language": "zh-TW"  # 設置返回結果為繁體中文
            }
            
            if keyword:
                nearby_params["keyword"] = keyword
            
            # 處理價格等級 - 如果是"平價"（2或以下），則設置maxprice
            if price_level is not None:
                # 確保 price_level 是整數
                if isinstance(price_level, str):
                    # 將文字描述轉換為數值
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
                
                if price_level <= 2:  # 平價範圍 ($$及以下)
                    nearby_params["maxprice"] = price_level
                    print(f"搜尋平價餐廳: 最高價格等級設為 {price_level} ($$及以下)")
                else:  # 高級範圍
                    nearby_params["minprice"] = price_level - 1
                    nearby_params["maxprice"] = price_level
                    print(f"搜尋高級餐廳: 價格等級範圍設為 {price_level-1}-{price_level}")
            
            print(f"搜索參數: {nearby_params}")
            response = requests.get(nearby_url, params=nearby_params, timeout=10)
            
            # 檢查響應
            result = response.json()
            print(f"搜索結果狀態: {result.get('status')}, 找到結果數量: {len(result.get('results', []))}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API請求錯誤: {str(e)}"
            print(error_msg)
            return {"status": "ERROR", "error_message": error_msg, "results": []}
        except Exception as e:
            error_msg = f"搜尋附近餐廳時發生未知錯誤: {str(e)}"
            print(error_msg)
            return {"status": "ERROR", "error_message": error_msg, "results": []}
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        獲取特定地點的詳細資訊
        
        參數:
            place_id: Google Places API 的地點ID
            
        返回:
            包含地點詳細資訊的字典
        """
        details_url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,rating,formatted_address,formatted_phone_number,opening_hours,price_level,review,website,photos,user_ratings_total,business_status,url,types,geometry",
            "key": self.api_key,
            "language": "zh-TW"  # 設置返回結果為繁體中文
        }
        
        response = requests.get(details_url, params=params)
        result = response.json()
        
        # 保留照片信息，但不再直接生成照片URL
        # 这个工作将交给Controller层或代理视图来处理
        
        # 如果成功获取信息，增加一些辅助字段
        if result.get("status") == "OK" and result.get("result"):
            try:
                # 提取并格式化一些字段，方便后续使用
                place_result = result["result"]
                
                # 1. 格式化营业状态
                if place_result.get("business_status") == "OPERATIONAL":
                    place_result["business_status_text"] = "營業中"
                elif place_result.get("business_status") == "CLOSED_TEMPORARILY":
                    place_result["business_status_text"] = "暫時休業"
                elif place_result.get("business_status") == "CLOSED_PERMANENTLY":
                    place_result["business_status_text"] = "永久停業"
                else:
                    place_result["business_status_text"] = "狀態未知"
                
                # 2. 格式化价格级别
                if place_result.get("price_level") is not None:
                    place_result["price_level_text"] = "$" * (place_result["price_level"] + 1)
                
                # 3. 提取餐厅类型
                if place_result.get("types"):
                    place_result["cuisine_type"] = ", ".join(place_result["types"][:3])
                
                print(f"成功获取餐厅详情: {place_result.get('name')}")
            except Exception as e:
                print(f"处理餐厅详情时出错: {str(e)}")
        
        return result
    
    def get_photo_url(self, photo_reference: str, max_width: int = 800) -> str:
        """
        獲取照片URL
        
        參數:
            photo_reference: 照片參考ID
            max_width: 照片最大寬度
            
        返回:
            照片URL
        """
        # 直接返回Google Places API的照片URL
        # 這個URL可以直接在<img>標籤中使用
        return f"{self.base_url}/photo?maxwidth={max_width}&photoreference={photo_reference}&key={self.api_key}"
    
    def get_photo_data(self, photo_reference: str, max_width: int = 800) -> Optional[bytes]:
        """
        直接獲取照片二進制數據
        
        參數:
            photo_reference: 照片參考ID
            max_width: 照片最大寬度
            
        返回:
            照片二進制數據，失敗時返回None
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 檢查API密鑰是否設置
                if not self.api_key or self.api_key == "":
                    print("错误：Google Places API密钥未设置")
                    return None
                    
                # 構建照片URL
                photo_url = self.get_photo_url(photo_reference, max_width)
                print(f"尝试获取照片: {photo_url[:70]}...（第{retry_count+1}次嘗試）")
                
                # 設定請求頭和參數
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
                }
                
                # 發送請求獲取照片
                response = requests.get(photo_url, headers=headers, timeout=15)
                
                # 檢查請求是否成功
                if response.status_code == 200:
                    content_length = len(response.content)
                    print(f"成功获取照片，大小: {content_length} 字节")
                    
                    # 檢查返回的內容是否為有效圖片（至少應該有幾KB）
                    if content_length > 1000:  # 至少1KB
                        return response.content
                    else:
                        print(f"警告：照片大小異常小（{content_length}字節），可能不是有效圖片")
                        retry_count += 1
                else:
                    print(f"獲取照片失敗，狀態碼: {response.status_code}, 响应: {response.text[:100]}")
                    retry_count += 1
                    
            except requests.exceptions.Timeout:
                print(f"获取照片超时")
                retry_count += 1
            except requests.exceptions.ConnectionError:
                print(f"获取照片连接错误")
                retry_count += 1
            except Exception as e:
                print(f"獲取照片數據時出錯: {str(e)}")
                retry_count += 1
            
            # 如果需要重試，等待一段時間
            if retry_count < max_retries and retry_count > 0:
                import time
                time.sleep(1)  # 重試間隔1秒
        
        print(f"獲取照片失敗，已重試{max_retries}次")
        return None 