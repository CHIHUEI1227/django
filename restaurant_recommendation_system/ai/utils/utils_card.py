# utils_card.py
import re
from .utils_common import normalize_text

def generate_map_url(name: str) -> str:
    return f"https://www.google.com/maps/search/{name}"

def format_open_status(is_open_raw) -> str:
    if isinstance(is_open_raw, bool):
        return "營業中" if is_open_raw else "休息中"
    elif isinstance(is_open_raw, str):
        return is_open_raw
    else:
        return "無資料"

def extract_district(address: str) -> str:
    match = re.search(r'(台北市|新北市)?(\w{2,3}區)', address)
    return match.group(2) if match else ""

def generate_price_description(price_level: str) -> str:
    mapping = {
        "$": "價格實惠",
        "$$": "價格中等",
        "$$$": "偏高價位"
    }
    return mapping.get(price_level, "")

def generate_recommend_reason(tags: list, highlight: str, district: str, price_desc: str) -> str:
    keywords = set(tags)
    if highlight:
        keywords.add(highlight)
    if district:
        keywords.add(district)
    if price_desc:
        keywords.add(price_desc)
    return "、".join(keywords)

def expand_exclusions(items: list) -> list:
    mapping = {
        "甜點": ["甜點", "甜品", "甜食", "蛋糕", "烘焙", "下午茶", "甜點店", "甜點專門", "甜點評價高"],
        "拉麵": ["拉麵", "ramen"],
        "燒烤": ["燒烤", "烤肉", "炭火", "燒肉"],
        "漢堡": ["漢堡", "burger"],
        "美式": ["美式", "美式餐廳", "美式風格", "美式漢堡"],
        "火鍋": ["火鍋", "鍋物", "涮涮鍋", "麻辣鍋"],
    }
    expanded = set()
    for it in items or []:
        raw = (it or "").strip()
        norm = normalize_text(raw)
        if not norm:
            continue
        candidates = set([raw, norm])
        for key, syns in mapping.items():
            if key == raw or key == norm:
                candidates |= set(syns)
        for c in candidates:
            expanded.add(normalize_text(c))
    return list(expanded)

def collect_blob(r: dict) -> str:
    parts = []
    for k in ["name", "highlight", "ai_reason", "comment_summary", "style", "address"]:
        v = r.get(k, "")
        if v:
            parts.append(str(v))
    for lk in ["matched_tags", "tags", "features"]:
        seq = r.get(lk) or []
        parts.extend([str(t) for t in seq])
    return normalize_text("｜".join(parts))

def uniq_keep_order(items):
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out

def deduplicate_semantic(phrases):
    from collections import OrderedDict
    cleaned = []
    seen = set()
    phrases_sorted = sorted(phrases, key=lambda x: -len(x))
    for p in phrases_sorted:
        if all(p not in s for s in seen):
            cleaned.append(p)
            seen.add(p)
    return list(OrderedDict.fromkeys(cleaned))

def sort_reasons(reason_list):
    priority = [
        "素食", "辛辣", "清爽", "重口味",
        "評價", "熱門", "氣氛",
        "價格", "CP", "高價", "便宜",
        "地點", "位於",
        "聚餐", "約會", "家庭", "宵夜", "早餐", "慶祝", "親子",
        "風格", "營業", "夜貓"
    ]
    return sorted(reason_list, key=lambda r: next((i for i, p in enumerate(priority) if p in r), len(priority)))

FEATURE_REASON_MAP = {
    "甜點專門": "甜點評價高",
    "氣氛佳": "氣氛佳",
    "聚餐推薦": "適合聚餐",
    "高 CP 值": "高 CP 值",
    "價格便宜": "價格實惠",
    "價格親民": "價格實惠",
    "人氣餐廳": "熱門店家",
    "宵夜好選擇": "適合宵夜",
    "異國料理": "異國風味"
}

STYLE_REASON_MAP = {
    "文青": "文青風格",
    "美式": "美式風格",
    "日式": "日式風格",
    "夜貓族": "適合夜貓子",
    "東南亞風": "東南亞風格"
}

USER_INPUT_RULES = {
    "吃素": "素食需求", "素食": "素食需求",
    "怕辣": "避免辛辣料理", "不吃辣": "避免辛辣料理",
    "不想太油": "清爽口味", "清爽": "清爽口味", "太油": "清爽口味", "油膩": "清爽口味",
    "朋友聚餐": "適合朋友聚會", "同學聚餐": "適合朋友聚會", "聚餐": "適合聚餐",
    "家庭聚餐": "適合家庭聚會", "帶爸媽": "適合家庭聚會", "爸媽": "適合家庭聚會", "家人吃飯": "適合家庭聚會",
    "約會": "氣氛佳，適合約會", "商務": "適合正式聚會", "請客": "適合正式聚會", "正式": "適合正式聚會",
    "慶生": "適合慶祝場合", "生日": "適合慶祝場合", "慶祝": "適合慶祝場合",
    "小孩": "親子友善", "兒童": "親子友善",
    "不貴": "價格實惠", "便宜": "價格實惠", "平價": "價格實惠", "價格實惠": "價格實惠",
    "高級": "精緻高價", "高價": "精緻高價", "高端": "精緻高價", "精緻": "精緻高價",
    "宵夜": "適合宵夜", "深夜": "適合宵夜", "早午餐": "適合早午餐", "早餐": "適合早餐",
    "時間不多": "快速方便", "趕時間": "快速方便", "快速吃": "快速方便",
    "想吃辣": "重口味料理", "重口味": "重口味料理", "辣的料理": "重口味料理", "麻辣": "重口味料理", "辣鍋": "重口味料理",
}
