from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from content_analyzer.analyze_restaurant_indicators import analyze_restaurant_indicators
from content_analyzer.analyze_user_preferences import analyze_user_preferences
from typing import Optional

app = FastAPI()

class RestaurantAnalyzeRequest(BaseModel):
    post_id: int
    content: str
    place_id: Optional[str] = None

class UserAnalyzeRequest(BaseModel):
    post_id: int
    content: str
    user_id: Optional[int] = None

@app.post("/analyze/restaurant/")
def analyze_restaurant(data: RestaurantAnalyzeRequest):
    result = analyze_restaurant_indicators(data.content, data.place_id)
    return {"status": "success", "data": result}

@app.post("/analyze/user/")
def analyze_user(data: UserAnalyzeRequest):
    result = analyze_user_preferences(data.content, data.user_id)
    return {"status": "success", "data": result}