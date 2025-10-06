from .ml_models import ws_driver, pos_driver, zero_shot, ner
from collections import Counter

def is_food_related(phrase, core_food_terms, ws=None):
    description_terms = ["湯頭", "口味", "味道", "外皮", "感覺", "香氣", "姊姊", "人員", "態度", "外帶"]
    if any(term in phrase for term in description_terms):
        return False
    if any(food_term in phrase for food_term in core_food_terms):
        return True
    if ws:
        for word in ws:
            if any(food_term in word for food_term in core_food_terms):
                return True
    food_categories = [
        "餐", "飯", "麵", "湯", "醬", "甜點", "冰", "炸", "烤", "煮", "蒸", "燉", "捲",
        "堡", "餅", "塔", "泥", "奶", "茶", "酪", "羅", "拋", "粥", "糕", "排", "肉",
        "菜", "豆", "鮮", "豬", "牛", "雞", "魚", "蝦", "貝", "米", "酥", "蛋", "泰式", 
        "義式", "日式", "韓式", "美式", "中式", "料理"
    ]
    if "口味" in phrase or "湯頭" in phrase:
        return False
    if any(category in phrase for category in food_categories):
        if any(word in phrase for word in ["姊姊", "感覺", "這次", "下次", "這家", "服務"]):
            return False
        return True
    non_food_indicators = [
        "服務", "這家", "下次", "朋友", "超", "很", "店", "感覺", "價格", "風景", "老闆",
        "環境", "這次", "桌子", "座位", "時間", "等待", "人員", "態度", "客人", "服務生", 
        "裝潢", "外觀", "打卡", "聚餐", "親友", "用餐", "地點", "位置", "停車", "交通",
        "點餐", "菜單", "介紹", "推薦", "建議", "評價", "評論", "心得", "感想", "網路",
        "網友", "朋友", "同事", "家人", "價錢", "便宜", "貴", "錢"
    ]
    if any(indicator in phrase for indicator in non_food_indicators):
        return False
    if "服務" in phrase and "人員" in phrase:
        return False
    if phrase.endswith("的") or phrase.endswith("了") or phrase.endswith("很") or phrase.endswith("也") or phrase.endswith("都"):
        return False
    facility_terms = ["店", "館", "餐廳", "廳", "攤", "屋", "小吃"]
    if any(term in phrase for term in facility_terms):
        return False
    return False


