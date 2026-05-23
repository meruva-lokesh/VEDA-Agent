"""
Intent Router Node for VEDA's LangGraph agent.
Classifies user message into an intent and extracts the topic.
This is the first node every message passes through.
"""
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from agent.state import AgentState
from config.settings import settings
import json


class IntentResult(BaseModel):
    """Structured output from intent classification."""
    intent: str = Field(
        ...,
        description="Classified intent: research, recall, general, study_mode, file_op, app_control"
    )
    topic: str = Field(
        default="",
        description="Main subject or topic (empty if general)"
    )
    tone: str = Field(
        default="normal",
        description="User tone: calm, stressed, confused, normal"
    )
    confidence: int = Field(
        default=5,
        description="Confidence score 1-10"
    )


INTENT_PROMPT = """You are VEDA's intent classifier.

Classify this message into ONE intent:
- research: user wants to learn about a topic, ask questions, understand something
- recall: user asks what they previously studied or researched
- general: casual conversation, greetings, simple chitchat
- study_mode: user wants to start a focused study session
- file_op: user wants to read, write, or manage files
- app_control: user wants to open or control an application

Message: "{message}"

Also extract:
- topic: the main subject (empty string "" if general chat)
- tone: ONE of: calm / stressed / confused / normal
- confidence: 1-10 how confident you are

Respond with ONLY valid JSON, no other text:
{{"intent": "...", "topic": "...", "tone": "...", "confidence": ...}}"""


async def intent_router(state: AgentState) -> AgentState:
    """
    Classify the user's message into an intent and extract topic.
    This is the first processing node - every query starts here.

    Args:
        state: Current AgentState containing user_message

    Returns:
        Updated AgentState with intent, topic, tone, confidence_score set
    """
    logger.info(
        f"[NODE: intent_router] START | "
        f"message='{state['user_message'][:50]}...'"
    )

    try:
        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.0,
            num_predict=250
        )

        prompt = ChatPromptTemplate.from_template(INTENT_PROMPT)
        chain = prompt | llm

        response = await chain.ainvoke(
            {"message": state["user_message"]}
        )

        # Parse JSON from response
        response_text = response.content if hasattr(
            response, "content"
        ) else str(response)
        
        # Try to extract JSON from response
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result_dict = json.loads(json_str)
            result = IntentResult(**result_dict)
        else:
            logger.warning(
                f"[NODE: intent_router] Could not parse JSON from response: "
                f"{response_text}"
            )
            # Fallback to safe defaults
            result = IntentResult(
                intent="general",
                topic="",
                tone="normal",
                confidence=3
            )

        logger.info(
            f"[NODE: intent_router] CLASSIFIED | "
            f"intent={result.intent} | topic={result.topic} | "
            f"tone={result.tone} | confidence={result.confidence}/10"
        )

        return {
            **state,
            "intent": result.intent,
            "topic": result.topic,
            "tone": result.tone,
            "confidence_score": result.confidence
        }

    except Exception as e:
        logger.error(
            f"[NODE: intent_router] FAILED | error={str(e)}",
            exc_info=True
        )
        return {
            **state,
            "intent": "general",
            "topic": "",
            "tone": "normal",
            "confidence_score": 1,
            "error": f"intent_router failed: {str(e)}"
        }
