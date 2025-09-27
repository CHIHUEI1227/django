import logging
import time
import random
import csv
import os
import requests
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import re
from utils import sanitize_filename, get_next_id, format_intro_content

def open_url(driver, url):
    """打開指定的 URL"""
    try:
        driver.get(url)
    except TimeoutException:
        logging.error("打開URL時超時，請檢查網絡連接或URL是否正確。")

def scroll_reviews(driver, store_name, pause_time=3, max_no_change_attempts=2, batch_size=50, max_scrolls=10000, store_id=None):
    """
    持續滾動評論區直到沒有新評論，並以 all_reviews.json 為依據計算數量
    """
    try:
        if store_id is None:
            logging.warning("未提供店家編號，無法追蹤評論數量")
            return

        review_count = 0
        review_with_text_count = 0
        all_reviews_file = "all_reviews.json"
        if os.path.exists(all_reviews_file):
            with open(all_reviews_file, 'r', encoding='utf-8') as f:
                all_reviews = json.load(f)
            for row in all_reviews:
                # 兼容字典格式和列表格式
                if isinstance(row, dict):
                    if str(row.get('店家編號')) == str(store_id):
                        review_count += 1
                        if row.get('評論內容') and row.get('評論內容') != "無評論":
                            review_with_text_count += 1
                elif isinstance(row, list) and len(row) > 0:
                    if row[0] == str(store_id):
                        review_count += 1
                        if len(row) > 4 and row[4] and row[4] != "無評論":
                            review_with_text_count += 1

        if review_with_text_count >= 50:
            logging.info(f"店家 {store_name}（編號：{store_id}）已達到50則有效評論上限，跳過抓取")
            update_completion_status(store_id, "已完成", f"已達到50則有效評論上限")
            return
        if review_count >= 70:
            logging.info(f"店家 {store_name}（編號：{store_id}）已達到70則評論上限，跳過抓取")
            update_completion_status(store_id, "已完成", f"已達到70則評論上限")
            return

        scrollable_div = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde'))
        )
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        scroll_count = 0
        no_change_attempts = 0
        processed_reviews = set()
        while no_change_attempts < max_no_change_attempts and scroll_count < max_scrolls:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            scroll_count += 1
            time.sleep(random.uniform(0.2, 0.3))
            reviews = driver.find_elements(By.CLASS_NAME, 'jftiEf')
            logging.info(f"第 {scroll_count} 次滾動，已加載 {len(reviews)} 條評論。")
            new_reviews = [review for review in reviews if review not in processed_reviews]
            if new_reviews:
                remaining_reviews = min(50 - review_with_text_count, 70 - review_count)
                if remaining_reviews <= 0:
                    logging.info(f"店家 {store_name}（編號：{store_id}）已達到評論上限")
                    if review_with_text_count >= 50:
                        update_completion_status(store_id, "已完成", f"已達到50則有效評論上限")
                    else:
                        update_completion_status(store_id, "已完成", f"已達到70則評論上限")
                    break
                reviews_to_process = min(len(new_reviews[:batch_size]), max(50, remaining_reviews * 2))
                new_text_reviews = fetch_reviews(driver, store_name, new_reviews[:reviews_to_process], store_id)
                processed_reviews.update(new_reviews[:reviews_to_process])
                review_with_text_count += new_text_reviews
                if review_with_text_count >= 50:
                    logging.info(f"店家 {store_name}（編號：{store_id}）已達到50則有效評論上限")
                    update_completion_status(store_id, "已完成", f"已達到50則有效評論上限")
                    break
            if new_height == last_height:
                no_change_attempts += 1
                logging.info(f"沒有更多新評論，連續未增加評論次數：{no_change_attempts}")
                time.sleep(pause_time)
            else:
                no_change_attempts = 0
                last_height = new_height
            if no_change_attempts >= max_no_change_attempts:
                logging.info("連續多次未增加評論，停止滾動。")
                update_completion_status(store_id, "已完成", "已抓取所有可用評論")
                break
    except Exception as e:
        logging.error(f"滾動評論區時出錯：{e}")
        logging.error("詳細錯誤信息：", exc_info=True)

def sort_reviews_by_latest(driver):
    """點擊排序按鈕並選擇最新排序"""
    try:
        sort_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="排序評論"]'))
        )
        sort_button.click()
        time.sleep(0.5)
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.fxNQSd[data-index="1"]'))
        ).click()
        time.sleep(1)
        logging.info("已選擇最新排序。")
    except Exception as e:
        logging.error(f"選擇最新排序時錯：{e}")

