"""
Planner Node for VEDA's LangGraph agent.
Creates a research plan and search strategy for complex queries.
Breaks down research needs into subtopics and search queries.
"""
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from agent.state import AgentState
from config.settings import settings
import json


class PlanResult(BaseModel):
    """Research plan output."""
    subtopics: list[str] = Field(
        default_factory=list,
        description="List of subtopics to research"
    )
    search_queries: list[str] = Field(
        default_factory=list,
        description="List of search queries for each subtopic"
    )
    approach: str = Field(
        default="web",
        description="Approach: web, academic, technical, general"
    )


PLANNER_PROMPT = """You are a research planner for VEDA.

Create a research plan for this topic:
Topic: {topic}
User message: {message}

Create:
1. 3-5 subtopics to cover
2. 1-2 search queries per subtopic
3. Overall research approach

Response format - ONLY valid JSON:
{{
  "subtopics": ["subtopic1", "subtopic2", ...],
  "search_queries": ["query1", "query2", ...],
  "approach": "web"
}}"""


async def planner(state: AgentState) -> AgentState:
    """
    Plan the research strategy for a complex query.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with subtopics and search_urls set
    """
    logger.info(
        f"[NODE: planner] START | "
        f"topic={state.get('topic')}"
    )

    try:
        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.5,
            num_predict=1000
        )

        prompt = ChatPromptTemplate.from_template(PLANNER_PROMPT)
        chain = prompt | llm

        response = await chain.ainvoke({
            "topic": state.get("topic", ""),
            "message": state.get("user_message", "")
        })

        response_text = response.content if hasattr(
            response, "content"
        ) else str(response)

        # Extract JSON
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            plan_dict = json.loads(json_str)
            result = PlanResult(**plan_dict)
        else:
            logger.warning("[NODE: planner] Could not parse JSON")
            result = PlanResult(
                subtopics=[state.get("topic", "Unknown topic")],
                search_queries=[state.get("user_message", "")]
            )

        logger.info(
            f"[NODE: planner] PLANNED | "
            f"subtopics={len(result.subtopics)} | "
            f"queries={len(result.search_queries)}"
        )

        return {
            **state,
            "subtopics": result.subtopics,
            "search_urls": result.search_queries
        }

    except Exception as e:
        logger.error(
            f"[NODE: planner] FAILED | error={str(e)}",
            exc_info=True
        )
        return {
            **state,
            "subtopics": [state.get("topic", "")],
            "search_urls": [state.get("user_message", "")],
            "error": f"planner failed: {str(e)}"
        }
