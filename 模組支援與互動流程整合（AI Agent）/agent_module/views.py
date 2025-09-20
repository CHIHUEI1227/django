# === 📦 imports ===

# 標準庫
import json
import re
import random

# Django
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# DRF
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from rest_framework.parsers import JSONParser

# 🔧 共用工具
from .utils_common import normalize_text  # ✅ 統一改從這裡匯入

# 🧩 功能一：條件分析
from .utils_semantic import extract_negative_phrases, split_conditions

# 🧠 功能四：欄位補強
from .utils_card_enhancer import enrich_restaurant_info

# 📊 功能三-1：語意分級
from .utils_prompt import analyze_prompt_level

# 🧰 功能二 & 共用
from .utils_card import (
    generate_map_url, format_open_status, generate_price_description,
    extract_district, expand_exclusions, collect_blob,
    deduplicate_semantic, uniq_keep_order, sort_reasons,
    FEATURE_REASON_MAP, STYLE_REASON_MAP, USER_INPUT_RULES
)

# 💬 功能三-2：語意引導模組
from .utils_guidance import analyze_input_guidance  # ✅ 新增這行


# 功能 1：反向推薦條件擷取（強化版 v6 - 語意補強完全命中）

class ExtractNegativeConditionsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get('type')
        user_input = request.data.get('text', '').strip()

        if req_type != 'text' or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 保留你原本的常數設計
        FUNCTION_PREFIXES = ['推薦', '餐廳', '地方', '那家', '這家', '店家', '吃', '想吃', '提供']
        TAIL_PARTICLES = r'[的了呢啦啊嘛唷喔哦耶呀囉吧]*$'
        PRESERVE_TERMS = ['吃到飽', '早午餐', '宵夜', '套餐', '內用', '外帶']
        CLEAN_SUFFIXES = ['的料理', '料理', '店家', '餐廳', '類型', '類', '那家', '這家', '店']
        EXCLUSION_WHITELIST = ['辣妹', '辣個', '辣個女生', '火辣的音樂']
        BLACKLIST_SUFFIX = ['那種', '這種']

        # ✅ 語意映射表（完全保留）
        SEMANTIC_NEGATIVE_MAP = {
            "太油": "油膩", "很油": "油膩", "油膩": "油膩", "太膩": "油膩", "吃完會膩": "油膩",
            "甜到膩": "甜膩", "太貴": "高價", "價格太高": "高價", "CP 值太低": "高價",
            "份量少又貴": "高價", "不夠飽": "份量少", "太吵": "吵雜", "很吵": "吵雜",
            "太擠": "擁擠", "不太乾淨": "不乾淨", "衛生不好": "不乾淨", "不乾淨": "不乾淨",
            "太鹹": "重口味", "太辣": "重口味", "太鹹太辣": "重口味",
            "太多醬": "醬多", "太多醬的": "醬多", "雷": "雷店", "有點雷": "雷店",
            "雷店": "雷店", "太文青": "文青風格", "這種太文青的": "文青風格",
            "網美店": "網美店", "打卡店": "網美店", "Instagram 打卡": "網美店"
        }

        excluded_items = []

        # ✅ 1. 句子匹配
        matches = extract_negative_phrases(user_input)

        # ✅ 2. 抽詞與清洗
        for phrase in matches:
            if isinstance(phrase, tuple):
                phrase = phrase[1] if len(phrase) > 1 else phrase[0]
            words = split_conditions(phrase)

            for word in words:
                if not word or word in EXCLUSION_WHITELIST or word in BLACKLIST_SUFFIX:
                    continue

                if word in PRESERVE_TERMS:
                    cleaned = word
                elif word.endswith("的") and word[:-1] in PRESERVE_TERMS:
                    cleaned = word[:-1]
                else:
                    for prefix_word in FUNCTION_PREFIXES:
                        if word.startswith(prefix_word):
                            word = word[len(prefix_word):]
                            break
                    word = re.sub(TAIL_PARTICLES, '', word)
                    for suffix in CLEAN_SUFFIXES:
                        if word.endswith(suffix) and len(word) > len(suffix):
                            word = word[:-len(suffix)]
                            break
                    cleaned = word

                if cleaned and len(cleaned) <= 6 and re.match(r'^[\u4e00-\u9fffA-Za-z0-9]+$', cleaned):
                    excluded_items.append(cleaned)

        # ✅ 3. 額外語意補強
        for phrase, keyword in SEMANTIC_NEGATIVE_MAP.items():
            if phrase in user_input and keyword not in excluded_items:
                excluded_items.append(keyword)

        # ✅ 4. 最終正規化與去重
        final_excluded = []
        for kw in excluded_items:
            normalized = SEMANTIC_NEGATIVE_MAP.get(kw, kw)
            if normalized not in final_excluded:
                final_excluded.append(normalized)

        return Response({
            "status": "success",
            "data": {
                "excluded": final_excluded
            },
            "message": "已擷取反向推薦條件"
        }, status=status.HTTP_200_OK)



