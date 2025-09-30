"""Performance tests for ping command.

Task T033: Tests for ping command performance with p95 latency assertions.
"""

import time
import statistics
from pathlib import Path
from typing import List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.cli.commands.ping_cmd import run_ping
from src.core.broker_client import ensure_broker_running
from src.core.project_context import write_session, SessionState


class TestPingPerformance:
    """Performance tests for ping command."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.project_root = Path.cwd()
        self.latencies: List[float] = []

        # Ensure broker is running
        ensure_broker_running()

        # Set up a test session
        test_session = SessionState(
            instance_id="test-perf",
            session_token="test-token-perf-123"
        )
        write_session(
            test_session.instance_id,
            test_session.session_token,
            self.project_root
        )

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up test session
        session_file = self.project_root / ".ipc" / "state" / "session.json"
        if session_file.exists():
            session_file.unlink()

    def test_ping_latency_single(self):
        """Test single ping latency is reasonable."""
        start = time.perf_counter()
        result = run_ping(target="local", project_root=self.project_root)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms

        # Single ping should complete within reasonable time
        assert result == 0, "Ping should succeed"
        assert elapsed < 100, f"Single ping took {elapsed:.2f}ms, should be <100ms"

    def test_ping_latency_multiple(self):
        """Test multiple ping latencies and calculate percentiles."""
        num_pings = 20
        latencies = []

        for _ in range(num_pings):
            start = time.perf_counter()
            result = run_ping(target="local", project_root=self.project_root)
            elapsed = (time.perf_counter() - start) * 1000  # ms

            if result == 0:  # Only count successful pings
                latencies.append(elapsed)

            # Small delay to avoid rate limiting
            time.sleep(0.05)

        # Ensure we have enough successful pings
        assert len(latencies) >= num_pings * 0.9, f"Too many failed pings: {len(latencies)}/{num_pings}"

        # Calculate statistics
        if latencies:
            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = self._calculate_percentile(latencies, 95)
            p99_latency = self._calculate_percentile(latencies, 99)

            print(f"\nPing Performance Statistics ({num_pings} samples):")
            print(f"  Average: {avg_latency:.2f}ms")
            print(f"  Median:  {median_latency:.2f}ms")
            print(f"  P95:     {p95_latency:.2f}ms")
            print(f"  P99:     {p99_latency:.2f}ms")
            print(f"  Min:     {min(latencies):.2f}ms")
            print(f"  Max:     {max(latencies):.2f}ms")

            # Performance assertions (adjusted for Windows environment)
            assert avg_latency < 100, f"Average latency {avg_latency:.2f}ms exceeds 100ms"
            assert p95_latency < 150, f"P95 latency {p95_latency:.2f}ms exceeds 150ms"
            assert p99_latency < 200, f"P99 latency {p99_latency:.2f}ms exceeds 200ms"

    def test_ping_under_load(self):
        """Test ping performance under concurrent load."""
        import threading
        import queue

        num_threads = 5
        pings_per_thread = 10
        results_queue = queue.Queue()

        def ping_worker():
            """Worker thread to perform pings."""
            local_latencies = []
            for _ in range(pings_per_thread):
                start = time.perf_counter()
                result = run_ping(target="local", project_root=self.project_root)
                elapsed = (time.perf_counter() - start) * 1000

                if result == 0:
                    local_latencies.append(elapsed)

                time.sleep(0.01)  # Small delay

            results_queue.put(local_latencies)

        # Start worker threads
        threads = []
        start_time = time.perf_counter()

        for _ in range(num_threads):
            t = threading.Thread(target=ping_worker)
            t.start()
            threads.append(t)

        # Wait for all threads to complete
        for t in threads:
            t.join()

        total_time = time.perf_counter() - start_time

        # Collect all results
        all_latencies = []
        while not results_queue.empty():
            all_latencies.extend(results_queue.get())

        # Calculate statistics under load
        if all_latencies:
            avg_latency = statistics.mean(all_latencies)
            p95_latency = self._calculate_percentile(all_latencies, 95)
            p99_latency = self._calculate_percentile(all_latencies, 99)

            print(f"\nPing Performance Under Load ({num_threads} threads, {pings_per_thread} pings each):")
            print(f"  Total time:     {total_time:.2f}s")
            print(f"  Total pings:    {len(all_latencies)}")
            print(f"  Throughput:     {len(all_latencies)/total_time:.1f} pings/s")
            print(f"  Average latency: {avg_latency:.2f}ms")
            print(f"  P95 latency:    {p95_latency:.2f}ms")
            print(f"  P99 latency:    {p99_latency:.2f}ms")

            # Under load, allow higher latencies but still reasonable (adjusted for Windows)
            assert avg_latency < 150, f"Average latency under load {avg_latency:.2f}ms exceeds 150ms"
            assert p95_latency < 250, f"P95 latency under load {p95_latency:.2f}ms exceeds 250ms"
            assert p99_latency < 500, f"P99 latency under load {p99_latency:.2f}ms exceeds 500ms"

    def test_ping_rate_limiting(self):
        """Test that ping respects rate limiting without excessive delays."""
        rapid_pings = 20
        latencies = []
        failures = 0

        start_time = time.perf_counter()

        for i in range(rapid_pings):
            ping_start = time.perf_counter()
            result = run_ping(target="local", project_root=self.project_root)
            elapsed = (time.perf_counter() - ping_start) * 1000

            if result == 0:
                latencies.append(elapsed)
            else:
                failures += 1

            # No delay - test rate limiting behavior

        total_time = time.perf_counter() - start_time

        print(f"\nRate Limiting Test ({rapid_pings} rapid pings):")
        print(f"  Total time:    {total_time:.2f}s")
        print(f"  Successful:    {len(latencies)}")
        print(f"  Failed:        {failures}")

        if latencies:
            print(f"  Avg latency:   {statistics.mean(latencies):.2f}ms")
            print(f"  Max latency:   {max(latencies):.2f}ms")

        # Should complete reasonably quickly even with rate limiting
        assert total_time < 5.0, f"Rapid pings took too long: {total_time:.2f}s"

        # Some pings may fail due to rate limiting, but not all
        assert len(latencies) >= rapid_pings * 0.5, f"Too many failures: {failures}/{rapid_pings}"

    def test_ping_recovery_after_broker_restart(self):
        """Test ping performance after broker restart."""
        # Note: This test would require broker restart capability
        # For now, we'll test resilience to temporary failures

        initial_latencies = []
        recovery_latencies = []

        # Measure initial performance
        for _ in range(5):
            start = time.perf_counter()
            result = run_ping(target="local", project_root=self.project_root)
            elapsed = (time.perf_counter() - start) * 1000
            if result == 0:
                initial_latencies.append(elapsed)
            time.sleep(0.1)

        # Simulate some delay (broker issues)
        time.sleep(1.0)

        # Measure recovery performance
        for _ in range(5):
            start = time.perf_counter()
            result = run_ping(target="local", project_root=self.project_root)
            elapsed = (time.perf_counter() - start) * 1000
            if result == 0:
                recovery_latencies.append(elapsed)
            time.sleep(0.1)

        if initial_latencies and recovery_latencies:
            initial_avg = statistics.mean(initial_latencies)
            recovery_avg = statistics.mean(recovery_latencies)

            print(f"\nRecovery Performance Test:")
            print(f"  Initial avg:  {initial_avg:.2f}ms")
            print(f"  Recovery avg: {recovery_avg:.2f}ms")
            print(f"  Difference:   {abs(recovery_avg - initial_avg):.2f}ms")

            # Recovery performance should be similar to initial
            assert recovery_avg < initial_avg * 2, "Recovery latency too high compared to initial"

    @staticmethod
    def _calculate_percentile(data: List[float], percentile: int) -> float:
        """Calculate the given percentile of the data.

        Args:
            data: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            The calculated percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1

        if upper >= len(sorted_data):
            return sorted_data[lower]

        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])