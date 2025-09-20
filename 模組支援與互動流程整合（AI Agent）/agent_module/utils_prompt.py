# agent_module/utils_prompt.py

# ✅ 模糊語句依照程度分類（可擴充）
VAGUE_PATTERNS = {
    "vague": [
        "隨便", "你決定", "沒靈感", "我想不到", "想破頭", "隨你", 
        "你挑", "你幫我決定", "交給你", "你說了算", "你來選", 
        "都行都可以", "怎樣都可以", "反正我都可以", "你有推薦就好"
    ],
    "medium": [
        "不知道", "不清楚", "都可以", "無所謂", "沒差", "我沒差", "我無所謂", "你看著辦", "你幫我選",
        "再說吧", "看心情", "看著辦", "可以啊都行", "沒關係", "你選吧", "怎樣都行", 
        "你決定好了", "不知道耶", "你來幫我看", "你安排一下", "其實我不太清楚",
        "我真的不知道", "要不你看看", "你幫我選，我無所謂"
    ],
    "slight": [
        "沒想法", "還沒想好", "沒特別想吃", "還不知道吃什麼", "需要想一下", "再看看", "再想想",
        "不確定要吃什麼", "還沒決定", "我再想想", "等一下再說", "可能要想一下", "我再看看",
        "我有點難選", "在猶豫", "我有點猶豫", "等一下再決定", "我現在還不太確定","我現在有點難選"

    ]
}



# ✅ 對應的引導語（可獨立管理）
GUIDANCE_BY_LEVEL = {
    "clear": "歡迎告訴我們今天想吃什麼，或也可以提供不想吃的類型，我們會幫你挑選適合的餐廳！",
    "slight": "今天想吃點簡單的還是來點特別的呢？幾個方向幫你發想一下～",
    "medium": "那你偏好什麼類型？或有不喜歡的料理嗎？我們可以幫你排除一部分喔！",
    "vague": "可以先從『不想吃什麼』開始講起唷～像是不吃辣、不吃炸物之類的都可以說出來！"
}

# ✅ 模糊程度分析主函式（順序修正：slight → medium → vague）
def analyze_prompt_level(user_input: str) -> tuple[str, str]:
    user_input = user_input.strip().lower()

    matched_level = None

    # 改成從所有關鍵字中找最模糊的那個
    for level in ["vague", "medium", "slight"]:
        for keyword in VAGUE_PATTERNS[level]:
            if keyword in user_input:
                matched_level = level
                break  # 先命中此等級，不急著 return，繼續找更模糊的
        if matched_level == "vague":
            break  # 最模糊的等級已命中就直接停

    if matched_level:
        return matched_level, GUIDANCE_BY_LEVEL[matched_level]

    return "clear", GUIDANCE_BY_LEVEL["clear"]

