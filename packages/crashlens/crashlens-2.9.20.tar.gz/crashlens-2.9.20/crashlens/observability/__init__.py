"""
CrashLens Observability Module

This module provides optional Prometheus metrics collection for monitoring
policy enforcement and token waste detection.

The metrics system is designed with these principles:
- Lazy loading: prometheus_client only imported when metrics are enabled
- Kill switch: CRASHLENS_DISABLE_METRICS=true disables all metrics
- Zero overhead: When disabled, no performance impact
- Cardinality protection: Limits on unique label values prevent explosion
- Fire-and-forget: Metric pushes never block CLI execution

Usage:
    from crashlens.observability import initialize_metrics, get_metrics
    
    # Initialize metrics (call once at CLI startup)
    metrics = initialize_metrics(enabled=True, max_rules=500)
    
    # Record metrics throughout execution
    if metrics:
        metrics.record_rule_hit('retry-loop', 'high', 'scan')
        metrics.record_violation('critical')
        metrics.update_run_timestamp('success')

Environment Variables:
    CRASHLENS_DISABLE_METRICS: Set to "true" to disable all metrics (highest precedence)

Installation:
    pip install crashlens[metrics]  # Installs with prometheus-client
    pip install crashlens           # Works without metrics support
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .metrics import CrashLensMetrics

# Module-level singleton
_metrics_instance: Optional["CrashLensMetrics"] = None


def initialize_metrics(
    enabled: bool = False, max_rules: int = 500, sample_rate: float = 1.0, per_rule_rates: Optional[dict] = None
) -> Optional["CrashLensMetrics"]:
    """
    Initialize the global metrics instance.

    This should be called once at CLI startup before any metric recording.

    Args:
        enabled: Whether to enable metrics collection
        max_rules: Maximum number of unique rule names before collapsing to overflow
        sample_rate: Global sampling probability (0.0-1.0, default: 1.0)
                    1.0 = record all metrics (100% sampling)
                    0.1 = record 10% of metrics (reduce overhead)
                    0.0 = record nothing (effectively disabled)
        per_rule_rates: Optional dict of rule_name -> sample_rate overrides
                       Allows different sampling rates for specific rules
                       Example: {"expensive_rule": 0.01, "rare_event": 1.0}

    Returns:
        CrashLensMetrics instance if enabled and available, None otherwise

    Raises:
        RuntimeError: If enabled=True but prometheus-client is not installed
        ValueError: If sample_rate is not between 0.0 and 1.0
    """
    from .metrics import _initialize_metrics_impl

    global _metrics_instance
    _metrics_instance = _initialize_metrics_impl(enabled, max_rules, sample_rate, per_rule_rates)
    return _metrics_instance


def get_metrics() -> Optional["CrashLensMetrics"]:
    """
    Get the global metrics instance.

    Returns:
        CrashLensMetrics instance if initialized and enabled, None otherwise

    Example:
        metrics = get_metrics()
        if metrics:
            metrics.record_rule_hit('my-rule', 'high', 'scan')
    """
    return _metrics_instance


__all__ = [
    "initialize_metrics",
    "get_metrics",
]
