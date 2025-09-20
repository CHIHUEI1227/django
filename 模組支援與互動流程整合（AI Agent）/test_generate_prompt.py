import sys
import os
import requests
from termcolor import colored

# ✅ 設定匯入路徑：將 'agent_module' 資料夾加進來
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_module'))

# ✅ 匯入 sample_data 中的 PROMPT_TEST_INPUTS
from sample_data import PROMPT_TEST_INPUTS

# 🌐 API URL（功能三-1：模糊提示）
API_URL = "http://localhost:8000/agent/generate_prompt/"

def test_generate_prompt():
    print(colored("🎯 功能三-1：模糊語句提示 測試開始", "cyan", attrs=["bold"]))
    print("--------------------------------------------------")

    success_count = 0
    fail_count = 0
    failures = []

    for idx, item in enumerate(PROMPT_TEST_INPUTS):
        text = item["text"]
        expected_level = item["expected_level"]

        payload = {
            "type": "text",
            "text": text
        }

        try:
            response = requests.post(API_URL, json=payload)
            result = response.json()

            print(f"📝 測試 {idx + 1}: {text}")
            print("🔁 回傳狀態碼:", response.status_code)

            if result.get("status") == "success":
                data = result.get("data", {})
                actual_level = data.get("level", "")
                guidance = data.get("guidance", "")

                print(f"📎 回傳提示語句：{colored(guidance, 'cyan')}")

                if actual_level == expected_level:
                    print(colored(f"✅ 判斷正確，模糊程度：{actual_level}", "green"))
                    success_count += 1
                else:
                    print(colored("❌ 判斷錯誤", "red"))
                    print(f"   ▶ 預期：{expected_level}")
                    print(f"   ▶ 實際：{actual_level}")
                    fail_count += 1
                    failures.append(text)
            else:
                print(colored("❌ 回傳格式異常或狀態非 success", "red"))
                print("回傳內容：", result)
                fail_count += 1
                failures.append(text)

        except Exception as e:
            print(colored(f"🚨 發生錯誤：{e}", "red"))
            fail_count += 1
            failures.append(text)

        print("--------------------------------------------------")

    # 📊 統整結果
    total = success_count + fail_count
    print(colored("\n📊 測試總結", "cyan", attrs=["bold"]))
    print(colored(f"✅ 通過：{success_count} / {total}", "green"))
    print(colored(f"❌ 失敗：{fail_count} / {total}", "red" if fail_count else "green"))
    if failures:
        print(colored("⚠️  失敗項目：", "yellow"), ", ".join(failures))

if __name__ == "__main__":
    test_generate_prompt()
