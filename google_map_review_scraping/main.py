import sys
import logging
from utils import initialize_driver
from scraper import open_url, click_update_results_checkbox, fetch_store_links, fetch_intro_info, fetch_places_from_api, open_reviews, sort_reviews_by_latest, scroll_reviews
import time
import json
import os

sys.stdout.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def merge_store_data(new_stores, store_json="store_intros.json"):
    """
    合併新店家資訊到store_intros.json中，已存在的店家則跳過
    """
    if os.path.exists(store_json):
        with open(store_json, 'r', encoding='utf-8') as f:
            existing_stores = json.load(f)
    else:
        existing_stores = []
    
    # 建立現有店家編號集合，用於快速查詢
    existing_ids = {store.get("編號") for store in existing_stores}
    
    # 合併新店家，如果ID已存在則跳過
    added_count = 0
    for new_store in new_stores:
        if new_store.get("編號") not in existing_ids:
            existing_stores.append(new_store)
            added_count += 1
    
    # 儲存合併後的數據
    with open(store_json, 'w', encoding='utf-8') as f:
        json.dump(existing_stores, f, ensure_ascii=False, indent=2)
    
    logging.info(f"合併完成，新增了 {added_count} 個新店家")
    return existing_stores

def main():
    keywords = "燒烤店"  # 你可以根據需求修改
    town_json_path = "town.json"
    api_key = "your_key"
    store_json = "store_intros.json"
    
    # 第一步：呼叫 Google Place API 取得店家資訊
    with open(town_json_path, "r", encoding='utf-8') as f:
        towns = json.load(f)

    # 篩選基隆市的前七筆鄉鎮區
    target_towns = [t for t in towns if t["CountyName"] == "基隆市"][0:7]

    for town in target_towns:
        lat = town["latitude"]
        lng = town["longitude"]
        temp_output_json = f"temp_stores_{town['TownName']}.json"
        
        # 1. 先抓這一區的店家資訊
        fetch_places_from_api(
            town_json_path=None,
            keywords=keywords,
            api_key=api_key,
            radius=2000,
            output_json=temp_output_json,
            lat=lat,
            lng=lng
        )
        logging.info(f"完成抓取 {town['TownName']} 的店家資訊，存於 {temp_output_json}")
        # 2. 將新店家資訊合併到store_intros.json
        with open(temp_output_json, 'r', encoding='utf-8') as f:
            new_stores = json.load(f)
        
        # 合併店家資料，返回更新後的店家列表
        all_stores = merge_store_data(new_stores, store_json)
        
        # 刪除臨時文件
        os.remove(temp_output_json)
        
        # 3. 針對這一區的店家抓簡介與評論
        driver = initialize_driver()
        try:
            for store in all_stores:
                if store.get("是否已完成") == "已完成":
                    continue
                url = store.get("店家google map網址")
                store_name = store.get("店名")
                store_id = store.get("編號")
                if not url:
                    logging.warning(f"{store_name} 沒有 Google Map 網址，跳過")
                    continue
                driver.get(url)
                time.sleep(2)
                fetch_intro_info(driver, store_name, keywords, json_path=store_json)
                logging.info(f"完成抓取店家 {store_name} 的簡介。")
                time.sleep(1)
                
                # 抓取評論流程
                try:
                    open_reviews(driver)
                    sort_reviews_by_latest(driver)
                    scroll_reviews(driver, store_name, pause_time=3, batch_size=50, store_id=store_id)
                    logging.info(f"完成抓取店家 {store_name} 的評論。")
                except Exception as e:
                    logging.error(f"抓取評論時出錯：{e}")
                time.sleep(1)
                
        except Exception as e:
            logging.error(f"錯誤：{e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    main() 