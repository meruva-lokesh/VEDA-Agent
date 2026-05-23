"""
Speech-to-text engine for VEDA.
Uses faster-whisper for offline transcription.
100% offline, no internet required.
Supports English and code-switched speech.
"""
import asyncio
import tempfile
import os
import re
import threading
from pathlib import Path
from loguru import logger
from config.settings import settings

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    from faster_whisper import WhisperModel
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("[STT] Audio libraries not installed yet. Install with: pip install -r requirements.txt")


class VedaSTT:
    """Handles all voice input and transcription for VEDA."""

    def __init__(self):
        """Load the Whisper model for offline transcription."""
        if not AUDIO_AVAILABLE:
            logger.error("[STT] Audio libraries not available")
            raise ImportError("Install audio requirements: pip install -r requirements.txt")

        try:
            logger.info(f"[STT] Loading WhisperModel size='{settings.stt_model_size}' (may take 30-60 seconds)...")
            self.model = WhisperModel(
                settings.stt_model_size,
                device="cpu",
                compute_type="int8"
            )
            self._model_lock = threading.Lock()
            self.sample_rate = 16000
            logger.info(
                f"[STT] Whisper model loaded | size={settings.stt_model_size} | "
                f"device=cpu | offline=true"
            )
        except Exception as e:
            logger.error(f"[STT] Failed to load Whisper model: {e}")
            raise

    async def listen_and_transcribe(
        self,
        duration_seconds: int = 8
    ) -> str:
        """
        Record audio from microphone and return transcribed text.
        Runs asynchronously to avoid blocking.

        Args:
            duration_seconds: How long to record (default 8 seconds)

        Returns:
            Transcribed text string, empty string on failure
        """
        max_duration = min(float(duration_seconds), settings.stt_command_max_seconds)
        logger.info(f"[STT] Recording command (max {max_duration:.1f}s)...")

        try:
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(
                None,
                self._record_audio,
                max_duration
            )
            
            if audio is None or len(audio) == 0:
                logger.warning("[STT] No audio recorded")
                return ""

            text = await loop.run_in_executor(
                None,
                self._transcribe,
                audio
            )
            
            logger.info(f"[STT] Transcribed: '{text}'")
            return text.strip()

        except Exception as e:
            logger.error(f"[STT] Transcription failed: {e}")
            return ""

    def contains_wake_word(self, audio, wake_word: str) -> bool:
        """
        Transcribe a short audio clip and check for the configured wake phrase.

        OpenWakeWord does not include a built-in "hey veda" model. This method
        gives VEDA a real phrase-level fallback while keeping the wake loop local
        and offline.
        """
        try:
            text = self._transcribe(audio, wake_phrase=True)
            normalized = self._normalize_text(text)
            aliases = self._wake_word_aliases(wake_word)

            matched = any(alias in normalized for alias in aliases)
            if self._normalize_text(wake_word) == "hey veda" and normalized == "hey":
                matched = True
            if text.strip():
                logger.info(
                    f"[STT] Wake phrase check | text='{text.strip()}' | matched={matched}"
                )
            return matched
        except Exception as e:
            logger.warning(f"[STT] Wake phrase check failed: {e}")
            return False

    def _record_audio(self, duration: float):
        """
        Record raw audio from microphone until speech ends or max duration.
        Called in executor thread pool to avoid blocking.
        """
        try:
            logger.info("[STT] Starting voice-activity capture")
            blocksize = 1024
            max_frames = int(duration * self.sample_rate)
            min_frames = int(settings.stt_command_min_seconds * self.sample_rate)
            silence_limit = max(1, int(settings.stt_silence_seconds * self.sample_rate / blocksize))

            chunks = []
            recorded_frames = 0
            speech_seen = False
            silence_frames = 0

            with sd.InputStream(
                samplerate=self.sample_rate,
                device=settings.voice_input_device_index,
                channels=1,
                dtype="float32",
                blocksize=blocksize,
            ) as stream:
                while recorded_frames < max_frames:
                    chunk, overflowed = stream.read(blocksize)
                    if overflowed:
                        logger.debug("[STT] Input overflow while recording command")

                    flat = chunk.reshape(-1, 1)
                    chunks.append(flat.copy())
                    recorded_frames += len(flat)

                    rms = float(np.sqrt(np.mean(flat ** 2)))
                    if rms >= settings.stt_speech_rms_threshold:
                        speech_seen = True
                        silence_frames = 0
                    elif speech_seen:
                        silence_frames += 1

                    if (
                        speech_seen
                        and recorded_frames >= min_frames
                        and silence_frames >= silence_limit
                    ):
                        break

            if not chunks:
                return None

            recording = np.concatenate(chunks, axis=0)
            seconds = len(recording) / self.sample_rate
            logger.info(
                f"[STT] Audio captured | samples={len(recording)} | seconds={seconds:.2f}"
            )
            return recording
        except Exception as e:
            logger.error(f"[STT] Audio recording failed: {e}")
            return None

    def _transcribe(self, audio, wake_phrase: bool = False) -> str:
        """
        Run Whisper inference on recorded audio.
        Called in executor thread pool to avoid blocking.
        """
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False
            ) as f:
                temp_path = f.name

            try:
                sf.write(temp_path, audio, self.sample_rate)
                logger.info(f"[STT] Transcribing audio | file={temp_path}")
                
                transcribe_options = {
                    "language": "en" if wake_phrase else None,
                    "beam_size": 1 if wake_phrase else 3,
                    "condition_on_previous_text": False,
                    "no_speech_threshold": 0.65 if wake_phrase else 0.6,
                    "vad_filter": True,
                    "vad_parameters": {
                        "min_silence_duration_ms": 350,
                        "speech_pad_ms": 250,
                    },
                }
                if wake_phrase:
                    transcribe_options["hotwords"] = "hey veda"
                    transcribe_options["initial_prompt"] = "The wake phrase is Hey VEDA."

                with self._model_lock:
                    segments, _ = self.model.transcribe(
                        temp_path,
                        **transcribe_options
                    )
                text = " ".join(segment.text for segment in segments)
                logger.info(f"[STT] Transcription complete | text={text[:60]}")
                return text

            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"[STT] Transcription inference failed: {e}")
            return ""

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize transcribed text for phrase matching."""
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()

    def _wake_word_aliases(self, wake_word: str) -> set[str]:
        """Return likely Whisper spellings for the configured wake word."""
        normalized = self._normalize_text(wake_word)
        aliases = {normalized}

        if normalized == "hey veda":
            aliases.update({
                "hey veda",
                "hey vida",
                "hey veeda",
                "hey vedha",
                "hey beta",
                "hey data",
                "hi veda",
            })

        return aliases


class VedaSTTMock:
    """Mock STT for testing without microphone."""

    async def listen_and_transcribe(self, duration_seconds: int = 8) -> str:
        """Return mock transcription."""
        logger.info(f"[STT-MOCK] Would record for {duration_seconds}s")
        return "mock transcription test"
