#!/usr/bin/env python3
"""
Enhanced Debug Monitor for FlowProcessor
Real-time monitoring and debugging capabilities.
"""

import os
import sys
import time
import psutil
import logging
import threading
import gc
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from flowproc.logging_config import setup_logging
    from flowproc.infrastructure.monitoring.health import health_checker
    from flowproc.application.handlers.error_handler import _error_handler
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root with venv activated")
    sys.exit(1)

class DebugMonitor:
    """Real-time debug monitor for FlowProcessor."""
    
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self.monitoring = False
        self.monitor_thread = None
        self.start_time = None
        self.metrics = {
            'memory_usage': [],
            'cpu_usage': [],
            'error_count': 0,
            'warning_count': 0,
            'processing_events': []
        }
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self) -> None:
        """Start the debug monitoring."""
        if self.monitoring:
            self.logger.warning("Monitoring already active")
            return
            
        self.monitoring = True
        self.start_time = time.time()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Debug monitoring started")
        
    def stop_monitoring(self) -> None:
        """Stop the debug monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Debug monitoring stopped")
        
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self._collect_metrics()
                self._check_system_health()
                self._check_error_history()
                self._log_status()
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.interval)
                
    def _collect_metrics(self) -> None:
        """Collect system metrics."""
        process = psutil.Process()
        
        # Memory usage
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        self.metrics['memory_usage'].append({
            'timestamp': time.time(),
            'memory_mb': memory_mb,
            'percent': process.memory_percent()
        })
        
        # CPU usage
        cpu_percent = process.cpu_percent()
        self.metrics['cpu_usage'].append({
            'timestamp': time.time(),
            'cpu_percent': cpu_percent
        })
        
        # Keep only last 100 entries
        for key in ['memory_usage', 'cpu_usage']:
            if len(self.metrics[key]) > 100:
                self.metrics[key] = self.metrics[key][-100:]
                
    def _check_system_health(self) -> None:
        """Check system health status."""
        try:
            health_status = health_checker.check_system_health()
            if health_status['status'] != 'healthy':
                self.logger.warning(f"System health issue: {health_status}")
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            
    def _check_error_history(self) -> None:
        """Check for new errors in error handler."""
        try:
            error_history = _error_handler.get_error_history()
            current_count = len(error_history)
            
            if current_count > self.metrics['error_count']:
                new_errors = current_count - self.metrics['error_count']
                self.logger.warning(f"New errors detected: {new_errors}")
                
                # Log recent errors
                for error in error_history[-new_errors:]:
                    self.logger.error(f"Recent error: {error['error_type']}: {error['error_message']}")
                    
            self.metrics['error_count'] = current_count
            
        except Exception as e:
            self.logger.error(f"Error checking error history: {e}")
            
    def _log_status(self) -> None:
        """Log current status."""
        if not self.metrics['memory_usage']:
            return
            
        latest_memory = self.metrics['memory_usage'][-1]
        latest_cpu = self.metrics['cpu_usage'][-1]
        
        runtime = time.time() - self.start_time if self.start_time else 0
        
        self.logger.debug(
            f"Status - Runtime: {runtime:.1f}s, "
            f"Memory: {latest_memory['memory_mb']:.1f}MB ({latest_memory['percent']:.1f}%), "
            f"CPU: {latest_cpu['cpu_percent']:.1f}%, "
            f"Errors: {self.metrics['error_count']}"
        )
        
    def get_summary(self) -> Dict:
        """Get monitoring summary."""
        if not self.metrics['memory_usage']:
            return {'status': 'No data collected'}
            
        memory_data = self.metrics['memory_usage']
        cpu_data = self.metrics['cpu_usage']
        
        return {
            'runtime_seconds': time.time() - self.start_time if self.start_time else 0,
            'memory_avg_mb': sum(m['memory_mb'] for m in memory_data) / len(memory_data),
            'memory_max_mb': max(m['memory_mb'] for m in memory_data),
            'cpu_avg_percent': sum(c['cpu_percent'] for c in cpu_data) / len(cpu_data),
            'cpu_max_percent': max(c['cpu_percent'] for c in cpu_data),
            'error_count': self.metrics['error_count'],
            'warning_count': self.metrics['warning_count']
        }
        
    def print_summary(self) -> None:
        """Print monitoring summary."""
        summary = self.get_summary()
        print("\n" + "="*60)
        print("FLOWPROCESSOR DEBUG MONITOR SUMMARY")
        print("="*60)
        
        if summary['status'] == 'No data collected':
            print("No monitoring data available")
            return
            
        print(f"Runtime: {summary['runtime_seconds']:.1f} seconds")
        print(f"Memory Usage: {summary['memory_avg_mb']:.1f}MB avg, {summary['memory_max_mb']:.1f}MB max")
        print(f"CPU Usage: {summary['cpu_avg_percent']:.1f}% avg, {summary['cpu_max_percent']:.1f}% max")
        print(f"Errors Detected: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")
        print("="*60)

def setup_enhanced_logging() -> None:
    """Setup enhanced logging for debugging."""
    # Create debug log file
    debug_log_path = Path("debug.log")
    
    # Configure debug logger
    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)
    
    # File handler for debug logs
    file_handler = logging.FileHandler(debug_log_path, mode='w')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for debug logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    debug_logger.addHandler(file_handler)
    debug_logger.addHandler(console_handler)
    
    print(f"Debug logging enabled - logs saved to: {debug_log_path.absolute()}")

def run_application_with_monitoring() -> None:
    """Run the application with debug monitoring."""
    print("Starting FlowProcessor with enhanced debugging...")
    
    # Setup enhanced logging
    setup_enhanced_logging()
    
    # Create and start monitor
    monitor = DebugMonitor(interval=2.0)
    monitor.start_monitoring()
    
    try:
        # Import and run the application
        from flowproc.presentation.gui import create_gui
        print("Launching GUI application...")
        create_gui()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        traceback.print_exc()
    finally:
        # Stop monitoring and print summary
        monitor.stop_monitoring()
        monitor.print_summary()
        
        # Force garbage collection
        gc.collect()
        print("Debug monitoring completed")

def run_health_check() -> None:
    """Run comprehensive health check."""
    print("Running comprehensive health check...")
    
    try:
        import sys
        import os
        # Add the debug directory to the path
        debug_dir = os.path.dirname(os.path.abspath(__file__))
        if debug_dir not in sys.path:
            sys.path.insert(0, debug_dir)
        
        from system_health_check import SystemHealthChecker
        checker = SystemHealthChecker(str(Path(__file__).parent))
        results = checker.run_all_checks()
        
        print("\nHealth Check Results:")
        for key, value in results.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Health check failed: {e}")
        traceback.print_exc()

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "health":
            run_health_check()
        elif command == "monitor":
            run_application_with_monitoring()
        else:
            print("Usage:")
            print("  python debug_monitor.py health    - Run health check")
            print("  python debug_monitor.py monitor   - Run app with monitoring")
    else:
        # Default: run with monitoring
        run_application_with_monitoring()

if __name__ == "__main__":
    main() 