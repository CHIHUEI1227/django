import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from torch.nn.functional import softmax

class LLMInferenceService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LLMInferenceService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, 
                 iree_model_name="hfl/chinese-roberta-wwm-ext", 
                 iree_num_labels=2, 
                 iree_model_path="./fine_tuned_llm_model", # Path to your fine-tuned IREE model
                 rrg_model_name="uer/t5-v1_1-base-chinese-cluecorpussmall", # Example for RRG, needs fine-tuning
                 rrg_model_path=None # Path to your fine-tuned RRG model
                ):
        if self._initialized:
            return
        
        print("Initializing LLM Inference Service...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # IREE Model (Intent Recognition and Entity Extraction)
        print(f"Loading IREE model: {iree_model_name} from {iree_model_path} to {self.device}")
        self.iree_tokenizer = AutoTokenizer.from_pretrained(iree_model_name)
        if iree_model_path and os.path.exists(iree_model_path):
            self.iree_model = AutoModelForSequenceClassification.from_pretrained(iree_model_path)
        else:
            # Fallback to pre-trained if fine-tuned model not found (for demonstration)
            print(f"IREE fine-tuned model not found at {iree_model_path}, loading pre-trained {iree_model_name}")
            self.iree_model = AutoModelForSequenceClassification.from_pretrained(iree_model_name, num_labels=iree_num_labels)
        self.iree_model.to(self.device)
        self.iree_model.eval()
        self.iree_num_labels = iree_num_labels
        self.iree_labels = ["general_intent", "negative_preference"] # Example labels

        # RRG Model (Recommendation Reason Generation)
        # For RRG, a Seq2Seq model like T5 or BART is more suitable.
        # This part is a placeholder and would require significant fine-tuning data.
        print(f"Loading RRG model: {rrg_model_name} to {self.device}")
        self.rrg_tokenizer = AutoTokenizer.from_pretrained(rrg_model_name)
        if rrg_model_path and os.path.exists(rrg_model_path):
            self.rrg_model = AutoModelForSeq2SeqLM.from_pretrained(rrg_model_path)
        else:
            print(f"RRG fine-tuned model not found at {rrg_model_path}, loading pre-trained {rrg_model_name}")
            self.rrg_model = AutoModelForSeq2SeqLM.from_pretrained(rrg_model_name)
        self.rrg_model.to(self.device)
        self.rrg_model.eval()

        self._initialized = True
        print("LLM Inference Service initialized.")

    def predict_intent_and_entities(self, text):
        inputs = self.iree_tokenizer(text, return_tensors="pt", truncation=True, padding="max_length").to(self.device)
        with torch.no_grad():
            logits = self.iree_model(**inputs).logits
        probabilities = softmax(logits, dim=-1).squeeze().tolist()
        prediction_idx = torch.argmax(logits, dim=-1).item()
        
        predicted_label = self.iree_labels[prediction_idx]

        # Placeholder for entity extraction - this would typically be a separate model or more complex logic
        entities = {}
        if "不吃" in text or "不要" in text or "不喜歡" in text:
            # Simple keyword-based extraction for demonstration
            if "辣" in text: entities["negative_preference"] = "辣"
            if "牛肉" in text: entities["negative_preference"] = "牛肉"
            if "海鮮" in text: entities["negative_preference"] = "海鮮"
        if "義式" in text: entities["cuisine"] = "義式"
        if "火鍋" in text: entities["cuisine"] = "火鍋"
        if "約會" in text: entities["occasion"] = "約會"
        if "中等" in text: entities["budget"] = "中等"

        return {
            "prediction_idx": prediction_idx,
            "predicted_label": predicted_label,
            "probabilities": {self.iree_labels[i]: prob for i, prob in enumerate(probabilities)},
            "entities": entities
        }

    def generate_recommendation_reason(self, restaurant_info, user_preferences):
        # This is a simplified example. A real RRG would require a fine-tuned Seq2Seq model.
        # For demonstration, we'll construct a prompt and use the RRG model to generate.
        prompt = f"根據以下餐廳資訊和使用者偏好，生成一段推薦理由：\n餐廳資訊：{restaurant_info}\n使用者偏好：{user_preferences}\n推薦理由："
        
        inputs = self.rrg_tokenizer(prompt, return_tensors="pt", truncation=True, padding="max_length").to(self.device)
        with torch.no_grad():
            outputs = self.rrg_model.generate(**inputs, max_new_tokens=100, num_beams=5, early_stopping=True)
        reason = self.rrg_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return reason

class LLMIntentPredictView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = request.data.get("text", "").strip()

        if not user_input:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 text 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            llm_service = LLMInferenceService()
            prediction_result = llm_service.predict_intent_and_entities(user_input)
            return Response({
                "status": "success",
                "data": {
                    "user_input": user_input,
                    "analysis": prediction_result
                },
                "message": "LLM 意圖與實體分析成功"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": "error",
                "data": None,
                "message": f"LLM 意圖與實體分析失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LLMReasonGenerateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        restaurant_info = request.data.get("restaurant_info", "")
        user_preferences = request.data.get("user_preferences", "")

        if not restaurant_info or not user_preferences:
            return Response({
                "status": "error",
                "data": None,
                "message": "請提供 restaurant_info 和 user_preferences 欄位"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            llm_service = LLMInferenceService()
            reason = llm_service.generate_recommendation_reason(restaurant_info, user_preferences)
            return Response({
                "status": "success",
                "data": {
                    "restaurant_info": restaurant_info,
                    "user_preferences": user_preferences,
                    "recommendation_reason": reason
                },
                "message": "LLM 推薦理由生成成功"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": "error",
                "data": None,
                "message": f"LLM 推薦理由生成失敗: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# 直接替換原本的 LLMPredictView
class LLMPredictView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 這裡先做最小可用；之後你要就接到 LLMInferenceService
        return Response({"ok": True, "message": "LLM endpoint stub"}, status=status.HTTP_200_OK)