def fetch_store_links(driver, keyword, latitude, longitude, zoom_level, max_scrolls=10, pause_time=3):
    """使用關鍵字滾動獲取所有店家的鏈接，並儲存店家資訊"""
    store_links = set()  # 使用集合避免重複
    try:
        driver.get(f'https://www.google.com/maps/search/{keyword}/@{latitude},{longitude},{zoom_level}z')
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception:
            pass

        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        driver.execute_script("""
            var scrollableDiv = arguments[0];
            function scrollWithinElement(scrollableDiv) {
                return new Promise((resolve, reject) => {
                    var totalHeight = 0;
                    var distance = 1000;
                    var scrollDelay = 10000;
                    
                    var timer = setInterval(() => {
                        var scrollHeightBefore = scrollableDiv.scrollHeight;
                        var elementsBefore = scrollableDiv.querySelectorAll('div[jsaction]').length;
                        scrollableDiv.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeightBefore) {
                            totalHeight = 0;
                            setTimeout(() => {
                                var scrollHeightAfter = scrollableDiv.scrollHeight;
                                var elementsAfter = scrollableDiv.querySelectorAll('div[jsaction]').length;
                                if (scrollHeightAfter > scrollHeightBefore || elementsAfter > elementsBefore) {
                                    return;
                                } else {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, scrollDelay);
                        }
                    }, 200);
                });
            }
            return scrollWithinElement(scrollableDiv);
        """, scrollable_div)

        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
        logging.info(f"找到 {len(items)} 個店家。")

        for item in items:
            try:
                # 等待元素可點擊，最多等待2秒
                WebDriverWait(item, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a'))
                )
                # 嘗試更精確的選擇器
                link_element = item.find_element(By.CSS_SELECTOR, 'a[href*="maps/place"]')
                if not link_element:
                    link_element = item.find_element(By.CSS_SELECTOR, 'a')
                
                link = link_element.get_attribute('href')
                if link:
                    store_links.add(link)
                    logging.info(f"成功獲取店家連結: {link[:60]}...")
                else:
                    logging.warning("找到連結元素但無法獲取href屬性")
                
                # # 獲取店名與評價
                # store_name = item.find_element(By.CSS_SELECTOR, 'div.qBF1Pd').text
                # try:
                #     rating = item.find_element(By.CSS_SELECTOR, 'span.MW4etd').text
                # except NoSuchElementException:
                #     rating = "無星數"
                    
                # save_store_info(store_name, rating, latitude, longitude,keyword)  # 存入 CSV
            except TimeoutException:
                logging.warning(f"等待連結元素超時，可能不是有效店家項目")
            except NoSuchElementException as e:
                logging.warning(f"找不到連結元素: {str(e).split('Stacktrace')[0]}")
            except Exception as e:
                logging.error(f"獲取店家鏈接時出錯：{str(e).split('Stacktrace')[0]}")

    except Exception as e:
        logging.error(f"獲取店家鏈接時出錯：{e}")
    return list(store_links)

def open_reviews(driver):
    """點擊評論按鈕"""
    try:
        reviews_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "評論")]'))
        )
        reviews_button.click()
        time.sleep(1)
    except Exception as e:
        logging.error(f"點擊評論按鈕時出錯：{e}")

