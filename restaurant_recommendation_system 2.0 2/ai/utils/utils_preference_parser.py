# utils/preference_parser.py
import re

def parse_preference_from_text(text: str):
    """
    從使用者輸入文字中解析出偏好。
    返回格式：
    {
        "long_term": {"喜歡": [...], "不喜歡": [...]},
        "short_term": {"喜歡": [...], "不喜歡": [...]}
    }
    """
    preferences = {
        "long_term": {"喜歡": [], "不喜歡": []},
        "short_term": {"喜歡": [], "不喜歡": []}
    }

    # 關鍵字分類
    long_like_keywords = ["喜歡", "愛吃", "偏好", "要吃"]
    long_dislike_keywords = ["不喜歡", "不吃", "討厭"]
    short_like_keywords = ["今天想吃", "現在想吃", "暫時想吃", "今天要吃"]
    short_dislike_keywords = ["今天不想吃", "不想吃", "現在不吃"]

    # 解析函數
    def extract_items(patterns, text):
        items = []
        for pattern in patterns:
            matches = re.findall(f"{pattern}[^，。；!?、]*", text)
            for match in matches:
                # 去掉關鍵字
                items_str = re.sub(pattern, "", match)
                # 拆分多個食物
                split_items = re.split("[、和與,，及 ]", items_str)
                # 去掉多餘詞，例如 "吃"、"愛吃"、"喝"、"愛喝"
                cleaned_items = []
                for s in split_items:
                    s = s.strip()
                    # 移除開頭常見動詞
                    s = re.sub(r"^(吃|愛吃|喝|愛喝)", "", s)
                    if s:
                        cleaned_items.append(s)
                items.extend(cleaned_items)
        return items

    # ---- 解析長期偏好 ----
    preferences["long_term"]["喜歡"] = extract_items(long_like_keywords, text)
    preferences["long_term"]["不喜歡"] = extract_items(long_dislike_keywords, text)

    # ---- 解析短期偏好 ----
    preferences["short_term"]["喜歡"] = extract_items(short_like_keywords, text)
    preferences["short_term"]["不喜歡"] = extract_items(short_dislike_keywords, text)

    # ---- 移除衝突項目，避免同一個食物同時出現在喜歡與不喜歡 ----
    def remove_conflict(pref_dict):
        like_set = set(pref_dict["喜歡"])
        dislike_set = set(pref_dict["不喜歡"])
        overlap = like_set & dislike_set
        if overlap:
            # 衝突時移除喜歡
            pref_dict["喜歡"] = [item for item in pref_dict["喜歡"] if item not in overlap]
    remove_conflict(preferences["long_term"])
    remove_conflict(preferences["short_term"])

    # ---- 如果都沒有，回傳 "無特別偏好" ----
    if not any(preferences["long_term"]["喜歡"] + preferences["long_term"]["不喜歡"] +
               preferences["short_term"]["喜歡"] + preferences["short_term"]["不喜歡"]):
        return ["無特別偏好"]

    return preferences