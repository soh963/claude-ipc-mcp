#!/usr/bin/env python3
"""
Metrics Collector for Unified IPC System
Gemini's implementation - Real-time performance monitoring and security event tracking
"""

import time
import json
import threading
from typing import Dict, List, Any, Optional, Deque, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import statistics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    type: str = 'gauge'  # gauge, counter, histogram


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    name: str
    count: int
    mean: float
    median: float
    min: float
    max: float
    std_dev: float
    p95: float
    p99: float


class TimeSeries:
    """Time series data storage with sliding window"""

    def __init__(self, window_size: int = 3600, max_points: int = 10000):
        self.window_size = window_size  # seconds
        self.max_points = max_points
        self.data: Deque[Tuple[float, float]] = deque(maxlen=max_points)
        self.lock = threading.Lock()

    def add(self, value: float, timestamp: float = None):
        """Add a data point"""
        if timestamp is None:
            timestamp = time.time()

        with self.lock:
            self.data.append((timestamp, value))
            self._cleanup_old()

    def _cleanup_old(self):
        """Remove data points outside the window"""
        cutoff = time.time() - self.window_size

        while self.data and self.data[0][0] < cutoff:
            self.data.popleft()

    def get_series(self, duration: int = None) -> List[Tuple[float, float]]:
        """Get time series data"""
        with self.lock:
            if duration is None:
                return list(self.data)

            cutoff = time.time() - duration
            return [(t, v) for t, v in self.data if t >= cutoff]

    def get_summary(self) -> Optional[Dict]:
        """Get summary statistics"""
        with self.lock:
            if not self.data:
                return None

            values = [v for _, v in self.data]

            return {
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0
            }


