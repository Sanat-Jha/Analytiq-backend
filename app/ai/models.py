from pydantic import BaseModel
from typing import List, Optional, Any

class WebsiteChatRequest(BaseModel):
    website_id: str
    message: str
    context_window: Optional[int] = 5  # Number of recent user messages to keep

class MetricChatRequest(BaseModel):
    website_id: str
    metric: str
    page: Optional[str] = None
    message: str

class AIResponse(BaseModel):
    summary: str
    root_causes: List[str] = []
    recommendations: List[str] = []
    priority: str = "medium"  # low, medium, high, critical
    full_response: Optional[str] = None # Fallback for non-structured
