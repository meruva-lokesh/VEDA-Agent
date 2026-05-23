"""
memory/hindsight_store.py

Hindsight (Vectorize) agent memory client for VEDA.

Wraps the hindsight-client SDK to provide three core operations:
  - retain : Store a fact or conversation turn into long-term memory
  - recall : Retrieve semantically relevant memories before responding
  - reflect: Synthesize accumulated memories into higher-order patterns

Hindsight runs in two modes:
  - local : Self-hosted via Docker at localhost:8888
  - cloud : Hindsight Cloud free tier (requires API key in .env)

This store runs ALONGSIDE ChromaDB. ChromaDB stores raw research
documents. Hindsight stores learned facts and conversation patterns.

Docs: https://hindsight.vectorize.io
GitHub: https://github.com/vectorize-io/hindsight
"""

import json
import asyncio
import socket
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

try:
    from hindsight_client import Hindsight
except ImportError:
    Hindsight = None

from loguru import logger
from config.settings import settings


class VedaHindsightStore:
    """
    Production wrapper around the Hindsight agent memory client.

    Provides async retain, recall, and reflect operations with full
    error handling, logging, and fallback behaviour so VEDA never
    crashes if Hindsight is unavailable.
    """

    def __init__(self) -> None:
        """
        Initialise the Hindsight client based on configured mode.

        Selects local or cloud base_url from settings. In cloud mode
        the API key from settings is passed as a bearer token.
        """
        self._enabled: bool = settings.hindsight_enabled
        self._bank_id: str = settings.hindsight_bank_id
        self._client: Optional[object] = None
        self._session_counter: int = 0
        self._bank_ready: bool = False
        self._last_bank_check: float = 0.0
        self._bank_retry_seconds: float = 30.0

        if not self._enabled:
            logger.warning("[HINDSIGHT] Disabled via settings — skipping init")
            return

        if Hindsight is None:
            logger.error(
                "[HINDSIGHT] hindsight-client not installed. "
                "Run: pip install hindsight-client==0.6.0"
            )
            return

        base_url = (
            settings.hindsight_cloud_url
            if settings.hindsight_mode == "cloud"
            else settings.hindsight_local_url
        )

        try:
            if settings.hindsight_mode == "cloud":
                self._client = Hindsight(
                    base_url=base_url,
                    api_key=settings.hindsight_api_key,
                    timeout=settings.hindsight_timeout_seconds,
                )
            else:
                self._client = Hindsight(
                    base_url=base_url,
                    timeout=settings.hindsight_timeout_seconds,
                )

            self._session_counter = self._load_session_counter()

            logger.info(
                f"[HINDSIGHT] Initialised | mode={settings.hindsight_mode} "
                f"| bank={self._bank_id} | url={base_url} "
                f"| sessions_so_far={self._session_counter}"
            )

        except Exception as e:
            logger.error(
                f"[HINDSIGHT] Failed to initialise client: {e}",
                exc_info=True,
            )
            self._client = None

    async def _ensure_bank(self) -> bool:
        """Create the configured Hindsight bank if it does not already exist."""
        if not self._enabled or self._client is None:
            return False

        if self._bank_ready:
            return True

        now = time.monotonic()
        if now - self._last_bank_check < self._bank_retry_seconds:
            return False

        self._last_bank_check = now

        if settings.hindsight_mode == "local" and not self._server_reachable():
            logger.warning(
                f"[HINDSIGHT] Local server not reachable at {settings.hindsight_local_url}; "
                "skipping memory for this turn"
            )
            return False

        try:
            await asyncio.to_thread(
                self._client.create_bank,
                bank_id=self._bank_id,
                name="VEDA Assistant Memory",
                mission=(
                    "Remember durable user preferences, recurring topics, "
                    "project context, and useful facts across VEDA sessions."
                ),
                retain_mission=(
                    "Extract stable facts about the user, their projects, "
                    "preferences, goals, and repeated learning needs. Avoid "
                    "retaining transient filler or raw transcripts."
                ),
                reflect_mission=(
                    "Synthesize VEDA's retained memories into practical "
                    "patterns that improve future responses."
                ),
            )
            logger.info(f"[HINDSIGHT] Memory bank ready | bank={self._bank_id}")
        except Exception as e:
            message = str(e).lower()
            if "409" not in message and "already" not in message and "exists" not in message:
                logger.warning(f"[HINDSIGHT] Could not create/check bank: {e}")
                return False
            logger.info(f"[HINDSIGHT] Memory bank exists | bank={self._bank_id}")

        self._bank_ready = True
        return True

    def _server_reachable(self) -> bool:
        """Fast local TCP check so a down Hindsight server does not slow responses."""
        parsed = urlparse(settings.hindsight_local_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        try:
            with socket.create_connection(
                (host, port),
                timeout=settings.hindsight_connect_timeout_seconds,
            ):
                return True
        except OSError:
            return False

    # ── Session counter (triggers periodic reflect) ──────────────────────

    def _load_session_counter(self) -> int:
        """
        Load the persisted session counter from disk.

        Returns:
            int: Number of sessions run so far, or 0 if file missing.
        """
        counter_path = Path(settings.hindsight_session_counter_file)
        try:
            if counter_path.exists():
                data = json.loads(counter_path.read_text(encoding="utf-8"))
                return int(data.get("count", 0))
        except Exception as e:
            logger.warning(f"[HINDSIGHT] Could not load session counter: {e}")
        return 0

    def _save_session_counter(self) -> None:
        """
        Persist the current session counter to disk.

        Creates parent directories if they do not exist.
        """
        counter_path = Path(settings.hindsight_session_counter_file)
        try:
            counter_path.parent.mkdir(parents=True, exist_ok=True)
            counter_path.write_text(
                json.dumps({"count": self._session_counter}),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"[HINDSIGHT] Could not save session counter: {e}")

    # ── Core operations ──────────────────────────────────────────────────

    async def retain(
        self,
        content: str,
        session_id: str,
    ) -> bool:
        """
        Store a conversation fact or summary into Hindsight memory.

        Formats the content with session context before storing so
        memories are traceable back to specific VEDA sessions.

        Args:
            content : Natural-language fact or summary to remember.
                      Example: "User prefers concise answers in Telugu."
            session_id: Current VEDA session identifier for traceability.

        Returns:
            bool: True if stored successfully, False on any failure.
        """
        if not self._enabled or self._client is None:
            return False

        if not await self._ensure_bank():
            return False

        enriched = f"[session:{session_id}] {content}"

        try:
            response = await asyncio.to_thread(
                self._client.retain,
                bank_id=self._bank_id,
                content=enriched,
                context=f"VEDA voice assistant session {session_id}",
                metadata={"session_id": session_id, "assistant": "veda"},
                tags=["veda", "conversation"],
            )
            success = bool(getattr(response, "success", response))
            logger.info(
                f"[HINDSIGHT] Retained | session={session_id} "
                f"| chars={len(enriched)} | success={success}"
            )
            return success

        except Exception as e:
            logger.error(
                f"[HINDSIGHT] retain() failed | session={session_id} | {e}",
                exc_info=True,
            )
            return False

    async def recall(
        self,
        query: str,
        session_id: str,
    ) -> list:
        """
        Retrieve semantically relevant memories for a given query.

        Called at the START of every VEDA turn so the LangGraph agent
        receives personalised context before generating a response.

        Args:
            query     : The user's current message or intent description.
            session_id: Current VEDA session identifier for logging.

        Returns:
            list: Up to hindsight_recall_top_k memory dicts, each
                  containing at minimum a 'content' key. Empty list
                  on failure so the agent always continues normally.
        """
        if not self._enabled or self._client is None:
            return []

        if not await self._ensure_bank():
            return []

        try:
            results = await asyncio.to_thread(
                self._client.recall,
                bank_id=self._bank_id,
                query=query,
                budget="mid",
                max_tokens=4096,
                include_source_facts=True,
            )
            memories = self._normalise_recall_results(results)
            memories = memories[:settings.hindsight_recall_top_k]
            logger.info(
                f"[HINDSIGHT] Recalled | session={session_id} "
                f"| query='{query[:60]}' | found={len(memories)}"
            )
            return memories

        except Exception as e:
            logger.warning(
                f"[HINDSIGHT] recall() failed | session={session_id} | {e}"
            )
            return []

    async def reflect(self, session_id: str) -> bool:
        """
        Trigger Hindsight's reflection pass to synthesise memories.

        Reflection consolidates raw retained facts into higher-order
        patterns (e.g. "User consistently asks about Python at night").
        This is called automatically every N sessions as configured.

        Args:
            session_id: Current session ID for logging context.

        Returns:
            bool: True if reflection succeeded, False otherwise.
        """
        if not self._enabled or self._client is None:
            return False

        if not await self._ensure_bank():
            return False

        try:
            response = await asyncio.to_thread(
                self._client.reflect,
                bank_id=self._bank_id,
                query=(
                    "What durable user preferences, goals, recurring topics, "
                    "and project context should VEDA remember for future help?"
                ),
                budget="low",
                max_tokens=500,
                include_facts=True,
            )
            reflected_text = getattr(response, "text", "")
            logger.info(
                f"[HINDSIGHT] Reflected | session={session_id} "
                f"| total_sessions={self._session_counter} "
                f"| chars={len(reflected_text)}"
            )
            return True

        except Exception as e:
            logger.error(
                f"[HINDSIGHT] reflect() failed | session={session_id} | {e}",
                exc_info=True,
            )
            return False

    # ── Session lifecycle ────────────────────────────────────────────────

    async def end_session(self, session_id: str) -> bool:
        """
        Increment the session counter and trigger reflect if threshold met.

        Call this at the END of every VEDA session (after retain). It
        automatically triggers reflect() every N sessions so memory
        stays consolidated without manual intervention.

        Args:
            session_id: Completed session ID for traceability.

        Returns:
            bool: True if reflect was triggered this session, False otherwise.
        """
        if not self._enabled or self._client is None:
            return False

        self._session_counter += 1
        self._save_session_counter()

        reflected = False
        if self._session_counter % settings.hindsight_reflect_every_n == 0:
            logger.info(
                f"[HINDSIGHT] Reflect threshold reached "
                f"(every {settings.hindsight_reflect_every_n} sessions) "
                f"| triggering reflect | session={session_id}"
            )
            reflected = await self.reflect(session_id)

        return reflected

    # ── Health check ─────────────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        """
        Ping the Hindsight server to verify it is reachable.

        Used by VedaHealthMonitor to include Hindsight in the
        30-second health check loop. Returns False gracefully if
        Hindsight is down — VEDA continues without memory.

        Returns:
            bool: True if server responds, False otherwise.
        """
        if not self._enabled or self._client is None:
            return False

        try:
            if not await self._ensure_bank():
                return False

            await asyncio.to_thread(
                self._client.recall,
                bank_id=self._bank_id,
                query="health_check_ping",
                budget="low",
                max_tokens=256,
            )
            return True
        except Exception:
            return False

    def _normalise_recall_results(self, response) -> list[dict]:
        """Convert Hindsight SDK response objects into simple dict memories."""
        if response is None:
            return []

        raw_results = response if isinstance(response, list) else getattr(response, "results", [])
        memories = []
        for item in raw_results or []:
            if isinstance(item, dict):
                data = dict(item)
            elif hasattr(item, "to_dict"):
                data = item.to_dict()
            elif hasattr(item, "model_dump"):
                data = item.model_dump(exclude_none=True)
            else:
                data = {"text": str(item)}

            text = data.get("text") or data.get("content") or ""
            if text:
                data["content"] = text
                memories.append(data)

        return memories


# Module-level singleton — import this everywhere
hindsight_store = VedaHindsightStore()
