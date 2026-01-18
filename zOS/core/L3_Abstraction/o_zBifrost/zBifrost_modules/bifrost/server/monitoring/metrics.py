# zCLI/subsystems/zBifrost/zBifrost_modules/bifrost/server/monitoring/metrics.py
"""
Phase 1: Prometheus Metrics for zBifrost Observability.

Provides basic metrics for monitoring zBifrost performance and health:
- Connection metrics (active, total, disconnects)
- Message metrics (received, sent, broadcasts)
- Latency histograms
- Error counters

These metrics are opt-in and only loaded if prometheus_client is available.
They expose at /metrics endpoint for Prometheus scraping.

Usage:
    from .monitoring.metrics import BifrostMetrics
    
    metrics = BifrostMetrics()  # Auto-detects if prometheus available
    
    if metrics.enabled:
        metrics.connection_opened()
        metrics.message_received()
        metrics.record_latency(duration_seconds)
"""

# Optional Prometheus dependency (graceful degradation)
try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False


class BifrostMetrics:
    """
    Optional Prometheus metrics for zBifrost.
    
    Gracefully degrades if prometheus_client not installed.
    All methods are no-ops if disabled.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize metrics collectors.
        
        Args:
            enabled: Whether to enable metrics (default: True if prometheus available)
        """
        self.enabled = enabled and _PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            return
        
        # Connection metrics
        self.active_connections = Gauge(
            'zbifrost_active_connections',
            'Number of active WebSocket connections'
        )
        
        self.total_connections = Counter(
            'zbifrost_total_connections',
            'Total connections since server start'
        )
        
        self.disconnections_total = Counter(
            'zbifrost_disconnections_total',
            'Total disconnections by reason',
            ['reason']  # normal, error, timeout, overflow
        )
        
        # Message metrics
        self.messages_received = Counter(
            'zbifrost_messages_received_total',
            'Total messages received from clients',
            ['event_type']  # execute_walker, form_submit, etc.
        )
        
        self.messages_sent = Counter(
            'zbifrost_messages_sent_total',
            'Total messages sent to clients',
            ['message_type']  # render_chunk, rbac_denied, etc.
        )
        
        self.broadcasts_total = Counter(
            'zbifrost_broadcasts_total',
            'Total broadcast operations'
        )
        
        # Latency metrics
        self.message_latency = Histogram(
            'zbifrost_message_latency_seconds',
            'Message processing latency',
            ['event_type'],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        self.walker_execution_latency = Histogram(
            'zbifrost_walker_execution_seconds',
            'Walker execution time',
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
        )
        
        # Error metrics
        self.errors_total = Counter(
            'zbifrost_errors_total',
            'Total errors by type',
            ['error_type']  # send_failed, handler_error, etc.
        )
        
        # Phase 1 optimization metrics
        self.schema_cache_hits = Counter(
            'zbifrost_schema_cache_hits_total',
            'DB connection reuse hits (Phase 1)'
        )
        
        self.schema_cache_misses = Counter(
            'zbifrost_schema_cache_misses_total',
            'DB connection cache misses (Phase 1)'
        )
    
    # Connection tracking
    def connection_opened(self):
        """Record a new connection."""
        if not self.enabled:
            return
        self.active_connections.inc()
        self.total_connections.inc()
    
    def connection_closed(self, reason: str = 'normal'):
        """
        Record a connection closure.
        
        Args:
            reason: Disconnect reason (normal, error, timeout, overflow)
        """
        if not self.enabled:
            return
        self.active_connections.dec()
        self.disconnections_total.labels(reason=reason).inc()
    
    def set_active_connections(self, count: int):
        """
        Set active connection count directly.
        
        Args:
            count: Current connection count
        """
        if not self.enabled:
            return
        self.active_connections.set(count)
    
    # Message tracking
    def message_received(self, event_type: str = 'unknown'):
        """
        Record a message received.
        
        Args:
            event_type: Event type (execute_walker, form_submit, etc.)
        """
        if not self.enabled:
            return
        self.messages_received.labels(event_type=event_type).inc()
    
    def message_sent(self, message_type: str = 'unknown'):
        """
        Record a message sent.
        
        Args:
            message_type: Message type (render_chunk, error, etc.)
        """
        if not self.enabled:
            return
        self.messages_sent.labels(message_type=message_type).inc()
    
    def broadcast_sent(self):
        """Record a broadcast operation."""
        if not self.enabled:
            return
        self.broadcasts_total.inc()
    
    # Latency tracking
    def record_message_latency(self, duration: float, event_type: str = 'unknown'):
        """
        Record message processing latency.
        
        Args:
            duration: Duration in seconds
            event_type: Event type
        """
        if not self.enabled:
            return
        self.message_latency.labels(event_type=event_type).observe(duration)
    
    def record_walker_latency(self, duration: float):
        """
        Record walker execution time.
        
        Args:
            duration: Duration in seconds
        """
        if not self.enabled:
            return
        self.walker_execution_latency.observe(duration)
    
    # Error tracking
    def record_error(self, error_type: str):
        """
        Record an error.
        
        Args:
            error_type: Error type (send_failed, handler_error, etc.)
        """
        if not self.enabled:
            return
        self.errors_total.labels(error_type=error_type).inc()
    
    # Phase 1 optimization tracking
    def schema_cache_hit(self):
        """Record a DB connection reuse (cache hit)."""
        if not self.enabled:
            return
        self.schema_cache_hits.inc()
    
    def schema_cache_miss(self):
        """Record a new DB connection (cache miss)."""
        if not self.enabled:
            return
        self.schema_cache_misses.inc()
    
    # Metrics export
    def generate_metrics(self) -> bytes:
        """
        Generate Prometheus metrics output.
        
        Returns:
            Metrics in Prometheus text format
        """
        if not self.enabled:
            return b"# Prometheus metrics disabled (prometheus_client not installed)\n"
        return generate_latest()
    
    @property
    def content_type(self) -> str:
        """Get Prometheus metrics content type."""
        if not self.enabled:
            return "text/plain"
        return CONTENT_TYPE_LATEST


# Singleton instance for global access
_metrics_instance = None

def get_metrics() -> BifrostMetrics:
    """
    Get singleton metrics instance.
    
    Returns:
        BifrostMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = BifrostMetrics()
    return _metrics_instance

