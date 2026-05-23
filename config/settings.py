"""
config/settings.py

VEDA configuration management with pydantic v2.

Loads settings from environment variables (.env file) with sensible defaults.
Supports both ChromaDB and Hindsight (Vectorize) memory systems.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    VEDA application settings loaded from environment variables.

    All settings can be overridden via .env file or direct environment
    variable assignment.
    """

    # ── General ──────────────────────────────────────────────────────────
    app_name: str = "VEDA"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    logs_path: str = "./memory/logs"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept common DEBUG environment values used by shells/tooling."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

    # ── ChromaDB Memory (Research Documents) ─────────────────────────────
    chromadb_path: str = "./memory/chromadb"
    chromadb_collection: str = "veda_research"

    # ── Hindsight (Vectorize) Agent Memory ──────────────────────────────
    hindsight_mode: str = Field(
        default="local",
        description="'local' (self-hosted Docker) or 'cloud' (Vectorize Cloud)"
    )
    hindsight_local_url: str = Field(
        default="http://localhost:8888",
        description="URL for local Hindsight Docker container"
    )
    hindsight_cloud_url: str = Field(
        default="https://api.hindsight.vectorize.io",
        description="URL for Hindsight Cloud (free tier)"
    )
    hindsight_api_key: str = Field(
        default="",
        description="API key for cloud mode (leave blank for local mode)"
    )
    hindsight_bank_id: str = Field(
        default="veda",
        description="Memory bank identifier — one per assistant"
    )
    hindsight_recall_top_k: int = Field(
        default=5,
        description="Number of memories to inject before each response"
    )
    hindsight_reflect_every_n: int = Field(
        default=10,
        description="Trigger memory reflection every N sessions"
    )
    hindsight_enabled: bool = Field(
        default=True,
        description="Master on/off switch for Hindsight memory"
    )
    hindsight_session_counter_file: str = Field(
        default="./memory/hindsight_session_count.json",
        description="Path to persistent session counter for reflection tracking"
    )
    hindsight_timeout_seconds: float = Field(
        default=5.0,
        description="SDK request timeout for local/cloud Hindsight calls"
    )
    hindsight_connect_timeout_seconds: float = Field(
        default=0.35,
        description="Fast socket probe timeout before calling local Hindsight"
    )

    # ── LLM Configuration ────────────────────────────────────────────────
    llm_provider: str = Field(
        default="ollama",
        description="'ollama' (local), 'openai', or 'anthropic'"
    )
    llm_model: str = Field(
        default="mistral",
        description="Model name: 'mistral', 'neural-chat', 'llama2', etc."
    )
    
    # Ollama configuration (local models)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API endpoint (default: localhost:11434)"
    )
    ollama_model: str = Field(
        default="gemma2:2b",
        description="Ollama model to use (must be pulled first)"
    )
    ollama_research_model: str = Field(
        default="llama3.2:3b",
        description="Ollama model for deeper research"
    )
    ollama_vision_model: str = Field(
        default="llava:7b",
        description="Ollama vision model for image analysis"
    )
    ollama_fallback_model: str = Field(
        default="gemma2:2b",
        description="Fallback model when others unavailable"
    )
    ollama_timeout: int = Field(
        default=20,
        description="Timeout for Ollama API calls in seconds"
    )
    
    # OpenAI configuration (cloud)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo"
    
    # Anthropic configuration (cloud)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus"
    
    # Common LLM settings
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.95
    top_k: int = 40

    # ── LangGraph Checkpointing ──────────────────────────────────────────
    checkpoint_db_path: str = "./memory/checkpoints.db"
    checkpoint_thread_id: str = "default"

    # ── Voice & I/O ──────────────────────────────────────────────────────
    enable_voice: bool = True
    voice_model: str = "pyttsx3"
    voice_language: str = "en"
    wake_word: str = Field(
        default="hey veda",
        description="Wake word for voice activation"
    )
    voice_input_device_index: Optional[int] = Field(
        default=None,
        description="Optional sounddevice input device index. Leave blank for system default."
    )
    stt_model_size: str = Field(
        default="base",
        description="faster-whisper model size: tiny, base, small, medium"
    )
    stt_command_max_seconds: float = Field(
        default=6.0,
        description="Maximum seconds to listen after wake word"
    )
    stt_command_min_seconds: float = Field(
        default=1.0,
        description="Minimum command recording duration"
    )
    stt_silence_seconds: float = Field(
        default=0.8,
        description="Stop command recording after this much silence"
    )
    stt_speech_rms_threshold: float = Field(
        default=0.018,
        description="RMS level treated as speech for command recording"
    )
    tts_rate: int = Field(
        default=175,
        description="Speech rate in words per minute"
    )
    
    # ── Dashboard & API Ports ────────────────────────────────────────────
    dashboard_port: int = Field(
        default=8765,
        description="Port for VEDA web dashboard"
    )
    phone_mic_port: int = Field(
        default=8766,
        description="Port for phone microphone integration"
    )

    class Config:
        """Pydantic config for BaseSettings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Module-level singleton
settings = Settings()
