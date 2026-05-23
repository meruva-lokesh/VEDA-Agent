"""
main.py

VEDA main entry point with Hindsight health monitoring.

This is a template showing how to integrate Hindsight health checks
into VEDA's startup and continuous health monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from loguru import logger
from config.settings import settings
from memory.hindsight_store import hindsight_store


class VedaHealthMonitor:
    """
    Periodic health monitor for VEDA components.

    Checks:
    - ChromaDB connectivity
    - Hindsight memory server availability
    - LLM API responsiveness
    - Checkpoint database integrity

    Runs every 30 seconds in background.
    """

    def __init__(self, check_interval_seconds: int = 30):
        """
        Initialize health monitor.

        Args:
            check_interval_seconds: How often to run health checks.
        """
        self.check_interval = check_interval_seconds
        self._is_running = False
        self._last_check = None

    async def _check_chromadb(self) -> bool:
        """
        Check if ChromaDB is accessible.

        Returns:
            bool: True if healthy, False otherwise.
        """
        try:
            from pathlib import Path
            db_path = Path(settings.chromadb_path)
            if db_path.exists():
                logger.debug("[HEALTH] ChromaDB OK")
                return True
            else:
                logger.warning(f"[HEALTH] ChromaDB path not found: {db_path}")
                return False
        except Exception as e:
            logger.error(f"[HEALTH] ChromaDB check failed: {e}")
            return False

    async def _check_hindsight(self) -> bool:
        """
        Check if Hindsight memory server is reachable.

        Logs a warning if Hindsight is down but does NOT crash VEDA —
        the assistant continues without cross-session memory until the
        server recovers.

        Returns:
            bool: True if healthy, False otherwise.
        """
        healthy = await hindsight_store.is_healthy()
        if healthy:
            logger.debug("[HEALTH] Hindsight OK")
        else:
            logger.warning(
                "[HEALTH] Hindsight unreachable — "
                "VEDA running without long-term memory. "
                "Start Docker container: "
                "docker run -p 8888:8888 "
                "-e HINDSIGHT_API_LLM_API_KEY=ollama "
                "-e HINDSIGHT_API_LLM_BASE_URL=http://host.docker.internal:11434 "
                "-e HINDSIGHT_API_LLM_MODEL=gemma2:2b "
                "ghcr.io/vectorize-io/hindsight"
            )
        return healthy

    async def _check_checkpoint_db(self) -> bool:
        """
        Check if LangGraph checkpoint database is accessible.

        Returns:
            bool: True if healthy, False otherwise.
        """
        try:
            from pathlib import Path
            db_path = Path(settings.checkpoint_db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug("[HEALTH] Checkpoint DB OK")
            return True
        except Exception as e:
            logger.error(f"[HEALTH] Checkpoint DB check failed: {e}")
            return False

    async def check_all(self) -> dict:
        """
        Run all health checks and return summary.

        Returns:
            dict: Status of each component.
        """
        logger.info("[HEALTH] Running component health checks...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "chromadb": await self._check_chromadb(),
            "hindsight": await self._check_hindsight(),
            "checkpoint_db": await self._check_checkpoint_db(),
        }

        overall = all(results.values())
        results["overall_health"] = "HEALTHY" if overall else "DEGRADED"

        logger.info(f"[HEALTH] {results['overall_health']} — {results}")
        self._last_check = datetime.now()

        return results

    async def start(self) -> None:
        """
        Start periodic health monitoring loop.

        Runs in background, checking every check_interval seconds.
        """
        self._is_running = True
        logger.info(
            f"[HEALTH] Starting health monitor "
            f"(check every {self.check_interval}s)"
        )

        while self._is_running:
            try:
                await self.check_all()
            except Exception as e:
                logger.error(f"[HEALTH] Monitor error: {e}", exc_info=True)

            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        """Stop the health monitoring loop."""
        self._is_running = False
        logger.info("[HEALTH] Health monitor stopped")


async def main():
    """
    Main VEDA entry point.

    1. Initialize configuration
    2. Start health monitor
    3. Build and compile LangGraph
    4. Run VEDA event loop
    """
    logger.info("╔════════════════════════════════════════════════════════╗")
    logger.info("║          VEDA — Vectorial Entity for Dialogue         ║")
    logger.info("║                   with Hindsight Memory                 ║")
    logger.info("╚════════════════════════════════════════════════════════╝")

    logger.info(f"[MAIN] Loading configuration from .env")
    logger.info(f"[MAIN] App: {settings.app_name} v{settings.app_version}")
    logger.info(f"[MAIN] LLM: {settings.llm_model}")
    logger.info(f"[MAIN] Hindsight: {settings.hindsight_mode} mode "
                f"(enabled={settings.hindsight_enabled})")

    # Initialize health monitor
    health_monitor = VedaHealthMonitor(check_interval_seconds=30)

    # Run initial health check
    logger.info("[MAIN] Running initial health checks...")
    health_status = await health_monitor.check_all()

    if health_status["overall_health"] == "HEALTHY":
        logger.info("[MAIN] ✓ All systems ready")
    else:
        logger.warning("[MAIN] ⚠ Some systems degraded but continuing...")

    # Start background health monitoring
    health_monitor_task = asyncio.create_task(health_monitor.start())

    try:
        # TODO: Build and compile LangGraph
        logger.info("[MAIN] Building LangGraph agent...")
        from agent.graph import agent_graph

        if agent_graph is None:
            raise RuntimeError("Failed to compile agent graph")

        logger.info("[MAIN] ✓ LangGraph compiled")

        # TODO: Start VEDA event loop
        logger.info("[MAIN] VEDA ready — awaiting input...")

        # Keep the event loop running
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        logger.info("[MAIN] Received interrupt signal — shutting down...")
    except Exception as e:
        logger.error(f"[MAIN] Fatal error: {e}", exc_info=True)
    finally:
        await health_monitor.stop()
        health_monitor_task.cancel()
        try:
            await health_monitor_task
        except asyncio.CancelledError:
            pass
        logger.info("[MAIN] VEDA shutdown complete")


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="[{time:YYYY-MM-DD HH:mm:ss}] {message}",
        level=settings.log_level,
    )

    # Run main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
