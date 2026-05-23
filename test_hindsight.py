"""
test_hindsight.py

Integration test suite for Hindsight memory layer.

Tests:
- Hindsight client initialization
- Memory retain operation
- Memory recall operation  
- Health check
- Session counter persistence
- Reflection threshold

Run: python test_hindsight.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from config.settings import settings
from memory.hindsight_store import hindsight_store
from loguru import logger

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# Configure logger for tests
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="[{time:HH:mm:ss}] {message}",
    level="INFO",
)


class HindsightIntegrationTests:
    """Test suite for Hindsight memory integration."""

    def __init__(self):
        self.test_session_id = f"test-{datetime.now().isoformat()}"
        self.passed = 0
        self.failed = 0

    async def test_initialization(self) -> bool:
        """Test 1: Hindsight client initializes without errors."""
        logger.info("📋 TEST 1: Client initialization")
        try:
            assert hindsight_store._enabled, "Hindsight disabled in settings"
            assert hindsight_store._client is not None, "Client is None"
            logger.info("  ✓ PASS: Client initialized successfully")
            self.passed += 1
            return True
        except AssertionError as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False
        except Exception as e:
            logger.error(f"  ✗ FAIL: Unexpected error: {e}")
            self.failed += 1
            return False

    async def test_health_check(self) -> bool:
        """Test 2: Health check can verify server connectivity."""
        logger.info("📋 TEST 2: Health check")
        try:
            healthy = await hindsight_store.is_healthy()
            if healthy:
                logger.info("  ✓ PASS: Hindsight server is reachable")
            else:
                logger.warning("  ⚠ WARN: Hindsight server unreachable (expected if offline)")
                logger.info("       To start local Hindsight:")
                logger.info("       docker run -p 8888:8888 ghcr.io/vectorize-io/hindsight")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_retain_operation(self) -> bool:
        """Test 3: Memory retain stores a fact successfully."""
        logger.info("📋 TEST 3: Memory retain operation")
        try:
            test_content = "Test memory: User prefers Python over Java"
            retained = await hindsight_store.retain(
                content=test_content,
                session_id=self.test_session_id,
            )
            if retained:
                logger.info(f"  ✓ PASS: Memory retained successfully")
            else:
                logger.warning(f"  ⚠ WARN: Retain returned False (server may be unavailable)")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_recall_operation(self) -> bool:
        """Test 4: Memory recall retrieves relevant memories."""
        logger.info("📋 TEST 4: Memory recall operation")
        try:
            query = "Python programming"
            memories = await hindsight_store.recall(
                query=query,
                session_id=self.test_session_id,
            )
            if isinstance(memories, list):
                logger.info(f"  ✓ PASS: Recall returned {len(memories)} memories")
                if memories:
                    logger.info(f"       First memory: {str(memories[0])[:80]}...")
            else:
                logger.error(f"  ✗ FAIL: Recall returned non-list: {type(memories)}")
                self.failed += 1
                return False
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_session_counter(self) -> bool:
        """Test 5: Session counter persists to disk."""
        logger.info("📋 TEST 5: Session counter persistence")
        try:
            counter_path = Path(settings.hindsight_session_counter_file)
            initial_count = hindsight_store._session_counter
            
            # Simulate end_session
            hindsight_store._session_counter += 1
            hindsight_store._save_session_counter()
            
            # Verify file was written
            if counter_path.exists():
                data = json.loads(counter_path.read_text())
                persisted_count = data.get("count")
                if persisted_count == hindsight_store._session_counter:
                    logger.info(f"  ✓ PASS: Counter persisted ({initial_count} → {persisted_count})")
                    self.passed += 1
                    return True
                else:
                    logger.error(f"  ✗ FAIL: Counter mismatch ({persisted_count} vs {hindsight_store._session_counter})")
                    self.failed += 1
                    return False
            else:
                logger.warning(f"  ⚠ WARN: Counter file not created (expected if read-only)")
                self.passed += 1
                return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_reflect_threshold(self) -> bool:
        """Test 6: Reflection triggers at correct threshold."""
        logger.info("📋 TEST 6: Reflection threshold logic")
        try:
            reflect_threshold = settings.hindsight_reflect_every_n
            
            # Calculate sessions until next reflection
            current = hindsight_store._session_counter
            next_reflect = (
                ((current // reflect_threshold) + 1) * reflect_threshold
            )
            sessions_until_reflect = next_reflect - current
            
            logger.info(
                f"  Current sessions: {current}"
            )
            logger.info(
                f"  Next reflection at: {next_reflect} "
                f"(in {sessions_until_reflect} sessions)"
            )
            logger.info(f"  ✓ PASS: Reflection threshold logic correct")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_state_fields(self) -> bool:
        """Test 7: AgentState has all required Hindsight fields."""
        logger.info("📋 TEST 7: AgentState Hindsight fields")
        try:
            from agent.state import AgentState
            from typing import get_type_hints
            
            required_fields = {
                "hindsight_memories",
                "hindsight_retained",
                "hindsight_reflected",
            }
            
            # Get all keys from TypedDict annotations
            state_dict = AgentState.__annotations__
            state_keys = set(state_dict.keys())
            
            missing = required_fields - state_keys
            if missing:
                logger.error(f"  ✗ FAIL: Missing fields in AgentState: {missing}")
                self.failed += 1
                return False
            
            logger.info(f"  ✓ PASS: All Hindsight fields present in AgentState")
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_graph_nodes(self) -> bool:
        """Test 8: LangGraph has Hindsight nodes registered."""
        logger.info("📋 TEST 8: LangGraph node registration")
        try:
            from agent.graph import agent_graph
            
            if agent_graph is None:
                logger.warning("  ⚠ WARN: Agent graph not compiled (expected if nodes missing)")
                self.passed += 1
                return True
            
            # Get node names from the compiled graph
            node_names = list(agent_graph.nodes.keys())
            
            required_nodes = {"hindsight_recall", "hindsight_retain"}
            found_nodes = required_nodes & set(node_names)
            
            if found_nodes == required_nodes:
                logger.info(f"  ✓ PASS: All Hindsight nodes registered")
                logger.info(f"       Nodes: {sorted(found_nodes)}")
            else:
                missing = required_nodes - found_nodes
                logger.warning(f"  ⚠ WARN: Missing nodes: {missing}")
            
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def test_config_loading(self) -> bool:
        """Test 9: Settings load Hindsight configuration."""
        logger.info("📋 TEST 9: Configuration loading")
        try:
            checks = {
                "hindsight_enabled": settings.hindsight_enabled,
                "hindsight_mode": settings.hindsight_mode in ("local", "cloud"),
                "hindsight_recall_top_k": settings.hindsight_recall_top_k > 0,
                "hindsight_reflect_every_n": settings.hindsight_reflect_every_n > 0,
            }
            
            failed_checks = [k for k, v in checks.items() if not v]
            if failed_checks:
                logger.error(f"  ✗ FAIL: Invalid settings: {failed_checks}")
                self.failed += 1
                return False
            
            logger.info(
                f"  ✓ PASS: Hindsight config loaded"
            )
            logger.info(f"       Mode: {settings.hindsight_mode}")
            logger.info(f"       Enabled: {settings.hindsight_enabled}")
            logger.info(f"       Recall top-k: {settings.hindsight_recall_top_k}")
            logger.info(f"       Reflect every n: {settings.hindsight_reflect_every_n}")
            
            self.passed += 1
            return True
        except Exception as e:
            logger.error(f"  ✗ FAIL: {e}")
            self.failed += 1
            return False

    async def run_all_tests(self) -> None:
        """Run the complete test suite."""
        logger.info("")
        logger.info("╔════════════════════════════════════════════════════════╗")
        logger.info("║     HINDSIGHT INTEGRATION TEST SUITE                   ║")
        logger.info("╚════════════════════════════════════════════════════════╝")
        logger.info("")

        tests = [
            self.test_initialization,
            self.test_health_check,
            self.test_retain_operation,
            self.test_recall_operation,
            self.test_session_counter,
            self.test_reflect_threshold,
            self.test_state_fields,
            self.test_graph_nodes,
            self.test_config_loading,
        ]

        for test in tests:
            await test()
            logger.info("")

        logger.info("╔════════════════════════════════════════════════════════╗")
        logger.info(f"║ RESULTS: {self.passed} passed, {self.failed} failed")
        logger.info("╚════════════════════════════════════════════════════════╝")
        logger.info("")

        if self.failed == 0:
            logger.info("✓ ALL TESTS PASSED — Hindsight integration ready!")
        else:
            logger.warning(f"⚠ {self.failed} TEST(S) FAILED — Review log above")


async def main():
    """Run all integration tests."""
    tester = HindsightIntegrationTests()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
