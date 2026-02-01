import os
import json
from openai import OpenAI
from app.ai.models import AIResponse

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("WARNING: OPENAI_API_KEY not found. AI features will not work.")
            self.client = None # Handle this in get_analysis
        else:
            self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo" # Or "gpt-4o-mini" / "gpt-4-turbo"

    def get_analysis(self, system_prompt: str, user_prompt: str) -> AIResponse:
        if not self.client:
            return AIResponse(
                summary="AI features are disabled (Missing OPENAI_API_KEY).",
                root_causes=[],
                recommendations=[],
                priority="low"
            )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON
            try:
                data = json.loads(content)
                return AIResponse(**data)
            except json.JSONDecodeError:
                 # Fallback if raw text is returned
                return AIResponse(
                    summary=content,
                    root_causes=[],
                    recommendations=[],
                    priority="medium",
                    full_response=content
                )
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            return AIResponse(
                summary="Sorry, I encountered an error while analyzing the data.",
                root_causes=[str(e)],
                recommendations=[],
                priority="high"
            )

llm_client = LLMClient()