class MetricRegistry:
    """Registry for all metrics"""

    def __init__(self):
        self.metrics: Dict[str, TimeSeries] = {}
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.lock = threading.Lock()

    def record_gauge(self, name: str, value: float, tags: Dict = None):
        """Record a gauge metric (current value)"""
        with self.lock:
            self.gauges[name] = value

            if name not in self.metrics:
                self.metrics[name] = TimeSeries()

            self.metrics[name].add(value)

    def record_counter(self, name: str, value: float = 1, tags: Dict = None):
        """Record a counter metric (cumulative)"""
        with self.lock:
            self.counters[name] += value

    def record_histogram(self, name: str, value: float, tags: Dict = None):
        """Record a histogram metric (distribution)"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = TimeSeries()

            self.metrics[name].add(value)

    def get_metric(self, name: str) -> Optional[Dict]:
        """Get metric data"""
        with self.lock:
            if name in self.gauges:
                return {'type': 'gauge', 'value': self.gauges[name]}

            if name in self.counters:
                return {'type': 'counter', 'value': self.counters[name]}

            if name in self.metrics:
                return {
                    'type': 'histogram',
                    'summary': self.metrics[name].get_summary()
                }

            return None

    def get_all_metrics(self) -> Dict:
        """Get all metrics"""
        with self.lock:
            result = {
                'gauges': dict(self.gauges),
                'counters': dict(self.counters),
                'histograms': {}
            }

            for name, series in self.metrics.items():
                summary = series.get_summary()
                if summary:
                    result['histograms'][name] = summary

            return result


class PerformanceMonitor:
    """Monitor system and application performance"""

    def __init__(self, registry: MetricRegistry):
        self.registry = registry
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None

    def start(self):
        """Start performance monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop(self):
        """Stop performance monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        import psutil

        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.registry.record_gauge('system.cpu.percent', cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.registry.record_gauge('system.memory.percent', memory.percent)
                self.registry.record_gauge('system.memory.available', memory.available)

                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.registry.record_counter('system.disk.read_bytes', disk_io.read_bytes)
                    self.registry.record_counter('system.disk.write_bytes', disk_io.write_bytes)

                # Network I/O
                net_io = psutil.net_io_counters()
                if net_io:
                    self.registry.record_counter('system.network.bytes_sent', net_io.bytes_sent)
                    self.registry.record_counter('system.network.bytes_recv', net_io.bytes_recv)

                # Process specific
                process = psutil.Process()
                self.registry.record_gauge('process.cpu.percent', process.cpu_percent())
                self.registry.record_gauge('process.memory.rss', process.memory_info().rss)
                self.registry.record_gauge('process.threads', process.num_threads())

                time.sleep(10)  # Monitor every 10 seconds

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(10)


class SecurityEventTracker:
    """Track security-related events"""

    def __init__(self, registry: MetricRegistry):
        self.registry = registry
        self.events: Deque[Dict] = deque(maxlen=1000)
        self.lock = threading.Lock()

    def track_authentication(self, success: bool, method: str = 'password'):
        """Track authentication attempts"""
        if success:
            self.registry.record_counter('security.auth.success')
        else:
            self.registry.record_counter('security.auth.failure')

        event = {
            'type': 'authentication',
            'success': success,
            'method': method,
            'timestamp': time.time()
        }

        with self.lock:
            self.events.append(event)

    def track_authorization(self, granted: bool, resource: str, action: str):
        """Track authorization decisions"""
        if granted:
            self.registry.record_counter('security.authz.granted')
        else:
            self.registry.record_counter('security.authz.denied')

        event = {
            'type': 'authorization',
            'granted': granted,
            'resource': resource,
            'action': action,
            'timestamp': time.time()
        }

        with self.lock:
            self.events.append(event)

    def track_violation(self, violation_type: str, details: str):
        """Track security violations"""
        self.registry.record_counter(f'security.violation.{violation_type}')

        event = {
            'type': 'violation',
            'violation_type': violation_type,
            'details': details,
            'timestamp': time.time()
        }

        with self.lock:
            self.events.append(event)

    def get_recent_events(self, count: int = 100) -> List[Dict]:
        """Get recent security events"""
        with self.lock:
            return list(self.events)[-count:]


class ApplicationMetrics:
    """Application-specific metrics"""

    def __init__(self, registry: MetricRegistry):
        self.registry = registry

    def track_message(self, msg_type: str, size: int, latency: float):
        """Track message metrics"""
        self.registry.record_counter(f'messages.{msg_type}.count')
        self.registry.record_histogram(f'messages.{msg_type}.size', size)
        self.registry.record_histogram(f'messages.{msg_type}.latency', latency)

    def track_connection(self, connected: bool, connection_type: str = 'tcp'):
        """Track connection metrics"""
        if connected:
            self.registry.record_counter(f'connections.{connection_type}.established')
        else:
            self.registry.record_counter(f'connections.{connection_type}.closed')

        self.registry.record_gauge(
            f'connections.{connection_type}.active',
            self.registry.counters.get(f'connections.{connection_type}.established', 0) -
            self.registry.counters.get(f'connections.{connection_type}.closed', 0)
        )

    def track_error(self, error_type: str, component: str):
        """Track application errors"""
        self.registry.record_counter(f'errors.{component}.{error_type}')

    def track_queue_size(self, queue_name: str, size: int):
        """Track queue sizes"""
        self.registry.record_gauge(f'queues.{queue_name}.size', size)


class MetricsCollector:
    """Main metrics collector integrating all monitoring components"""

    def __init__(self, export_path: Path = None):
        self.export_path = export_path or Path.home() / '.claude-ipc-data' / 'metrics'
        self.export_path.mkdir(parents=True, exist_ok=True)

        # Core components
        self.registry = MetricRegistry()
        self.performance = PerformanceMonitor(self.registry)
        self.security = SecurityEventTracker(self.registry)
        self.application = ApplicationMetrics(self.registry)

        # Export settings
        self.export_interval = 60  # seconds
        self.export_thread: Optional[threading.Thread] = None
        self.running = False

        logger.info("Metrics Collector initialized")

    def start(self):
        """Start metrics collection"""
        self.running = True

        # Start performance monitoring
        self.performance.start()

        # Start export thread
        self.export_thread = threading.Thread(target=self._export_loop, daemon=True)
        self.export_thread.start()

        logger.info("Metrics collection started")

    def stop(self):
        """Stop metrics collection"""
        self.running = False

        # Stop performance monitoring
        self.performance.stop()

        # Stop export thread
        if self.export_thread:
            self.export_thread.join(timeout=5)

        # Final export
        self._export_metrics()

        logger.info("Metrics collection stopped")

    def _export_loop(self):
        """Periodically export metrics"""
        while self.running:
            time.sleep(self.export_interval)
            self._export_metrics()

    def _export_metrics(self):
        """Export metrics to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.export_path / f'metrics_{timestamp}.json'

            metrics = {
                'timestamp': time.time(),
                'metrics': self.registry.get_all_metrics(),
                'security_events': self.security.get_recent_events(100)
            }

            with open(filename, 'w') as f:
                json.dump(metrics, f, indent=2)

            logger.debug(f"Metrics exported to {filename}")

            # Cleanup old exports (keep last 24 hours)
            self._cleanup_old_exports()

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

    def _cleanup_old_exports(self):
        """Remove old metric exports"""
        cutoff = time.time() - 86400  # 24 hours

        for file in self.export_path.glob('metrics_*.json'):
            if file.stat().st_mtime < cutoff:
                file.unlink()

    def collect_metrics(self, request: Dict, response: Dict):
        """Hook for broker to collect metrics"""
        start_time = request.get('_start_time', time.time())
        latency = time.time() - start_time

        # Track message metrics
        msg_type = request.get('type', 'unknown')
        size = len(json.dumps(request))

        self.application.track_message(msg_type, size, latency)

        # Track errors
        if response.get('status') == 'error':
            self.application.track_error('request_failed', msg_type)

    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard display"""
        return {
            'metrics': self.registry.get_all_metrics(),
            'security': {
                'recent_events': self.security.get_recent_events(20),
                'auth_success': self.registry.counters.get('security.auth.success', 0),
                'auth_failure': self.registry.counters.get('security.auth.failure', 0)
            },
            'application': {
                'total_messages': sum(v for k, v in self.registry.counters.items() if k.startswith('messages.')),
                'active_connections': self.registry.gauges.get('connections.tcp.active', 0),
                'error_count': sum(v for k, v in self.registry.counters.items() if k.startswith('errors.'))
            },
            'timestamp': time.time()
        }


def main():
    """Test metrics collector"""
    collector = MetricsCollector()

    # Start collection
    collector.start()

    # Simulate some metrics
    for i in range(10):
        # Track messages
        collector.application.track_message('send', 1024, 0.05)
        collector.application.track_message('receive', 512, 0.03)

        # Track connections
        collector.application.track_connection(True, 'tcp')

        # Track security
        collector.security.track_authentication(True)

        time.sleep(1)

    # Get dashboard data
    dashboard = collector.get_dashboard_data()
    print(json.dumps(dashboard, indent=2))

    # Stop collection
    collector.stop()


if __name__ == "__main__":
    main()