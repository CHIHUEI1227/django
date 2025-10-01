from datetime import datetime

def get_current_context_info():
    now = datetime.now()
    current_hour = now.hour
    weekday = now.weekday()  # 0 = Monday, 6 = Sunday

    # 時段判斷
    if 6 <= current_hour < 11:
        meal_time = "早餐"
    elif 11 <= current_hour < 14:
        meal_time = "午餐"
    elif 14 <= current_hour < 17:
        meal_time = "下午茶"
    elif 17 <= current_hour < 21:
        meal_time = "晚餐"
    elif 21 <= current_hour < 24:
        meal_time = "宵夜"
    else:
        # 凌晨0點到6點
        meal_time = "深夜"

    # 平日 / 週末
    day_type = "週末" if weekday >= 5 else "平日"

    # 常見台灣節日（國曆）
    holidays = {
        "01-01": "元旦",
        "02-14": "西洋情人節",
        "02-28": "和平紀念日",
        "04-04": "兒童節",
        "04-05": "清明節",  # 若清明節不同年份有不同日期可手動調整
        "05-01": "勞動節",
        "08-08": "父親節",
        "09-28": "教師節",
        "10-10": "國慶日",
        "12-25": "聖誕節"
    }

    # 可手動依年份增補農曆節日國曆日期，如中秋、端午（以下為範例）
    holidays.update({
        "06-05": "端午節",    # 2025年端午
        "09-06": "中秋節",    # 2025年中秋
    })

    today_mm_dd = now.strftime("%m-%d")
    holiday = holidays.get(today_mm_dd, None)

    return {
        "meal_time": meal_time,
        "day_type": day_type,
        "holiday": holiday
    }

if __name__ == "__main__":
    context = get_current_context_info()
    print(context)