import logging
import csv
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Iterable
from urllib.parse import urljoin, urlencode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# -----------------------------
# WebDriver（預設無頭，Selenium Manager 自動找 driver）
# -----------------------------
def initialize_driver(headless: Optional[bool] = None, window_size: str = "1280,900"):
    """
    建立 Chrome WebDriver。
    - headless: 預設 True，可用環境變數 HEADLESS=0 關閉無頭
    - 自動使用 Selenium Manager 處理 chromedriver
    """
    if headless is None:
        headless = os.getenv("HEADLESS", "1") != "0"

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--window-size={window_size}")
    # opts.add_argument("--disable-blink-features=AutomationControlled")

    service = Service()  # 不指定 path → 交給 Selenium Manager
    driver = webdriver.Chrome(service=service, options=opts)
    return driver


# -----------------------------
# 檔名清理
# -----------------------------
_WINDOWS_RESERVED = {
    "CON","PRN","AUX","NUL",
    "COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9",
    "LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9",
}

def sanitize_filename(name: str, replacement: str = "_", max_len: int = 100) -> str:
    """移除不合法的檔名字元、尾端空白/點、Windows 保留名，並限制長度。"""
    if not name:
        return "untitled"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', replacement, name)  # 非法字元
    name = re.sub(r"\s+", " ", name).strip()                   # 壓縮空白
    name = name.rstrip(" .")                                   # 尾端空白/點
    if name.upper() in _WINDOWS_RESERVED:                      # 保留名
        name = f"_{name}_"
    return name[:max_len] or "untitled"


# -----------------------------
# 產生下一個 ID
# -----------------------------
def _keyword_code(keyword: str) -> str:
    """使用關鍵字第一個字的 Unicode 編碼前 3 位作為前綴（與你原邏輯相容）。"""
    if not keyword:
        return ""
    c = keyword[0]
    return f"{ord(c):03d}"[:3]

def _looks_like_header(row: List[str]) -> bool:
    """粗略判斷第一列是否標題列。"""
    if not row:
        return False
    head = row[0].lower()
    return any(k in head for k in ("id", "編號", "index"))

def get_next_id(csv_file, keyword: str = "", width: int = 5) -> str:
    """
    取得下一個可用 ID。
    - 若有 keyword：回傳 <keyword_code><流水號>，例如 '24500001'
    - 若無 keyword：回傳純數字，左側補零至 width
    - 會自動忽略空行、非數字/不符前綴的 ID
    """
    csv_path = Path(csv_file)
    prefix = _keyword_code(keyword)

    try:
        if not csv_path.exists():
            return f"{prefix}{'1'.zfill(width)}" if prefix else str(1).zfill(width)

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        start_idx = 1 if rows and _looks_like_header(rows[0]) else 0
        ids = [r[0] for r in rows[start_idx:] if r]

        def _num_tail(s: str) -> Optional[int]:
            """取去除前綴後的數字尾巴；不是數字就回 None。"""
            if prefix:
                if not s.startswith(prefix):
                    return None
                tail = s[len(prefix):]
                return int(tail) if tail.isdigit() else None
            else:
                return int(s) if s.isdigit() else None

        nums = [n for n in (_num_tail(s) for s in ids) if n is not None]
        next_num = (max(nums) + 1) if nums else 1
        return f"{prefix}{str(next_num).zfill(width)}" if prefix else str(next_num).zfill(width)

    except Exception as e:
        logging.error(f"取得下一個 ID 時出錯：{e}")
        # 安全退回
        return f"{prefix}{'1'.zfill(width)}" if prefix else str(1).zfill(width)


# -----------------------------
# 簡介文字格式化
# -----------------------------
_PUA_PATTERN = re.compile(r"[\uE000-\uF8FF]")     # 私用區字元
_ESCAPE_PATTERN = re.compile(r"\\u[0-9a-fA-F]{4}") # 形如 \uXXXX 的序列

def _clean_line(s: str) -> str:
    s = _ESCAPE_PATTERN.sub("", s)
    s = _PUA_PATTERN.sub("", s)
    s = s.replace("\u200b", "")  # 零寬空白
    s = re.sub(r"\s+", " ", s).strip(" 、，,;；")
    return s.strip()

def format_intro_content(intro_text: List[str]) -> str:
    """
    將「多段簡介文字」整理成「Title：[item1, item2]，...」的字串（與你原本相容）。
    規則：
      - 逐段清理特殊字元與空白
      - 每段第一行視為標題，後續為項目
      - 項目去重（大小寫/空白不敏感）
    """
    try:
        intro_dict: Dict[str, List[str]] = {}

        for section in intro_text or []:
            section = _clean_line(section)
            if not section:
                continue
            lines = [ln for ln in map(_clean_line, section.split("\n")) if ln]
            if not lines:
                continue

            title = lines[0]
            items = [ln for ln in lines[1:] if ln]

            # 若只有一行但含冒號，拆成 title: items
            if len(lines) == 1 and (":" in title or "：" in title):
                t, _, rest = re.split(r"[:：]", title, maxsplit=1)
                title = _clean_line(t)
                items = [_clean_line(x) for x in re.split(r"[、,，;；]", rest) if _clean_line(x)]

            if not title:
                continue

            # 去重（忽略大小寫與多餘空白）
            seen = set()
            deduped = []
            for it in items:
                key = it.casefold().strip()
                if key and key not in seen:
                    seen.add(key)
                    deduped.append(it)

            if deduped:
                intro_dict.setdefault(title, [])
                intro_dict[title].extend(deduped)

        # 再做一次每個標題底下的去重
        for k, vals in list(intro_dict.items()):
            seen = set()
            unique_vals = []
            for v in vals:
                key = v.casefold().strip()
                if key not in seen:
                    seen.add(key)
                    unique_vals.append(v)
            intro_dict[k] = unique_vals

        parts = []
        for title, items in intro_dict.items():
            if items:
                parts.append(f"{title}：[{', '.join(items)}]")

        return "， ".join(parts) if parts else ""

    except Exception as e:
        logging.error(f"格式化簡介內容時出錯：{e}")
        return " , ".join(intro_text or [])


