"""
Wake Word Detector for VEDA.
Listens for the wake word "Hey VEDA" in continuous background audio.
Triggers voice conversation when wake word is detected.
"""
import asyncio
import time
from collections import deque

from loguru import logger
from config.settings import settings

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    import openwakeword
    from openwakeword.model import Model
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    logger.warning("[WAKE] OpenWakeWord not installed")


class WakeWordDetector:
    """Listens continuously for the VEDA wake word."""

    def __init__(
        self,
        on_detected_callback,
        wake_word: str = "hey jarvis",
        phrase_detector=None,
    ):
        """
        Initialize wake word detector.

        Args:
            on_detected_callback: Async function called when wake word heard.
            wake_word: Wake word to listen for.
            phrase_detector: Optional sync function that confirms custom phrases
                from recent PCM audio. This is used for "hey veda" because
                OpenWakeWord does not ship a built-in VEDA model.
        """
        if not AUDIO_AVAILABLE:
            raise ImportError("Audio libraries not available")

        self.callback = on_detected_callback
        self.phrase_detector = phrase_detector
        self.wake_word = wake_word
        self.running = False
        self.sample_rate = 16000
        self.input_device = settings.voice_input_device_index
        self.blocksize = 1280
        self.cooldown_seconds = 2.0
        self.openwakeword_threshold = 0.5
        self.noise_floor = 0.0
        self.speech_rms_threshold = 0.025
        self.speech_start_frames = 3
        self.speech_end_silence_frames = 8
        self.min_phrase_frames = 8
        self.max_phrase_frames = int((self.sample_rate * 3.5) / self.blocksize)
        self.loop = None

        logger.info(
            f"[WAKE] Detector initialized | "
            f"wake_word='{wake_word}' | "
            f"openwakeword={'available' if OPENWAKEWORD_AVAILABLE else 'unavailable'}"
        )

        if OPENWAKEWORD_AVAILABLE:
            try:
                logger.info("[WAKE] Downloading OpenWakeWord models (may take 1-2 minutes)...")
                openwakeword.utils.download_models()
                logger.info("[WAKE] Loading OpenWakeWord model...")

                model_mapping = {
                    "hey veda": "hey_jarvis",
                    "hey jarvis": "hey_jarvis",
                    "hey google": "hey_google",
                    "hello world": "hello_world",
                    "alexa": "alexa",
                }

                model_name = model_mapping.get(wake_word.lower(), "hey_jarvis")
                logger.info(
                    f"[WAKE] Mapping '{wake_word}' -> OpenWakeWord model: '{model_name}'"
                )
                if wake_word.lower() != "hey jarvis" and self.phrase_detector:
                    logger.info(
                        f"[WAKE] Whisper phrase fallback enabled for exact phrase: '{wake_word}'"
                    )

                self.model = Model(wakeword_models=[model_name])
                self.use_openwakeword = True
                logger.info("[WAKE] OpenWakeWord model loaded successfully")
            except Exception as e:
                logger.warning(f"[WAKE] Could not load OpenWakeWord: {e}")
                self.model = None
                self.use_openwakeword = False
        else:
            self.model = None
            self.use_openwakeword = False

    async def start_listening(self):
        """
        Start the continuous background wake word listener.
        Runs in executor to avoid blocking async event loop.
        """
        self.running = True
        self.loop = asyncio.get_running_loop()
        logger.info(f"[WAKE] Listening for '{self.wake_word}'...")

        try:
            await self.loop.run_in_executor(None, self._listen_sync)
        except Exception as e:
            logger.error(f"[WAKE] Listening failed: {e}")
            self.running = False

    def _listen_sync(self):
        """Synchronous listening loop, run in executor."""
        try:
            self._log_audio_devices()

            chunk_count = 0
            pre_roll_chunks = deque(maxlen=5)
            speech_chunks = []
            speech_frames = 0
            silence_frames = 0
            is_collecting_phrase = False

            while self.running:
                detected = False
                detection_reason = ""

                with sd.InputStream(
                    samplerate=self.sample_rate,
                    device=self.input_device,
                    channels=1,
                    dtype="int16",
                    blocksize=self.blocksize,
                    latency="low",
                ) as stream:
                    logger.info("[WAKE] Audio stream opened - listening for wake word...")

                    while self.running and not detected:
                        audio_chunk, overflowed = stream.read(self.blocksize)
                        if overflowed:
                            logger.debug("[WAKE] Input overflow while reading microphone")

                        audio_int16 = audio_chunk.flatten().astype(np.int16)
                        audio_float = audio_int16.astype(np.float32) / 32768.0
                        audio_level = float(np.sqrt(np.mean(audio_float ** 2)))
                        chunk_count += 1

                        if chunk_count == 20:
                            logger.info(
                                f"[WAKE] Calibrated noise floor: {self.noise_floor:.4f}; "
                                f"speech threshold: {self.speech_rms_threshold:.4f}"
                            )
                        elif chunk_count < 20:
                            self._update_noise_floor(audio_level)

                        if chunk_count % 100 == 0:
                            logger.debug(
                                f"[WAKE] Audio level: {audio_level:.4f} "
                                f"(chunks: {chunk_count})"
                            )

                        if self.use_openwakeword and self.model:
                            detected, detection_reason = self._check_openwakeword(audio_int16)

                        if not detected and self.phrase_detector:
                            if is_collecting_phrase:
                                speech_chunks.append(audio_int16.copy())
                                if audio_level >= self.speech_rms_threshold:
                                    silence_frames = 0
                                else:
                                    silence_frames += 1

                                phrase_too_long = len(speech_chunks) >= self.max_phrase_frames
                                phrase_ended = silence_frames >= self.speech_end_silence_frames
                                if phrase_ended or phrase_too_long:
                                    if len(speech_chunks) >= self.min_phrase_frames:
                                        wake_clip = np.concatenate(speech_chunks)
                                        detected = self._check_phrase_detector(wake_clip)
                                        if detected:
                                            detection_reason = f"phrase '{self.wake_word}'"
                                    is_collecting_phrase = False
                                    speech_chunks = []
                                    pre_roll_chunks.clear()
                                    speech_frames = 0
                                    silence_frames = 0
                            else:
                                pre_roll_chunks.append(audio_int16.copy())
                                if audio_level >= self.speech_rms_threshold:
                                    speech_frames += 1
                                else:
                                    speech_frames = 0
                                    self._update_noise_floor(audio_level)

                                if speech_frames >= self.speech_start_frames:
                                    logger.debug(
                                        f"[WAKE] Speech segment started | rms={audio_level:.4f}"
                                    )
                                    is_collecting_phrase = True
                                    speech_chunks = list(pre_roll_chunks)
                                    silence_frames = 0

                        time.sleep(0.01)

                if detected and self.running:
                    logger.info(f"[WAKE] Wake word triggered by {detection_reason}")
                    self._run_callback()
                    time.sleep(self.cooldown_seconds)

        except Exception as e:
            logger.error(f"[WAKE] Stream error: {e}")
        finally:
            logger.info("[WAKE] Listening stopped")

    def _log_audio_devices(self):
        """Log input devices once at startup for microphone debugging."""
        devices = sd.query_devices()
        logger.info(f"[WAKE] Available audio devices: {len(devices)}")
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                logger.info(f"  [{i}] {dev['name']} (channels: {dev['max_input_channels']})")

        default_device = sd.default.device[0]
        selected_device = self.input_device if self.input_device is not None else default_device
        logger.info(f"[WAKE] Using input device: {selected_device}")

    def _update_noise_floor(self, audio_level):
        """Track quiet-room RMS and derive a speech threshold from it."""
        if audio_level <= 0:
            return

        if self.noise_floor == 0:
            self.noise_floor = audio_level
        else:
            self.noise_floor = (self.noise_floor * 0.95) + (audio_level * 0.05)

        self.speech_rms_threshold = max(0.025, min(0.12, self.noise_floor * 4.0))

    def _check_openwakeword(self, audio_int16):
        """Run OpenWakeWord on one 80 ms chunk of 16-bit PCM audio."""
        try:
            prediction = self.model.predict(audio_int16)

            for name, score in prediction.items():
                if score > 0.3:
                    logger.info(f"[WAKE] OpenWakeWord '{name}' | score={score:.3f}")

                if score > self.openwakeword_threshold:
                    return True, f"OpenWakeWord '{name}' score={score:.3f}"
        except Exception as e:
            logger.warning(f"[WAKE] OpenWakeWord prediction failed: {e}")

        return False, ""

    def _check_phrase_detector(self, wake_clip):
        """Use STT to confirm custom phrases that OpenWakeWord does not provide."""
        try:
            return bool(self.phrase_detector(wake_clip, self.wake_word))
        except Exception as e:
            logger.warning(f"[WAKE] Phrase fallback failed: {e}")
            return False

    def _run_callback(self):
        """Run the async wake callback on the main event loop."""
        if self.loop and self.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self.callback(), self.loop)
            future.result()
        else:
            asyncio.run(self.callback())

    def stop(self):
        """Stop the wake word listener."""
        self.running = False
        logger.info("[WAKE] Stop requested")


class WakeWordDetectorMock:
    """Mock wake word detector for testing without audio."""

    def __init__(self, on_detected_callback, wake_word: str = "hey veda"):
        self.callback = on_detected_callback
        self.wake_word = wake_word
        self.running = False
        logger.info("[WAKE-MOCK] Initialized")

    async def start_listening(self):
        """Mock listening - just log it."""
        self.running = True
        logger.info(f"[WAKE-MOCK] Would listen for '{self.wake_word}'")
        while self.running:
            await asyncio.sleep(10)
            logger.info("[WAKE-MOCK] Simulated wake word detection")
            await self.callback()

    def stop(self):
        """Stop listening."""
        self.running = False