def fetch_reviews(driver, store_name, reviews, store_id=None):
    """
    抓取評論並保存到 all_reviews.json，使用字典結構
    """
    try:
        all_reviews_file = "all_reviews.json"
        new_text_reviews_count = 0  # 追蹤新增的有效評論數量

        # 讀取已存在的評論
        if os.path.exists(all_reviews_file):
            with open(all_reviews_file, 'r', encoding='utf-8') as f:
                all_reviews = json.load(f)
        else:
            all_reviews = []

        # 建立檢查重複的集合
        existing_reviews = set()
        for review in all_reviews:
            # 兼容舊格式的評論數據
            if isinstance(review, list) and len(review) >= 4:
                existing_reviews.add((str(review[0]), review[1], review[3]))  # (店家編號, 用戶, 日期)
            elif isinstance(review, dict):
                existing_reviews.add((str(review.get('店家編號')), review.get('用戶名稱'), review.get('評論日期')))


        logging.info(f"共找到 {len(reviews)} 條評論：\n")

        for review in reviews:
            try:
                # 先檢查評論是否有全文按鈕
                try:
                    try:
                        review_content = review.find_element(By.CLASS_NAME, 'MyEned')
                    except NoSuchElementException:
                        review_content = review.find_element(By.CLASS_NAME, 'jJc9Ad')
                    full_text_button = review_content.find_element(By.CSS_SELECTOR, 'button.w8nwRe.kyuRq[aria-label="顯示更多"]')
                    if full_text_button and full_text_button.is_displayed():
                        logging.info("找到全文按鈕，點擊展開...")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", full_text_button)
                        full_text_button.click()
                        time.sleep(0.1)
                        retry_count = 0
                        max_retries = 5
                        while retry_count < max_retries:
                            time.sleep(0.1)
                            try:
                                retry_button = review_content.find_element(By.CSS_SELECTOR, 'button.w8nwRe.kyuRq[aria-label="顯示更多"]')
                                if retry_button.is_displayed():
                                    logging.info(f"檢測到全文按鈕仍然存在，第 {retry_count + 1} 次嘗試點擊...")
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", retry_button)
                                    time.sleep(0.1)
                                    retry_button.click()
                                    time.sleep(0.1)
                                    retry_count += 1
                                else:
                                    break
                            except NoSuchElementException:
                                break
                        if retry_count >= max_retries:
                            logging.info("已達到最大重試次數，停止嘗試點擊全文按鈕")
                except NoSuchElementException:
                    logging.info("未找到全文按鈕或評論內容區域")
                except Exception as e:
                    logging.info(f"處理全文按鈕時出錯: {str(e).split('Stacktrace')[0]}")

                user_name = review.find_element(By.CLASS_NAME, 'd4r55').text
                rating_text = review.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute("aria-label")
                rating = ''.join(filter(str.isdigit, rating_text))
                review_date = review.find_element(By.CLASS_NAME, 'rsqaWe').text

                user_profile_url = "無評論記錄網址"
                try:
                    user_profile_button = review.find_element(By.CSS_SELECTOR, 'button.al6Kxe')
                    if user_profile_button:
                        user_profile_url = user_profile_button.get_attribute('data-href')
                        logging.info(f"找到用戶評論記錄網址：{user_profile_url}")
                except NoSuchElementException:
                    logging.info("未找到用戶評論記錄網址")
                except Exception as e:
                    logging.error(f"獲取用戶評論記錄網址時出錯：{e}")

                is_duplicate = (str(store_id), user_name, review_date) in existing_reviews

                if not is_duplicate:
                    try:
                        review_text = "無評論"
                        structured_review_text = "無類別及評分"
                        try:
                            review_text_element = review.find_element(By.CSS_SELECTOR, 'span.wiI7pd')
                            if review_text_element:
                                review_text = review_text_element.text.replace('\n', ' ').strip()
                                logging.info(f"{user_name} 評論文字：{review_text}")
                        except NoSuchElementException:
                            logging.info("未找到文字評論")
                            review_text = "無評論"
                        try:
                            structured_review = review.find_element(By.CSS_SELECTOR, 'div[jslog="127691"]')
                            if structured_review:
                                structured_review_text = structured_review.text.replace('\n', ' ').strip()
                                logging.info(f"{user_name} 類別及評分：{structured_review_text}")
                        except NoSuchElementException:
                            logging.info("未找到類別及評分")
                            structured_review_text = "無類別及評分"
                    except Exception as e:
                        logging.error(f"處理評論文本時出錯：{e}")
                        review_text = "無評論"
                        structured_review_text = "無類別及評分"

                    # 創建評論字典
                    review_dict = {
                        '店家編號': store_id,
                        '用戶名稱': user_name,
                        '評分': rating,
                        '評論日期': review_date,
                        '評論內容': review_text,
                        '類別及評分': structured_review_text,
                        # '抓取日期': current_date,  # 已移除
                        '用戶評論記錄網址': user_profile_url
                    }
                    
                    # 寫入 all_reviews.json
                    all_reviews.append(review_dict)
                    existing_reviews.add((str(store_id), user_name, review_date))
                    if review_text != "無評論":
                        new_text_reviews_count += 1
                    logging.info(f"抓取評論: 用戶: {user_name}, 評分: {rating}, 日期: {review_date}, 評論: {review_text}")
                    logging.info('-' * 30)
                else:
                    logging.info(f"評論已存在（店家編號 {store_id}、用戶 {user_name}、日期 {review_date} 都相同），跳過")
            except Exception as e:
                logging.error(f"無法解析評論的部分內容：{e}")

        # 回寫 all_reviews.json
        with open(all_reviews_file, 'w', encoding='utf-8') as f:
            json.dump(all_reviews, f, ensure_ascii=False, indent=2)
        logging.info(f"本次新增 {len(reviews)} 條評論，其中有含文字的評論 {new_text_reviews_count} 條。")
        return new_text_reviews_count  # 返回新增的有效評論數量
    except Exception as e:
        logging.error(f"抓取評論時出錯：{e}")
        return 0

