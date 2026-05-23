"""
Text-to-speech engine for VEDA.
Uses pyttsx3 for 100% offline speech output.
No internet required, works completely locally.
"""
import pyttsx3
import asyncio
import threading
from loguru import logger
from config.settings import settings


class VedaTTS:
    """Handles all speech output for VEDA."""

    def __init__(self):
        """Initialize the pyttsx3 TTS engine with configured settings."""
        try:
            self.timeout_seconds = 20
            logger.info(
                f"[TTS] Initialized | rate={settings.tts_rate} | "
                f"offline=true"
            )
        except Exception as e:
            logger.error(f"[TTS] Initialization failed: {e}")
            raise

    async def speak(self, text: str) -> None:
        """
        Convert text to speech and play it aloud.
        Runs asynchronously to avoid blocking.

        Args:
            text: The string to be spoken aloud
        """
        if not text or not text.strip():
            logger.warning("[TTS] Empty text provided")
            return

        try:
            logger.info(
                f"[TTS] Speaking: {text[:60]}{'...' if len(text) > 60 else ''}"
            )
            timeout = max(self.timeout_seconds, min(60, len(text) / 8))
            completed = await self._speak_with_timeout(text, timeout)
            if completed:
                logger.info("[TTS] Speech complete")
            else:
                logger.warning("[TTS] Speech timed out; continuing without blocking VEDA")
        except Exception as e:
            logger.error(f"[TTS] Failed to speak: {e}")

    async def _speak_with_timeout(self, text: str, timeout: float) -> bool:
        """Run pyttsx3 in a daemon thread so speech can never block startup."""
        done = threading.Event()

        def target():
            try:
                self._speak_sync(text)
            finally:
                done.set()

        thread = threading.Thread(target=target, daemon=True)
        thread.start()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, done.wait, timeout)

    def _speak_sync(self, text: str) -> None:
        """
        Synchronous speak call, run in executor to avoid blocking.
        This method is called in a thread pool.
        """
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", settings.tts_rate)
            engine.setProperty("volume", 1.0)

            try:
                voices = engine.getProperty("voices")
                if voices:
                    engine.setProperty("voice", voices[0].id)
            except Exception:
                pass

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            logger.error(f"[TTS] Sync speak failed: {e}")


class VedaTTSMock:
    """Mock TTS for testing without audio output."""

    async def speak(self, text: str) -> None:
        """Print text instead of speaking."""
        logger.info(f"[TTS-MOCK] Would speak: {text}")
