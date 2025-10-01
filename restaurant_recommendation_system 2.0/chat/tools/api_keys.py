"""
API密鑰管理模組，集中存放所有外部API的密鑰
"""

import os

# API 密鑰設置
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_CX_ID = os.environ.get("GOOGLE_CX_ID", "")
GPT_API_KEY = os.environ.get("GPT_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") 