def fetch_intro_info(driver, store_name, keyword, json_path="store_intros.json"):
    """抓取店家簡介信息，並存成 json 檔案"""
    try:
        store_brief = "無簡述"
        intro_text = []
        address = "無地址"
        coordinates = "無經緯度"
        business_hours = []  # 營業時間改為列表
        website = "無官方網站"
        rating = "無星數"
        price_level = "無價位資訊"
        image_filename = ""
        is_completed = "未完成"  # 預設為未完成
        store_types = ""  # 新增店家類型欄位
        
        # API抓取的特殊欄位，預設為空
        google_map_url = ""
        business_status = ""

        # 先獲取店家編號
        next_id = get_next_id(json_path, keyword)

        # 讀取現有 json
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                stores = json.load(f)
        else:
            stores = []

        # 檢查是否已存在
        found_duplicate = False
        store_id_to_use = next_id
        is_already_completed = False
        missing_fields = {}
        
        for store in stores:
            if store.get('店名') == store_name:
                store_id_to_use = store.get('編號', next_id)
                if store.get('是否已完成') == "已完成":
                    # 檢查已完成的店家是否缺少新增的欄位
                    missing_new_fields = False
                    
                    # 檢查店家類型欄位
                    if 'store_types' not in locals():
                        store_types = ""
                        
                    if 'shop_types' not in locals():
                        shop_types = ""
                        
                    if '店家類型' not in store or not store.get('店家類型'):
                        missing_new_fields = True
                        store_types = store.get('店家類型', "")
                        logging.info(f"店家 {store_name} 已完成但缺少店家類型欄位，將補充該欄位")
                    
                    # 如果只缺少新增欄位，則僅補充這些欄位而不重新抓取評論
                    if missing_new_fields:
                        store_data = store.copy()
                        
                        # 補充店家類型欄位
                        if '店家類型' not in store_data or not store_data.get('店家類型'):
                            store_data['店家類型'] = store_types
                        
                        # 更新store_intros.json
                        for i, s in enumerate(stores):
                            if s.get('店名') == store_name:
                                stores[i] = store_data
                                break
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(stores, f, ensure_ascii=False, indent=2)
                        
                        logging.info(f"已補充店家 {store_name} 缺少的欄位")
                        return
                    
                    logging.info(f"店家 {store_name}（編號：{store_id_to_use}）已完成評論抓取且欄位完整，跳過。")
                    return
                
                # 檢查必要欄位是否缺失
                if store.get('地址', "無地址") == "無地址" or not store.get('地址'):
                    missing_fields['地址'] = True
                    logging.info(f"店家 {store_name} 缺少地址資料，將重新抓取")
                    
                if store.get('經緯度', "無經緯度") == "無經緯度" or not store.get('經緯度'):
                    missing_fields['經緯度'] = True
                    logging.info(f"店家 {store_name} 缺少經緯度資料，將重新抓取")
                    
                if not store.get('營業時間') or (isinstance(store.get('營業時間'), list) and len(store.get('營業時間')) == 0):
                    missing_fields['營業時間'] = True
                    logging.info(f"店家 {store_name} 缺少營業時間資料，將重新抓取")
                    
                if store.get('官方網站', "無官方網站") == "無官方網站" or not store.get('官方網站'):
                    missing_fields['官方網站'] = True
                    logging.info(f"店家 {store_name} 缺少官方網站資料，將重新抓取")
                    
                if store.get('星數', "無星數") == "無星數" or not store.get('星數'):
                    missing_fields['星數'] = True
                    logging.info(f"店家 {store_name} 缺少星數資料，將重新抓取")
                    
                if store.get('價位', "無價位資訊") == "無價位資訊" or not store.get('價位'):
                    missing_fields['價位'] = True
                    logging.info(f"店家 {store_name} 缺少價位資料，將重新抓取")
                    
                if not store.get('圖片檔案名稱'):
                    missing_fields['圖片'] = True
                    logging.info(f"店家 {store_name} 缺少圖片資料，將重新抓取")
                
                found_duplicate = True
                # 若找到了對應店家且有缺失欄位，先將現有資料取出
                address = store.get('地址', "無地址")
                coordinates = store.get('經緯度', "無經緯度")
                # 統一將營業時間轉為列表格式
                if isinstance(store.get('營業時間'), list):
                    business_hours = store.get('營業時間', [])
                elif store.get('營業時間') and store.get('營業時間') != "無營業時間":
                    # 如果是字符串且不為空，則按換行符分割成列表
                    business_hours = store.get('營業時間').split('\n')
                
                website = store.get('官方網站', "無官方網站")
                rating = store.get('星數', "無星數")
                price_level = store.get('價位', "無價位資訊")
                store_brief = store.get('店家簡述', "無簡述")
                image_filename = store.get('圖片檔案名稱', "")
                
                # 保留API抓取的特殊欄位
                google_map_url = store.get('店家google map網址', "")
                business_status = store.get('營業狀態', "")
                
                # 保留店家類型字段（如果存在）
                store_types = store.get('店家類型', "")
                
                # 如果原本的簡述是由API抓取產生的類型列表，且我們現在要抓取真正的簡述，則設為空
                if "," in store_brief and any(keyword in store_brief for keyword in ["餐廳", "咖啡", "美食", "小吃"]):
                    store_brief = "無簡述"
                    logging.info(f"檢測到店家 {store_name} 的簡述可能只是類型列表，將重新抓取")
                
                break

        # 圖片
        if not image_filename or '圖片' in missing_fields:
            img_dir = "img"
            if not os.path.exists(img_dir):
                os.makedirs(img_dir)
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, 'img[src*="googleusercontent.com"]')
                if img_element:
                    img_url = img_element.get_attribute('src')
                    if img_url:
                        image_filename = f"{store_id_to_use}.jpg"
                        img_path = os.path.join(img_dir, image_filename)
                        try:
                            response = requests.get(img_url)
                            if response.status_code == 200:
                                with open(img_path, 'wb') as f:
                                    f.write(response.content)
                                logging.info(f"已保存店家圖片：{image_filename}")
                            else:
                                logging.error(f"下載圖片失敗，狀態碼：{response.status_code}")
                                image_filename = ""
                        except Exception as e:
                            logging.error(f"下載圖片時出錯：{e}")
                            image_filename = ""
            except NoSuchElementException:
                logging.info("未找到店家圖片")

        # 星數
        if rating == "無星數" or '星數' in missing_fields:
            try:
                rating_element = driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]')
                if rating_element:
                    rating = rating_element.text
                    logging.info(f"找到店家星數：{rating}")
            except NoSuchElementException:
                logging.info("未找到店家星數")

        # 抓取分類標籤
        category_keywords = set()
        try:
            category_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.DkEaL')
            for button in category_buttons:
                category_text = button.text.strip()
                if category_text:
                    category_keywords.add(category_text)
                    logging.info(f"找到分類標籤：{category_text}")
        except NoSuchElementException:
            logging.info("未找到分類標籤")
        except Exception as e:
            logging.error(f"抓取分類標籤時出錯：{e}")

        # 價位
        if price_level == "無價位資訊" or '價位' in missing_fields:
            try:
                price_element = driver.find_element(By.CSS_SELECTOR, 'span.mgr77e span[aria-label^="價格"]')
                if price_element:
                    price_level = price_element.get_attribute('aria-label').replace('價格: ', '')
                    logging.info(f"找到店家價位：{price_level}")
            except NoSuchElementException:
                logging.info("未找到店家價位")

        # 地址
        if address == "無地址" or '地址' in missing_fields:
            try:
                address_element = driver.find_element(By.CSS_SELECTOR, 'div.Io6YTe.fontBodyMedium')
                if address_element:
                    address = address_element.text
                    logging.info(f"找到店家地址：{address}")
            except NoSuchElementException:
                logging.info("未找到店家地址")

        # 如果沒有Google Map網址但目前有URL，則抓取當前URL
        if not google_map_url:
            current_url = driver.current_url
            if current_url and "google.com/maps" in current_url:
                google_map_url = current_url
                logging.info(f"沒有Google Map網址，使用當前URL作為Google Map網址：{google_map_url}")
            else:
                google_map_url = ""
                logging.warning(f"無法獲取有效的Google Map網址，當前URL不是Google Maps頁面：{current_url}")
        else:
            logging.info(f"已有Google Map網址：{google_map_url}")
            # 經緯度只使用 API 抓取，不再從 URL 解析

        time.sleep(random.uniform(1.5, 2.5))
        
        # 營業時間
        if (len(business_hours) == 0) or '營業時間' in missing_fields:
            try:
                hours_element = driver.find_element(By.CSS_SELECTOR, 'div[aria-label*="星期"]')
                if hours_element:
                    hours_text = hours_element.get_attribute('aria-label')
                    hours_text = hours_text.split('. ')[0]
                    logging.info(f"找到營業時間：{hours_text}")
                    
                    # 將營業時間文本按星期拆分為列表
                    days_of_week = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
                    parsed_hours = []
                    
                    # 處理完整的營業時間文本
                    if hours_text:
                        current_text = hours_text
                        for day in days_of_week:
                            day_index = current_text.find(day)
                            if day_index != -1:
                                # 找到下一個天的位置或文本結束
                                next_day_index = -1
                                for next_day in days_of_week:
                                    next_index = current_text.find(next_day, day_index + len(day))
                                    if next_index != -1 and (next_day_index == -1 or next_index < next_day_index):
                                        next_day_index = next_index
                                
                                if next_day_index == -1:
                                    day_text = current_text[day_index:].strip()
                                else:
                                    day_text = current_text[day_index:next_day_index].strip()
                                
                                parsed_hours.append(day_text)
                    
                    # 如果成功解析出日期，則使用解析結果
                    if parsed_hours:
                        business_hours = parsed_hours
                    # 否則保持為一個包含整個文本的列表
                    elif hours_text:
                        business_hours = [hours_text]
            except NoSuchElementException:
                logging.info("未找到營業時間")
        
        # 官方網站
        if website == "無官方網站" or '官方網站' in missing_fields:
            try:
                website_element = driver.find_element(By.CSS_SELECTOR, 'a.CsEnBe[data-item-id="authority"]')
                if website_element:
                    website = website_element.get_attribute('href')
                    logging.info(f"找到官方網站：{website}")
            except NoSuchElementException:
                logging.info("未找到官方網站")
        
        try:
            intro_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "簡介")]'))
            )
            intro_button.click()
            time.sleep(1)
        except (NoSuchElementException, TimeoutException):
            logging.info(f"{store_name} 找不到簡介按鈕，跳過...")
            # 直接寫入 json
            store_data = {
                "編號": store_id_to_use,
                "店名": store_name,
                "地址": address,
                "經緯度": coordinates,
                "營業時間": business_hours,  # 以列表形式存儲營業時間
                "官方網站": website,
                "店家簡述": "無簡述",
                "簡介": "無詳細簡介",
                "關鍵字": keyword,
                "星數": rating,
                "價位": price_level,
                "圖片檔案名稱": image_filename,
                "是否已完成": is_completed
            }
            
            # 加入API抓取的特殊欄位，如果有的話
            if google_map_url:
                store_data["店家google map網址"] = google_map_url
            if business_status:
                store_data["營業狀態"] = business_status
            # 加入店家類型字段（如果存在）
            if store_types:
                store_data["店家類型"] = store_types
            
            if found_duplicate:
                for i, store in enumerate(stores):
                    if store.get('店名') == store_name:
                        stores[i] = store_data
                        break
            else:
                stores.append(store_data)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(stores, f, ensure_ascii=False, indent=2)
            return
        try:
            hlvsq_element = driver.find_element(By.CSS_SELECTOR, 'div.PbZDve span.HlvSq')
            if hlvsq_element:
                store_brief = hlvsq_element.text
                logging.info(f"找到店家簡短描述：{store_brief}")
        except NoSuchElementException:
            logging.info("未找到店家簡短描述，將繼續抓取其他簡介內容")
        try:
            scrollable_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde'))
            )
            scroll_intro_section(driver, scrollable_div)
            intro_blocks = driver.find_elements(By.CLASS_NAME, 'iP2t7d')
            for block in intro_blocks:
                try:
                    content = block.text.strip()
                    if content:
                        intro_text.append(content)
                except Exception as e:
                    logging.error(f"處理簡介塊時出錯：{e}")
        except TimeoutException:
            logging.info(f"{store_name} 沒有找到簡介內容")
        logging.info(f"簡介內容：{intro_text}")
        formatted_intro = format_intro_content(intro_text) if intro_text else "無詳細簡介"
        # 合併關鍵字
        all_keywords = set([keyword])
        all_keywords.update(category_keywords)
        keywords_str = ','.join(sorted(all_keywords))
        store_data = {
            "編號": store_id_to_use,
            "店名": store_name,
            "地址": address,
            "經緯度": coordinates,
            "營業時間": business_hours,  # 以列表形式存儲營業時間
            "官方網站": website,
            "店家簡述": store_brief,
            "簡介": formatted_intro,
            "關鍵字": keywords_str,
            "星數": rating,
            "價位": price_level,
            "圖片檔案名稱": image_filename,
            "是否已完成": is_completed
        }
        
        # 加入API抓取的特殊欄位，如果有的話
        if google_map_url:
            store_data["店家google map網址"] = google_map_url
        if business_status:
            store_data["營業狀態"] = business_status
        # 加入店家類型字段（如果存在）
        if store_types:
            store_data["店家類型"] = store_types
        
        if found_duplicate:
            for i, store in enumerate(stores):
                if store.get('店名') == store_name:
                    stores[i] = store_data
                    break
        else:
            stores.append(store_data)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(stores, f, ensure_ascii=False, indent=2)
        time.sleep(1)
    except Exception as e:
        logging.error(f"抓取 {store_name} 信息時出錯：{e}", exc_info=True)