# ============================================================
#  圖片連結工具（關鍵：輸出「圖片連結」而非檔名）
# ============================================================

# 從 HTML 抓 <img> 各種屬性（src/data-src/data-original/...）
_IMG_SRC_RE = re.compile(
    r'<img[^>]+(?:src|data-src|data-original|data-lazy-src)\s*=\s*["\']([^"\']+)["\']',
    re.I
)

def _normalize_urls(urls: Iterable[str], base_url: Optional[str] = None) -> List[str]:
    """淨化、補絕對路徑、去重，只保留 http(s)。"""
    out: List[str] = []
    seen = set()
    for u in urls or []:
        if not u:
            continue
        u = u.strip()
        if u.startswith("//"):
            u = "https:" + u
        if base_url and not re.match(r"^https?://", u):
            u = urljoin(base_url, u)
        if not re.match(r"^https?://", u):
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def extract_image_urls_from_html(html: str, base_url: Optional[str] = None, limit: int = 5) -> List[str]:
    """
    從一般頁面 HTML 直接萃取圖片連結（不用額外套件）。
    - 會抓 src / data-src / data-original / data-lazy-src
    - 自動補絕對網址與去重
    """
    try:
        candidates = _IMG_SRC_RE.findall(html or "")
        urls = _normalize_urls(candidates, base_url)
        return urls[:limit] if limit else urls
    except Exception as e:
        logging.warning(f"extract_image_urls_from_html 失敗：{e}")
        return []

def build_places_photo_url(photo_reference: str, api_key: str, maxwidth: int = 1200) -> str:
    """產生 Google Places Photo API 的可用連結（可直接給前端，會 302 到圖片）。"""
    base = "https://maps.googleapis.com/maps/api/place/photo"
    q = urlencode({"maxwidth": maxwidth, "photo_reference": photo_reference, "key": api_key})
    return f"{base}?{q}"

def resolve_gmaps_photo_url(photo_api_url: str, timeout: int = 10) -> str:
    """
    （可選）把 Photo API 302 的連結解析成最終 gstatic 圖片 URL（不下載內容）。
    解析失敗就回傳原始 photo_api_url。
    """
    try:
        import requests  # 延遲匯入，避免沒用到時增加依賴
        r = requests.get(photo_api_url, allow_redirects=False, timeout=timeout)
        if r.status_code in (301, 302, 303) and "Location" in r.headers:
            return r.headers["Location"]
    except Exception:
        pass
    return photo_api_url

def extract_image_urls_from_details(details: dict, api_key: str, maxwidth: int = 1200,
                                   resolve: bool = False, limit: int = 5) -> List[str]:
    """
    從 Google Places Details 結果的 photos 陣列產生圖片連結清單。
    - 預設回傳 Photo API 連結；resolve=True 可解析成最終 gstatic 連結
    """
    try:
        refs = [p.get("photo_reference") for p in (details.get("photos") or []) if p.get("photo_reference")]
        urls = [build_places_photo_url(ref, api_key, maxwidth) for ref in refs[:limit]]
        if resolve:
            urls = [resolve_gmaps_photo_url(u) for u in urls]
        return _normalize_urls(urls)
    except Exception as e:
        logging.warning(f"extract_image_urls_from_details 失敗：{e}")
        return []

def merge_image_sources(
    details: Optional[dict] = None,
    html: Optional[str] = None,
    base_url: Optional[str] = None,
    raw_urls: Optional[Iterable[str]] = None,
    api_key: Optional[str] = None,
    limit: int = 5,
    resolve: bool = False,
) -> List[str]:
    """
    綜合多來源（Places Details / HTML / 已有清單）輸出「圖片連結」list。
    - 會去重、補絕對網址
    - limit 是最終回傳數量上限（0 表示不限制）
    """
    urls: List[str] = []

    # 1) Places Details → Photo API
    if details and api_key:
        urls.extend(extract_image_urls_from_details(details, api_key=api_key, resolve=resolve, limit=limit or 20))

    # 2) HTML <img> 抽取
    if html:
        urls.extend(extract_image_urls_from_html(html, base_url=base_url, limit=limit or 50))

    # 3) 既有清單或逗號字串
    if raw_urls:
        if isinstance(raw_urls, str):
            parts = re.split(r"[,\s]+", raw_urls.strip())
        else:
            parts = list(raw_urls)
        urls.extend(_normalize_urls(parts, base_url=base_url))

    # 去重並限制數量
    final = _normalize_urls(urls)
    return final[:limit] if limit else final
