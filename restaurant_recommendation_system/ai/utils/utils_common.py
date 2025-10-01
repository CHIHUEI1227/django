import re

# ✅ 文本正規化（統一清洗用）
def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    return re.sub(r"[，,。.!？?、/\\|()\[\]【】{}\-＿_~^'\"`：:；;@#*$＋+＝=．·･\s]+", "", s)
