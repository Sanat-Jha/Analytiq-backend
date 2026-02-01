"""
insight_detector.py - Scheduled job for automatic AI insights
"""
import datetime
from app.db import con
from app.ai.services.llm_client import llm_client
from app.ai.services.prompts import WEBSITE_ANALYSIS_PROMPT
from app.ai.services.rag_service import rag_service

INSIGHT_RULES = [
    # (description, SQL, threshold, insight_type)
    ("Performance regression (LCP > 4s)",
     "SELECT page, lcp FROM performance_metrics WHERE lcp > 4 AND date = current_date", 4, "performance_issue"),
    ("Bounce rate spike (bounce_rate > 0.7)",
     "SELECT page, bounce_rate FROM page_metrics WHERE bounce_rate > 0.7 AND date = current_date", 0.7, "bounce_rate_spike"),
    # Add more rules as needed
]

def detect_insights(website_id):
    insights = []
    for desc, sql, threshold, insight_type in INSIGHT_RULES:
        rows = con.execute(sql + " AND website_id = ?", [website_id]).fetchall()
        for row in rows:
            # Build context for LLM
            metrics_summary = f"{desc}: {row}"
            seo_context = rag_service.retrieve_context(desc)
            system_prompt = WEBSITE_ANALYSIS_PROMPT.format(
                website_id=website_id,
                metrics_summary=metrics_summary,
                recent_insights="None",
                seo_context=seo_context,
                user_query=f"Explain the issue: {desc}"
            )
            ai_response = llm_client.get_analysis(system_prompt, f"Explain the issue: {desc}")
            insights.append({
                "website_id": website_id,
                "insight_type": insight_type,
                "page": row[0] if len(row) > 1 else None,
                "description": desc,
                "ai_response": ai_response.dict(),
                "date": str(datetime.date.today())
            })
    return insights

# Example: store insights in a table or file (not implemented here)
# def store_insights(insights): ...

# To be run as a scheduled job (e.g., daily)
# Example usage:
# insights = detect_insights('your_website_id')
# store_insights(insights)