def scroll_intro_section(driver, scrollable_div, max_scrolls=10, max_no_change_attempts=1, pause_time=1):
    """滾動簡介區塊"""
    try:
        last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
        scroll_count = 0
        no_change_attempts = 0

        while no_change_attempts < max_no_change_attempts and scroll_count < max_scrolls:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(random.uniform(0.4, 0.6))
            
            new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
            scroll_count += 1

            logging.info(f"第 {scroll_count} 次滾动，當前高度 {new_height}")

            if new_height == last_height:
                no_change_attempts += 1
                logging.info(f"未加載新內容，連續未變化次數：{no_change_attempts}")
                time.sleep(pause_time)
            else:
                no_change_attempts = 0
                last_height = new_height

            if no_change_attempts >= max_no_change_attempts:
                logging.info("簡介內容已完全加載，停止滾动。")
                break

    except Exception as e:
        logging.error(f"滾動簡介區塊時出錯：{e}", exc_info=True)

def click_update_results_checkbox(driver):
    """點擊 '地圖移動時更新結果' 復選框"""
    try:
        checkbox_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@role="checkbox"]'))
        )
        
        driver.execute_script("arguments[0].scrollIntoView(true);", checkbox_button)
        checkbox_button.click()
        logging.info("已點擊 '地圖移動時更新結果' 復選框。")
    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"點擊 '地圖移動時更新結果' 復選框時出錯：{e}") 

