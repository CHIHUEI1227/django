# restaurants/crawlers/main.py
import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict

# 讀 .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 日誌 & stdout
sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 相對匯入
from .utils import initialize_driver
from .scraper import (
    fetch_intro_info,
    fetch_places_from_api,
    open_reviews,
    sort_reviews_by_latest,
    scroll_reviews,
)
from .paths import DATA_DIR, STORES_JSON, REVIEWS_JSON  # ★ 路徑統一由 paths.py 管

from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

# 參數（支援 .env／環境變數）
GOOGLE_API_KEY = (
    os.getenv("GOOGLE_PLACES_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or ""
)
KEYWORDS      = os.getenv("KEYWORDS", "燒烤店")
COUNTY        = os.getenv("COUNTY", "臺北市")    # 注意「臺」不是「台」
TOWN_LIMIT    = int(os.getenv("TOWN_LIMIT", "7"))
RADIUS        = int(os.getenv("RADIUS", "2000"))
HEADLESS      = os.getenv("HEADLESS", "1") != "0"

# 指定/排除「鄉鎮區」
TOWNS = [s.strip() for s in os.getenv("TOWNS", "").split(",") if s.strip()]
EXCLUDE_TOWNS = [s.strip() for s in os.getenv("EXCLUDE_TOWNS", "").split(",") if s.strip()]

# towns.json 搜尋位置
TOWNS_JSON_CANDIDATES = [
    DATA_DIR / "town.json",            # 優先使用 restaurants/current/town.json
    Path.cwd() / "town.json",          # 其次：專案根目錄
]

# ---------- 小工具 ----------
def _safe_load_json(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _safe_write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # 原子替換

def merge_store_data(new_stores: List[Dict], store_json: Path = STORES_JSON) -> List[Dict]:
    """合併新店家到 store_intros.json（以「編號」去重）。"""
    existing = _safe_load_json(store_json)
    existing_ids = {s.get("編號") for s in existing}
    added = 0
    for s in new_stores:
        sid = s.get("編號")
        if sid and sid not in existing_ids:
            existing.append(s)
            existing_ids.add(sid)
            added += 1
    _safe_write_json(store_json, existing)
    logging.info(f"合併完成：新增 {added} 筆，總數 {len(existing)}")
    return existing

def _init_driver():
    """初始化 WebDriver；舊版 utils 不支援 headless 參數時自動降級。"""
    try:
        return initialize_driver(headless=HEADLESS)
    except TypeError:
        return initialize_driver()

def ensure_driver_alive(driver):
    """確認 driver 還活著；掛了就重開。"""
    try:
        _ = driver.current_url
        return driver
    except Exception:
        try:
            driver.quit()
        except Exception:
            pass
        return _init_driver()

def _call_scroll_reviews(driver, store_name, store_id):
    """
    統一呼叫 scroll_reviews：
    1) 先嘗試新簽名（可指定輸出檔案，避免寫到錯誤位置）
    2) 不支援就自動降級舊簽名
    """
    try:
        return scroll_reviews(
            driver=driver,
            store_name=store_name,
            store_id=store_id,
            pause_time=3,
            max_no_change_attempts=2,
            batch_size=50,
            max_scrolls=2000,
            reviews_json=str(REVIEWS_JSON),  # ★ 指定固定輸出檔
            store_json=str(STORES_JSON),     # ★ 更新完成狀態用
        )
    except TypeError:
        # 舊版相容（沒有 reviews_json / store_json 參數）
        return scroll_reviews(driver, store_name, store_id=store_id)

# ---------- 主流程 ----------
def main():
    if not GOOGLE_API_KEY:
        raise RuntimeError("缺少 Google API Key。請在 .env 設定 GOOGLE_PLACES_API_KEY=你的金鑰")

    # 確保資料夾存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"輸出資料夾：{DATA_DIR}")
    logging.info(f"店家檔：{STORES_JSON}")
    logging.info(f"評論檔：{REVIEWS_JSON}")

    # 1) 準備 towns 資料
    towns_path = next((p for p in TOWNS_JSON_CANDIDATES if p.exists()), None)
    if not towns_path:
        raise FileNotFoundError(
            f"找不到 town.json，請放在：\n- {TOWNS_JSON_CANDIDATES[0]}\n或\n- {TOWNS_JSON_CANDIDATES[1]}"
        )
    logging.info(f"使用 towns 檔案：{towns_path}")
    towns = _safe_load_json(towns_path)

    # 2) 依縣市 + TOWNS/EXCLUDE_TOWNS/TOWN_LIMIT 選出目標行政區
    county_towns = [t for t in towns if t.get("CountyName") == COUNTY]

    if TOWNS:
        target_towns = [t for name in TOWNS for t in county_towns if t.get("TownName") == name]
    else:
        target_towns = county_towns[:TOWN_LIMIT]

    if EXCLUDE_TOWNS:
        target_towns = [t for t in target_towns if t.get("TownName") not in EXCLUDE_TOWNS]

    if not target_towns:
        raise RuntimeError(f"{COUNTY} 沒有符合條件的鄉鎮（請檢查 TOWNS/EXCLUDE_TOWNS/TOWN_LIMIT）")

    logging.info("縣市：%s，本次抓取行政區：%s",
                 COUNTY, "、".join([t["TownName"] for t in target_towns]))

    # 3) 逐行政區打 Places API，先把所有結果合併
    all_new: List[Dict] = []
    for town in target_towns:
        lat, lng = town["latitude"], town["longitude"]
        tmp_out = DATA_DIR / f"temp_stores_{town['TownName']}.json"
        fetch_places_from_api(
            town_json_path=None,  # 改用 lat/lng
            keywords=KEYWORDS,
            api_key=GOOGLE_API_KEY,
            radius=RADIUS,
            output_json=str(tmp_out),
            lat=lat,
            lng=lng,
        )
        logging.info(f"完成抓取 {town['TownName']} 的店家 → {tmp_out.name}")
        all_new.extend(_safe_load_json(tmp_out))
        tmp_out.unlink(missing_ok=True)

    # 合併一次（避免每區合併一次造成反覆掃整包）
    all_stores = merge_store_data(all_new, STORES_JSON)

    # 4) 開瀏覽器：對「尚未完成」的店家抓簡介與評論
    pending = [s for s in all_stores if s.get("是否已完成") != "已完成"]
    if not pending:
        logging.info("沒有需要更新的店家，結束。")
        return

    driver = _init_driver()
    try:
        for store in pending:
            url = store.get("店家google map網址")
            store_name = store.get("店名") or store.get("name") or ""
            store_id = store.get("編號") or store.get("place_id")
            if not url:
                logging.warning(f"{store_name or store_id} 沒有 Google Map 網址，跳過")
                continue

            # 每家店最多重試 2 次（driver 掛掉時）
            for attempt in (1, 2):
                try:
                    driver = ensure_driver_alive(driver)
                    driver.get(url)
                    time.sleep(2)

                    # 簡介 → 寫回 STORES_JSON
                    try:
                        fetch_intro_info(driver, store_name, KEYWORDS, json_path=str(STORES_JSON))
                        logging.info(f"[簡介] {store_name} 完成")
                    except Exception as e:
                        logging.error(f"[簡介] {store_name} 失敗：{e}")

                    # 評論 → 寫回 REVIEWS_JSON
                    try:
                        open_reviews(driver)
                        sort_reviews_by_latest(driver)
                        _call_scroll_reviews(driver, store_name, store_id)
                        logging.info(f"[評論] {store_name} 完成")
                    except InvalidSessionIdException:
                        # 抓評論途中 session 掛了，交由外層 retry
                        raise
                    except Exception as e:
                        logging.error(f"[評論] {store_name} 失敗：{e}")

                    # 成功則不再重試
                    break

                except (InvalidSessionIdException, WebDriverException) as e:
                    logging.error(f"Driver 失效（第 {attempt} 次）：{e}")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = _init_driver()

                    if attempt == 2:
                        logging.error(f"{store_name} 連續兩次 driver 掛掉，跳過這家。")

            time.sleep(1)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
