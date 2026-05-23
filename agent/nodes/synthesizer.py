"""
Synthesizer Node for VEDA's LangGraph agent.
Generates comprehensive responses from research content and memories.
Injects hindsight memories into the response generation.
"""
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from agent.state import AgentState
from config.settings import settings


SYNTHESIZER_PROMPT = """You are VEDA synthesizing research into a comprehensive response.

User asked: {message}
Topic: {topic}
Tone: {tone}

Research findings:
{synthesis}

Relevant memories/past learning:
{memories}

Create a comprehensive answer that:
1. Directly answers the user's question
2. Synthesizes information from the research
3. Incorporates relevant past learning
4. Is clear and well-structured
5. Appropriate for the user's tone

If tone is stressed: be brief (2-3 paragraphs)
If tone is calm: give full detailed answer (4-5 paragraphs)

Synthesized response:"""


async def synthesizer(state: AgentState) -> AgentState:
    """
    Generate a comprehensive response from research and memories.
    
    Args:
        state: Current agent state with synthesis, memories, tone set
    
    Returns:
        Updated state with final synthesis ready for writer
    """
    logger.info(
        f"[NODE: synthesizer] START | "
        f"topic={state.get('topic')} | "
        f"has_content={bool(state.get('synthesis'))}"
    )

    try:
        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.5,
            num_predict=2000
        )

        prompt = ChatPromptTemplate.from_template(SYNTHESIZER_PROMPT)
        chain = prompt | llm

        # Build memories text
        memories_text = "No relevant memories"
        if state.get("memory_retrieved"):
            memories_list = state["memory_retrieved"]
            if isinstance(memories_list, list) and memories_list:
                memories_text = "\n".join([
                    str(m) for m in memories_list[:3]
                ])

        response = await chain.ainvoke({
            "message": state.get("user_message", ""),
            "topic": state.get("topic", ""),
            "tone": state.get("tone", "normal"),
            "synthesis": state.get("synthesis", "No research data"),
            "memories": memories_text
        })

        synthesis_text = response.content if hasattr(
            response, "content"
        ) else str(response)

        logger.info(
            f"[NODE: synthesizer] COMPLETE | "
            f"synthesis_length={len(synthesis_text)}"
        )

        return {
            **state,
            "synthesis": synthesis_text,
            "reflection_score": 7  # Provisional score for reflector
        }

    except Exception as e:
        logger.error(
            f"[NODE: synthesizer] FAILED | error={str(e)}",
            exc_info=True
        )
        return {
            **state,
            "synthesis": state.get("synthesis", ""),
            "reflection_score": 0,
            "error": f"synthesizer failed: {str(e)}"
        }
