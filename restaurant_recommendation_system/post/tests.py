import emoji

from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from transformers import pipeline
from tqdm import tqdm
import re
from keybert import KeyBERT

if __name__ == "__main__":
    def clean_text(text):
        # 移除 emoji
        text = emoji.replace_emoji(text, replace='')
        # 可在此加入更多雜訊清理規則（如多餘空白、特殊符號等）
        text = re.sub(r'[\s]+', ' ', text)
        return text.strip()
    # 初始化模型
    ws_driver = CkipWordSegmenter(model="bert-base")
    pos_driver = CkipPosTagger(model="bert-base")
    zero_shot = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
    sentiment = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
    kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')

    print("\n====== 店家評論分析 ======")
    fake_posts = [
        "這家火鍋的湯頭很棒，服務生態度親切，價格也很合理，下次還會再來！",
        "壽司不新鮮，環境有點髒亂，服務也不太好。",
        "牛排很好吃，CP值高，推薦給大家！",
        "冰淇淋口味普通，服務速度很慢。",
        "拉麵湯頭太鹹，價格偏貴，但環境很舒適。",
        "拉麵湯頭很鹹但是我很喜歡XD",
        "拉麵湯頭很鹹，但是我很喜歡XD",
        "樓上風景很好看，點了昆布火鍋和味噌火鍋，飲料還有可以加到火鍋的菜跟醬料很多元，霜淇淋可以自己做，還有很多小料可以加，超讚👍👍，下次還要來吃😊",
        "餐點美味份量十足，主廚手藝一流，還有擺盤裝飾質感升級，希望增加一些青菜類或能單點就更完美了！",
        "肉品好吃，小菜可以一直續，cp值非常高",
        "精緻燒肉！很不錯👍",
        "像韓國人的姊姊烤肉超好吃，服務也很到位，價錢配得上品質跟服務",
        "很好吃呦～ 服務人員態度都很好～～ 很多小細節服務人員都會注意！"
    ]
    candidate_labels = ["體驗", "食物", "服務", "價格", "環境", "其他"]
    sentiment_labels = ["正面", "中立", "負面"]
    overall_keywords = ["再來", "推薦", "不會再來", "下次", "大家", "值得", "不推", "不推薦"]
    for idx, content in enumerate(tqdm(fake_posts, desc="分析店家評論")):
        print(f"\n=== 評論{idx+1} ===")
        print("原文：", content)
        sentences = re.split(r'[。！？!？，,～~]+|\\s{2,}', content)
        sentences = [s for s in sentences if s.strip()]
        ws_list = ws_driver(sentences)
        pos_list = pos_driver(ws_list)
        stopwords = set(["的", "了", "和", "可以", "還有", "很多", "自己", "到", "跟", "有", "是", "在", "要", "很", "不", "再", "會", "來", "加", "做"])
        valid_pos = set(["Na", "Nb", "Nc", "A", "V"])
        last_keywords = None
        sentence_to_keywords = []
        keyword_to_category = {}
        keyword_to_sentences = {}
        for sent, ws, pos in zip(sentences, ws_list, pos_list):
            is_summary = any(kw in sent for kw in overall_keywords)
            # CKIP 斷詞+詞性過濾+去除停用詞+長度>1
            ckip_words = [w for w, p in zip(ws, pos) if p in valid_pos and w not in stopwords and len(w) > 1]
            # KeyBERT 關鍵詞（限制長度6以內）
            keybert_keywords = [kw for kw, score in kw_model.extract_keywords(sent, top_n=2) if len(kw) <= 6]
            # 合併並去重（保留最短的關鍵詞）
            all_keywords = ckip_words + keybert_keywords
            keywords = []
            for k in all_keywords:
                if not any((k != other and k in other) for other in all_keywords):
                    keywords.append(k)
            keywords = list(dict.fromkeys(keywords))  # 去重且保留順序
            print(f"句子：「{sent}」→ 關鍵詞：{keywords}")
            if keywords:
                last_keywords = keywords
                for keyword in keywords:
                    if keyword not in keyword_to_category:
                        # summary/overall 關鍵詞直接分類為體驗
                        if any(kw in keyword for kw in overall_keywords):
                            best_label = "體驗"
                            score = 1.0
                        # 希望/建議/期望/如果能/希望能 直接分類為其他
                        elif any(x in keyword for x in ["希望", "建議", "期望", "如果能", "希望能"]):
                            best_label = "其他"
                            score = 1.0
                        elif "價格" in keyword or "貴" in keyword or "便宜" in keyword or "CP" in keyword:
                            best_label = "價格"
                            score = 1.0
                        elif any(food in keyword for food in ["小料","湯頭", "口味","飲料"]):
                            best_label = "食物"
                            score = 1.0
                        elif any(env in keyword for env in ["樓上", "風景", "裝潢", "氣氛", "環境", "地點", "位置", "空間"]):
                            best_label = "環境"
                            score = 1.0
                        elif any(srv in keyword for srv in ["細節", "人員", "態度"]):
                            best_label = "服務"
                            score = 1.0
                        else:
                            result = zero_shot(keyword, candidate_labels=candidate_labels)
                            best_label = result['labels'][0]
                            score = result['scores'][0]
                        # 如果分類為其他，則針對整句再做一次 zero-shot 分類
                        if best_label == "其他":
                            sent_result = zero_shot(sent, candidate_labels=candidate_labels)
                            sent_label = sent_result['labels'][0]
                            sent_score = sent_result['scores'][0]
                            if sent_label != "其他" and sent_score > 0.5:
                                best_label = sent_label
                                score = sent_score
                        if best_label != "其他" and score <= 0.5:
                            continue
                        keyword_to_category[keyword] = best_label
                        keyword_to_sentences.setdefault(keyword, []).append(sent)
            else:
                if last_keywords:
                    for keyword in last_keywords:
                        keyword_to_sentences.setdefault(keyword, []).append(sent)
            sentence_to_keywords.append(last_keywords)
        category_sentiments = {cat: [] for cat in candidate_labels}
        # rule-based emoji/極端詞彙情感判斷
        positive_emojis = ["😊", "👍", "XD", "😂", "😍", ":D", ":)", "^_^", "^O^", "😃", "😄", "😆", "😁", "🥰", "😋", "😎"]
        negative_emojis = ["😡", "👎", "QQ", "哭", ":(", ">:(", "T_T", "QAQ", "😢", "😞", "😠", "😣", "😖", "😔"]
        # 僅極端詞彙直接給極端分數
        positive_extreme_words = ["超讚", "超棒", "超好吃", "超滿意", "超推薦", "超喜歡", "超值"]
        negative_extreme_words = ["超爛", "超難吃", "超失望", "超糟糕", "超差", "超討厭"]
        # 一般情感詞交給模型判斷
        neutral_patterns = ["點了"]
        sentiment_words = ["好吃", "難吃", "推薦", "失望", "滿意", "討厭", "棒", "喜歡", "推", "不推", "不推薦", "不值得", "值得", "讚"]
        summary_positive = ["下次還要來吃", "下次還會再來", "還要來", "還會來", "值得", "推薦給大家"]
        weaken_words = ["有點", "稍微", "有些"]
        def has_sentiment_word(sent, sentiment_words):
            return any(w in sent for w in sentiment_words)
        for keyword, cat in keyword_to_category.items():
            # 新增：記錄每分類已加過分數的句子
            if 'cat_sent_added' not in locals():
                cat_sent_added = {c: set() for c in candidate_labels}
            first_print = True
            for sent in keyword_to_sentences.get(keyword, []):
                # 跳過：同一句話已加過該分類分數
                if sent in cat_sent_added[cat]:
                    continue
                if first_print:
                    print(f"\n  關鍵詞：{keyword}（分類：{cat}）")
                    first_print = False
                
                # emoji/極端詞彙加分或扣分
                pos_bonus = 0.2 if (any(e in sent for e in positive_emojis) or any(w in sent for w in positive_extreme_words)) else 0.0
                neg_bonus = 0.2 if (any(e in sent for e in negative_emojis) or any(w in sent for w in negative_extreme_words)) else 0.0
                # 清除 emoji 與雜訊
                sent_for_model = clean_text(sent)
                # 明顯正面 summary 關鍵詞直接給正面分數（非極端）
                if any(sp in sent_for_model for sp in summary_positive):
                    sent_label = "正面"
                    sent_score = 0.5
                # 純描述句且無情感詞，判斷為中立
                elif any(p in sent_for_model for p in neutral_patterns) and not has_sentiment_word(sent_for_model, sentiment_words):
                    sent_label = "中立"
                    sent_score = 0.0
                else:
                    sent_result = sentiment(sent_for_model, candidate_labels=sentiment_labels)
                    sent_label = sent_result['labels'][0]
                    sent_score = sent_result['scores'][0]
                # 加分或扣分
                if sent_label == "正面":
                    score_val = sent_score + pos_bonus - neg_bonus
                elif sent_label == "負面":
                    score_val = -sent_score - neg_bonus + pos_bonus
                else:
                    score_val = 0 + pos_bonus - neg_bonus
                # 語氣詞弱化調整
                if any(w in sent for w in weaken_words):
                    if sent_label == "正面":
                        score_val -= 0.35  # 正面語氣弱化
                    elif sent_label == "負面":
                        score_val += 0.35  # 負面語氣弱化
                # 分數限制在[-1, 1]
                score_val = max(min(score_val, 1.0), -1.0)

                # 轉換為1~5分制（細分區間）
                if sent_label == "負面":
                    # -1 ~ -0.5 對應 1~2分
                    if score_val <= -0.5:
                        mapped_score = 1 + (score_val + 1) * (1/0.5)  # -1~ -0.5 → 1~2
                        mapped_score = min(max(mapped_score, 1), 2)
                    else:
                        # -0.5 ~ 0 對應 2~3分
                        mapped_score = 2 + (score_val + 0.5) * (1/0.5)  # -0.5~0 → 2~3
                        mapped_score = min(max(mapped_score, 2), 3)
                elif sent_label == "中立":
                    mapped_score = 3
                else:  # 正面
                    # 0 ~ 0.5 對應 3~4分
                    if score_val <= 0.5:
                        mapped_score = 3 + score_val * (1/0.5)  # 0~0.5 → 3~4
                        mapped_score = min(max(mapped_score, 3), 4)
                    else:
                        # 0.5 ~ 1 對應 4~5分
                        mapped_score = 4 + (score_val - 0.5) * (1/0.5)  # 0.5~1 → 4~5
                        mapped_score = min(max(mapped_score, 4), 5)

                print(f"    句子：「{sent}」→ 情感：{sent_label}（原分數：{score_val:.2f}，五分制：{mapped_score:.2f}）")
                category_sentiments[cat].append(mapped_score)
                cat_sent_added[cat].add(sent)
        print("\n店家各面向評價：")
        for cat, scores in category_sentiments.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score > 3:
                    overall = "正面"
                elif avg_score == 3:
                    overall = "中立"
                else:
                    overall = "負面"
                print(f"  {cat}：平均分數 {avg_score:.2f}，總體：{overall}")