def update_completion_status(store_id, status, reason=""):
    """
    更新店家的完成狀態，直接操作 store_intros.json
    """
    csv_file = "store_intros.json"
    if not os.path.exists(csv_file):
        logging.error(f"找不到檔案 {csv_file}，無法更新完成狀態")
        return
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            stores = json.load(f)
        updated = False
        for store in stores:
            if store.get("編號") == str(store_id):
                store["是否已完成"] = status
                updated = True
                logging.info(f"更新店家（編號：{store_id}）狀態為 {status}：{reason}")
                break
        if updated:
            with open(csv_file, 'w', encoding='utf-8') as f:
                json.dump(stores, f, ensure_ascii=False, indent=2)
        else:
            logging.warning(f"找不到對應店家（編號: {store_id}），無法更新狀態。")
    except Exception as e:
        logging.error(f"更新完成狀態時出錯：{e}", exc_info=True) 

def fetch_places_from_api(town_json_path=None, keywords="", api_key="", radius=2000, output_json="store_intros.json", lat=None, lng=None):
    """
    根據 town.json 內容或直接給定經緯度與 keywords，呼叫 Google Place API 取得店家資訊，並存入 store_intros.json。
    """
    import json
    import requests
    import logging
    import os

    # 先檢查現有的店家資料，用於後續比對和補充資料
    existing_stores = {}
    if os.path.exists(output_json):
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # 建立店家ID到店家資料的映射
                for store in existing_data:
                    if "編號" in store and store["編號"]:
                        existing_stores[store["編號"]] = store
        except Exception as e:
            logging.error(f"讀取現有店家資料時出錯: {e}")
    
    all_places = []
    place_ids = set()

    # 如果有 lat/lng，直接查詢
    if lat is not None and lng is not None:
        locations = [(lat, lng)]
    else:
        # 否則讀取 town_json_path
        if not town_json_path or not os.path.exists(town_json_path):
            logging.error(f"找不到 {town_json_path}")
            return
        with open(town_json_path, 'r', encoding='utf-8') as f:
            towns = json.load(f)
            if isinstance(towns, dict):
                towns = [towns]
            locations = [(t['latitude'], t['longitude']) for t in towns]

    for lat, lng in locations:
        location = f"{lat},{lng}"
        url = (
            f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
            f"location={location}&radius={radius}&keyword={keywords}&language=zh-TW&key={api_key}"
        )
        try:
            resp = requests.get(url)
            data = resp.json()
            if data.get('status') != 'OK':
                logging.warning(f"API 回傳非 OK: {data.get('status')}, {data.get('error_message', '')}")
                continue
            for result in data.get('results', []):
                # 從 result 對象中取得 place_id 並檢查是否已存在
                place_id = result.get('place_id')
                if place_id in place_ids:
                    continue
                place_ids.add(place_id)
                
                # 檢查是否已存在於現有店家資料中
                existing_store = existing_stores.get(place_id)
                
                # 先從搜尋結果嘗試獲取 url
                initial_url = result.get('url', '')
                if not initial_url:
                    initial_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                    logging.info(f"搜尋結果未包含 url，使用 place_id 生成臨時 URL: {initial_url}")
                else:
                    logging.info(f"從搜尋結果獲取 URL: {initial_url}")
                
                # 取得詳細資料，移除了 menu 欄位
                detail_url = (
                    f"https://maps.googleapis.com/maps/api/place/details/json?"
                    f"place_id={place_id}&language=zh-TW&fields="
                    f"place_id,name,formatted_address,geometry,opening_hours,website,types,business_status,rating,price_level,url&key={api_key}"
                )
                detail_resp = requests.get(detail_url)
                detail = detail_resp.json().get('result', {})
                
                # 從詳細資料獲取 url，如果沒有就使用之前的 initial_url
                final_url = detail.get('url', '')
                if not final_url:
                    final_url = initial_url
                    logging.warning(f"詳細資料中沒有 URL，使用之前的 URL: {final_url}")
                else:
                    logging.info(f"從詳細資料獲取 URL: {final_url}")
                
                # 確保最終的 URL 不為空
                if not final_url:
                    final_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                    logging.warning(f"未能獲取 URL，生成臨時 URL: {final_url}")
                
                # 獲取營業時間，以列表方式存儲
                business_hours = []
                if detail.get('opening_hours') and detail.get('opening_hours').get('weekday_text'):
                    business_hours = detail.get('opening_hours').get('weekday_text')
                
                # 處理店家網站，確保有默認值
                website = detail.get('website', '')
                if website == '':
                    website = "無官方網站"
                    logging.info(f"店家 {detail.get('name', '')} 無官方網站")
                
                # 處理店家類型，確保有默認值
                types = detail.get('types', [])
                types_str = ','.join(types) if types else ""
                
                # 處理評分，確保有默認值
                rating = detail.get('rating', '')
                if rating == '':
                    rating = "無星數"
                
                # 處理價位，確保有默認值
                price_level = detail.get('price_level', '')
                if price_level == '':
                    price_level = "無價位資訊"
                
                # 處理地址，確保有默認值
                address = detail.get('formatted_address', '')
                if not address:
                    address = "無地址"
                
                # 處理經緯度，確保有默認值
                lat_val = detail.get('geometry', {}).get('location', {}).get('lat', '')
                lng_val = detail.get('geometry', {}).get('location', {}).get('lng', '')
                coordinates = f"{lat_val},{lng_val}" if lat_val and lng_val else "無經緯度"
                
                # 組合欄位，移除了菜單相關欄位和照片相關欄位
                place_info = {
                    "編號": place_id,
                    "店名": detail.get('name', ''),
                    "地址": address,
                    "經緯度": coordinates,
                    "營業時間": business_hours,  # 以列表存儲營業時間
                    "官方網站": website,
                    "店家類型": types_str,
                    "星數": rating,
                    "價位": price_level,
                    "營業狀態": detail.get('business_status', ''),
                    "店家google map網址": final_url,
                    "搜尋關鍵字": keywords,
                    "簡介": "無",
                    "店家簡述": "無簡述",
                    "是否已完成": "未完成"
                }
                
                # 如果店家已存在，則只更新空值欄位
                if existing_store:
                    updated_store = existing_store.copy()
                    # 檢查每個欄位，如果原本是空值或空字串，則使用新抓取的資料
                    for field, value in place_info.items():
                        # 特殊處理官方網站欄位：只有當現有值是空字串且新值不是"無官方網站"時更新
                        if field == "官方網站":
                            # 如果API返回空字串，則意味著確實沒有官方網站
                            if value == "無官方網站" and updated_store.get(field, "") != "":
                                # 如果API確認沒有官方網站，但現有值不是空，則更新為"無官方網站"
                                updated_store[field] = value
                                logging.info(f"更新店家 {updated_store.get('店名', '')} 的 {field} 欄位: API確認店家無官方網站")
                            elif value != "無官方網站" and updated_store.get(field, "") in ["", "無官方網站"]:
                                # 只有當API抓到了有效的官方網站，而現有值是空或"無官方網站"時更新
                                updated_store[field] = value
                                logging.info(f"更新店家 {updated_store.get('店名', '')} 的 {field} 欄位: 找到有效官方網站")
                        # 對其他欄位的處理
                        elif field not in updated_store or updated_store[field] == "":
                            updated_store[field] = value
                            logging.info(f"更新店家 {updated_store.get('店名', '')} 的 {field} 欄位")
                    all_places.append(updated_store)
                else:
                    all_places.append(place_info)
        except Exception as e:
            logging.error(f"呼叫 Google Place API 發生錯誤: {e}")
    
    # 合併現有店家資料（未被更新的）
    for store_id, store in existing_stores.items():
        if store_id not in place_ids:
            all_places.append(store)
    
    # 寫入 json
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)
    logging.info(f"已將 {len(all_places)} 筆店家資訊寫入 {output_json}")