# 功能 2：推薦理由補強 + 結構化輸出（強化版：去重與排序 + 保底排除閘門）
class GenerateRecommendReasonView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        import json

        DEBUG = True

        user_input = (request.data.get("user_input", "") if hasattr(request, "data") else "").lower().strip()
        req_excluded_items = (request.data.get("excluded_items", []) if hasattr(request, "data") else []) or []

        if hasattr(request, 'data'):
            req_type = request.data.get('type')
            restaurants = request.data.get('restaurants', [])
        else:
            req_type = request.POST.get('type')
            try:
                restaurants = json.loads(request.body.decode()).get("restaurants", [])
            except Exception:
                restaurants = []

        if req_type != 'restaurant_list' or not isinstance(restaurants, list):
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='restaurant_list' 且包含 restaurants 清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ========== 保底排除機制 ==========
        def extract_negatives(text: str) -> list:
            import re
            if not text:
                return []
            pattern = re.compile(
                r"(?:不想吃|不想要|不要|不吃|別推薦|不要推薦)\s*"
                r"([^\n，,。！!？?\s]+(?:(?:[、,/和與及或]|或是|[,，/ ])+[^\n，,。！!？?\s]+)*)"
            )
            m = pattern.search(text)
            if not m:
                return []
            seg = m.group(1)
            parts = re.split(r"(?:[、,/和與及或]|或是|[,，\s])+", seg)
            return [p.strip() for p in parts if p.strip()]

        extracted_from_input = extract_negatives(user_input)
        raw_excluded = list({x for x in (req_excluded_items + extracted_from_input) if x})
        expanded_ex = set(expand_exclusions(raw_excluded))

        if DEBUG:
            print("🧩 擴充後排除詞：", sorted(expanded_ex))

        filtered_restaurants = []
        debug_hits = []
        for r in restaurants:
            blob = collect_blob(r)
            hit = next((ex for ex in expanded_ex if ex in blob), None)
            if hit:
                debug_hits.append((r.get("name", ""), hit))
            else:
                filtered_restaurants.append(r)

        # fallback：若一間都沒剔除，再檢查 name
        if len(filtered_restaurants) == len(restaurants) and raw_excluded:
            tmp = []
            for r in filtered_restaurants:
                name = r.get("name", "")
                if any(x in name for x in raw_excluded):
                    debug_hits.append((name, f"fallback:{'/'.join(raw_excluded)}"))
                else:
                    tmp.append(r)
            filtered_restaurants = tmp

        if DEBUG:
            print("🔎 被排除清單/命中詞：", debug_hits)

        restaurants = filtered_restaurants
        # ==================================

        results = []
        for r in restaurants:
            name = r.get('name', '')
            address = r.get('address', '')
            rating = r.get('rating', 0)
            is_open_raw = r.get('is_open')
            price_level = r.get('price_level', '')
            review_count = r.get('review_count')
            distance_m = r.get('distance_m')
            reason_score = r.get('reason_score', 0)

            map_url = generate_map_url(name)
            is_open = format_open_status(is_open_raw)
            price_desc = generate_price_description(price_level)
            district = extract_district(address)
            distance = f"{distance_m} 公尺" if distance_m else "未知"

            highlight = r.get('highlight', '')
            matched_tags = r.get('matched_tags', [])
            features = r.get('features', [])
            style = r.get('style', '')
            opening_hours = r.get('opening_hours', '')

            ai_reason = r.get('ai_reason', '')
            comment_summary = r.get('comment_summary', '')

            # 核心推薦理由
            reason_source = "inference"
            if ai_reason:
                core_reason = ai_reason
                reason_source = "ai"
            elif comment_summary:
                core_reason = comment_summary
                reason_source = "summary"
            else:
                core_reasons = []
                if rating >= 4.5:
                    core_reasons.append("評價很高")
                if "台北" in address or "新北" in address:
                    core_reasons.append("地點方便")
                if not core_reasons:
                    core_reasons.append("整體評價不錯")
                core_reason = "、".join(core_reasons)

            # 補強推薦關鍵字
            extra_reasons = []
            if highlight:
                extra_reasons.append(highlight)
            if matched_tags:
                extra_reasons.extend(matched_tags)
            if price_desc:
                extra_reasons.append(price_desc)
            if district:
                extra_reasons.append(f"位於{district}")
            for f in features:
                if f in FEATURE_REASON_MAP:
                    extra_reasons.append(FEATURE_REASON_MAP[f])
            if style in STYLE_REASON_MAP:
                extra_reasons.append(STYLE_REASON_MAP[style])
            if opening_hours:
                if "00" in opening_hours or "02" in opening_hours:
                    extra_reasons.append("夜間營業")
                if "23" in opening_hours or "22" in opening_hours:
                    extra_reasons.append("適合宵夜")
                if "全天" in opening_hours:
                    extra_reasons.append("全天營業")
            if user_input:
                for k, v in USER_INPUT_RULES.items():
                    if k in user_input:
                        extra_reasons.append(v)

            # ✅ 語意去重 + 排序
            clean_reasons = deduplicate_semantic(extra_reasons)
            sorted_reasons = sort_reasons(clean_reasons)
            full_reason = "、".join([core_reason] + sorted_reasons)

            tags = uniq_keep_order(list(matched_tags) + list(sorted_reasons))

            results.append({
                "name": name,
                "address": address,
                "rating": rating,
                "price_level": price_level,
                "review_count": review_count,
                "highlight": highlight,
                "tags": tags,
                "matched_tags": matched_tags,
                "is_open": is_open,
                "distance": distance,
                "reason_score": reason_score,
                "map_url": map_url,
                "reason_summary": {
                    "source": reason_source,
                    "core": core_reason,
                    "extra": sorted_reasons
                },
                "recommend_reason": full_reason
            })

        sorted_results = sorted(results, key=lambda x: (
            x.get('reason_score') or 0,
            x.get('rating') or 0,
            x.get('review_count') or 0
        ), reverse=True)

        return Response({
            "status": "success",
            "data": {
                "results": sorted_results
            },
            "message": "推薦理由已產生"
        }, status=status.HTTP_200_OK)


