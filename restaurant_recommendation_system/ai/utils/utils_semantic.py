import re
from .utils_common import normalize_text

# ✅ 分割句子中的否定條件句群
def extract_negative_phrases(user_input: str) -> list[str]:
    prefix = r'(?:我|不過|那就|可能)?'
    negative_verbs = r'(不想吃|不想要|不要|不吃|別推薦|不要推薦|不太想吃|沒有很喜歡|那種我不愛|不會選|不太喜歡|不喜歡|不愛|我不會選|不考慮|無法接受)'
    pattern = rf'{prefix}{negative_verbs}(.+?)(?:[，。!！,\.\s]|$)'
    matches = re.findall(pattern, user_input)
    return matches

# ✅ 分割詞句成多個條件詞
def split_conditions(phrase: str) -> list[str]:
    return [w.strip() for w in re.split(r'[,、，和跟以及或還有\s]+', phrase) if w.strip()]
