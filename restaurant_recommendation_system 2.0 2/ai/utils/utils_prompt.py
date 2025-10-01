# ✅ 模糊語句依照程度分類（可擴充）
VAGUE_PATTERNS = {
    "vague": [
        "隨便", "你決定", "不知道", "不清楚", "沒意見", "沒想吃的", "不知道吃什麼", "不確定", "沒靈感", "隨你"
    ],
    "medium": [
        "都可以", "無所謂", "你看著辦", "你幫我選", "再說吧", "看心情", "看著辦", "可以啊都行", "沒關係"
    ],
    "slight": [
        "沒想法", "還沒想好", "沒特別想吃", "還不知道吃什麼", "需要想一下", "再看看", "再想想"
    ]
}

# ✅ 對應的引導語（可獨立管理）
GUIDANCE_BY_LEVEL = {
    "clear": "歡迎告訴我們今天想吃什麼，或也可以提供不想吃的類型，我們會幫你挑選適合的餐廳！",
    "slight": "今天想吃點簡單的還是來點特別的呢？幾個方向幫你發想一下～",
    "medium": "那你偏好什麼類型？或有不喜歡的料理嗎？我們可以幫你排除一部分喔！",
    "vague": "可以先從『不想吃什麼』開始講起唷～像是不吃辣、不吃炸物之類的都可以說出來！"
}

# ✅ 模糊程度分析主函式
def analyze_prompt_level(user_input: str) -> tuple[str, str]:
    user_input = user_input.strip().lower()

    for level in ["vague", "medium", "slight"]:
        keywords = VAGUE_PATTERNS[level]
        if any(k in user_input for k in keywords):
            return level, GUIDANCE_BY_LEVEL[level]

    return "clear", GUIDANCE_BY_LEVEL["clear"]