# 功能 3-1：模糊語句提示（最終優化版）
class GeneratePromptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get("type")
        user_input = request.data.get("text", "").strip()

        if req_type != "text" or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 呼叫 utils 中的分析邏輯
        level, guidance = analyze_prompt_level(user_input)

        return Response({
            "status": "success",
            "data": {
                "level": level,
                "guidance": guidance
            },
            "message": "模糊語句提示已產生"
        }, status=status.HTTP_200_OK)

# 功能 3-2：互動式語句引導建議（使用模組版）
class SuggestInputGuidanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        req_type = request.data.get("type")
        user_input = request.data.get("text", "").lower().strip()

        if req_type != "text" or not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='text' 且包含 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        result = analyze_input_guidance(user_input)
        summary = result["summary"]
        guidance = result["guidance"]
        levels = result["level"]

        return Response({
            "status": "success",
            "data": {
                "summary": summary,
                "guidance": guidance,
                "level": levels
            },
            "message": "已產生語意引導建議"
        }, status=status.HTTP_200_OK)

# 功能 4：推薦卡片欄位模擬輸出（重構版）

class GenerateCardDataView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # ✅ 支援 JSON 格式的安全處理
        if hasattr(request, 'data'):
            req_type = request.data.get('type')
            restaurants = request.data.get('restaurants', [])
        else:
            req_type = request.POST.get('type')
            try:
                restaurants = json.loads(request.body.decode()).get("restaurants", [])
            except Exception:
                restaurants = []

        if req_type != 'restaurant_list' or not isinstance(restaurants, list):
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 type='restaurant_list' 且包含 restaurants 清單"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ 呼叫補強邏輯
        results = [enrich_restaurant_info(r) for r in restaurants]

        return Response({
            "status": "success",
            "data": {
                "results": results
            },
            "message": "卡片欄位資料已產生"
        }, status=status.HTTP_200_OK)