def analyze_user_preferences(content, user_id=None):
    """
    分析使用者偏好，回傳食物與口味關鍵詞。
    :param content: 貼文內容 (str)
    :param user_id: 使用者 id (可選)
    :return: dict {user_id, foods, flavors}
    """
    # print(f"[DEBUG] 取得貼文內容: {content}")

    zero_shot_threshold = 0.75
    max_phrase_length = 6

    core_food_terms = [
        "火鍋", "壽司", "牛排", "冰淇淋", "拉麵", "小菜", "燒肉", "霜淇淋", 
        "蛋糕", "豆腐", "雞肉", "豬排", "蝦仁", "飯", "麵", "奶茶", "咖哩", 
        "鴨", "牛肉", "魚", "紅豆", "抹茶", "巧克力", "芒果", "檸檬", "馬鈴薯", 
        "蒜", "雞", "炸雞", "炸豬排", "海鮮", "燉飯", "鹽酥雞", "椒麻雞"
    ]
    exclude_nouns = set(["東西", "餐點", "料理", "食物", "東西們", "感覺", "服務", "這家", "下次", "這次"])
    exclude_foods = set([
        "這家", "這個", "口", "有機", "份", "公共", "一", "一份", "本家", "家", "價格", 
        "湯頭", "質感", "份量", "口味", "部分", "一些", "新品", "主廚手藝", "香氣", 
        "甜點部分", "肉質", "肉品", "味噌湯鹹度", "紅豆餡", "紅豆餅外皮", "冰塊", "茶香", 
        "抹茶布丁口感", "九層塔香氣", "巧克力慕斯蛋", "糕", "白飯", "餅皮", "餡", "肉", 
        "甜麵醬", "青菜", "菜", "飲料", "醬料", "蔥段", "布丁口感", "慕斯蛋糕", "蛋糕味道",
        "冰淇淋口味", "拉麵湯頭", "牛肉麵湯頭", "義大利麵蒜味", "烏龍麵Q彈", "姊姊烤"
    ])
    flavor_keywords = set([
        "鹹", "甜", "辣", "苦", "酸", "香", "口味", "酥脆", "濃郁", "綿密", 
        "清爽", "香濃", "鮮嫩", "爽口", "Q彈", "多汁", "彈牙", "入味",
        "香脆", "嫩滑", "香甜", "鬆軟", "滑順", "酸甜", "香辣", "軟嫩", "微酸"
    ])
    candidate_labels = ["食物", "食物種類", "食物口味"]

    ws = ws_driver([content])[0]
    pos = pos_driver([ws])[0]

    ner_candidates = set()
    ckip_candidates = set()
    phrase_candidates = set()
    ckip_flavors = set()

    ner_results = ner(content)
    for ent in ner_results:
        if ent['entity_group'] == 'PRODUCT':
            phrase = ent['word']
            if phrase not in exclude_foods and len(phrase) <= max_phrase_length:
                ner_candidates.add(phrase)

    cur_phrase = []
    special_food_phrases = ["鹽酥雞", "椒麻雞", "炸豬排", "霜淇淋", "冰淇淋", "宮保雞丁鐵板麵"]
    for phrase in special_food_phrases:
        if phrase in content:
            ckip_candidates.add(phrase)

    for i in range(len(ws)):
        w, p = ws[i], pos[i]
        if p.startswith("N"):
            cur_phrase.append(w)
        else:
            if cur_phrase:
                phrase = ''.join(cur_phrase)
                if (phrase not in exclude_nouns and 
                    phrase not in exclude_foods and 
                    len(phrase) <= max_phrase_length):
                    ckip_candidates.add(phrase)
                cur_phrase = []
        if w in flavor_keywords:
            ckip_flavors.add(w)
        if p.startswith("N") and i+1 < len(ws) and pos[i+1].startswith("N"):
            nn_phrase = ws[i] + ws[i+1]
            if (nn_phrase not in exclude_foods and 
                ws[i] not in exclude_foods and 
                ws[i+1] not in exclude_foods and
                len(nn_phrase) <= max_phrase_length):
                component_ws = [ws[i], ws[i+1]]
                if is_food_related(nn_phrase, core_food_terms, component_ws):
                    phrase_candidates.add(nn_phrase)
        if p.startswith("A") and i+1 < len(ws) and pos[i+1].startswith("N"):
            an_phrase = ws[i] + ws[i+1]
            if (an_phrase not in exclude_foods and 
                ws[i] not in exclude_foods and 
                ws[i+1] not in exclude_foods and
                len(an_phrase) <= max_phrase_length):
                component_ws = [ws[i], ws[i+1]]
                if is_food_related(an_phrase, core_food_terms, component_ws) or ws[i] in flavor_keywords:
                    phrase_candidates.add(an_phrase)
        if p.startswith("N") and i+1 < len(ws) and pos[i+1].startswith("A"):
            na_phrase = ws[i] + ws[i+1]
            if (na_phrase not in exclude_foods and 
                ws[i] not in exclude_foods and 
                ws[i+1] not in exclude_foods and
                len(na_phrase) <= max_phrase_length):
                component_ws = [ws[i], ws[i+1]]
                if is_food_related(na_phrase, core_food_terms, component_ws) or ws[i+1] in flavor_keywords:
                    phrase_candidates.add(na_phrase)
        if (p.startswith("N") and i+2 < len(ws) and 
            pos[i+1].startswith("N") and pos[i+2].startswith("N")):
            nnn_phrase = ws[i] + ws[i+1] + ws[i+2]
            if (nnn_phrase not in exclude_foods and 
                ws[i] not in exclude_foods and 
                ws[i+1] not in exclude_foods and 
                ws[i+2] not in exclude_foods and
                len(nnn_phrase) <= max_phrase_length):
                component_ws = [ws[i], ws[i+1], ws[i+2]]
                if is_food_related(nnn_phrase, core_food_terms, component_ws):
                    phrase_candidates.add(nnn_phrase)
        if (p.startswith("N") and i+3 < len(ws) and 
            pos[i+1].startswith("N") and 
            pos[i+2].startswith("N") and 
            pos[i+3].startswith("N")):
            nnnn_phrase = ws[i] + ws[i+1] + ws[i+2] + ws[i+3]
            if (nnnn_phrase not in exclude_foods and 
                ws[i] not in exclude_foods and 
                ws[i+1] not in exclude_foods and 
                ws[i+2] not in exclude_foods and 
                ws[i+3] not in exclude_foods and
                len(nnnn_phrase) <= max_phrase_length):
                component_ws = [ws[i], ws[i+1], ws[i+2], ws[i+3]]
                if is_food_related(nnnn_phrase, core_food_terms, component_ws):
                    phrase_candidates.add(nnnn_phrase)
    if cur_phrase:
        phrase = ''.join(cur_phrase)
        if (phrase not in exclude_nouns and 
            phrase not in exclude_foods and 
            len(phrase) <= max_phrase_length):
            ckip_candidates.add(phrase)

    special_foods = ["鹽酥雞", "椒麻雞", "炸豬排", "炸雞"]
    for food in special_foods:
        if food in content and food not in ner_candidates and food not in ckip_candidates:
            phrase_candidates.add(food)

    all_candidates = ner_candidates | ckip_candidates | phrase_candidates
    # print(f"[DEBUG] 所有候選詞: {all_candidates}")

    filtered_candidates = set()
    for candidate in all_candidates:
        if not any(term in candidate for term in ["湯頭", "口味", "味道", "姊姊", "服務", "店", "餐廳", "館"]):
            filtered_candidates.add(candidate)
    all_candidates = filtered_candidates
    # print(f"[DEBUG] 過濾後候選詞: {all_candidates}")

    filtered_foods = set()
    if all_candidates:
        all_candidates_list = list(all_candidates)
        z_results = zero_shot(
            all_candidates_list, 
            candidate_labels=candidate_labels,
            multi_label=False
        )
        if isinstance(z_results, dict):
            z_results = [z_results]
        core_food_keywords = ["火鍋", "壽司", "牛排", "冰淇淋", "拉麵", "燒肉", "豬排", "麵", "飯", 
                             "奶茶", "炸雞", "鹽酥雞", "椒麻雞", "蛋糕", "豆腐"] 
        for i, phrase in enumerate(all_candidates_list):
            score = z_results[i]['scores'][0]
            label = z_results[i]['labels'][0]
            if (label in candidate_labels and score > zero_shot_threshold) or \
               any(food_key in phrase for food_key in core_food_keywords):
                if not any(exclude in phrase for exclude in ["這家", "下次", "服務", "湯頭", "口味"]):
                    if not phrase.endswith("的") and not phrase.endswith("很") and not phrase.endswith("了"):
                        filtered_foods.add(phrase)

    # 回傳分析結果
    return {
        "user_id": user_id,
        "foods": list(filtered_foods),
    }