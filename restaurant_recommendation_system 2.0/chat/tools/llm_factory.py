"""
LLM 工廠類，用於創建不同大型語言模型的實例
"""

from typing import Any
from .gpt_api import GPTAPI
from .gemini_api import GeminiAPI

class LLMFactory:
    """LLM工廠類，用於創建指定類型的LLM實例"""
    
    @staticmethod
    def create_llm(llm_type: str = None) -> Any:
        """
        創建LLM實例
        
        參數:
            llm_type: LLM類型，可選值: 'gpt', 'gemini'
                     如果為None，使用設置中的默認值
            
        返回:
            LLM實例，支持相同的接口
        """
        from django.conf import settings
        
        # 如果未指定，使用默認設置
        if llm_type is None:
            llm_type = getattr(settings, 'DEFAULT_LLM', 'gemini-2.0-flash')
        
        if llm_type.lower() == 'gpt':
            return GPTAPI()
        else:
            # 默認返回Gemini API (2.0 Flash)
            return GeminiAPI() 