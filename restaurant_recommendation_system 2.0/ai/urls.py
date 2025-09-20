from django.urls import path
from .views import (
    ExtractNegativeConditionsView,
    GenerateRecommendReasonView,
    GeneratePromptView,
    SuggestInputGuidanceView,
    GenerateCardDataView,
    IntegrationTestView,
    recommend_restaurant,
    save_user_preference,
    get_user_preference,
    delete_user_preference_item,
    LLMPredictView,
)

urlpatterns = [
    path('extract-negative/', ExtractNegativeConditionsView.as_view(), name='extract_negative'),
    path('generate-reason/', GenerateRecommendReasonView.as_view(), name='generate_reason'),
    path('generate-prompt/', GeneratePromptView.as_view(), name='generate_prompt'),
    path('suggest-input/', SuggestInputGuidanceView.as_view(), name='suggest_input'),
    path('generate-cards/', GenerateCardDataView.as_view(), name='generate_cards'),
    path('integration-test/', IntegrationTestView.as_view(), name='integration_test'),
    path('recommend/', recommend_restaurant, name='recommend_restaurant'),
    path('save_preference/', save_user_preference, name='save_user_preference'),
    path('get_preference/', get_user_preference, name='get_user_preference'),
    path('delete_preference_item/', delete_user_preference_item, name='elete_user_preference_item'), 
]

urlpatterns = [
    path("llm-predict/", LLMPredictView.as_view(), name="llm_predict"),
]