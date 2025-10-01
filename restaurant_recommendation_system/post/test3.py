from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline
from tqdm import tqdm
import re
from keybert import KeyBERT

class RestaurantAnalysisSystem:
    @classmethod
    def setUpClass(cls):
        # CKIP 斷詞、詞性
        cls.ws_driver = CkipWordSegmenter(model="bert-base")
        cls.pos_driver = CkipPosTagger(model="bert-base")
        # Zero-shot 分類模型（支援繁體中文）
        cls.zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        # 三分類情感分析模型
        cls.sentiment = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        # KeyBERT 關鍵詞抽取模型
        cls.kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')

    def analyze_restaurant_reviews(self):
        """店家評論分析：針對餐廳整體服務、環境、價格等多面向評價"""
        print("\n====== 店家評論分析 ======")
        
        fake_posts = [
            "這家火鍋的湯頭很棒，服務生態度親切，價格也很合理，下次還會再來！",
            "壽司不新鮮，環境有點髒亂，服務也不太好。",
            "牛排很好吃，CP值高，推薦給大家！",
            "冰淇淋口味普通，服務速度很慢。",
            "拉麵湯頭太鹹，價格偏貴，但環境很舒適。",
            "拉麵湯頭很鹹但是我很喜歡XD",
            "拉麵湯頭很鹹，但是我很喜歡XD",
        ]
        
        # 使用「其他」分類
        candidate_labels = ["食物", "服務", "價格", "環境", "其他"]
        sentiment_labels = ["正面", "中立", "負面"]

        # 總結性質的關鍵詞
        overall_keywords = ["再來", "推薦", "不會再來", "下次", "大家", "值得", "不推", "不推薦"]

        for idx, content in enumerate(tqdm(fake_posts, desc="分析店家評論")):
            print(f"\n=== 評論{idx+1} ===")
            print("原文：", content)

            # 斷句，包含逗號
            sentences = re.split(r'[。！？!？，,]', content)
            sentences = [s for s in sentences if s.strip()]

            # 斷詞與詞性標註
            ws_list = self.ws_driver(sentences)
            pos_list = self.pos_driver(ws_list)

            last_keywords = None
            sentence_to_keywords = []
            keyword_to_category = {}
            keyword_to_sentences = {}

            for sent, ws, pos in zip(sentences, ws_list, pos_list):
                # 判斷是否為總結句
                is_summary = any(kw in sent for kw in overall_keywords)
                
                # 抽取關鍵詞（top 1~2）
                keywords = [kw for kw, score in self.kw_model.extract_keywords(sent, top_n=2)]
                print(f"句子：「{sent}」→ 關鍵詞：{keywords}")
                if keywords:
                    last_keywords = keywords
                    for keyword in keywords:
                        if keyword not in keyword_to_category:
                            # 若為總結句，直接分類為「其他」
                            if is_summary:
                                best_label = "其他"
                                score = 1.0
                            else:
                                result = self.zero_shot(keyword, candidate_labels=candidate_labels)
                                best_label = result['labels'][0]
                                score = result['scores'][0]
                            
                            # 特定關鍵詞分類規則
                            if "價格" in keyword or "貴" in keyword or "便宜" in keyword or "CP" in keyword:
                                best_label = "價格"
                                score = 1.0
                            
                            if any(food in keyword for food in ["湯頭", "口味", "牛排", "拉麵", "冰淇淋", "壽司"]):
                                best_label = "食物"
                                score = 1.0
                                
                            if best_label != "其他" and score <= 0.5:
                                continue
                            keyword_to_category[keyword] = best_label
                            keyword_to_sentences.setdefault(keyword, []).append(sent)
                else:
                    # 無關鍵詞，補述上一個關鍵詞
                    if last_keywords:
                        for keyword in last_keywords:
                            keyword_to_sentences.setdefault(keyword, []).append(sent)
                sentence_to_keywords.append(last_keywords)

            # 每個分類的情感分數累加
            category_sentiments = {cat: [] for cat in candidate_labels}

            # 針對每個關鍵詞的情感分析
            for keyword, cat in keyword_to_category.items():
                print(f"\n  關鍵詞：{keyword}（分類：{cat}）")
                for sent in keyword_to_sentences.get(keyword, []):
                    sent_result = self.sentiment(sent, candidate_labels=sentiment_labels)
                    sent_label = sent_result['labels'][0]
                    sent_score = sent_result['scores'][0]
                    print(f"    句子：「{sent}」→ 情感：{sent_label}（分數：{sent_score:.2f}）")
                    # 轉換為分數：正面+1，中立0，負面-1
                    if sent_label == "正面":
                        score_val = sent_score
                    elif sent_label == "負面":
                        score_val = -sent_score
                    else:
                        score_val = 0
                    category_sentiments[cat].append(score_val)

            # 顯示各分類情感加總結果
            print("\n店家各面向評價：")
            for cat, scores in category_sentiments.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    if avg_score > 0.2:
                        overall = "正面"
                    elif avg_score < -0.2:
                        overall = "負面"
                    else:
                        overall = "中立"
                    print(f"  {cat}：平均分數 {avg_score:.2f}，總體：{overall}")

    def analyze_user_preferences(self):
        """使用者偏好分析：針對食物評論提取主要偏好"""
        print("\n====== 使用者食物偏好分析 ======")
        
        fake_posts = [
            "這家火鍋的湯頭很棒，服務生態度親切，價格也很合理，下次還會再來！",
            "壽司不新鮮，環境有點髒亂，服務也不太好。",
            "牛排很好吃，CP值高，推薦給大家！",
            "冰淇淋口味普通，服務速度很慢。",
            "拉麵湯頭太鹹，價格偏貴，但環境很舒適。",
            "拉麵湯頭很鹹但是我很喜歡XD",
            "拉麵湯頭很鹹，但是我很喜歡XD",
        ]
        candidate_labels = ["食物", "服務", "價格", "環境", "其他"]
        sentiment_labels = ["正面", "中立", "負面"]
        turn_words = ["但是", "但", "可是", "不過"]
        
        # 使用者食物偏好彙整
        food_preferences = {}

        for idx, content in enumerate(tqdm(fake_posts, desc="分析使用者偏好")):
            print(f"\n=== 評論{idx+1} ===")
            print("原文：", content)

            # 只用句號、驚嘆號、問號斷句，保留逗號內部子句
            sentences = re.split(r'[。！？!？]', content)
            sentences = [s for s in sentences if s.strip()]

            last_food_noun = None

            for sent in sentences:
                # 先用逗號切分子句
                sub_sentences = re.split(r'[，,]', sent)
                for sub_sent in sub_sentences:
                    if not sub_sent.strip():
                        continue
                    
                    # 處理以轉折詞開頭的子句
                    starts_with_turn = False
                    for turn in turn_words:
                        if sub_sent.strip().startswith(turn):
                            starts_with_turn = True
                            if last_food_noun:
                                turn_clause = sub_sent.replace(turn, "").strip()
                                ws_turn = self.ws_driver([turn_clause])[0]
                                pos_turn = self.pos_driver([ws_turn])[0]
                                noun_candidates_turn = [w for w, p in zip(ws_turn, pos_turn) if p.startswith("N")]
                                has_food_noun_turn = False
                                has_other_noun_turn = False
                                for noun in noun_candidates_turn:
                                    result = self.zero_shot(noun, candidate_labels=candidate_labels)
                                    best_label = result['labels'][0]
                                    score = result['scores'][0]
                                    if best_label == "食物" and score > 0.5:
                                        has_food_noun_turn = True
                                    elif best_label != "食物" and score > 0.5:
                                        has_other_noun_turn = True
                                        
                                # 處理轉折後情感
                                if not has_food_noun_turn and not has_other_noun_turn:
                                    sent_result = self.sentiment(turn_clause, candidate_labels=sentiment_labels)
                                    sent_label = sent_result['labels'][0]
                                    sent_score = sent_result['scores'][0]
                                    print(f"句子：「{sub_sent}」→ 食物主題詞：{last_food_noun}")
                                    print(f"    主要情感（以轉折後為主）：{sent_label}（分數：{sent_score:.2f}）")
                                    
                                    # 更新食物偏好
                                    if last_food_noun not in food_preferences:
                                        food_preferences[last_food_noun] = []
                                    food_preferences[last_food_noun].append((sent_label, sent_score))
                            break
                            
                    if starts_with_turn:
                        continue
                        
                    # 處理中間有轉折詞的子句
                    if any(w in sub_sent for w in turn_words):
                        sub_sents = re.split(r'(但是|但|可是|不過)', sub_sent)
                        if len(sub_sents) > 1:
                            main_clause = ''.join(sub_sents[:-2]).strip() if len(sub_sents) > 2 else sub_sents[0].strip()
                            turn_clause = sub_sents[-1].strip()
                            if not main_clause or not turn_clause:
                                continue
                                
                            # 找主句的食物主題詞
                            ws_main = self.ws_driver([main_clause])[0]
                            pos_main = self.pos_driver([ws_main])[0]
                            noun_candidates_main = [w for w, p in zip(ws_main, pos_main) if p.startswith("N")]
                            food_noun = None
                            for noun in noun_candidates_main:
                                result = self.zero_shot(noun, candidate_labels=candidate_labels)
                                best_label = result['labels'][0]
                                score = result['scores'][0]
                                if best_label == "食物" and score > 0.5:
                                    food_noun = noun
                                    last_food_noun = food_noun
                                    break
                                    
                            # 判斷轉折後子句是否有自己的主題詞
                            ws_turn = self.ws_driver([turn_clause])[0]
                            pos_turn = self.pos_driver([ws_turn])[0]
                            noun_candidates_turn = [w for w, p in zip(ws_turn, pos_turn) if p.startswith("N")]
                            has_food_noun_turn = False
                            has_other_noun_turn = False
                            for noun in noun_candidates_turn:
                                result = self.zero_shot(noun, candidate_labels=candidate_labels)
                                best_label = result['labels'][0]
                                score = result['scores'][0]
                                if best_label == "食物" and score > 0.5:
                                    has_food_noun_turn = True
                                elif best_label != "食物" and score > 0.5:
                                    has_other_noun_turn = True
                                    
                            # 處理轉折後情感
                            if food_noun and not has_food_noun_turn and not has_other_noun_turn:
                                sent_result = self.sentiment(turn_clause, candidate_labels=sentiment_labels)
                                sent_label = sent_result['labels'][0]
                                sent_score = sent_result['scores'][0]
                                print(f"句子：「{sub_sent}」→ 食物主題詞：{food_noun}")
                                print(f"    主要情感（以轉折後為主）：{sent_label}（分數：{sent_score:.2f}）")
                                
                                # 更新食物偏好
                                if food_noun not in food_preferences:
                                    food_preferences[food_noun] = []
                                food_preferences[food_noun].append((sent_label, sent_score))
                        continue
                        
                    # 普通子句處理
                    main_clause = sub_sent.strip()
                    ws_main = self.ws_driver([main_clause])[0]
                    pos_main = self.pos_driver([ws_main])[0]
                    noun_candidates = [w for w, p in zip(ws_main, pos_main) if p.startswith("N")]
                    food_noun = None
                    for noun in noun_candidates:
                        result = self.zero_shot(noun, candidate_labels=candidate_labels)
                        best_label = result['labels'][0]
                        score = result['scores'][0]
                        if best_label == "食物" and score > 0.5:
                            food_noun = noun
                            break
                    if food_noun:
                        sent_result = self.sentiment(sub_sent, candidate_labels=sentiment_labels)
                        sent_label = sent_result['labels'][0]
                        sent_score = sent_result['scores'][0]
                        print(f"句子：「{sub_sent}」→ 食物主題詞：{food_noun}")
                        print(f"    主要情感：{sent_label}（分數：{sent_score:.2f}）")
                        last_food_noun = food_noun
                        
                        # 更新食物偏好
                        if food_noun not in food_preferences:
                            food_preferences[food_noun] = []
                        food_preferences[food_noun].append((sent_label, sent_score))

        # 總結使用者食物偏好
        print("\n使用者食物偏好彙整：")
        for food, sentiments in food_preferences.items():
            positive = [score for label, score in sentiments if label == "正面"]
            neutral = [score for label, score in sentiments if label == "中立"]
            negative = [score for label, score in sentiments if label == "負面"]
            
            avg_score = 0
            if positive:
                avg_score += sum(positive)
            if negative:
                avg_score -= sum(negative)
            if sentiments:
                avg_score /= len(sentiments)
                
            if avg_score > 0.2:
                preference = "喜歡"
            elif avg_score < -0.2:
                preference = "不喜歡"
            else:
                preference = "中立"
                
            print(f"  {food}：整體評價 {avg_score:.2f}，使用者{preference}此食物")


if __name__ == "__main__":
    # 初始化系統
    system = RestaurantAnalysisSystem()
    RestaurantAnalysisSystem.setUpClass()
    
    # 分析店家評論
    system.analyze_restaurant_reviews()
    
    # 分析使用者偏好
    system.analyze_user_preferences()