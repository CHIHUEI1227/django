
# ====== 集中管理模型初始化與 pipeline ======
import emoji
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline
from keybert import KeyBERT

# 全域模型初始化（只初始化一次，供全專案 import 使用）
ws_driver = CkipWordSegmenter(model="bert-base")
pos_driver = CkipPosTagger(model="bert-base")
zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
sentiment = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')
ner = pipeline("ner", model="ckiplab/bert-base-chinese-ner", tokenizer="ckiplab/bert-base-chinese-ner", aggregation_strategy="simple")
