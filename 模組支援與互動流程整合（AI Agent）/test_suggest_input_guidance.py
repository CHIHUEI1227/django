import sys
import os
import requests
from termcolor import colored

# ✅ 匯入 sample data
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))
from sample_data import GUIDANCE_TEST_INPUTS

# 🌐 API URL（功能三-2：語意引導建議）
API_URL = "http://localhost:8000/agent/suggest_input_guidance/"

def test_suggest_input_guidance():
    print(colored("🎯 功能三-2：語意引導建議 測試開始", "cyan", attrs=["bold"]))
    print("--------------------------------------------------")

    success_count = 0
    failures = []

    for idx, item in enumerate(GUIDANCE_TEST_INPUTS):
        text = item["text"]
        expected_levels = set(item.get("expected_levels", []))
        expected_keywords = set(item.get("expected_keywords", []))

        payload = {
            "type": "text",
            "text": text
        }

        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()
            data = result.get("data", {})
            actual_levels_raw = data.get("level", [])
            guidance = data.get("guidance", "")

            print(f"📝 測試 {idx + 1}: {text}")
            print("🔁 回傳狀態碼:", response.status_code)
            print(colored(f"📎 回傳提示語句：{guidance}", "blue"))

            if result.get("status") == "success" and isinstance(actual_levels_raw, list):
                actual_levels = set(actual_levels_raw)

                # ✅ 分類比對
                level_ok = expected_levels.issubset(actual_levels)
                keyword_ok = all(keyword in guidance for keyword in expected_keywords)

                if level_ok and keyword_ok:
                    print(colored(f"✅ 判斷正確，分類：{actual_levels}，關鍵字命中：{expected_keywords}", "green"))
                    success_count += 1
                else:
                    print(colored("❌ 判斷錯誤", "red"))
                    if not level_ok:
                        print(colored("  🔸 分類比對錯誤", "yellow"))
                        print(f"     ▶ 預期：{expected_levels}")
                        print(f"     ▶ 實際：{actual_levels}")
                    if not keyword_ok:
                        print(colored("  🔸 關鍵字比對錯誤", "magenta"))
                        print(f"     ▶ 預期：{expected_keywords}")
                        print(f"     ▶ guidance 回傳：{guidance}")
                    failures.append(text)
            else:
                print(colored("❌ 回傳格式錯誤或缺少欄位", "red"))
                print("回傳內容：", result)
                failures.append(text)

        except Exception as e:
            print(colored(f"🚨 發生錯誤：{e}", "red"))
            failures.append(text)

        print("--------------------------------------------------")

    # 📊 統整結果
    total = len(GUIDANCE_TEST_INPUTS)
    fail_count = total - success_count

    print(colored("\n📊 測試總結", "cyan", attrs=["bold"]))
    print(colored(f"✅ 成功：{success_count}/{total}", "green"))
    print(colored(f"❌ 失敗：{fail_count}/{total}", "red" if fail_count else "green"))

    if failures:
        print(colored("🔍 失敗項目：", "red"))
        for fail_text in failures:
            print(f"  - {fail_text}")

if __name__ == "__main__":
    test_suggest_input_guidance()
