"""
VEDA Voice module.
Handles all audio input/output for voice-first interaction.
100% offline using pyttsx3 (TTS) and faster-whisper (STT).
"""

from voice.tts import VedaTTS, VedaTTSMock
from voice.stt import VedaSTT, VedaSTTMock

__all__ = ["VedaTTS", "VedaTTSMock", "VedaSTT", "VedaSTTMock"]
