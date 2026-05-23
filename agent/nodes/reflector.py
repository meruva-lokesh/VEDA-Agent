"""
Reflector Node for VEDA's LangGraph agent.
Quality gate that evaluates synthesis and decides if rewriting is needed.
Implements reflection loop control.
"""
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from agent.state import AgentState
from config.settings import settings
import json


class ReflectionResult(BaseModel):
    """Output from quality reflection."""
    quality_score: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Response quality 1-10"
    )
    should_rewrite: bool = Field(
        default=False,
        description="Should we rewrite the response?"
    )
    feedback: str = Field(
        default="",
        description="Feedback for improvement"
    )


REFLECTOR_PROMPT = """You are VEDA's quality reflection system.

User question: {message}
Response: {synthesis}

Evaluate this response on:
1. Accuracy (answers the question correctly)
2. Completeness (covers the topic)
3. Clarity (easy to understand)
4. Relevance (stays on topic)

Score 1-10 overall quality.
Decide: does it need rewriting?

Response format - ONLY valid JSON:
{{
  "quality_score": 7,
  "should_rewrite": false,
  "feedback": "Good coverage of topic, could be more specific"
}}"""


async def reflector(state: AgentState) -> AgentState:
    """
    Evaluate synthesis quality and decide if rewriting is needed.
    
    Args:
        state: Current agent state with synthesis
    
    Returns:
        Updated state with reflection_score and reflection_critique
    """
    logger.info(
        f"[NODE: reflector] START | "
        f"loop_count={state.get('reflection_loop_count', 0)}"
    )

    try:
        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            num_predict=500
        )

        prompt = ChatPromptTemplate.from_template(REFLECTOR_PROMPT)
        chain = prompt | llm

        response = await chain.ainvoke({
            "message": state.get("user_message", ""),
            "synthesis": state.get("synthesis", "")
        })

        response_text = response.content if hasattr(
            response, "content"
        ) else str(response)

        # Extract JSON
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            reflection_dict = json.loads(json_str)
            result = ReflectionResult(**reflection_dict)
        else:
            logger.warning("[NODE: reflector] Could not parse JSON")
            result = ReflectionResult(quality_score=6, should_rewrite=False)

        logger.info(
            f"[NODE: reflector] EVALUATED | "
            f"quality={result.quality_score}/10 | "
            f"rewrite={result.should_rewrite}"
        )

        return {
            **state,
            "reflection_score": result.quality_score,
            "reflection_critique": result.feedback,
            "reflection_loop_count": state.get("reflection_loop_count", 0) + 1
        }

    except Exception as e:
        logger.error(
            f"[NODE: reflector] FAILED | error={str(e)}",
            exc_info=True
        )
        return {
            **state,
            "reflection_score": 5,
            "reflection_critique": f"Reflection failed: {str(e)}",
            "error": f"reflector failed: {str(e)}"
        }
