#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, argparse, re
from pathlib import Path
from datetime import datetime, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restaurant_recommendation_system.settings")
import django
django.setup()

from django.db import transaction
from django.utils import timezone
from django.core.files import File
from restaurants.models import Restaurant, RestaurantReview

# ----------------- 小工具 -----------------
def load_json(p: str):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default

def as_int(x):
    try:
        if isinstance(x, str) and (x.strip() == "" or "無價位" in x):
            return None
        return int(float(x))
    except Exception:
        return None

def as_float(x):
    try:
        if isinstance(x, str) and x.strip() == "":
            return None
        return float(x)
    except Exception:
        return None

def parse_price_level(v):
    if v in (None, ""): return None
    if isinstance(v, int): return v
    s = str(v).strip()
    if set(s) <= {"$"}: return len(s)
    return as_int(s)

def parse_open_status(v):
    if v in ("open", "closed", "unknown"): return v
    s = str(v or "").strip().lower()
    if s in ("營業中", "open", "true", "yes"): return "open"
    if s in ("已打烊", "closed", "false", "no"): return "closed"
    return "unknown"

def parse_latlng(s):
    if not s: return (None, None)
    parts = [p.strip() for p in str(s).split(",")]
    if len(parts) >= 2:
        try: return float(parts[0]), float(parts[1])
        except Exception: return (None, None)
    return (None, None)

def parse_types(s):
    if not s: return None
    if isinstance(s, list): return s
    return [t.strip() for t in str(s).replace("，", ",").split(",") if t.strip()]

def as_url(s):
    if not s: return ""
    s = str(s).strip()
    return s if s.startswith("http") else ""

def parse_weekday_text(v):
    if v is None or v == "": return None
    if isinstance(v, list): return v
    txt = str(v).strip()
    if not txt: return None
    lines = [seg.strip() for seg in re.split(r"[\n、;；]", txt) if seg.strip()]
    return lines or None

# 類別細項評分
_score_pat = re.compile(r"(餐點|服務|氣氛)\s*[:：]\s*([0-9])")
def parse_category_scores(s):
    if not s or "無類別" in str(s): return None
    out = {}
    for k, v in _score_pat.findall(str(s)):
        out[k] = int(v)
    return out or None

# 多格式時間解析
def parse_dt(v):
    if v in (None, "", 0): return None
    if isinstance(v, (int, float)) and v > 10_000:
        try: return datetime.fromtimestamp(int(v), tz=timezone.utc)
        except Exception: return None
    s = str(v).strip().replace("年", "-").replace("月", "-").replace("日", "")
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                return timezone.make_aware(dt, timezone=timezone.get_current_timezone())
            return dt
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

# ----------------- 營業時間 → 明細＆即時狀態 -----------------
WEEK_MAP = {"星期一":0,"星期二":1,"星期三":2,"星期四":3,"星期五":4,"星期六":5,"星期日":6,
            "週一":0,"週二":1,"週三":2,"週四":3,"週五":4,"週六":5,"週日":6}
TIME_RE = re.compile(r"(\d{1,2}:\d{2})\s*[–—\-~至到]?\s*(\d{1,2}:\d{2})")
BLOCK_RE = re.compile(r"([\u4e00-\u9fffA-Za-z0-9／/]+)\s*[:：]\s*\[(.*?)\]")

def _to_time(hhmm: str) -> time | None:
    try:
        h, m = hhmm.split(":")
        return time(int(h), int(m))
    except Exception:
        return None

def parse_opening_lines(lines):
    """輸入 weekday_text 列表，輸出多時段 [(weekday, open_time, close_time, crosses_midnight), ...]"""
    results = []
    if not isinstance(lines, list): return results
    for ln in lines:
        s = str(ln)
        wd = next((WEEK_MAP[k] for k in WEEK_MAP if k in s), None)
        if wd is None: continue
        if "休" in s:  # 公休/休息
            continue
        if "24" in s and "小時" in s:
            results.append((wd, time(0,0), time(23,59), False))
            continue
        for m in TIME_RE.finditer(s.replace("～","-")):
            t1, t2 = _to_time(m.group(1)), _to_time(m.group(2))
            if not (t1 and t2): 
                continue
            crosses = (t2 <= t1)  # 22:00→02:00
            results.append((wd, t1, t2, crosses))
    return results

def is_open_now(tuples, now):
    wd = now.weekday()
    t = now.time()
    for (w, t1, t2, cross) in tuples:
        if cross:
            if (wd == w and t >= t1) or (wd == (w + 1) % 7 and t <= t2):
                return True
        else:
            if wd == w and t1 <= t <= t2:
                return True
    return False

