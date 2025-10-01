from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline
from tqdm import tqdm
from collections import Counter
import re
import time
from keybert import KeyBERT

class CKIPTransformersTests:
    @classmethod
    def setUpClass(cls):
        print("載入模型中...")
        start_time = time.time()
        cls.ws_driver = CkipWordSegmenter(model="bert-base")
        cls.pos_driver = CkipPosTagger(model="bert-base")
        cls.zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        cls.ner = pipeline("ner", model="ckiplab/bert-base-chinese-ner", 
                           tokenizer="ckiplab/bert-base-chinese-ner", 
                           aggregation_strategy="simple")
        cls.kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')
        print(f"模型載入完成，耗時 {time.time() - start_time:.2f} 秒")

    def test_fake_post_analysis(self):
        total_start_time = time.time()
        fake_posts = [
            "今天點了昆布火鍋和味噌火鍋，覺得都很好吃。",
            "這家牛肉麵湯頭很濃郁，牛肉也很嫩。",
            "抹茶蛋糕和紅豆餅都很推薦！",
            "這家餐廳的CP值很高，服務態度也很好"
        ]
        candidate_labels = ["食物"]
        # 常見停用詞與助詞
        stop_pos = {"SHI", "DE", "DER", "SP", "T", "P", "C", "D", "Ba", "BEI", "SB", "LB"}
        stop_words = set(["的", "了", "也", "很", "和", "都", "在", "是", "有", "與", "及", "與", "或", "而", "被", "把", "讓", "給", "對", "著", "於", "並", "還", "就", "但", "呢", "嗎", "啊", "吧", "啦", "喔", "哦", "呀", "嘛", "呢"])
        for idx, content in enumerate(fake_posts):
            print(f"\n=== 貼文{idx+1} ===")
            print("原文：", content)
            # CKIP 斷詞+詞性標註
            ws = self.ws_driver([content])[0]
            pos = self.pos_driver([ws])[0]
            # 過濾助詞/停用詞
            ckip_terms = [w for w, p in zip(ws, pos) if p not in stop_pos and w not in stop_words and re.match(r'^[\u4e00-\u9fa5A-Za-z0-9]+$', w)]
            print("CKIP斷詞(過濾後)：", ckip_terms)
            # KeyBERT 語意片語
            keybert_phrases = [kw for kw, score in self.kw_model.extract_keywords(content, top_n=5) if len(kw) <= 6]
            print("KeyBERT關鍵詞：", keybert_phrases)
            # 合併去重，保留最有意義片語
            merged = set(ckip_terms)
            for phrase in keybert_phrases:
                # 如果片語包含於 merged 中的多個單詞，則移除這些單詞
                parts = [w for w in ckip_terms if w in phrase and w != phrase]
                if len(parts) > 1:
                    merged -= set(parts)
                merged.add(phrase)
            # 再次去重，避免單詞被片語覆蓋
            final_terms = []
            for term in merged:
                if not any(term != t and term in t for t in merged):
                    final_terms.append(term)
            print("合併後片語：", final_terms)
            # zero-shot 分類
            for kw in final_terms:
                result = self.zero_shot(kw, candidate_labels=candidate_labels)
                print(f"  片語：{kw} → 分類：{result['labels'][0]} (信心分數: {result['scores'][0]:.2f})")
        print(f"\n分析完成，總耗時: {time.time() - total_start_time:.2f} 秒\n")

if __name__ == "__main__":
    print("==== 食物實體專用 Pipeline 啟動中 ====\n")
    start_time = time.time()
    CKIPTransformersTests.setUpClass()
    tester = CKIPTransformersTests()
    tester.test_fake_post_analysis()
    print(f"\n==== 分析完成，總執行時間: {time.time() - start_time:.2f} 秒 ====\n")