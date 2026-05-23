"""
Writer Node for VEDA's LangGraph agent.
Formats and delivers the final response to the user.
Last node before END in every pipeline path.
"""
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from agent.state import AgentState
from config.settings import settings


WRITER_PROMPT = """You are VEDA, a helpful and intelligent AI assistant.
You speak naturally and conversationally.

Context about the user:
- Tone: {tone}
- They asked: {message}
- Research/synthesis: {synthesis}
- Relevant memories: {memories}

Rules:
- If tone is "stressed": be brief and direct (2-3 sentences max)
- If tone is "calm": give detailed thoughtful answers
- If tone is "confused": start by clarifying what they're asking
- Always speak naturally, as if having a real conversation
- If no research/synthesis available, answer from your general knowledge
- Keep responses concise but complete (150-300 words typical)

Provide your response now:"""


async def writer(state: AgentState) -> AgentState:
    """
    Generate and format the final response from synthesized content.
    This is the last processing node before output.

    Args:
        state: Current AgentState with synthesis and context

    Returns:
        Updated AgentState with final_response set
    """
    logger.info(
        f"[NODE: writer] START | "
        f"intent={state.get('intent')} | tone={state.get('tone')}"
    )

    try:
        llm = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.3,
            num_predict=650
        )

        prompt = ChatPromptTemplate.from_template(WRITER_PROMPT)
        chain = prompt | llm

        # Build memories text from Hindsight recall results.
        memories_text = "No relevant memories."
        memory_list = state.get("hindsight_memories") or state.get("memory_retrieved")
        if memory_list:
            if isinstance(memory_list, list) and len(memory_list) > 0:
                memories_formatted = []
                for mem in memory_list[:3]:
                    if isinstance(mem, dict):
                        content = mem.get("content") or mem.get("text") or ""
                    else:
                        content = str(mem)
                    if content:
                        memories_formatted.append(content)
                
                if memories_formatted:
                    memories_text = "\n".join(memories_formatted)

        # Get synthesis or empty string
        synthesis = state.get("synthesis", "") or ""

        # Use invoke in a sync context (LangChain Ollama doesn't support ainvoke well)
        response = chain.invoke({
            "tone": state.get("tone", "normal"),
            "message": state.get("user_message", ""),
            "synthesis": synthesis,
            "memories": memories_text
        })

        final_text = response.content if hasattr(
            response, "content"
        ) else str(response)

        logger.info(
            f"[NODE: writer] COMPLETE | "
            f"response_length={len(final_text)} chars"
        )

        return {
            **state,
            "final_response": final_text,
            "memory_saved": False
        }

    except Exception as e:
        logger.error(
            f"[NODE: writer] FAILED | error={str(e)}",
            exc_info=True
        )
        fallback = (
            "I encountered an error processing your request. "
            "Please try again."
        )
        return {
            **state,
            "final_response": fallback,
            "error": f"writer failed: {str(e)}"
        }