def compute_open_status_from_lines(lines):
    tuples = parse_opening_lines(lines or [])
    if not tuples: return "unknown"
    now = timezone.localtime()  # 以專案時區（建議 Asia/Taipei）
    return "open" if is_open_now(tuples, now) else "closed"

# ----------------- 屬性＆來源 -----------------
def extract_attributes(desc: str, keywords: str | None):
    """回傳 dict[key] = '值1, 值2, 值3'（同 key 合併成一筆，符合 unique_together(restaurant,key)）"""
    out = {}
    if desc:
        for label, content in BLOCK_RE.findall(desc):
            vals = [v.strip() for v in re.split(r"[、,，/／]", content) if v.strip()]
            if vals: out[label.strip()] = ", ".join(dict.fromkeys(vals))
    if keywords:
        vals = [v.strip() for v in re.split(r"[、,，/／\s]+", keywords) if v.strip()]
        if vals: out["關鍵字"] = ", ".join(dict.fromkeys(vals))
    return out

def upsert_attributes(restaurant, desc: str | None, keywords: str | None):
    from restaurants.models import RestaurantAttribute
    kv = extract_attributes(desc or "", keywords or "")
    for k, v in kv.items():
        RestaurantAttribute.objects.update_or_create(
            restaurant=restaurant, key=k,
            defaults={"value": v, "source": "manual"}
        )

def upsert_source_meta(restaurant, row: dict):
    from restaurants.models import RestaurantSourceMeta
    src = "gmaps_scrape" if str(row.get("店家google map網址","")).startswith("http") else "manual"
    RestaurantSourceMeta.objects.update_or_create(
        restaurant=restaurant, source=src,
        defaults={
            "fetched_at": timezone.now(),
            "status_code": "",
            "etag": row.get("圖片檔案名稱",""),
            "quota_cost": None,
            "raw_json": row,
        }
    )

# ----------------- 圖片（URL 連結 & 本機檔） -----------------
def _normalize_urls(v):
    """接受 list 或逗號/空白分隔字串，回傳乾淨的 URL list。"""
    if not v:
        return []
    if isinstance(v, list):
        raw = v
    else:
        raw = re.split(r"[\s,，]+", str(v))
    urls = []
    for u in raw:
        u = as_url(u)
        if u:
            urls.append(u)
    return urls

def import_photos_from_urls(restaurant, row, max_photos: int = 10):
    """
    從 JSON 欄位『圖片連結』匯入到 RestaurantPhoto.remote_url。
    去重：同一餐廳 + 同一 remote_url 就略過。
    """
    from restaurants.models import RestaurantPhoto
    urls = first(row, "圖片連結", "image_urls", "images")
    urls = _normalize_urls(urls)
    created = skipped = 0
    for url in urls[:max_photos]:
        obj, is_new = RestaurantPhoto.objects.get_or_create(
            restaurant=restaurant,
            remote_url=url,
            defaults={"source": "gmap_photo"},
        )
        if is_new:
            created += 1
        else:
            skipped += 1
    return created, skipped

def import_photo_file(restaurant, row, photos_dir: Path):
    """
    舊版：圖片檔案名稱 -> 到 photos_dir 找檔案，存到 ImageField。
    去重：用 (restaurant, photo_reference=檔名) update_or_create。
    """
    from restaurants.models import RestaurantPhoto
    fname = first(row, "圖片檔案名稱", "photo_filename", "photo", "photo_reference")
    if not fname:
        return False
    fp = photos_dir / fname
    if not fp.exists():
        return False
    obj, _ = RestaurantPhoto.objects.update_or_create(
        restaurant=restaurant, photo_reference=fname,
        defaults={"source": "gmap_photo"}
    )
    if not obj.file:
        with open(fp, "rb") as f:
            obj.file.save(fp.name, File(f), save=True)
    return True

