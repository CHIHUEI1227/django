"""
Google Gemini API 工具類，用於處理自然語言生成任務
"""

import os
from typing import List, Dict, Any
import google.generativeai as genai
from .api_keys import GEMINI_API_KEY

class GeminiAPI:
    """Google Gemini API 工具類"""
    
    def __init__(self, api_key: str = GEMINI_API_KEY):
        self.api_key = api_key if api_key else os.environ.get("GEMINI_API_KEY", "")
        genai.configure(api_key=self.api_key)
        # 只使用Gemini 2.0 Flash模型
        self.model_name = 'gemini-2.0-flash'
        self.model = genai.GenerativeModel(self.model_name)
    
    def get_completion(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        使用Gemini API獲取回應
        
        參數:
            messages: 消息列表，格式與OpenAI兼容
            
        返回:
            包含生成回應的字典
        """
        try:
            # 轉換格式，從OpenAI格式轉為Gemini格式
            gemini_messages = []
            for message in messages:
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role == "system":
                    # Gemini沒有system角色，將system消息作為用戶消息加入
                    gemini_messages.append({"role": "user", "parts": [content]})
                    gemini_messages.append({"role": "model", "parts": ["我明白了，我會遵循這些指示。"]})
                elif role == "user":
                    gemini_messages.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    gemini_messages.append({"role": "model", "parts": [content]})
            
            try:
                # 如果是空對話或只有system消息，直接傳入內容
                if not gemini_messages or (len(gemini_messages) == 2 and gemini_messages[0]["role"] == "user" and gemini_messages[1]["role"] == "model"):
                    response = self.model.generate_content(messages[0]["content"])
                else:
                    # 使用聊天歷史
                    chat = self.model.start_chat(history=gemini_messages[:-1])
                    response = chat.send_message(gemini_messages[-1]["parts"][0])
                
                # 將Gemini響應轉換為與OpenAI相容的格式
                return {
                    "choices": [
                        {
                            "message": {
                                "content": response.text
                            }
                        }
                    ]
                }
            except Exception as e:
                print(f"Gemini API 調用出錯: {str(e)}")
                return {"choices": [{"message": {"content": f"很抱歉，處理您的請求時出錯: {str(e)}"}}]}
        except Exception as e:
            print(f"Gemini API 調用出錯: {str(e)}")
            return {"choices": [{"message": {"content": f"很抱歉，處理您的請求時出錯: {str(e)}"}}]} 