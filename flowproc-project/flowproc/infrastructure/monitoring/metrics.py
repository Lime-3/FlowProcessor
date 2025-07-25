"""
Performance metrics and monitoring for flow cytometry processing.
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and manages performance metrics."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        
    def start_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking an operation.
        
        Args:
            operation_name: Name of the operation
            metadata: Additional metadata
            
        Returns:
            Operation ID for tracking
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metric)
        
        logger.debug(f"Started tracking operation: {operation_id}")
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, 
                     error_message: Optional[str] = None) -> None:
        """
        End tracking an operation.
        
        Args:
            operation_id: Operation ID from start_operation
            success: Whether the operation was successful
            error_message: Error message if operation failed
        """
        with self._lock:
            # Find the metric by operation name and start time
            for metric in self.metrics:
                if metric.end_time is None:  # Not yet ended
                    metric.end_time = time.time()
                    metric.duration = metric.end_time - metric.start_time
                    metric.success = success
                    metric.error_message = error_message
                    
                    # Collect system metrics
                    metric.memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
                    metric.cpu_usage_percent = psutil.cpu_percent()
                    
                    logger.debug(f"Ended tracking operation: {operation_id}")
                    break
    
    def get_metrics(self, operation_name: Optional[str] = None) -> List[PerformanceMetrics]:
        """
        Get collected metrics.
        
        Args:
            operation_name: Filter by operation name
            
        Returns:
            List of performance metrics
        """
        with self._lock:
            if operation_name:
                return [m for m in self.metrics if m.operation_name == operation_name]
            return self.metrics.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of collected metrics."""
        with self._lock:
            if not self.metrics:
                return {}
            
            completed_metrics = [m for m in self.metrics if m.end_time is not None]
            
            if not completed_metrics:
                return {}
            
            durations = [m.duration for m in completed_metrics if m.duration is not None]
            memory_usage = [m.memory_usage_mb for m in completed_metrics if m.memory_usage_mb is not None]
            cpu_usage = [m.cpu_usage_percent for m in completed_metrics if m.cpu_usage_percent is not None]
            
            summary = {
                'total_operations': len(self.metrics),
                'completed_operations': len(completed_metrics),
                'successful_operations': len([m for m in completed_metrics if m.success]),
                'failed_operations': len([m for m in completed_metrics if not m.success]),
                'average_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'average_memory_usage_mb': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'average_cpu_usage_percent': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0
            }
            
            return summary
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self.metrics.clear()
            logger.info("Cleared all performance metrics")


class SystemMonitor:
    """Monitors system resources."""
    
    def __init__(self):
        """Initialize the system monitor."""
        self._monitoring = False
        self._monitor_thread = None
        self.metrics_history: List[Dict[str, Any]] = []
        
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start system monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            logger.warning("System monitoring already started")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.info("Started system monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
        logger.info("Stopped system monitoring")
    
    def _monitor_loop(self, interval: float) -> None:
        """Monitoring loop."""
        while self._monitoring:
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 entries
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used / (1024 * 1024),
            'memory_available_mb': psutil.virtual_memory().available / (1024 * 1024),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'disk_free_gb': psutil.disk_usage('/').free / (1024 * 1024 * 1024)
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self._collect_system_metrics()
    
    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get metrics history."""
        return self.metrics_history.copy()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of metrics history."""
        if not self.metrics_history:
            return {}
        
        cpu_values = [m['cpu_percent'] for m in self.metrics_history]
        memory_values = [m['memory_percent'] for m in self.metrics_history]
        
        return {
            'total_samples': len(self.metrics_history),
            'average_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'min_cpu_percent': min(cpu_values),
            'average_memory_percent': sum(memory_values) / len(memory_values),
            'max_memory_percent': max(memory_values),
            'min_memory_percent': min(memory_values),
            'monitoring_duration_seconds': len(self.metrics_history)
        }


# Global instances
metrics_collector = MetricsCollector()
system_monitor = SystemMonitor() 