# ----------------- 餐廳匯入 -----------------
def import_restaurants(path: str, photos_dir: Path | None = None, max_photos_per_store: int = 8):
    data = load_json(path)
    created = updated = skipped = 0
    url_created = url_skipped = 0
    file_ok = file_missing = 0

    with transaction.atomic():
        for row in data:
            place_id = first(row, "編號", "place_id", "placeId", "google_id")
            if not place_id:
                skipped += 1
                continue

            weekday_text_list = parse_weekday_text(first(row, "營業時間", "weekday_text"))
            # 判斷 open_status：若官方是永久停業 → closed；否則依營業時間估算
            business_status = first(row, "營業狀態", "business_status") or "OPERATIONAL"
            if business_status == "CLOSED_PERMANENTLY":
                open_status = "closed"
            else:
                open_status = compute_open_status_from_lines(weekday_text_list)

            lat, lng = parse_latlng(first(row, "經緯度", "latlng"))
            defaults = {
                "name": (first(row, "店名", "name") or "").strip(),
                "formatted_address": (first(row, "地址", "formatted_address", "vicinity") or "").strip(),
                "lat": lat, "lng": lng,
                "business_status": business_status,
                "open_status": open_status,
                "price_level": parse_price_level(first(row, "價位", "price_level")),
                "rating": as_float(first(row, "星數", "rating")),
                "user_ratings_total": as_int(first(row, "評分數量", "評論數", "user_ratings_total")),
                "types": parse_types(first(row, "店家類型", "types")),
                "website": as_url(first(row, "官方網站", "website")),
                "google_maps_url": as_url(first(row, "店家google map網址", "google_maps_url")),
                "weekday_text": weekday_text_list,
                "description": first(row, "店家簡述", "簡介", "description") or "",
            }

            obj, was_created = Restaurant.objects.update_or_create(
                place_id=place_id, defaults=defaults
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

            # 屬性 & 來源
            upsert_attributes(obj, first(row, "簡介", "description"), first(row, "搜尋關鍵字", "關鍵字", "keywords"))
            upsert_source_meta(obj, row)

            # ① 先處理「圖片連結」
            c, s = import_photos_from_urls(obj, row, max_photos=max_photos_per_store)
            url_created += c
            url_skipped += s

            # ② 相容舊格式：有指定資料夾且有「圖片檔案名稱」才嘗試
            if photos_dir:
                if import_photo_file(obj, row, photos_dir):
                    file_ok += 1
                else:
                    file_missing += 1

    return created, updated, skipped, url_created, url_skipped, file_ok, file_missing

# ----------------- 評論匯入 -----------------
def import_reviews(path: str):
    data = load_json(path)
    created = updated = skipped = 0

    for row in data:
        place_id = first(row, "店家編號", "place_id", "placeId", "google_id")
        if not place_id:
            skipped += 1
            continue
        try:
            restaurant = Restaurant.objects.get(place_id=place_id)
        except Restaurant.DoesNotExist:
            skipped += 1
            continue

        author_name = (first(row, "用戶名稱", "author_name", "user", "displayName") or "").strip()[:120]
        author_url  = as_url(first(row, "用戶評論記錄網址", "author_url", "profile_url"))
        rating      = as_int(first(row, "評分", "rating"))
        published_at= parse_dt(first(row, "評論日期", "published_at", "date", "time", "timestamp"))
        text        = (first(row, "評論內容", "text", "content") or "").strip()
        category_scores = parse_category_scores(first(row, "類別及評分", "category_scores"))

        filter_key = {"restaurant": restaurant, "author_name": author_name, "rating": rating, "text": text}
        if published_at: filter_key["published_at"] = published_at
        defaults = {"author_url": author_url, "category_scores": category_scores}

        _, was_created = RestaurantReview.objects.update_or_create(**filter_key, defaults=defaults)
        created += 1 if was_created else 0
        updated += 0 if was_created else 1

    return created, updated, skipped

# ----------------- 入口 -----------------
def main():
    ap = argparse.ArgumentParser(description="Import restaurants, photos & reviews JSON into DB (支援圖片連結).")
    ap.add_argument("--restaurants", default="restaurants/current/store_intros.json")
    ap.add_argument("--reviews",     default="restaurants/current/all_reviews.json")
    ap.add_argument("--photos-dir",  default="", help="(選擇性) 舊版本機圖片資料夾；若未提供則不處理檔案")
    ap.add_argument("--max-photos",  type=int, default=8, help="每家店最多匯入的圖片連結數")
    ap.add_argument("--skip-reviews", action="store_true")
    args = ap.parse_args()

    photos_dir = Path(args.photos_dir) if args.photos_dir else None
    if photos_dir and not photos_dir.exists():
        print(f"⚠️ 找不到圖片資料夾：{photos_dir}（將略過本機圖片匯入）")
        photos_dir = None

    if args.restaurants:
        c, u, s, uc, us, fk, fm = import_restaurants(args.restaurants, photos_dir, args.max_photos)
        msg = f"【餐廳】新增 {c}、更新 {u}、略過 {s}；【圖片(URL)】新增 {uc}、略過 {us}"
        if photos_dir:
            msg += f"；【圖片(檔案)】成功 {fk}、未找到 {fm}"
        print(msg)

    if not args.skip_reviews and args.reviews:
        c, u, s = import_reviews(args.reviews)
        print(f"【評論】新增 {c}、更新 {u}、略過 {s}")

    print("✅ 匯入完成")

if __name__ == "__main__":
    main()