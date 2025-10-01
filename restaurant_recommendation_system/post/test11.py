from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline

class FoodNLP:
    @classmethod
    def setUpClass(cls):
        print("載入模型中...")
        cls.ws_driver = CkipWordSegmenter(model="bert-base")
        cls.pos_driver = CkipPosTagger(model="bert-base")
        cls.zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        cls.ner = pipeline("ner", model="ckiplab/bert-base-chinese-ner", 
                           tokenizer="ckiplab/bert-base-chinese-ner", 
                           aggregation_strategy="simple")
        print("模型載入完成")

    @classmethod
    def classify_flavor(cls, text):
        # 針對食物口味分類
        candidate_labels = ["食物口味", "食物", "食物種類"]
        result = cls.zero_shot(text, candidate_labels=candidate_labels, multi_label=True)
        return result

    @classmethod
    def segment_and_pos(cls, text):
        # 斷詞與詞性標註
        ws = cls.ws_driver([text])[0]
        pos = cls.pos_driver([ws])[0]
        return ws, pos

if __name__ == "__main__":
    FoodNLP.setUpClass()
    sample = "今天點了昆布火鍋跟味噌火鍋，覺得味道還不錯，尤其是昆布湯頭很鮮甜。"
    res = FoodNLP.classify_flavor(sample)
    print("分類結果：", res)
    ws, pos = FoodNLP.segment_and_pos(sample)
    print("分詞結果：", ws)
    print("詞性標註：", pos)
    # 顯示詞與詞性對應
    print("詞與詞性：")
    for w, p in zip(ws, pos):
        print(f"{w}\t{p}")
