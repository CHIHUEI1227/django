def parse_emotion_from_text(text):
    emotion_keywords = {
        "開心": ["開心", "快樂", "療癒", "幸福", "喜悅", "興奮", "愉快"],
        "放鬆": ["放鬆", "悠閒", "舒服", "輕鬆", "自在"],
        "解壓": ["壓力", "解壓", "需要放鬆", "煩悶"],
        "慶祝": ["慶祝", "聚餐", "節日", "生日", "派對"],
        "溫暖": ["溫暖", "暖", "熱呼呼", "溫馨"],
        "難過": ["難過", "傷心", "失落", "沮喪", "哭泣", "憂傷"],
        "生氣": ["生氣", "憤怒", "不滿", "氣憤", "激動"],
        "焦慮": ["焦慮", "緊張", "擔心", "不安", "煩躁"],
        "疲倦": ["累", "疲倦", "無力", "倦怠"],
        "孤單": ["孤單", "寂寞", "孤獨", "想念"],
        "驚訝": ["驚訝", "震驚", "意外", "嚇到"],
    }

    detected_emotions = []

    for emotion, keywords in emotion_keywords.items():
        if any(word in text for word in keywords):
            detected_emotions.append(emotion)

    if detected_emotions:
        return detected_emotions
    else:
        return ["一般"]  # 預設為一般狀態