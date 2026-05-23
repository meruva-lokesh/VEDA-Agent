"""
VEDA Main Entry Point.
Starts all components: wake word detection, voice I/O, agent, health monitoring.
This is the complete voice-first Jarvis-like AI assistant.

Usage:
    python main_new.py

The system will:
1. Say "VEDA is online"
2. Listen for "Hey VEDA"
3. Record 8 seconds of speech
4. Process through agent graph
5. Synthesize response
6. Speak response aloud
7. Store in persistent memory
8. Repeat
"""
import asyncio
import os
import re
import sys
from pathlib import Path
from datetime import datetime
import uuid

from loguru import logger

# Configure logging
logs_path = Path("./memory/logs")
logs_path.mkdir(parents=True, exist_ok=True)

logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    logs_path / "veda_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

from config.settings import settings
from voice.tts import VedaTTS, VedaTTSMock
from voice.stt import VedaSTT, VedaSTTMock
from voice.wake_word import WakeWordDetector, WakeWordDetectorMock
from agent.graph import build_graph
from agent.state import AgentState


def clean_transcribed_command(text: str) -> str:
    """Remove wake-word spillover and common STT artifacts from commands."""
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"^[^A-Za-z0-9]+", "", cleaned).strip()
    cleaned = re.sub(r"^[A-Za-z]?\s*veda[,\.\s:-]*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(
        r"^(hey|hi)\s+(veda|veeda|vida|vedha|beta|data)[,\.\s:-]*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned


class VEDA:
    """
    Main VEDA orchestrator.
    Runs all components: wake detection, speech input/output, agent, memory.
    """

    def __init__(self, use_mock: bool = False):
        """
        Initialize VEDA components.

        Args:
            use_mock: If True, use mock audio for testing
        """
        logger.info("[VEDA] Initializing...")
        
        self.use_mock = use_mock
        self.running = False

        try:
            # Initialize voice components
            if use_mock:
                logger.info("[VEDA] Using MOCK voice components (testing mode)")
                self.tts = VedaTTSMock()
                self.stt = VedaSTTMock()
            else:
                logger.info("[VEDA] Initializing real voice components")
                self.tts = VedaTTS()
                self.stt = VedaSTT()

            # Initialize agent
            logger.info("[VEDA] Building agent graph...")
            self.graph = build_graph()
            if self.graph is None:
                raise RuntimeError("Failed to build agent graph")

            # Initialize wake word detector
            self.wake_detector = WakeWordDetectorMock(
                on_detected_callback=self.on_wake_word,
                wake_word=settings.wake_word
            ) if use_mock else WakeWordDetector(
                on_detected_callback=self.on_wake_word,
                wake_word=settings.wake_word,
                phrase_detector=self.stt.contains_wake_word
            )

            logger.info("[VEDA] ✓ All components initialized")

        except Exception as e:
            logger.error(f"[VEDA] ✗ Initialization failed: {e}", exc_info=True)
            raise

    async def on_wake_word(self):
        """
        Called when wake word "Hey VEDA" is detected.
        Runs the full voice conversation pipeline.
        """
        logger.info("[VEDA] Wake word detected!")

        try:
            # Acknowledge wake
            await self.tts.speak("Yes?")
            logger.info("[VEDA] Prompt sent, listening for input...")

            # Listen for user input
            text = await self.stt.listen_and_transcribe(duration_seconds=8)
            text = clean_transcribed_command(text)

            if not text or len(text.strip()) == 0:
                await self.tts.speak("I did not catch that. Try again.")
                logger.warning("[VEDA] No speech detected")
                return

            logger.info(f"[VEDA] User said: '{text}'")
            await self.tts.speak("On it.")

            # Process through agent
            logger.info("[VEDA] Processing through agent...")
            session_id = str(uuid.uuid4())
            
            state = AgentState(
                user_message=text,
                tone="normal",
                screen_context=None,
                intent="general",
                topic=None,
                subtopics=None,
                search_urls=None,
                raw_content=None,
                synthesis=None,
                reflection_score=None,
                reflection_critique=None,
                reflection_loop_count=0,
                confidence_score=None,
                confidence_reason=None,
                final_response=None,
                sources_used=None,
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
                memory_retrieved=None,
                memory_saved=False,
                journal_path=None,
                error=None,
                fallback_used=False,
                raw_audio_path=None
            )

            config = {"configurable": {"thread_id": session_id}}

            # Invoke agent (this runs the graph)
            result = await self.graph.ainvoke(state, config)

            response = result.get("final_response", "")
            if not response:
                response = "I could not generate a response. Please try again."
                logger.warning("[VEDA] No response generated")

            logger.info(f"[VEDA] Generated response ({len(response)} chars)")

            # Speak response
            logger.info("[VEDA] Speaking response...")
            await self.tts.speak(response)
            logger.info("[VEDA] Response complete")

        except Exception as e:
            logger.error(f"[VEDA] Conversation failed: {e}", exc_info=True)
            try:
                await self.tts.speak("An error occurred. Please try again.")
            except Exception as speak_error:
                logger.error(f"[VEDA] Failed to speak error: {speak_error}")

    async def start(self):
        """
        Start VEDA main loop.
        Continuously listens for wake word and processes conversations.
        """
        self.running = True
        logger.info("\n" + "="*70)
        logger.info("VEDA IS STARTING...")
        logger.info("="*70 + "\n")

        try:
            # Startup greeting
            await self.tts.speak(
                "VEDA is online. Say Hey VEDA to activate me."
            )

            logger.info("[VEDA] ✓ READY - Listening for wake word...")
            logger.info("[VEDA] Say: 'Hey VEDA, what is machine learning?'\n")

            # Start listening (blocks until stopped)
            await self.wake_detector.start_listening()

        except KeyboardInterrupt:
            logger.info("\n[VEDA] Shutdown requested by user")
        except Exception as e:
            logger.error(f"[VEDA] Fatal error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean shutdown of VEDA."""
        logger.info("\n[VEDA] Shutting down...")
        self.running = False
        self.wake_detector.stop()
        logger.info("[VEDA] ✓ Shutdown complete")


async def main():
    """Main entry point for VEDA."""
    # Determine if running in mock mode for testing
    use_mock = os.environ.get("VEDA_MOCK_MODE", "false").lower() == "true"

    try:
        veda = VEDA(use_mock=use_mock)
        await veda.start()
        return 0
    except Exception as e:
        logger.error(f"[MAIN] Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    logger.info("[MAIN] Starting VEDA...")
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
