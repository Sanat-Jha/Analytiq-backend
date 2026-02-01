"""
ai_insights.py - API endpoint to fetch recent AI insights for a website
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.ai.models import AIResponse
# from app.db import con  # Uncomment and implement if storing in DB

router = APIRouter()

# For demo: in-memory store (replace with DB in production)
INSIGHTS_STORE = {}

@router.get("/ai/insights/{website_id}", response_model=List[AIResponse])
def get_ai_insights(website_id: str):
    # Replace with DB fetch in production
    insights = INSIGHTS_STORE.get(website_id, [])
    if not insights:
        return []
    return [AIResponse(**ins["ai_response"]) for ins in insights]

# To be called by the scheduled job after detection
# def save_insights(website_id, insights):
#     INSIGHTS_STORE[website_id] = insights
