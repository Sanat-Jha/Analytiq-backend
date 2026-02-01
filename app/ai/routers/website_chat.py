from fastapi import APIRouter, HTTPException
from app.ai.models import WebsiteChatRequest, AIResponse
from app.ai.services.llm_client import llm_client
from app.ai.services.rag_service import rag_service
from app.ai.services.prompts import WEBSITE_ANALYSIS_PROMPT
from app.ai.services.context_builder import build_site_context
from app.db import con

router = APIRouter()

@router.post("/chat/website", response_model=AIResponse)
async def chat_website(request: WebsiteChatRequest):
    """AI chat with full access to all website analytics data"""
    try:
        # Verify site exists
        site = con.execute("SELECT * FROM sites WHERE site_id = ?", [request.website_id]).fetchone()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")

        # Build quick summary
        stats = con.execute("""
            SELECT 
                count(*) as total_events,
                count(distinct session_id) as total_sessions,
                count(distinct visitor_id) as total_visitors
            FROM raw_events 
            WHERE site_id = ? 
            AND ts > current_timestamp - INTERVAL '7' DAY
        """, [request.website_id]).fetchone()
        
        metrics_summary = f"""
        Time Range: Last 7 Days
        Total Events: {stats[0]}
        Total Sessions: {stats[1]}
        Total Visitors: {stats[2]}
        """
        
        # Build comprehensive analytics context with ALL user data
        full_user_data = build_site_context(request.website_id, days=7)
        
        # Retrieve RAG Context
        seo_context = rag_service.retrieve_context(request.message)
        
        # Build System Prompt with full context
        system_prompt = WEBSITE_ANALYSIS_PROMPT.format(
            website_id=request.website_id,
            metrics_summary=metrics_summary,
            full_user_data=full_user_data,
            recent_insights="None",
            seo_context=seo_context,
            user_query=request.message
        )
        
        # Call LLM
        response = llm_client.get_analysis(system_prompt, request.message)
        return response

    except Exception as e:
        print(f"Error in website chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