# ✅ 整合測試：功能一 → 四 → 二（最終強化版，一次到位）
class IntegrationTestView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]  # ✅ 支援 application/json

    def post(self, request):
        from .sample_data import RESTAURANTS_SAMPLE
        from .views import ExtractNegativeConditionsView, GenerateCardDataView, GenerateRecommendReasonView

        factory = APIRequestFactory()

        input_text = request.data.get("text", "").strip()

        # ✅ 安全布林解析：避免 "false" 仍被當成 True
        raw_allow = request.data.get("allow_backfill", True)
        if isinstance(raw_allow, str):
            allow_backfill = raw_allow.strip().lower() in ("1", "true", "t", "yes", "y", "on")
        else:
            allow_backfill = bool(raw_allow)

        if not input_text:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        print("\n🎯 整合測試開始 >>>")
        print(f"📝 使用者輸入：{input_text}")
        print(f"🧩 allow_backfill = {allow_backfill}")

        # =========================
        # ✅ Step 1：功能一（排除條件擷取）
        request_exclusion = factory.post("/fake_path/", {"text": input_text}, format='json')
        wrapped_request = Request(request_exclusion, parsers=[JSONParser()])
        exclusion_response = ExtractNegativeConditionsView().post(wrapped_request)

        if hasattr(exclusion_response, "data") and isinstance(exclusion_response.data, dict):
            exclusion_data_raw = exclusion_response.data
        elif hasattr(exclusion_response, "_data") and isinstance(exclusion_response._data, dict):
            exclusion_data_raw = exclusion_response._data
        else:
            exclusion_data_raw = {}

        excluded_items = []
        if isinstance(exclusion_data_raw, dict):
            data_field = exclusion_data_raw.get("data", {})
            if isinstance(data_field, dict):
                excluded_items = data_field.get("excluded", [])
        print(f"🚫 上游排除項目：{excluded_items}")

        # =========================
        # ✅ Step 2：進階比對排除（清理標點/全形空白 + 同義詞 + 合併欄位字串 + 二次保底 + 可控補位）
        import re

        def _normalize(s: str) -> str:
            if not isinstance(s, str):
                return ""
            s = s.strip().lower()
            # 移除常見中英標點、全形空白與符號
            s = re.sub(r"[，,。.!？?、/\\|()\[\]【】{}\-＿_~^'\"`：:；;@#*$＋+＝=．·･\s]+", "", s)
            return s

        def _expand_exclusions(items: list) -> list:
            mapping = {
                "甜點": ["甜點", "甜品", "甜食", "蛋糕", "烘焙", "下午茶", "甜點店", "甜點專門", "甜點評價高"],
                "拉麵": ["拉麵", "ramen"],
                "燒烤": ["燒烤", "烤肉", "炭火", "燒肉"],
                "漢堡": ["漢堡", "burger"],
                "美式": ["美式", "美式餐廳", "美式風格", "美式漢堡"],
                "火鍋": ["火鍋", "鍋物", "涮涮鍋", "麻辣鍋"],
            }
            expanded = set()
            for it in items or []:
                raw = (it or "").strip()
                norm = _normalize(raw)
                if not norm:
                    continue
                # 原字與正規化字都拿去 mapping 找同義詞
                candidates = set([raw, norm])
                for key, syns in mapping.items():
                    if key == raw or key == norm:
                        candidates |= set(syns)
                # 所有候選詞正規化後加入
                for c in candidates:
                    expanded.add(_normalize(c))
            return list(expanded)

        def _collect_blob(r: dict) -> str:
            # 把可能包含品類訊息的欄位合併，提升命中率
            parts = []
            for k in ["name", "highlight", "ai_reason", "comment_summary", "style", "address"]:
                v = r.get(k, "")
                if v:
                    parts.append(str(v))
            for lk in ["matched_tags", "tags", "features"]:
                seq = r.get(lk) or []
                parts.extend([str(t) for t in seq])
            return _normalize("｜".join(parts))

        expanded_ex = set(_expand_exclusions(excluded_items))
        print(f"🧩 擴充後排除詞（norm）：{sorted(expanded_ex)}")

        # 統一先生成每間餐廳的「正規化合併字串」
        normalized_blobs = [(_collect_blob(r), r) for r in RESTAURANTS_SAMPLE]

        filtered = []
        debug_hits = []
        for blob, r in normalized_blobs:
            hit = None
            for ex in expanded_ex:
                if ex and ex in blob:
                    hit = ex
                    break
            if hit:
                debug_hits.append((r.get("name", ""), hit))
            else:
                filtered.append(r)

        # 🛡️ 二次保底：若完全沒剔除，用「名稱包含原始排除詞」再過一輪
        if len(filtered) == len(RESTAURANTS_SAMPLE):
            _raw_ex = [(it or "").strip() for it in (excluded_items or []) if (it or "").strip()]
            if _raw_ex:
                tmp = []
                for r in filtered:
                    name = r.get("name", "")
                    if any(x in name for x in _raw_ex):
                        debug_hits.append((name, f"fallback:{'/'.join(_raw_ex)}"))
                    else:
                        tmp.append(r)
                filtered = tmp

        print(f"✅ 通過排除篩選的餐廳數：{len(filtered)}")
        print("🔎 被排除清單/命中詞：", debug_hits)

        # —— 補位機制（可控）——
        TARGET_N = 5
        before_fill = len(filtered)
        used_backfill_pool = False

        if allow_backfill and len(filtered) < TARGET_N:
            picked_names = set(r.get("name", "") for r in filtered)
            candidate_pool = []
            for r in RESTAURANTS_SAMPLE:
                nm = r.get("name", "")
                if nm in picked_names:
                    continue
                blob = _collect_blob(r)
                if any(ex in blob for ex in expanded_ex):
                    continue
                candidate_pool.append(r)

            # 用 rating、review_count 做排序補位
            candidate_pool.sort(
                key=lambda x: (float(x.get("rating") or 0), int(x.get("review_count") or 0)),
                reverse=True
            )
            for r in candidate_pool:
                if len(filtered) >= TARGET_N:
                    break
                nm = r.get("name", "")
                if nm not in picked_names:
                    filtered.append(r)
                    picked_names.add(nm)

        # 可選：後備名單（若仍不足 5）
        if allow_backfill and len(filtered) < TARGET_N:
            BACKFILL_POOL = [
                {
                    "name": "青蔬便當舖",
                    "address": "台北市中正區",
                    "rating": 4.3, "review_count": 210,
                    "price_level": "$", "style": "家常",
                    "features": ["價格實惠", "快速方便"],
                    "matched_tags": ["素食需求", "清爽口味"],
                    "highlight": "平價清爽",
                    "ai_reason": "平價清爽、便當選擇多，適合快速用餐",
                },
                {
                    "name": "小巷清粥店",
                    "address": "台北市大同區",
                    "rating": 4.2, "review_count": 180,
                    "price_level": "$", "style": "傳統",
                    "features": ["清爽口味", "親子友善"],
                    "matched_tags": ["清爽口味"],
                    "highlight": "清粥小菜",
                    "ai_reason": "口味清爽、適合帶長輩，餐點選擇多",
                },
                {
                    "name": "南洋米線館",
                    "address": "台北市萬華區",
                    "rating": 4.4, "review_count": 260,
                    "price_level": "$$", "style": "東南亞風",
                    "features": ["價格實惠", "高 CP 值"],
                    "matched_tags": ["東南亞風格", "價格實惠"],
                    "highlight": "異國風味",
                    "ai_reason": "東南亞風味、份量充足、價格實惠",
                },
            ]
            picked_names = set(r.get("name", "") for r in filtered)
            safe_backfills = []
            for r in BACKFILL_POOL:
                if r["name"] in picked_names:
                    continue
                blob = _collect_blob(r)
                if any(ex in blob for ex in expanded_ex):
                    continue
                safe_backfills.append(r)

            safe_backfills.sort(
                key=lambda x: (float(x.get("rating") or 0), int(x.get("review_count") or 0)),
                reverse=True
            )
            for r in safe_backfills:
                if len(filtered) >= TARGET_N:
                    break
                filtered.append(r)
                picked_names.add(r.get("name", ""))
                used_backfill_pool = True

        if allow_backfill:
            print(
                f"📌 補位後的餐廳數：{len(filtered)}（目標 {TARGET_N}）；"
                f"來源：{'BACKFILL_POOL' if used_backfill_pool else ('RESTAURANTS_SAMPLE' if len(filtered) > before_fill else '無')}"
            )

        # =========================
        # ✅ Step 3：功能四（欄位補強）
        request_card_data = factory.post("/fake_path/", {
            "type": "restaurant_list",
            "restaurants": filtered
        }, format='json')
        wrapped_card_request = Request(request_card_data, parsers=[JSONParser()])
        card_data_response = GenerateCardDataView().post(wrapped_card_request)

        if hasattr(card_data_response, "data") and isinstance(card_data_response.data, dict):
            card_data_raw = card_data_response.data
        elif hasattr(card_data_response, "_data") and isinstance(card_data_response._data, dict):
            card_data_raw = card_data_response._data
        else:
            card_data_raw = {}

        card_restaurants = card_data_raw.get("data", {}).get("results", [])
        print(f"📦 補完欄位的餐廳數：{len(card_restaurants)}")

        # =========================
        # ✅ Step 4：功能二（推薦理由補強 + 保底排除）
        request_reason = factory.post("/fake_path/", {
            "type": "restaurant_list",
            "restaurants": card_restaurants,
            "user_input": input_text,
            "excluded_items": excluded_items,   # ⭐ 關鍵：把上游排除詞傳下去
        }, format='json')
        wrapped_reason_request = Request(request_reason, parsers=[JSONParser()])
        final_response = GenerateRecommendReasonView().post(wrapped_reason_request)

        if hasattr(final_response, "data") and isinstance(final_response.data, dict):
            final_data_raw = final_response.data
        elif hasattr(final_response, "_data") and isinstance(final_response._data, dict):
            final_data_raw = final_response._data
        else:
            final_data_raw = {}

        # 正確計算最終筆數（results 是 list）
        results_list = final_data_raw.get("data", {}).get("results", [])
        print(f"🌟 最終推薦結果筆數：{len(results_list) if isinstance(results_list, list) else 0}")

        # ✅ 回傳結構：維持你原本風格，外加把 excluded_items 一起回傳，方便測試印出或驗證
        return Response({
            "status": "success",
            "data": final_data_raw.get("data", {}),
            "excluded_items": excluded_items,
            "message": "整合流程已執行完成"
        }, status=status.HTTP_200_OK)

